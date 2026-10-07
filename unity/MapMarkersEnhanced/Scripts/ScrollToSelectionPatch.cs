using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Scrolls the marker dialog's icon and variant rows so the selected tiles are
    /// visible when the dialog opens for an existing preset.
    /// <c>MapMarkerCustomizationPanel.Open</c> scrolls both rows to their start, and
    /// since <see cref="IconOrderPatch"/> puts the mod's icons behind vanilla's, a
    /// preset using one of them opened with its icon (and often its variant) out of
    /// view. This 8-parameter overload is the only one the game calls (from
    /// <c>MapUI</c>); it reaches the 5-parameter one, which always selects the first
    /// icon, only through itself.
    /// <para>
    /// The scroll cannot happen in the postfix: <c>ScrollableUIComponent</c> learns
    /// its content (<c>child</c>) and its <c>scrollableExtent</c> only in its own
    /// <c>LateUpdate</c>. Before the first one <c>ScrollTo</c> does nothing, and after
    /// a row was rebuilt — the variant row is, for every icon — it clamps to the old
    /// row's extent. So the postfix records the request and <see cref="Tick"/>, called
    /// from <c>IMod.Update</c>, carries it out on the following frames.
    /// </para>
    /// <para>
    /// When the selection is one of the mod's icons, a dialog whose selected tile or
    /// enclosing <c>ScrollableUIComponent</c> cannot be found is warned about once per
    /// session: that is a changed UI hierarchy, and the icon would open out of view
    /// again. A tile that is merely inactive, or a panel closed before the scroll,
    /// stays silent.
    /// </para>
    /// </summary>
    [HarmonyPatch(
        typeof(MapMarkerCustomizationPanel),
        "Open",
        new[]
        {
            typeof(DataBlockAddress),
            typeof(int),
            typeof(string),
            typeof(MapMarkerPreset),
            typeof(Action<DataBlockAddress, int, string>),
            typeof(Action),
            typeof(string),
            typeof(string),
        }
    )]
    internal static class ScrollToSelectionPatch
    {
        /// <summary>
        /// Frames after <c>Open</c> on which the scroll is applied. Two rather than one:
        /// if the scrollable's <c>LateUpdate</c> has not run between <c>Open</c> and the
        /// first <see cref="Tick"/>, that attempt is a no-op or clamped to a stale extent,
        /// and the second one lands. Applying it twice is harmless — a tile already in
        /// view does not move.
        /// </summary>
        private const int FramesToApply = 2;

        private static MapMarkerCustomizationPanel s_panel;
        private static UIelement s_iconTile;
        private static UIelement s_variantTile;
        private static int s_openFrame;
        private static bool s_modSelection;

        private static bool s_warningLogged;
        private static bool s_tileMissingLogged;
        private static bool s_scrollableMissingLogged;

        [HarmonyPostfix]
        private static void Postfix(
            MapMarkerCustomizationPanel __instance,
            DataBlockAddress iconAddress,
            List<ToggleUIElement> ____iconOptions,
            List<DataBlockAddress> ____iconAddresses,
            List<MapMarkerColorToggleElement> ____variantOptions,
            int ____selectedVariantIndex
        )
        {
            try
            {
                Clear();

                UIelement icon = null;
                if (____iconOptions != null)
                {
                    foreach (ToggleUIElement option in ____iconOptions)
                    {
                        if (option != null && option.isOn)
                        {
                            icon = option;
                            break;
                        }
                    }
                }

                UIelement variant = null;
                if (____variantOptions != null && ____selectedVariantIndex >= 0 && ____selectedVariantIndex < ____variantOptions.Count)
                {
                    MapMarkerColorToggleElement option = ____variantOptions[____selectedVariantIndex];
                    if (option != null && option.gameObject.activeSelf)
                    {
                        variant = option;
                    }
                }

                // SelectIcon does nothing for an address the row lacks, which leaves the
                // 5-parameter Open's first icon selected, so compare against the row itself.
                bool modSelection = IconOrderPatch.IsOurAddress(iconAddress);
                if (modSelection)
                {
                    int index = ____iconAddresses == null ? -1 : ____iconAddresses.IndexOf(iconAddress);
                    if (index < 0 || ____iconOptions == null || index >= ____iconOptions.Count || ____iconOptions[index] != icon)
                    {
                        WarnOnce(ref s_tileMissingLogged, "the icon row has no selected tile for it");
                    }
                }

                if (__instance == null || (icon == null && variant == null))
                {
                    return;
                }

                s_panel = __instance;
                s_iconTile = icon;
                s_variantTile = variant;
                s_openFrame = Time.frameCount;
                s_modSelection = modSelection;
            }
            catch (Exception e)
            {
                Clear();
                Warn(e);
            }
        }

        /// <summary>Carries out a pending scroll request. Called once per frame from <c>IMod.Update</c>.</summary>
        internal static void Tick()
        {
            if (s_panel == null)
            {
                // Also true for a panel Unity destroyed: its reference compares equal to null.
                return;
            }

            int frame = Time.frameCount;
            if (frame <= s_openFrame)
            {
                return;
            }

            try
            {
                if (!s_panel.gameObject.activeInHierarchy)
                {
                    Clear();
                    return;
                }

                string iconProblem = ScrollIntoView(s_iconTile);
                string variantProblem = ScrollIntoView(s_variantTile);
                if (s_modSelection && (iconProblem ?? variantProblem) != null)
                {
                    WarnOnce(ref s_scrollableMissingLogged, iconProblem ?? variantProblem);
                }

                if (frame - s_openFrame >= FramesToApply)
                {
                    Clear();
                }
            }
            catch (Exception e)
            {
                Clear();
                Warn(e);
            }
        }

        /// <summary>
        /// Scrolls the nearest enclosing <see cref="ScrollableUIComponent"/> so the tile is
        /// fully visible. Mirrors vanilla's private <c>UIComponentMonoBehaviour.ScrollIntoView()</c>
        /// — walk up summing <c>localPosition</c> until the parent's parent is the scrollable,
        /// then <c>ScrollTo(position, extent)</c> with scroll-into-view on — with one
        /// correction. Vanilla passes the tile's pivot position relative to the content's
        /// pivot, while <c>ScrollTo</c> measures from the content's start edge; the two agree
        /// only for a top-left pivot on both. The marker dialog's rows are centred
        /// (<c>LinearLayoutUIComponent</c>, TopCenter) with centred 16-pixel tiles
        /// (<c>WrapperUIComponent</c>, MiddleCenter), where vanilla's figure would be off by
        /// half the row: with fifteen icons (eight vanilla and seven mod icons) the last one reads as position 7 of an 8-wide
        /// viewport, so nothing scrolls. Both pivots are therefore converted out here.
        /// </summary>
        /// <returns>
        /// Null when the tile was scrolled into view, or is absent or inactive; otherwise
        /// what in the hierarchy was not as expected.
        /// </returns>
        private static string ScrollIntoView(UIelement tile)
        {
            if (tile == null || !tile.gameObject.activeInHierarchy)
            {
                return null;
            }

            UIComponentMonoBehaviour tileComponent = tile.GetComponent<UIComponentMonoBehaviour>();
            if (tileComponent == null)
            {
                return "the selected tile has no UIComponentMonoBehaviour";
            }

            float x = 0f;
            float y = 0f;
            Transform current = tile.transform;
            while (current != null && current.parent != null)
            {
                ScrollableUIComponent scrollable = current.parent.GetComponent<ScrollableUIComponent>();
                if (scrollable != null)
                {
                    // `current` is the scrollable's content; x/y are the tile's pivot in its space.
                    UIComponentMonoBehaviour content = current.GetComponent<UIComponentMonoBehaviour>();
                    if (content == null)
                    {
                        return "the scrollable's content has no UIComponentMonoBehaviour";
                    }

                    UIComponentMonoBehaviour.PivotPosition tilePivot = tileComponent.GetUIComponentPivotPosition();
                    UIComponentMonoBehaviour.PivotPosition contentPivot = content.GetUIComponentPivotPosition();
                    if (scrollable.horizontal)
                    {
                        float width = tileComponent.GetUIComponentRenderWidth();
                        float tileStart = x - HorizontalPivotOffset(tilePivot, width);
                        float contentStart = -HorizontalPivotOffset(contentPivot, content.GetUIComponentRenderWidth());
                        scrollable.ScrollTo(tileStart - contentStart, width);
                    }
                    else
                    {
                        float height = tileComponent.GetUIComponentRenderHeight();
                        float tileTop = y + VerticalPivotOffset(tilePivot, height);
                        float contentTop = VerticalPivotOffset(contentPivot, content.GetUIComponentRenderHeight());
                        scrollable.ScrollTo(contentTop - tileTop, height);
                    }
                    return null;
                }

                x += current.localPosition.x;
                y += current.localPosition.y;
                current = current.parent;
            }
            return "no ScrollableUIComponent above the selected tile";
        }

        /// <summary>Distance from a component's left edge to its pivot.</summary>
        private static float HorizontalPivotOffset(UIComponentMonoBehaviour.PivotPosition pivot, float width)
        {
            switch (pivot)
            {
                case UIComponentMonoBehaviour.PivotPosition.TopCenter:
                case UIComponentMonoBehaviour.PivotPosition.MiddleCenter:
                case UIComponentMonoBehaviour.PivotPosition.BottomCenter:
                    return width / 2f;
                case UIComponentMonoBehaviour.PivotPosition.TopRight:
                case UIComponentMonoBehaviour.PivotPosition.MiddleRight:
                case UIComponentMonoBehaviour.PivotPosition.BottomRight:
                    return width;
                default:
                    return 0f;
            }
        }

        /// <summary>Distance from a component's pivot up to its top edge.</summary>
        private static float VerticalPivotOffset(UIComponentMonoBehaviour.PivotPosition pivot, float height)
        {
            switch (pivot)
            {
                case UIComponentMonoBehaviour.PivotPosition.MiddleLeft:
                case UIComponentMonoBehaviour.PivotPosition.MiddleCenter:
                case UIComponentMonoBehaviour.PivotPosition.MiddleRight:
                    return height / 2f;
                case UIComponentMonoBehaviour.PivotPosition.BottomLeft:
                case UIComponentMonoBehaviour.PivotPosition.BottomCenter:
                case UIComponentMonoBehaviour.PivotPosition.BottomRight:
                    return height;
                default:
                    return 0f;
            }
        }

        private static void Clear()
        {
            s_panel = null;
            s_iconTile = null;
            s_variantTile = null;
            s_modSelection = false;
        }

        private static void WarnOnce(ref bool logged, string problem)
        {
            if (!logged)
            {
                logged = true;
                Debug.LogWarning($"[MapMarkersEnhanced] cannot scroll the marker dialog to a mod icon: {problem}");
            }
        }

        private static void Warn(Exception e)
        {
            if (!s_warningLogged)
            {
                s_warningLogged = true;
                Debug.LogWarning($"[MapMarkersEnhanced] could not scroll the marker dialog to the selection: {e}");
            }
        }
    }
}

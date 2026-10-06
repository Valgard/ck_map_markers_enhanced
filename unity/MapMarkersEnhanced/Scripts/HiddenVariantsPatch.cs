using System;
using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Hides the variant tiles of the mod's icons that have a vanilla twin
    /// (<see cref="VanillaTargets"/>) in the marker dialog.
    /// <c>BuildVariantRow</c> runs on every icon click: it reactivates every pooled tile below
    /// the variant count, rebuilds the toggle group from them, and clicks the selected index.
    /// The postfix deactivates the hidden tiles, takes them out of the group, rewires the
    /// left/right navigation over the visible tiles, and moves the selection off a hidden
    /// tile. The tile pool is shared by all icons, so the navigation is rewired on every
    /// call, also for icons without hidden variants — otherwise an earlier rewire would stay.
    /// Never throws into the game. On a failure the row is put back the way vanilla built it —
    /// every variant tile active, in the toggle group and linked left/right, vanilla's
    /// selection on — so every variant is visible; the first failure of a session is warned
    /// about with the icon's address, and says so if putting the row back failed as well.
    /// </summary>
    [HarmonyPatch(typeof(MapMarkerCustomizationPanel), "BuildVariantRow")]
    internal static class HiddenVariantsPatch
    {
        private static bool s_failedLogged;

        // Number of Open/OnResetToDefaultClicked calls in progress: while non-zero, the selection
        // was set on purpose and is kept by index. Open nests (the 8-parameter one calls the other).
        private static int s_explicitDepth;
        private static bool s_depthUnderflowLogged;

        /// <summary>An explicit selection (Open, OnResetToDefaultClicked) starts; called from a prefix.</summary>
        internal static void EnterExplicit()
        {
            s_explicitDepth++;
        }

        /// <summary>
        /// An explicit selection ends; called from a finalizer. Clamps at 0, and warns once per
        /// session when an exit has no matching enter, which would mean a prefix did not run.
        /// </summary>
        internal static void ExitExplicit()
        {
            if (s_explicitDepth > 0)
            {
                s_explicitDepth--;
                return;
            }

            if (!s_depthUnderflowLogged)
            {
                s_depthUnderflowLogged = true;
                Debug.LogWarning(
                    "[MapMarkersEnhanced] explicit-selection depth would go below 0: a finalizer of Open or OnResetToDefaultClicked ran without its prefix; kept at 0"
                );
            }
        }

        private static bool s_hasPrev;
        private static DataBlockAddress s_prevIcon;
        private static int s_prevCount;
        private static int s_oldIndex;

        /// <summary>Forgets the previously built icon; the dialog is being opened afresh.</summary>
        internal static void ForgetPrevious()
        {
            s_hasPrev = false;
        }

        /// <summary>Records vanilla's selected index before <c>BuildVariantRow</c> clamps it.</summary>
        [HarmonyPrefix]
        private static void Prefix(int ____selectedVariantIndex)
        {
            s_oldIndex = ____selectedVariantIndex;
        }

        /// <summary>
        /// The index that should be selected, or -1 to leave vanilla's choice. A selection set on
        /// purpose keeps its index, moved off a hidden tile to the next visible one after it, or
        /// the last visible one before it when none follows. A user's
        /// switch from another icon keeps the selection's visible position, because vanilla
        /// carries the index over and the two differ once tiles are hidden.
        /// </summary>
        private static int ChooseSelection(DataBlockAddress icon, int count, bool hasHidden, int selected)
        {
            if (s_explicitDepth > 0 || !s_hasPrev)
            {
                return hasHidden && selected >= 0 && selected < count && VanillaTargets.IsHidden(icon, selected) ? NearestVisible(icon, count, selected) : -1;
            }

            int position = 0;
            int limit = Math.Min(s_oldIndex, s_prevCount);
            for (int i = 0; i < limit; i++)
            {
                if (!VanillaTargets.IsHidden(s_prevIcon, i))
                {
                    position++;
                }
            }

            int last = -1;
            for (int i = 0; i < count; i++)
            {
                if (VanillaTargets.IsHidden(icon, i))
                {
                    continue;
                }
                last = i;
                if (position-- == 0)
                {
                    break;
                }
            }
            return last;
        }

        [HarmonyPostfix]
        private static void Postfix(
            MapMarkerCustomizationPanel __instance,
            MapMarkerIconDataBlock iconBlock,
            List<MapMarkerColorToggleElement> ____variantOptions,
            int ____selectedVariantIndex
        )
        {
            try
            {
                if (__instance == null || iconBlock == null || ____variantOptions == null)
                {
                    return;
                }

                DataBlockAddress icon = iconBlock.address;
                int count = Math.Min(iconBlock.variants.Count, ____variantOptions.Count);
                bool hasHidden = VanillaTargets.HasHidden(icon);

                if (hasHidden)
                {
                    List<ToggleUIElement> group = __instance.variantToggleGroup != null ? __instance.variantToggleGroup.toggleUIElements : null;
                    for (int i = 0; i < count; i++)
                    {
                        if (!VanillaTargets.IsHidden(icon, i))
                        {
                            continue;
                        }

                        MapMarkerColorToggleElement tile = ____variantOptions[i];
                        if (tile == null)
                        {
                            continue;
                        }
                        // Out of the group, it would stay switched on once another tile is clicked.
                        tile.ToggleOff();
                        tile.gameObject.SetActive(false);
                        group?.Remove(tile);
                    }
                }

                RewireNavigation(____variantOptions, icon, count, hasHidden);

                int wanted = ChooseSelection(icon, count, hasHidden, ____selectedVariantIndex);
                if (wanted >= 0 && wanted != ____selectedVariantIndex && ____variantOptions[wanted] != null)
                {
                    ____variantOptions[wanted].OnLeftClicked(false, false);
                }
                s_prevIcon = icon;
                s_prevCount = count;
                s_hasPrev = true;

                if (__instance.variantRowParent != null)
                {
                    __instance.variantRowParent.RenderUIComponent(true);
                }
            }
            catch (Exception e)
            {
                bool restored = RestoreVanillaRow(__instance, iconBlock, ____variantOptions, ____selectedVariantIndex);
                if (!s_failedLogged)
                {
                    s_failedLogged = true;
                    string address = SafeAddress(iconBlock);
                    Debug.LogWarning(
                        restored
                            ? $"[MapMarkersEnhanced] hiding marker variants failed for icon {address}; the row was put back as vanilla built it, all variants visible"
                            : $"[MapMarkersEnhanced] hiding marker variants failed for icon {address}, and putting the row back failed too; the variant row may be incomplete"
                    );
                    Debug.LogException(e);
                }
            }
        }

        private static string SafeAddress(MapMarkerIconDataBlock iconBlock)
        {
            try
            {
                return iconBlock != null ? iconBlock.address.ToString() : "<null>";
            }
            catch (Exception)
            {
                return "<unknown>";
            }
        }

        /// <summary>
        /// Puts the row back the way vanilla's <c>BuildVariantRow</c> left it before the postfix:
        /// every tile below the variant count active, in the toggle group in index order, linked
        /// left/right over those tiles as vanilla's <c>UpdateHorizontalNavigation</c> links them,
        /// and vanilla's selected tile switched on. Each step is guarded on its own, so the
        /// restore cannot throw; returns whether every step succeeded.
        /// </summary>
        private static bool RestoreVanillaRow(
            MapMarkerCustomizationPanel panel,
            MapMarkerIconDataBlock iconBlock,
            List<MapMarkerColorToggleElement> tiles,
            int selected
        )
        {
            if (tiles == null)
            {
                return true;
            }

            bool ok = true;
            int count;
            try
            {
                count = Math.Min(iconBlock.variants.Count, tiles.Count);
            }
            catch (Exception)
            {
                return false;
            }

            for (int i = 0; i < count; i++)
            {
                try
                {
                    if (tiles[i] != null)
                    {
                        tiles[i].gameObject.SetActive(true);
                    }
                }
                catch (Exception)
                {
                    ok = false;
                }
            }

            try
            {
                if (panel.variantToggleGroup != null)
                {
                    if (panel.variantToggleGroup.toggleUIElements == null)
                    {
                        panel.variantToggleGroup.toggleUIElements = new List<ToggleUIElement>();
                    }
                    List<ToggleUIElement> group = panel.variantToggleGroup.toggleUIElements;
                    group.Clear();
                    for (int i = 0; i < count; i++)
                    {
                        if (tiles[i] != null)
                        {
                            group.Add(tiles[i]);
                        }
                    }
                }
            }
            catch (Exception)
            {
                ok = false;
            }

            try
            {
                RewireNavigation(tiles, default, count, false);
            }
            catch (Exception)
            {
                ok = false;
            }

            try
            {
                if (selected >= 0 && selected < count && tiles[selected] != null && !tiles[selected].isOn)
                {
                    tiles[selected].OnLeftClicked(false, false);
                }
            }
            catch (Exception)
            {
                ok = false;
            }

            try
            {
                if (panel.variantRowParent != null)
                {
                    panel.variantRowParent.RenderUIComponent(true);
                }
            }
            catch (Exception)
            {
                ok = false;
            }

            return ok;
        }

        /// <summary>The first visible index after <paramref name="from"/>, else the last visible one before it, else -1.</summary>
        private static int NearestVisible(DataBlockAddress icon, int count, int from)
        {
            for (int i = from + 1; i < count; i++)
            {
                if (!VanillaTargets.IsHidden(icon, i))
                {
                    return i;
                }
            }
            for (int i = from - 1; i >= 0; i--)
            {
                if (!VanillaTargets.IsHidden(icon, i))
                {
                    return i;
                }
            }
            return -1;
        }

        /// <summary>
        /// Wires left/right like vanilla's <c>UpdateHorizontalNavigation</c>, but over the visible
        /// tiles only. Every pooled tile is cleared first, so tiles an earlier icon wired and this
        /// one does not use keep no stale links.
        /// </summary>
        private static void RewireNavigation(List<MapMarkerColorToggleElement> tiles, DataBlockAddress icon, int count, bool hasHidden)
        {
            foreach (MapMarkerColorToggleElement tile in tiles)
            {
                if (tile != null)
                {
                    tile.leftUIElements.Clear();
                    tile.rightUIElements.Clear();
                }
            }

            var visible = new List<MapMarkerColorToggleElement>();
            for (int i = 0; i < count; i++)
            {
                if (tiles[i] != null && !(hasHidden && VanillaTargets.IsHidden(icon, i)))
                {
                    visible.Add(tiles[i]);
                }
            }

            for (int i = 0; i < visible.Count; i++)
            {
                if (i > 0)
                {
                    visible[i].leftUIElements.Add(visible[i - 1]);
                }
                if (i < visible.Count - 1)
                {
                    visible[i].rightUIElements.Add(visible[i + 1]);
                }
            }
        }
    }

    /// <summary>
    /// Shows a visible variant on the icon-row tile of an icon whose variant 0 is hidden.
    /// Vanilla draws every unselected tile with variant 0, which for such an icon is a
    /// duplicate the dialog no longer offers; the first visible variant is drawn instead.
    /// The selected tile shows the chosen variant through vanilla. Never throws into the game:
    /// each row is guarded on its own, so a failing row keeps vanilla's sprite while the rest
    /// are still drawn, and the first failure of a session is warned about with the icon's address.
    /// </summary>
    [HarmonyPatch(typeof(MapMarkerCustomizationPanel))]
    internal static class IconPreviewPatch
    {
        private static bool s_failedLogged;

        [HarmonyPostfix]
        [HarmonyPatch("PopulateIconRow")]
        private static void AfterPopulate(List<ToggleUIElement> ____iconOptions, List<MapMarkerIconDataBlock> ____iconBlocks)
        {
            ApplyPreviews(____iconOptions, ____iconBlocks);
        }

        [HarmonyPostfix]
        [HarmonyPatch("UpdateIconRowSprites")]
        private static void AfterUpdate(List<ToggleUIElement> ____iconOptions, List<MapMarkerIconDataBlock> ____iconBlocks)
        {
            ApplyPreviews(____iconOptions, ____iconBlocks);
        }

        private static void ApplyPreviews(List<ToggleUIElement> options, List<MapMarkerIconDataBlock> blocks)
        {
            if (options == null || blocks == null)
            {
                return;
            }

            int rows;
            try
            {
                rows = Math.Min(options.Count, blocks.Count);
            }
            catch (Exception e)
            {
                WarnOnce(null, e);
                return;
            }

            // Guarded per row: one bad row keeps vanilla's sprite, the others still get theirs.
            for (int i = 0; i < rows; i++)
            {
                MapMarkerIconDataBlock block = null;
                try
                {
                    ToggleUIElement option = options[i];
                    block = blocks[i];
                    if (option == null || block == null || option.isOn)
                    {
                        continue;
                    }
                    if (!VanillaTargets.HasHidden(block.address) || !VanillaTargets.IsHidden(block.address, 0))
                    {
                        continue;
                    }

                    int first = VanillaTargets.FirstVisible(block.address, block.variants.Count);
                    if (first < 0)
                    {
                        continue;
                    }

                    Sprite sprite = block.GetVariant(first).largeMapSprite;
                    if (sprite != null)
                    {
                        SetSpriteAndColor(option.activatedSprites, sprite, Color.white);
                        SetSpriteAndColor(option.deactivatedSprites, sprite, new Color(1f, 1f, 1f, 0.25f));
                    }
                }
                catch (Exception e)
                {
                    WarnOnce(block, e);
                }
            }
        }

        private static void WarnOnce(MapMarkerIconDataBlock block, Exception e)
        {
            if (s_failedLogged)
            {
                return;
            }
            s_failedLogged = true;
            string address = "<unknown>";
            try
            {
                if (block != null)
                {
                    address = block.address.ToString();
                }
            }
            catch (Exception) { }
            Debug.LogWarning(
                $"[MapMarkersEnhanced] icon-row preview failed for icon {address}; that tile keeps vanilla's sprite, the other rows are still drawn"
            );
            Debug.LogException(e);
        }

        /// <summary>Copy of vanilla's private <c>SetSpriteAndColor</c>.</summary>
        private static void SetSpriteAndColor(List<SpriteRenderer> renderers, Sprite sprite, Color color)
        {
            if (renderers == null)
            {
                return;
            }
            foreach (SpriteRenderer renderer in renderers)
            {
                if (renderer != null)
                {
                    renderer.sprite = sprite;
                    renderer.color = color;
                }
            }
        }
    }
}

namespace MapMarkersEnhanced
{
    // The selection is set on purpose by these three; the row they build keeps its index.
    // The depth counter is released in a finalizer, so an exception cannot leave it raised.
    [HarmonyPatch(
        typeof(MapMarkerCustomizationPanel),
        "Open",
        new[] { typeof(MapMarkerPreset), typeof(Action<DataBlockAddress, int, string>), typeof(Action), typeof(string), typeof(string) }
    )]
    internal static class ExplicitOpenPatch
    {
        [HarmonyPrefix]
        private static void Prefix()
        {
            HiddenVariantsPatch.ForgetPrevious();
            HiddenVariantsPatch.EnterExplicit();
        }

        [HarmonyFinalizer]
        private static void Finalizer()
        {
            HiddenVariantsPatch.ExitExplicit();
        }
    }

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
    internal static class ExplicitOpenWithPresetPatch
    {
        [HarmonyPrefix]
        private static void Prefix()
        {
            HiddenVariantsPatch.EnterExplicit();
        }

        [HarmonyFinalizer]
        private static void Finalizer()
        {
            HiddenVariantsPatch.ExitExplicit();
        }
    }

    [HarmonyPatch(typeof(MapMarkerCustomizationPanel), "OnResetToDefaultClicked")]
    internal static class ExplicitResetPatch
    {
        [HarmonyPrefix]
        private static void Prefix()
        {
            HiddenVariantsPatch.EnterExplicit();
        }

        [HarmonyFinalizer]
        private static void Finalizer()
        {
            HiddenVariantsPatch.ExitExplicit();
        }
    }
}

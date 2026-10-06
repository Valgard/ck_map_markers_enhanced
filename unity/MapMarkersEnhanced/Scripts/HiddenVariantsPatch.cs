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
    /// Never throws into the game; a failure is warned about once per session and leaves
    /// every variant visible.
    /// </summary>
    [HarmonyPatch(typeof(MapMarkerCustomizationPanel), "BuildVariantRow")]
    internal static class HiddenVariantsPatch
    {
        private static bool s_failedLogged;

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

                if (hasHidden && ____selectedVariantIndex >= 0 && ____selectedVariantIndex < count && VanillaTargets.IsHidden(icon, ____selectedVariantIndex))
                {
                    int target = NearestVisible(icon, count, ____selectedVariantIndex);
                    if (target >= 0 && ____variantOptions[target] != null)
                    {
                        ____variantOptions[target].OnLeftClicked(false, false);
                    }
                }

                if (__instance.variantRowParent != null)
                {
                    __instance.variantRowParent.RenderUIComponent(true);
                }
            }
            catch (Exception e)
            {
                if (!s_failedLogged)
                {
                    s_failedLogged = true;
                    Debug.LogWarning("[MapMarkersEnhanced] hiding marker variants failed; all variants stay visible");
                    Debug.LogException(e);
                }
            }
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
    /// The selected tile shows the chosen variant through vanilla. Never throws into the game.
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
            try
            {
                if (options == null || blocks == null)
                {
                    return;
                }

                int rows = Math.Min(options.Count, blocks.Count);
                for (int i = 0; i < rows; i++)
                {
                    ToggleUIElement option = options[i];
                    MapMarkerIconDataBlock block = blocks[i];
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
            }
            catch (Exception e)
            {
                if (!s_failedLogged)
                {
                    s_failedLogged = true;
                    Debug.LogWarning("[MapMarkersEnhanced] icon-row previews failed; the row keeps vanilla's sprites");
                    Debug.LogException(e);
                }
            }
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

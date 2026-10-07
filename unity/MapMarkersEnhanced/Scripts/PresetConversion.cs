using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Rewrites the player's marker presets that point at a retired variant to its target — the
    /// same-named variant in the mod's new blocks, or a vanilla marker
    /// (<see cref="RetiredTargets"/>). Presets live client-side in the game's
    /// prefs, so this runs where the player is. The slots are the five that
    /// <c>MapUI.EnsurePresetsInitialized</c> fills (<c>Pug.Other:346760</c>); the roadmap item
    /// "More than five presets" has to raise <see cref="PresetSlots"/> together with the game's
    /// own bound.
    /// </summary>
    internal static class PresetConversion
    {
        internal const int PresetSlots = 5;

        private static bool s_unresolvedLogged;

        /// <summary>
        /// Converts every preset on a retired variant whose target resolves
        /// (<see cref="RetiredTargets.Resolves"/>; needs <c>ScriptableData.isLoaded</c>, which the
        /// caller checks); returns how many were rewritten. A preset whose target does not resolve
        /// is left as it is, with one warning per session.
        /// </summary>
        internal static int Run()
        {
            int converted = 0;
            for (int i = 0; i < PresetSlots; i++)
            {
                MapMarkerPreset preset = Manager.prefs.GetMapMarkerPreset(i);
                if (preset.iconAddress == DataBlockAddress.Empty)
                {
                    continue;
                }

                if (RetiredTargets.TryGet(preset.iconAddress, preset.variantIndex, out DataBlockAddress address, out int targetVariant))
                {
                    if (!RetiredTargets.Resolves(address, targetVariant))
                    {
                        if (!s_unresolvedLogged)
                        {
                            s_unresolvedLogged = true;
                            Debug.LogWarning(
                                $"[MapMarkersEnhanced] vanilla target {address} variant {targetVariant} is not a registered map marker icon with that variant; "
                                    + $"preset {i + 1} is left as it is"
                            );
                        }
                        continue;
                    }

                    Manager.prefs.SetMapMarkerPreset(
                        i,
                        new MapMarkerPreset
                        {
                            iconAddress = address,
                            variantIndex = targetVariant,
                            name = preset.name,
                        }
                    );
                    converted++;
                }
            }
            return converted;
        }
    }
}

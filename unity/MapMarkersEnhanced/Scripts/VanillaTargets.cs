using System.Collections.Generic;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Lookup over <see cref="IconTable.ToVanilla"/>: which of the mod's icon variants have a
    /// vanilla twin. A variant is hidden from the customisation dialog exactly when it has a
    /// target here (see docs/adrs/002-hide-vanilla-duplicates.md). Built once, on first use; a parse failure
    /// surfaces as a <see cref="System.TypeInitializationException"/> at the caller, which
    /// each consumer catches.
    /// </summary>
    internal static class VanillaTargets
    {
        private static readonly Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)> Targets = Build();
        private static readonly HashSet<DataBlockAddress> Hiding = BuildHiding();

        private static Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)> Build()
        {
            var targets = new Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)>();
            foreach (KeyValuePair<(string icon, int variant), (string address, int variant)> entry in IconTable.ToVanilla)
            {
                targets[(new DataBlockAddress(entry.Key.icon), entry.Key.variant)] = (new DataBlockAddress(entry.Value.address), entry.Value.variant);
            }
            return targets;
        }

        private static HashSet<DataBlockAddress> BuildHiding()
        {
            var hiding = new HashSet<DataBlockAddress>();
            foreach (KeyValuePair<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)> entry in Targets)
            {
                hiding.Add(entry.Key.icon);
            }
            return hiding;
        }

        /// <summary>The vanilla block and variant a mod icon variant converts to.</summary>
        internal static bool TryGet(DataBlockAddress icon, int variant, out DataBlockAddress address, out int vanillaVariant)
        {
            if (Targets.TryGetValue((icon, variant), out var target))
            {
                address = target.address;
                vanillaVariant = target.variant;
                return true;
            }

            address = default;
            vanillaVariant = 0;
            return false;
        }

        /// <summary>
        /// Whether a write target — a conversion's vanilla target or a restoration's mod or vanilla
        /// target — is registered: a <see cref="MapMarkerIconDataBlock"/> at
        /// <paramref name="address"/> with at least <paramref name="variant"/> + 1 variants. The
        /// vanilla addresses were measured on 1.3.0.4; a game update that drops or renumbers a block
        /// must not get markers or presets written onto an address that shows nothing. Only
        /// meaningful once <c>ScriptableData.isLoaded</c>; callers check that first.
        /// </summary>
        internal static bool Resolves(DataBlockAddress address, int variant)
        {
            // TryGetDataBlock reports any block at the address; the cast leaves null for another type.
            return ScriptableData.TryGetDataBlock<MapMarkerIconDataBlock>(address, out MapMarkerIconDataBlock block)
                && block != null
                && block.variants != null
                && variant >= 0
                && variant < block.variants.Count;
        }

        /// <summary>Whether the variant has a vanilla target, i.e. is hidden from the dialog.</summary>
        internal static bool IsHidden(DataBlockAddress icon, int variant) => Targets.ContainsKey((icon, variant));

        /// <summary>The lowest index in <c>[0, count)</c> that is not hidden, or -1 if every one is.</summary>
        internal static int FirstVisible(DataBlockAddress icon, int count)
        {
            for (int i = 0; i < count; i++)
            {
                if (!Targets.ContainsKey((icon, i)))
                {
                    return i;
                }
            }
            return -1;
        }

        /// <summary>Whether any variant of the icon is hidden.</summary>
        internal static bool HasHidden(DataBlockAddress icon) => Hiding.Contains(icon);
    }
}

using System.Collections.Generic;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Lookup over <see cref="IconTable.Retired"/>: which (address, variant) pairs belong to the
    /// retired 1.x blocks, and the new mod variant or vanilla marker each converts to. A pair the
    /// table does not hold — an index outside a retired block included — is simply not retired.
    /// Built once, on first use; a parse failure surfaces as a
    /// <see cref="System.TypeInitializationException"/> at the caller, which each consumer catches.
    /// </summary>
    internal static class RetiredTargets
    {
        private static readonly Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)> Targets = Build();

        private static Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)> Build()
        {
            var targets = new Dictionary<(DataBlockAddress icon, int variant), (DataBlockAddress address, int variant)>();
            foreach (KeyValuePair<(string icon, int variant), (string address, int variant)> entry in IconTable.Retired)
            {
                targets[(new DataBlockAddress(entry.Key.icon), entry.Key.variant)] = (new DataBlockAddress(entry.Value.address), entry.Value.variant);
            }
            return targets;
        }

        /// <summary>The new mod variant or vanilla marker a retired variant converts to.</summary>
        internal static bool TryGet(DataBlockAddress icon, int variant, out DataBlockAddress address, out int targetVariant)
        {
            if (Targets.TryGetValue((icon, variant), out var target))
            {
                address = target.address;
                targetVariant = target.variant;
                return true;
            }

            address = default;
            targetVariant = 0;
            return false;
        }

        /// <summary>Whether the variant belongs to a retired 1.x block, i.e. has a target.</summary>
        internal static bool IsRetired(DataBlockAddress icon, int variant) => Targets.ContainsKey((icon, variant));

        /// <summary>
        /// Whether a write target — a conversion's target or a restoration's target, a mod block or
        /// a vanilla one — is registered: a <see cref="MapMarkerIconDataBlock"/> at
        /// <paramref name="address"/> with at least <paramref name="variant"/> + 1 variants. The
        /// vanilla addresses were measured on 1.3.0.4; a game update that drops or renumbers a block,
        /// or a mod block that fails to register, must not get markers or presets written onto an
        /// address that shows nothing. Only meaningful once <c>ScriptableData.isLoaded</c>; callers
        /// check that first.
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
    }
}

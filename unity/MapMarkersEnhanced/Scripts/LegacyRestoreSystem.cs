using System;
using System.Collections.Generic;
using Unity.Entities;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Restores the markers MapMarkers+ placed and the 1.3 world migration
    /// (version 13) turned into question marks. Such a marker still carries
    /// MapMarkers+'s <c>Amount</c> of <c>6000 + PlusMarkerType</c>; the system
    /// gives it the mapped icon and variant from <see cref="IconTable.Legacy"/>
    /// and sets <c>Amount</c> to 1, vanilla's value, which is what makes the
    /// restoration happen once per marker. A marker restyled since (no longer
    /// the question mark) and an amount the table does not know are left alone;
    /// the first pass in a world that finds legacy-amount markers which are not
    /// the question mark warns how many, with one of them as an example, so a
    /// changed migration default does not leave restoration off without a trace.
    /// Runs in the server world only; the serializer and ghost replication carry
    /// the change to the save and to every client.
    /// </summary>
    [WorldSystemFilter(WorldSystemFilterFlags.ServerSimulation)]
    [UpdateInGroup(typeof(RunSimulationSystemGroup))]
    public partial class LegacyRestoreSystem : PugSimulationSystemBase
    {
        /// <summary>Updates between two passes; the first pass runs on the first update.</summary>
        private const int PassInterval = 60;

        /// <summary>The icon the version-13 migration gives an old variation-1 marker (<c>Pug.Other</c> <c>GetDefaultIconForVariation</c>).</summary>
        private const string QuestionMarkAddress = "7e09f30c-8838-5604-2b46-8c13b0ef771e";

        /// <summary>The variant the migration gives it (<c>GetDefaultVariantForOldVariation(1)</c>).</summary>
        private const int QuestionMarkVariant = 9;

        private readonly Dictionary<int, (DataBlockAddress address, int variant)> _legacy = new Dictionary<int, (DataBlockAddress address, int variant)>();
        private readonly List<Entity> _matches = new List<Entity>();
        private readonly List<(DataBlockAddress address, int variant)> _skipped = new List<(DataBlockAddress address, int variant)>();

        private DataBlockAddress _questionMark;
        private int _updatesUntilPass;
        private bool _failureLogged;
        private bool _skippedLogged;

        protected override void OnCreate()
        {
            try
            {
                _questionMark = new DataBlockAddress(QuestionMarkAddress);
                foreach (KeyValuePair<int, (string address, int variant)> entry in IconTable.Legacy)
                {
                    _legacy[entry.Key] = (new DataBlockAddress(entry.Value.address), entry.Value.variant);
                }
            }
            catch (Exception e)
            {
                // With an empty table every amount falls through and the system restores nothing.
                _legacy.Clear();
                _failureLogged = true;
                Debug.LogError("[MapMarkersEnhanced] legacy marker table could not be parsed; restoration is off");
                Debug.LogException(e);
            }

            base.OnCreate();
        }

        protected override void OnUpdate()
        {
            if (_updatesUntilPass > 0)
            {
                _updatesUntilPass--;
            }
            else
            {
                _updatesUntilPass = PassInterval - 1;
                try
                {
                    Pass();
                }
                catch (Exception e)
                {
                    if (!_failureLogged)
                    {
                        _failureLogged = true;
                        Debug.LogError("[MapMarkersEnhanced] legacy marker restoration failed; will keep trying silently");
                        Debug.LogException(e);
                    }
                }
            }

            base.OnUpdate();
        }

        private void Pass()
        {
            if (_legacy.Count == 0)
            {
                return;
            }

            // Find candidates read-only, so a pass that restores nothing leaves
            // every chunk's change version alone: a write access would make the
            // serializer and ghost replication revisit all markers every pass.
            Dictionary<int, (DataBlockAddress address, int variant)> legacy = _legacy;
            List<Entity> matches = _matches;
            List<(DataBlockAddress address, int variant)> skipped = _skipped;
            DataBlockAddress questionMark = _questionMark;
            matches.Clear();
            skipped.Clear();

            Entities
                .ForEach(
                    (Entity entity, in ObjectDataCD data, in MapMarkerCustomDataCD custom) =>
                    {
                        if (data.objectID == ObjectID.MapMarker && legacy.ContainsKey(data.amount))
                        {
                            if (custom.iconAddress == questionMark && custom.variantIndex == QuestionMarkVariant)
                            {
                                matches.Add(entity);
                            }
                            else
                            {
                                // Copied out of the `in` parameter; the scan stays read-only.
                                skipped.Add((custom.iconAddress, custom.variantIndex));
                            }
                        }
                    }
                )
                .WithoutBurst()
                .Run();

            if (skipped.Count > 0 && !_skippedLogged)
            {
                // On CK 1.3.0.2 a placed marker cannot be edited (MapUI.ApplyEditToExistingMarker
                // has no caller), so nothing a player does leaves a legacy amount on another
                // icon. A skipped marker therefore most likely means a game update changed
                // what the version-13 migration writes, which stops restoration entirely; the
                // example is the new icon and variant to compare against the constants above.
                // A player edit becomes possible only in a future version that allows editing.
                _skippedLogged = true;
                (DataBlockAddress address, int variant) sample = skipped[0];
                Debug.LogWarning(
                    $"[MapMarkersEnhanced] skipped {skipped.Count} legacy markers that are not the migration's question mark "
                        + $"(expected {QuestionMarkAddress} variant {QuestionMarkVariant}, e.g. {sample.address} variant {sample.variant}); "
                        + "they are not restored"
                );
            }
            skipped.Clear();

            if (matches.Count == 0)
            {
                return;
            }

            int restored = 0;
            foreach (Entity entity in matches)
            {
                ObjectDataCD data = EntityManager.GetComponentData<ObjectDataCD>(entity);
                if (!legacy.TryGetValue(data.amount, out var target))
                {
                    continue;
                }

                MapMarkerCustomDataCD custom = EntityManager.GetComponentData<MapMarkerCustomDataCD>(entity);
                custom.iconAddress = target.address;
                custom.variantIndex = target.variant;
                EntityManager.SetComponentData(entity, custom);

                data.amount = 1;
                EntityManager.SetComponentData(entity, data);
                restored++;
            }
            matches.Clear();

            if (restored > 0)
            {
                Debug.Log($"[MapMarkersEnhanced] restored {restored} legacy markers");
            }
        }
    }
}

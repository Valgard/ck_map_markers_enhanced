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
    /// <para>
    /// Rule 2 converts a marker whose icon and variant are in
    /// <see cref="IconTable.ToVanilla"/> (a variant the dialog hides) to its vanilla
    /// target, leaving <c>Amount</c> alone, but only once <see cref="VanillaTargets.Resolves"/>
    /// confirms that target is registered; a target that is not stays unwritten and is warned
    /// about once per instance. A converted marker carries a vanilla address
    /// and cannot match again. The rules are disjoint within a pass (rule 1 needs a
    /// vanilla address, rule 2 a mod address). Across passes rule 2 writes the question
    /// mark onto exactly the icon and variant rule 1 looks for, which is safe because the
    /// game creates every placed marker with <c>Amount</c> 1 and restoration writes 1.
    /// Should a legacy-amount marker ever reach a hidden variant, rule 1 restores it on a
    /// later pass if rule 2 left it on the question mark.
    /// </para>
    /// <para>
    /// Both rules share one read-only scan per pass; each rule's writes then run under a try
    /// of its own with its own once-per-instance error, so a throw in one rule's write loop
    /// never stops the other. A table that fails to parse in <c>OnCreate</c> turns off its own
    /// rule; <see cref="IconTable.Legacy"/> also names the vanilla targets of hidden types, so a
    /// malformed vanilla address would fail both tables, which is why the generator rejects one.
    /// A throw in the shared scan stops both rules for that pass. Every failure is retried on
    /// the next pass.
    /// </para>
    /// Runs in the server world only; the serializer and ghost replication carry
    /// the change to the save and to every client.
    /// </summary>
    [WorldSystemFilter(WorldSystemFilterFlags.ServerSimulation)]
    [UpdateInGroup(typeof(RunSimulationSystemGroup))]
    public partial class MarkerMigrationSystem : PugSimulationSystemBase
    {
        /// <summary>Updates between two passes; the first pass runs on the first update.</summary>
        private const int PassInterval = 60;

        /// <summary>The icon the version-13 migration gives an old variation-1 marker (<c>Pug.Other</c> <c>GetDefaultIconForVariation</c>).</summary>
        private const string QuestionMarkAddress = "7e09f30c-8838-5604-2b46-8c13b0ef771e";

        /// <summary>The variant the migration gives it (<c>GetDefaultVariantForOldVariation(1)</c>).</summary>
        private const int QuestionMarkVariant = 9;

        private readonly Dictionary<int, (DataBlockAddress address, int variant)> _legacy = new Dictionary<int, (DataBlockAddress address, int variant)>();
        private readonly List<Entity> _matches = new List<Entity>();
        private readonly List<Entity> _conversions = new List<Entity>();
        private readonly List<(DataBlockAddress address, int variant)> _skipped = new List<(DataBlockAddress address, int variant)>();
        private readonly Dictionary<(DataBlockAddress address, int variant), bool> _resolved = new Dictionary<(DataBlockAddress address, int variant), bool>();
        private readonly HashSet<(DataBlockAddress address, int variant)> _unresolvedWarned = new HashSet<(DataBlockAddress address, int variant)>();

        private DataBlockAddress _questionMark;
        private int _updatesUntilPass;
        private bool _passFailureLogged;
        private bool _restoreFailureLogged;
        private bool _conversionFailureLogged;
        private bool _conversionOff;
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
                Debug.LogError("[MapMarkersEnhanced] legacy marker table could not be parsed; restoration is off");
                Debug.LogException(e);
            }

            try
            {
                // Forces VanillaTargets' static initialisation here, so a parse failure turns off rule 2 alone.
                VanillaTargets.HasHidden(default);
            }
            catch (Exception e)
            {
                _conversionOff = true;
                Debug.LogError("[MapMarkersEnhanced] vanilla target table could not be parsed; conversion is off");
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
                Pass();
            }

            base.OnUpdate();
        }

        /// <summary>
        /// One scan, then each rule's writes under a try of its own, so a throw in one rule's
        /// loop never stops the other. A throw in the scan stops both for that pass.
        /// </summary>
        private void Pass()
        {
            try
            {
                Scan();
            }
            catch (Exception e)
            {
                if (!_passFailureLogged)
                {
                    _passFailureLogged = true;
                    Debug.LogError("[MapMarkersEnhanced] marker migration failed: the scan threw, so neither rule ran; will keep trying silently");
                    Debug.LogException(e);
                }
                _matches.Clear();
                _conversions.Clear();
                return;
            }

            try
            {
                RestoreLegacy();
            }
            catch (Exception e)
            {
                if (!_restoreFailureLogged)
                {
                    _restoreFailureLogged = true;
                    Debug.LogError("[MapMarkersEnhanced] legacy restoration failed; conversion still runs, restoration will keep trying silently");
                    Debug.LogException(e);
                }
            }
            _matches.Clear();

            try
            {
                ConvertHidden();
            }
            catch (Exception e)
            {
                if (!_conversionFailureLogged)
                {
                    _conversionFailureLogged = true;
                    Debug.LogError("[MapMarkersEnhanced] conversion to vanilla icons failed; restoration still runs, conversion will keep trying silently");
                    Debug.LogException(e);
                }
            }
            _conversions.Clear();
        }

        private void Scan()
        {
            // Find candidates read-only, so a pass that changes nothing leaves
            // every chunk's change version alone: a write access would make the
            // serializer and ghost replication revisit all markers every pass.
            Dictionary<int, (DataBlockAddress address, int variant)> legacy = _legacy;
            List<Entity> matches = _matches;
            List<(DataBlockAddress address, int variant)> skipped = _skipped;
            DataBlockAddress questionMark = _questionMark;
            bool conversionOn = !_conversionOff;
            List<Entity> conversions = _conversions;
            matches.Clear();
            skipped.Clear();
            conversions.Clear();

            Entities
                .ForEach(
                    (Entity entity, in ObjectDataCD data, in MapMarkerCustomDataCD custom) =>
                    {
                        if (data.objectID != ObjectID.MapMarker)
                        {
                            return;
                        }

                        if (conversionOn && VanillaTargets.IsHidden(custom.iconAddress, custom.variantIndex))
                        {
                            conversions.Add(entity);
                        }
                        else if (legacy.ContainsKey(data.amount))
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
        }

        /// <summary>Rule 1's writes, over the markers the scan matched.</summary>
        private void RestoreLegacy()
        {
            int restored = 0;
            foreach (Entity entity in _matches)
            {
                ObjectDataCD data = EntityManager.GetComponentData<ObjectDataCD>(entity);
                if (!_legacy.TryGetValue(data.amount, out var target))
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

            if (restored > 0)
            {
                Debug.Log($"[MapMarkersEnhanced] restored {restored} legacy markers");
            }
        }

        /// <summary>Rule 2's writes, over the markers the scan found on a hidden variant.</summary>
        private void ConvertHidden()
        {
            if (_conversions.Count == 0 || !ScriptableData.isLoaded)
            {
                // Without loaded data no target can be checked; nothing is written, the next pass retries.
                return;
            }

            // Each distinct target is resolved once per pass, not per marker.
            _resolved.Clear();
            int converted = 0;
            foreach (Entity entity in _conversions)
            {
                MapMarkerCustomDataCD custom = EntityManager.GetComponentData<MapMarkerCustomDataCD>(entity);
                if (!VanillaTargets.TryGet(custom.iconAddress, custom.variantIndex, out DataBlockAddress address, out int variant))
                {
                    continue;
                }

                if (!_resolved.TryGetValue((address, variant), out bool resolves))
                {
                    resolves = VanillaTargets.Resolves(address, variant);
                    _resolved[(address, variant)] = resolves;
                    if (!resolves && _unresolvedWarned.Add((address, variant)))
                    {
                        Debug.LogWarning(
                            $"[MapMarkersEnhanced] vanilla target {address} variant {variant} is not a registered map marker icon with that variant; "
                                + "markers that convert to it are left as they are"
                        );
                    }
                }
                if (!resolves)
                {
                    continue;
                }

                custom.iconAddress = address;
                custom.variantIndex = variant;
                EntityManager.SetComponentData(entity, custom);
                converted++;
            }

            if (converted > 0)
            {
                Debug.Log($"[MapMarkersEnhanced] converted {converted} markers to vanilla icons");
            }
        }
    }
}

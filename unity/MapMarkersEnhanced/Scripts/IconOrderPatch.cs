using System;
using System.Collections.Generic;
using System.Text;
using HarmonyLib;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Lists the mod's icons after vanilla's in the marker dialog.
    /// <c>ScriptableData.TryGetDataBlocks</c> hands out the live typed
    /// <c>List&lt;MapMarkerIconDataBlock&gt;</c>, and <c>PopulateIconRow</c> is the
    /// only reader of that typed list, so reordering it before the row is built is
    /// enough. Runtime IDs cannot shift: <c>ScriptableData</c> resolves them through
    /// a separate, untyped list and lookup that this patch never touches.
    /// The game calls <c>PopulateIconRow</c> once per panel instance (guarded by
    /// the panel's <c>_iconsPopulated</c>); on every later panel's call the list is
    /// already partitioned and <see cref="IconOrder.MoveToEnd{T}"/> moves nothing.
    /// <para>
    /// The patch re-reads the list afterwards rather than trusting that it is live,
    /// and warns once per session per cause: no list, a list that is not a
    /// <c>List&lt;&gt;</c> or did not keep the new order (icons stay in front),
    /// fewer than all of the mod's icons registered, or the mod's icons at the end
    /// but not in table order. It never throws into the game.
    /// </para>
    /// </summary>
    [HarmonyPatch(typeof(MapMarkerCustomizationPanel), "PopulateIconRow")]
    internal static class IconOrderPatch
    {
        private static readonly HashSet<string> s_ours = new HashSet<string>(IconTable.ModIconAddresses);

        private static bool s_orderLogged;
        private static bool s_failedLogged;
        private static bool s_noListLogged;
        private static bool s_notListLogged;
        private static bool s_notLiveLogged;
        private static bool s_missingLogged;
        private static bool s_misorderedLogged;

        /// <summary>Whether an icon address is one of the mod's.</summary>
        internal static bool IsOurAddress(DataBlockAddress address)
        {
            return s_ours.Contains(address.ToString());
        }

        [HarmonyPrefix]
        private static bool Prefix()
        {
            try
            {
                Reorder();
            }
            catch (Exception e)
            {
                if (WarnOnce(ref s_failedLogged, "icon order failed with an exception; icons stay where the game put them"))
                {
                    Debug.LogException(e);
                }
            }
            return true;
        }

        private static void Reorder()
        {
            if (!ScriptableData.TryGetDataBlocks<MapMarkerIconDataBlock>(out var blocks) || blocks == null)
            {
                WarnOnce(ref s_noListLogged, "icon order: no MapMarkerIconDataBlock list registered");
                return;
            }

            if (!(blocks is List<MapMarkerIconDataBlock> list))
            {
                WarnOnce(ref s_notListLogged, "icon order: the icon list is not a List<>, so it cannot be reordered; icons stay in front");
                return;
            }

            int moved = IconOrder.MoveToEnd(list, IsOurs);

            ScriptableData.TryGetDataBlocks<MapMarkerIconDataBlock>(out var again);
            Verify(again);

            if (!s_orderLogged)
            {
                s_orderLogged = true;
                Debug.Log($"[MapMarkersEnhanced] icon order: moved {moved}, ours at {OurIndices(again)} of {again?.Count ?? 0}");
            }
        }

        private static bool IsOurs(MapMarkerIconDataBlock block)
        {
            return block != null && IsOurAddress(block.address);
        }

        /// <summary>
        /// Checks the re-read list: all of the mod's icons present, all of them at the
        /// end, and there in <see cref="IconTable.ModIconAddresses"/> order.
        /// </summary>
        private static void Verify(IReadOnlyList<MapMarkerIconDataBlock> blocks)
        {
            string[] wanted = IconTable.ModIconAddresses;
            var present = new List<string>();
            if (blocks != null)
            {
                foreach (MapMarkerIconDataBlock block in blocks)
                {
                    if (IsOurs(block))
                    {
                        present.Add(block.address.ToString());
                    }
                }
            }

            if (present.Count < wanted.Length)
            {
                WarnOnce(ref s_missingLogged, $"icon order: only {present.Count} of the mod's {wanted.Length} icons are registered");
            }

            if (present.Count == 0)
            {
                return;
            }

            int start = blocks.Count - present.Count;
            for (int i = start; i < blocks.Count; i++)
            {
                if (!IsOurs(blocks[i]))
                {
                    WarnOnce(ref s_notLiveLogged, "icon order: the reorder did not stick (the list is not live); icons stay in front");
                    return;
                }
            }

            // The mod's icons that are present, in the order the table wants them.
            var expected = new List<string>();
            foreach (string address in wanted)
            {
                if (present.Contains(address))
                {
                    expected.Add(address);
                }
            }
            for (int i = 0; i < expected.Count; i++)
            {
                if (present[i] != expected[i])
                {
                    WarnOnce(ref s_misorderedLogged, "icon order: the mod's icons are at the end but not in table order");
                    return;
                }
            }
        }

        private static string OurIndices(IReadOnlyList<MapMarkerIconDataBlock> blocks)
        {
            if (blocks == null)
            {
                return "none";
            }

            var indices = new StringBuilder();
            for (int i = 0; i < blocks.Count; i++)
            {
                if (IsOurs(blocks[i]))
                {
                    if (indices.Length > 0)
                    {
                        indices.Append(',');
                    }
                    indices.Append(i);
                }
            }
            return indices.Length > 0 ? indices.ToString() : "none";
        }

        /// <summary>Logs the warning the first time its cause occurs this session.</summary>
        /// <returns>True when it was logged now.</returns>
        private static bool WarnOnce(ref bool logged, string message)
        {
            if (logged)
            {
                return false;
            }
            logged = true;
            Debug.LogWarning("[MapMarkersEnhanced] " + message);
            return true;
        }
    }
}

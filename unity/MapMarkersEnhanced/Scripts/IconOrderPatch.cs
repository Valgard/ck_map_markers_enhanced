using System;
using System.Collections.Generic;
using System.Text;
using HarmonyLib;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Lists the mod's icons after vanilla's in the marker dialog.
    /// <c>ScriptableData.TryGetDataBlocks</c> hands out the live
    /// <c>List&lt;MapMarkerIconDataBlock&gt;</c>, and <c>PopulateIconRow</c> is its
    /// only reader, so reordering that list before the row is built is enough.
    /// The game calls <c>PopulateIconRow</c> once per panel instance (guarded by
    /// the panel's <c>_iconsPopulated</c>); on every later call the list is
    /// already partitioned and <see cref="IconOrder.MoveToEnd{T}"/> moves nothing.
    /// </summary>
    [HarmonyPatch(typeof(MapMarkerCustomizationPanel), "PopulateIconRow")]
    internal static class IconOrderPatch
    {
        private static readonly HashSet<string> s_ours = new HashSet<string>(IconTable.ModIconAddresses);

        private static bool s_orderLogged;
        private static bool s_warningLogged;

        [HarmonyPrefix]
        private static bool Prefix()
        {
            try
            {
                Reorder();
            }
            catch (Exception e)
            {
                Warn();
                Debug.LogException(e);
            }
            return true;
        }

        private static void Reorder()
        {
            if (!ScriptableData.TryGetDataBlocks<MapMarkerIconDataBlock>(out var blocks) || !(blocks is List<MapMarkerIconDataBlock> list))
            {
                Warn();
                return;
            }

            int moved = IconOrder.MoveToEnd(list, IsOurs);

            ScriptableData.TryGetDataBlocks<MapMarkerIconDataBlock>(out var again);
            if (!OursAreLast(again))
            {
                Warn();
            }

            if (!s_orderLogged)
            {
                s_orderLogged = true;
                Debug.Log($"[MapMarkersEnhanced] icon order: moved {moved}, ours at {OurIndices(again)} of {again?.Count ?? 0}");
            }
        }

        private static bool IsOurs(MapMarkerIconDataBlock block)
        {
            return block != null && s_ours.Contains(block.address.ToString());
        }

        /// <summary>True when the last entries of the list are the mod's icons, in <see cref="IconTable.ModIconAddresses"/> order.</summary>
        private static bool OursAreLast(IReadOnlyList<MapMarkerIconDataBlock> blocks)
        {
            string[] wanted = IconTable.ModIconAddresses;
            if (blocks == null || blocks.Count < wanted.Length)
            {
                return false;
            }

            int start = blocks.Count - wanted.Length;
            for (int i = 0; i < wanted.Length; i++)
            {
                MapMarkerIconDataBlock block = blocks[start + i];
                if (block == null || block.address.ToString() != wanted[i])
                {
                    return false;
                }
            }
            return true;
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

        private static void Warn()
        {
            if (!s_warningLogged)
            {
                s_warningLogged = true;
                Debug.LogWarning("[MapMarkersEnhanced] icon order could not be changed; icons stay in front");
            }
        }
    }
}

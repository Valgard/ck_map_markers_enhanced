using System.Text;
using PugMod;
using UnityEngine;

namespace MapMarkersEnhanced
{
    /// <summary>
    /// Mod bootstrap. The Pugstorm mod loader instantiates this class on game
    /// start and calls the IMod lifecycle methods. Harmony patch classes are
    /// auto-discovered by the loader — there is no PatchAll() call.
    /// </summary>
    public sealed class MapMarkersEnhancedMod : IMod
    {
        private static bool s_iconsLogged;

        public void EarlyInit() { }

        public void Init()
        {
            Debug.Log("[MapMarkersEnhanced] Mod initialized.");
        }

        public void ModObjectLoaded(Object obj) { }

        public void Shutdown() { }

        public void Update()
        {
            if (!s_iconsLogged && ScriptableData.isLoaded)
            {
                s_iconsLogged = true;
                LogIcons();
            }

            ScrollToSelectionPatch.Tick();
        }

        /// <summary>
        /// Logs which of the mod's icon addresses the game registered, once per
        /// session, as a warning when fewer than all of them are there. The addresses
        /// are compared as <c>ToString()</c> output against
        /// <see cref="IconTable.ModIconAddresses"/>; when none match, every
        /// registered address is printed so a format mismatch is visible.
        /// </summary>
        private static void LogIcons()
        {
            if (!ScriptableData.TryGetDataBlocks<MapMarkerIconDataBlock>(out var blocks) || blocks == null)
            {
                Debug.LogWarning("[MapMarkersEnhanced] icons: no MapMarkerIconDataBlock list registered");
                return;
            }

            var found = new StringBuilder();
            var indices = new StringBuilder();
            int count = 0;
            foreach (string wanted in IconTable.ModIconAddresses)
            {
                for (int i = 0; i < blocks.Count; i++)
                {
                    if (blocks[i] != null && blocks[i].address.ToString() == wanted)
                    {
                        count++;
                        found.Append(' ').Append(wanted);
                        indices.Append(' ').Append(i);
                        break;
                    }
                }
            }

            string line = $"[MapMarkersEnhanced] icons: {count}{found} (indices:{indices} of {blocks.Count})";
            if (count < IconTable.ModIconAddresses.Length)
            {
                // A missing icon turns every marker using it into the game's fallback sprite.
                Debug.LogWarning($"{line}; only {count} of {IconTable.ModIconAddresses.Length} registered");
            }
            else
            {
                Debug.Log(line);
            }

            if (count == 0)
            {
                var all = new StringBuilder();
                for (int i = 0; i < blocks.Count; i++)
                {
                    all.Append(' ').Append(blocks[i] == null ? "<null>" : blocks[i].address.ToString());
                }
                Debug.LogWarning($"[MapMarkersEnhanced] icons: none matched; registered addresses:{all}");
            }
        }
    }
}

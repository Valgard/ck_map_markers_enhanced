# Manual tests

This mod has no C# test harness, so behaviour that only the running game can
show is checked here, in game, after a build. Each section lists what to check,
then what the last run found.

## Reading the log

Every line the mod writes starts with `[MapMarkersEnhanced]`, so
`grep MapMarkersEnhanced Player.log` shows all of them. A healthy session prints
only these, each at most once:

- `Mod initialized.` — at load.
- `icons: 5 <addresses> (indices: <i> … of <count>)` — once the game data is
  loaded; the five addresses are `ModIconAddresses` in `IconTable.g.cs`.
- `icon order: moved <n>, ours at <indices> of <count>` — the first time the
  marker dialog opens; `<indices>` are the last five of `<count>`.
- `restored <n> legacy markers` — only on a world with MapMarkers+ markers the
  1.3 migration turned into question marks, and only on the first load there. It
  comes from the server world, so with a dedicated server it is in the server's
  log, not the client's.
- `converted <n> presets` — only when a preset pointed at one of the variants
  the dialog no longer offers, and then once per session.
- `converted <n> markers to vanilla icons` — only on a world with markers that
  use one of those variants. It comes from the server world, so with a dedicated
  server it is in the server's log, not the client's.

Anything else is a warning or an error. Each is logged once per session (the
restoration ones once per world), never per frame:

- `icons: no MapMarkerIconDataBlock list registered` — the game has no icon list
  at all, so the icon type or its loading changed in a game update. Check the
  decompile for `MapMarkerIconDataBlock` and `ScriptableData.TryGetDataBlocks`.
- `icons: <n> <addresses> (indices: … of <count>); only <n> of 5 registered` —
  some of the mod's icons did not load, and markers using a missing one show
  the game's fallback sprite. Check that the five `.asset` files are in the
  build and that `uv run tools/generate_icons.py --check` passes.
- `icons: none matched; registered addresses: <all addresses>` — follows the
  line above when not one icon matched. Compare the printed addresses with
  `ModIconAddresses`: a different format means `DataBlockAddress.ToString()`
  changed, the same format means the icons were not loaded.
- `icon order failed with an exception; icons stay where the game put them` —
  followed by the exception. The dialog still opens, the mod's icons most likely
  in front of vanilla's; the stack trace names the cause.
- `icon order: no MapMarkerIconDataBlock list registered` — as the `icons:`
  line of the same text, seen from the dialog.
- `icon order: the icon list is not a List<>, so it cannot be reordered; icons
  stay in front` — `ScriptableData.TryGetDataBlocks` now hands out another
  collection type. Check its return value in the decompile.
- `icon order: the reorder did not stick (the list is not live); icons stay in
  front` — the list is a copy rather than the game's own, so the dialog reads
  another one. Check what `PopulateIconRow` iterates.
- `icon order: only <n> of the mod's 5 icons are registered` — as the `only <n>
  of 5 registered` line above.
- `icon order: the mod's icons are at the end but not in table order` — the
  addresses no longer sort in table order. Check the address rule in
  `CLAUDE.md` and run `uv run tools/generate_icons.py --check`.
- `cannot scroll the marker dialog to a mod icon: <problem>` — a preset with a
  mod icon opened with its icon or variant out of view. `<problem>` is one of
  `the icon row has no selected tile for it` (the icon is missing from the row,
  or the game's selection works differently), `the selected tile has no
  UIComponentMonoBehaviour`, `the scrollable's content has no
  UIComponentMonoBehaviour` or `no ScrollableUIComponent above the selected
  tile` (the dialog's UI hierarchy changed). Check the icon lines above first,
  then `MapMarkerCustomizationPanel` in the decompile.
- `could not scroll the marker dialog to the selection: <exception>` — the
  scroll threw. The dialog still works, unscrolled; the exception names the
  cause.
- `skipped <n> legacy markers that are not the migration's question mark
  (expected <address> variant 9, e.g. <address> variant <v>); they are not
  restored` — markers still carry a MapMarkers+ amount but not the icon the
  migration is known to write. On 1.3.0.2 a player cannot produce this, since a
  placed marker cannot be edited, so it most likely means a game update changed
  what the version-13 migration writes, and restoration no longer runs. Compare
  the example with `QuestionMarkAddress` and `QuestionMarkVariant` in
  `MarkerMigrationSystem.cs` and with `ConvertOldMapMarkersSystem` in the
  decompile.

Three errors, each followed by the exception:
`legacy marker table could not be parsed; restoration is off` (an address in
`IconTable.g.cs` does not parse — regenerate and check), `vanilla target table
could not be parsed; conversion is off` (the same for `ToVanilla`; restoration
keeps running) and `marker migration failed; will keep trying silently` (a pass
threw; the stack trace names the cause).

## Icons in the dialog and on the map

Open the map-marker dialog (create a marker on the large map).

- `Player.log` holds `Successfully compiled MapMarkersEnhanced` and one
  `[MapMarkersEnhanced] icons: 5 <address> …` line whose five addresses equal
  `ModIconAddresses` in `IconTable.g.cs`; no error line names the mod or one of
  its icons.
- The dialog shows five extra icons — General, Ores and Gems, Flags, Numbers,
  Letters — each with all of its variants (Ores and Gems: 11, Copper included;
  Letters: A–Z).
- Place one marker per icon: each shows its icon on the large map and on the
  minimap.
- Restart the game: every placed marker still shows its icon.

**Result, 2026-09-29 (CK 1.3.0.2):**

Passed, with one known limitation. All five addresses were registered as in the
table; the dialog showed every icon and variant; five placed markers (cross,
flag, 6, F, an ore) showed their icons on the large map and kept them after a
restart. **On the minimap, Numbers and Letters are too large**: they use their
full-size sprite, which fills the cell and overlaps neighbouring markers. The
slots below them in the sheet are blank placeholder buttons, not usable small
sprites — kept for 1.0.0, redraw planned in `docs/roadmap.md`.

## Icon order and scrolling

- The icon row reads: the vanilla icons (8), then General, Ores and Gems, Flags,
  Numbers, Letters.
- Close and reopen the dialog five times: the order stays the same and no tiles
  are added.
- `Player.log` holds one `[MapMarkersEnhanced] icon order: moved <n>, ours at
  <indices> of <count>` line per session, and `<indices>` are the last five
  indices of `<count>` (with 13 icons in total: `8,9,10,11,12 of 13`); no icon
  order warning.
- Edit a preset that uses a mod icon deep in the row (e.g. Letters, variant Z):
  on open, both the selected icon and the selected variant are visible without
  scrolling. A preset with a vanilla icon still opens at the start of the row.

**Result, 2026-09-29 (CK 1.3.0.2):**

Passed. Log: `moved 13, ours at 8,9,10,11,12 of 13`, no warning; repeated
opening kept the order. Scrolling was added after the first run showed the row
opening at its start, with the mod's icons now out of view — an ore preset, a
Letters/Z preset and a vanilla preset then all opened correctly.

## Legacy restoration

Only ever on a copy of a world whose MapMarkers+ markers went through the 1.3
migration, never on a live save. How the copy was made: with the game closed,
back up `worlds/`, `worldinfos/` and `maps/`; copy `worlds/<n>.world.gzip` to a
free slot number and `worldinfos/<n>.worldinfo` beside it, changing only its
`"name"`. The copy keeps the original's `guid`; that caused no problem here.
Load the copy with the mod enabled.

- Every question mark the migration made of a MapMarkers+ marker shows its
  original icon again, and `Player.log` holds one `[MapMarkersEnhanced] restored
  <n> legacy markers` line.
- Restart the game and load the copy again: every restored marker still shows
  its icon, and no further `restored` line appears. A scan of the saved copy
  (method: `docs/ck/savegame-formats.md` in the parent repository) shows the
  restored markers at `Amount` 1 and none left at `6000 +` a mapped type — the
  check that settles whether a changed `Amount` on an existing entity is
  persisted.
- When the game can edit placed markers: a question mark renamed before the
  mod's first load becomes its icon and keeps its name; one restyled to another
  icon stays as it was; a restored marker set back to the question mark stays a
  question mark after a restart.

**Result, 2026-09-29 (CK 1.3.0.2, single-player copy):**

- `restored 62 legacy markers`, once. The map showed ores and music notes where
  the question marks were; no unresolved icon in the log.
- Save scan before/after: 62 markers at `6016`–`6028` before, none at or above
  `6000` after — a changed `Amount` on an existing entity **is** persisted.
- Second launch of the same copy: no further `restored` line.
- **Not testable in 1.3.0.2:** the renamed, restyled and set-back cases. The
  game cannot edit a placed marker — `MapUI.ApplyEditToExistingMarker` exists
  but has no caller — so these states cannot be produced. The guards stay;
  `docs/roadmap.md` ("Edit a placed marker") notes that they become testable
  once editing exists.
- Marker counts by byte-pattern scan, player markers at `Amount` 1 / legacy:
  original world 9 / 62, copy before 9 / 62, after the restoring launch 72 / 0,
  after the next launch **71 / 0** = 9 + 62. The extra record in the first save
  was transient — a stale entity-pool record the next save dropped — so compare
  two consecutive saves before trusting such a count.

## Legacy restoration on a dedicated server

A fresh copy of the MapMarkers+ world in its own slot, served by the local
dedicated server with the mod installed (normal `relink`).

**Result, 2026-09-29 (CK 1.3.0.2):**

Passed. The server log shows `restored 62 legacy markers` only after a player
joined — an empty server does not simulate — and the map showed the restored
icons. After a clean server stop, the saved world held no marker at or above
`6000` and 71 = 9 + 62 player markers at `Amount` 1. The dedicated server's
later `IMod.Init()` does not affect the restore system: it is a managed system
that needs no Burst workaround.

## Hidden variants in the marker dialog

Five variants are no longer offered, because vanilla has the same motif: General
0 (question mark), 3 (cross), 16 (skull), 17 (red skull) and Ores and Gems 0
(ancient crystal). Open the map-marker dialog.

- General shows 18 variants, none of them the `?`, the `X`, the skull or the red
  skull; Ores and Gems shows 10, no diamond; Flags 14, Numbers 10, Letters 26.
- The icon-row preview of General shows `!`, and that of Ores and Gems copper,
  while the icon is not selected.
- Select Flags variant 3, then switch to General: the selection lands on index
  4 (`ArrowLeft`), the next visible tile after the hidden index 3.
- Switch General, Flags, General: Flags still shows 14 tiles.
- Move left and right with keyboard or controller across General's gaps (2 to
  4, 15 to 18) and through all of Flags: the selection never stops on an
  invisible tile.
- The row has no visible gap where tiles are hidden.
- Place a marker from each visible tile: each works and shows its icon.

**Result:** Not run yet.

## Presets on hidden variants

- Before installing the build, with the 1.0.0 mod, set one preset to General 0
  (`?`) and one to General 3 (`X`).
- After the first launch with the build: `Player.log` holds `converted 2
  presets`, and both presets open on the vanilla question mark (yellow) and the
  vanilla cross (yellow), names kept.
- Second launch: no `converted … presets` line.
- Open the marker dialog from a preset that still points at a hidden variant
  (one the rewrite did not reach), using the map's preset buttons: the variant
  row selects a visible tile, and a marker placed with it is converted to its
  vanilla counterpart by the world.

**Result:** Not run yet.

## World conversion to vanilla icons

Only ever on a copy of a world, never on a live save.

- With 1.0.0, place one marker each with General 0, 3, 16, 17 and Ores and Gems
  0, plus one FlagGreen. Load the world with the new build: `converted 5 markers
  to vanilla icons`; the five show the vanilla motifs (yellow `?`, yellow `X`,
  white skull, red skull, blue diamond); the FlagGreen is unchanged.
- On the copy from "Legacy restoration" (62 restored markers): the restored
  `Cross` and `SkullRed` markers turn vanilla, and the log reads `converted <n>
  markers to vanilla icons` with `<n>` the number of restored Cross and SkullRed
  markers on that copy; no new `restored` line appears.
- With the mod switched off on that copy, the five converted markers still show
  their icons.
- Dedicated server with the mod, on a copy of the first check's world: after a
  player joins, the server log (not the client's) holds `converted 5 markers to
  vanilla icons`, and the five show the vanilla motifs.

**Result:** Not run yet.

## Server without the mod

Local dedicated server (`utils/server.sh`), started with the mod on the client's
`disabledMods` for the duration of `start` only — `relink` mirrors every mod the
client has enabled — and switched back on for the client afterwards.

- Join from a client that has the mod: no mod dialog, no version error.
- Place a marker with one of the mod's icons, stop the server (quit handlers
  run, world written), start it again the same way, rejoin: the marker still
  shows its icon.
- With a marker that uses a hidden variant already in the world (placed with the
  1.0.0 mod or an old preset before the rewrite): the server log holds no
  `converted … markers to vanilla icons` line, the marker is not converted, and
  it still renders with its mod icon for a client that has the mod.

**Result, 2026-09-29 (CK 1.3.0.2), first two checks only; the hidden-variant
check has not been run:**

Passed. The server log lists 31 loaded mods, none of them MapMarkers — that is
what shows the server ran without the mod. Both joins raised no mod dialog; the
client log shows no unresolved icon and no join error.

## Without the mod on the client

Load a world that holds markers placed with the mod's icons while the mod is
switched off on the client — the state a player is in after uninstalling, or a
player without the mod on a shared world.

**Result, 2026-09-29 (CK 1.3.0.2):**

Right after launch such a marker showed a blue diamond — the marker prefab's
default sprite, since its display element was freshly instantiated — not
nothing, and `Player.log` repeats `Failed to resolve MapMarkerIconDataBlock at
address <address> for map marker entity …` on every redraw (over 1000 lines in a
few minutes for two markers). Re-enabling the mod brings the icons back.

The diamond is not guaranteed: the game assigns no sprite when the icon cannot
be resolved, and it reuses display elements from a pool without resetting their
sprite, so a reused element can go on showing another marker's icon. That case
was not observed in this run.

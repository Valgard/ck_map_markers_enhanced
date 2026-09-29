# Manual tests

This mod has no C# test harness, so behaviour that only the running game can
show is checked here, in game, after a build. Each section lists what to check,
then what the last run found.

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

## Server without the mod

Local dedicated server (`utils/server.sh`), started with the mod on the client's
`disabledMods` for the duration of `start` only — `relink` mirrors every mod the
client has enabled — and switched back on for the client afterwards.

- Join from a client that has the mod: no mod dialog, no version error.
- Place a marker with one of the mod's icons, stop the server (quit handlers
  run, world written), start it again the same way, rejoin: the marker still
  shows its icon.

**Result, 2026-09-29 (CK 1.3.0.2):**

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

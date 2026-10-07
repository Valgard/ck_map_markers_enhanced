# Manual tests

This mod has no C# test harness, so behaviour that only the running game can
show is checked here, in game, after a build. Each section lists what to check,
then what the last run found.

## Reading the log

Every line the mod writes starts with `[MapMarkersEnhanced]`, so
`grep MapMarkersEnhanced Player.log` shows all of them. A healthy session prints
only these, each at most once except the conversion line below:

- `Mod initialized.` — at load.
- `icons: 7 <addresses> (indices: <i> … of <count>)` — once the game data is
  loaded; the seven addresses are `ModIconAddresses` in `IconTable.g.cs`.
- `icon order: moved <n>, ours at <indices> of <count>` — the first time the
  marker dialog opens; `<indices>` are the last seven of `<count>`.
- `restored <n> legacy markers` — only on a world with MapMarkers+ markers the
  1.3 migration turned into question marks, and only on the first load there. It
  comes from the server world, so with a dedicated server it is in the server's
  log, not the client's.
- `converted <n> presets` — only when a preset pointed at a retired 1.x variant,
  and then once per session.
- `converted <n> markers on retired icons` — only on a world with markers that
  use a retired 1.x variant. It comes from the server world, so with a dedicated
  server it is in the server's log, not the client's. Unlike the others it can
  appear on any pass that converts something, so again whenever such a marker
  turns up later (for instance one placed by a 1.x client).

Anything else is a warning or an error. Each is logged once per session (the
ones from the server world once per world), never per frame:

- `icons: no MapMarkerIconDataBlock list registered` — the game has no icon list
  at all, so the icon type or its loading changed in a game update. Check the
  decompile for `MapMarkerIconDataBlock` and `ScriptableData.TryGetDataBlocks`.
- `icons: <n> <addresses> (indices: … of <count>); only <n> of 7 registered` —
  some of the mod's icons did not load, and markers using a missing one show
  the game's fallback sprite. Check that the seven `.asset` files are in the
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
- `icon order: only <n> of the mod's 7 icons are registered` — as the `only <n>
  of 7 registered` line above.
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
- `icon target <address> variant <v> is not a registered map marker icon with
  that variant; markers that would be restored or converted to it are left as
  they are` — from the server world, once per target and world. The block a
  restoration or conversion would write is not registered or has fewer
  variants: a game update dropped or renumbered a vanilla block, or one of the
  mod's own icons did not load (see the `icons:` lines). Nothing was written; a
  legacy marker keeps its MapMarkers+ amount and is restored once the target
  resolves. Compare the address with `tools/icons.toml` and the game's current
  `MapMarkerIconDataBlock` list.
- `game data still not loaded after 10 passes; <n> restorations and <m>
  conversions wait` — from the server world, once per world. Markers need
  restoring or converting, but `ScriptableData.isLoaded` has stayed false for
  ten passes, so no target can be checked and nothing is written; the system
  keeps waiting. Check the game's data loading in the log before this line.
- `preset target <address> variant <v> is not a registered map marker icon with
  that variant; preset <n> is left as it is` — the same, for a preset, on the
  player's computer, once per session.
- `preset conversion failed; remaining presets stay as they are` — followed by
  the exception; presets before the failing slot may already be rewritten. Check
  `PrefsManager.GetMapMarkerPreset`/`SetMapMarkerPreset` in the decompile.

Five errors, each followed by the exception: `legacy marker table could not be
parsed; restoration is off` (an address in `IconTable.g.cs` does not parse —
regenerate and check), `retired icon table could not be parsed; conversion is
off` (the same for `Retired`; restoration keeps running), `legacy restoration
failed; conversion still runs, restoration will keep trying silently` and
`conversion of retired icons failed; restoration still runs, conversion will
keep trying silently` (one rule's writes threw; the other rule is unaffected),
and `marker migration failed: the scan threw, so neither rule ran; will keep
trying silently` (the shared scan threw; the stack trace names the cause). One
cause of the last seen in practice is `Exception: This method should have been
replaced by codegen`: the build shipped without
`Scripts/Generated/MarkerMigrationSystem__System_*.g.cs`, so `Player.log` also
lacks `Replacing method MapMarkersEnhanced.MarkerMigrationSystem/Scan_T0 …`
(`Pass_T0` in builds before the scan had a method of its own). `utils/build.sh`
now guards against it (exit 4); rebuild, and the build output must contain
`Adding generated file …MarkerMigrationSystem__System_…g.cs`.

## Icons in the dialog and on the map

Open the map-marker dialog (create a marker on the large map).

- `Player.log` holds `Successfully compiled MapMarkersEnhanced` and one
  `[MapMarkersEnhanced] icons: 7 <address> …` line whose seven addresses equal
  `ModIconAddresses` in `IconTable.g.cs`; no error line names the mod or one of
  its icons.
- The dialog shows seven extra icons — General, Ores, Flags, Tapestry, Orbs,
  Numbers, Letters — each with all of its variants (counts 18, 11, 14, 15, 19,
  10, 26) in the order of the Pixaki's layers.
- Place one marker per icon: each shows its icon on the large map and on the
  minimap.
- Restart the game: every placed marker still shows its icon.

**Result, 2026-09-29 (CK 1.3.0.2, version 1.0.0 with five icons; not yet run for
2.0.0):**

Passed, with one known limitation. All five addresses were registered as in the
table; the dialog showed every icon and variant; five placed markers (cross,
flag, 6, F, an ore) showed their icons on the large map and kept them after a
restart. **On the minimap, Numbers and Letters are too large**: they use their
full-size sprite, which fills the cell and overlaps neighbouring markers. The
slots below them in the sheet are blank placeholder buttons, not usable small
sprites — kept for 1.0.0, replaced by the 2.0.0 redraw.

## Icon order and scrolling

- The icon row reads: the vanilla icons (8), then General, Ores, Flags,
  Tapestry, Orbs, Numbers, Letters.
- Close and reopen the dialog five times: the order stays the same and no tiles
  are added.
- `Player.log` holds one `[MapMarkersEnhanced] icon order: moved <n>, ours at
  <indices> of <count>` line per session, and `<indices>` are the last seven
  indices of `<count>` (with 15 icons in total: `8,9,10,11,12,13,14 of 15`); no
  icon order warning.
- Edit a preset that uses a mod icon deep in the row (e.g. Letters, variant Z):
  on open, both the selected icon and the selected variant are visible without
  scrolling. A preset with a vanilla icon still opens at the start of the row.

**Result, 2026-09-29 (CK 1.3.0.2, version 1.0.0; not yet run for 2.0.0):**

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

_Historical: version 1.1.0 only. 2.0.0 hides nothing and the patches are gone;
the checks are kept as the record of what was run._

Five variants are no longer offered, because vanilla has the same motif: General
0 (question mark), 3 (cross), 16 (skull), 17 (red skull) and Ores and Gems 0
(ancient crystal). Open the map-marker dialog.

- General shows 18 variants, none of them the `?`, the `X`, the skull or the red
  skull; Ores and Gems shows 10, no diamond; Flags 14, Numbers 10, Letters 26.
- The icon-row preview of General shows `!`, and that of Ores and Gems copper,
  while the icon is not selected.
- Switching icons keeps the selection's visible position, not its index. With
  General's first visible tile (`!`, index 1) selected, switch to Flags: the
  first flag is selected. Select Flags' 4th flag (index 3), switch to General:
  its 4th visible tile is selected, which is index 5 (General's visible order is
  1, 2, 4, 5, ...). Ores and Gems behaves the same way. Reopening the dialog or
  resetting to the default still selects by index.
- Switch General, Flags, General: Flags still shows 14 tiles.
- Move left and right with the controller (the dialog has no keyboard
  navigation) across General's gaps (2 to 4, 15 to 18) and through all of Flags:
  the selection never stops on an invisible tile.
- The row has no visible gap where tiles are hidden.
- Place a marker from each visible tile: each works and shows its icon.

**Result, 2026-10-06 (CK 1.3.0.4, single-player, build edcc457):**

- The dialog offers 18 variants in General (no `?`, `X`, skull or red skull), 10
  in Ores and Gems (no diamond), 14 in Flags, 10 in Numbers and 26 in Letters.
  The icon-row preview shows `!` for General and copper for Ores and Gems; the
  row has no visible gaps.
- A first build carried the selected index across icon switches, so switching
  from General to another icon landed one tile too far (Ores and Gems happened to
  be right). edcc457 keeps the visible position instead. Retested: General's
  first visible tile selects Flags' first flag, and Flags' 4th flag selects
  General's 4th visible tile (index 5, the right arrow).
- The dialog has no keyboard navigation, so that check does not apply.
  **Controller navigation was not tested** (no controller available).
- No result was recorded for the Flags tile count after switching back, or for
  placing a marker from every visible tile.

## Presets on hidden variants

_Historical: version 1.1.0. The 2.0.0 preset check is under "Icon rework
in game" below._

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

**Result, 2026-10-06 (CK 1.3.0.4, single-player):**

- `Player.log` holds `[MapMarkersEnhanced] converted 2 presets`. The two presets
  set with 1.0.0 on `?` and `X` showed the yellow vanilla question mark and the
  yellow vanilla cross, names kept. Presets can only be checked inside a world,
  because the map exists only there.
- Not tested: the second launch (absence of the line) and a preset that still
  points at a hidden variant.

## World conversion to vanilla icons

_Historical: version 1.1.0, with the log texts of that version (`converted <n>
markers to vanilla icons`). 2.0.0 logs `converted <n> markers on retired icons`;
see "Icon rework in game"._

Only ever on a copy of a world, never on a live save.

- With 1.0.0, place one marker each with General 0, 3, 16, 17 and Ores and Gems
  0, plus one FlagGreen. Load the world with the new build: `converted 5 markers
  to vanilla icons`; the five show the vanilla motifs (yellow `?`, yellow `X`,
  white skull, red skull, blue diamond); the FlagGreen is unchanged.
- **Not applicable to the copy from "Legacy restoration":** its 62 restored
  markers are all types `6016`–`6028`, with no `Cross` (`6072`) or `SkullRed`
  (`6073`) among them, so nothing there converts and no `converted` line can
  appear. The path it was meant to cover — a `Cross` or `SkullRed` restored by
  1.0.0 and then converted by 1.1.0 — needs a world that holds such a marker,
  and has not been run in game.
- With the mod switched off on that copy, the five converted markers still show
  their icons.
- Dedicated server with the mod, on a copy of the first check's world: after a
  player joins, the server log (not the client's) holds `converted 5 markers to
  vanilla icons`, and the five show the vanilla motifs.

**Result, 2026-10-06 (CK 1.3.0.4):**

- Single-player copy "MME Vanilla Test", markers placed with 1.0.0: `converted 5
  markers to vanilla icons`. The five became a yellow `?`, a yellow `X`, a white
  skull, a red skull and a blue diamond, as vanilla, without a frame; the MME
  green flag stayed.
- Uninstall check, with the MME dev build uninstalled and the mod.io
  subscription disabled: the five converted markers kept their icons. The MME
  green flag showed the fallback sprite, the blue diamond — the prefab default
  `map_markers_1`, 1.2's first user marker (see `docs/ck/world-and-mechanics.md`
  in the parent repository).
- Legacy chain on a pre-1.3 backup (a copy of a 2026-08-16 world, loaded in
  1.3.0.4): the game logged `Converted 67 old map markers` and the mod `restored
  60 legacy markers`. The map showed ores, notes and so on instead of question
  marks; the question marks and white skulls that remain were created by vanilla.
- Cross and SkullRed through a 1.2.1.5 round trip (Steam branch 1.2.1.5,
  MapMarkers+ enabled, a fresh copy of the same backup): 12 markers placed with
  MapMarkers+, including a red skull. **No cross was placed** (forgotten). Back on
  1.3.0.4 the game logged `Converted 79 old map markers` and the mod `restored 68
  legacy markers` (8 new). The red skull came back as the vanilla red skull, no
  frame; `!`, a note, a heart, copper, 5, 1 and a white flag came back as MME
  icons; `?`, the white skull, the diamond and the green flag were vanilla (the
  game's own conversion). The cross is covered by the generator test (6072 to
  Cross 9) and the same code path, which was agreed with the owner, not by an
  in-game marker.
- Dedicated server, world "MME Server Test": see "Server without the mod" for
  the server without the mod, then **with** the new mod the server log read
  `converted 5 markers to vanilla icons` and the client showed the five as
  vanilla. Live, same server with the new mod, client on 1.0.0 (which still
  offers the hidden variants, and may join: the join check matches mods by id or
  GUID, not by version): three markers placed on hidden variants were each
  converted on the next pass — server log `converted 1 markers to vanilla icons`
  three times — and the connected client's map switched to the vanilla icons
  without reopening it.
- A build problem met on the way: a rebuild without source changes shipped the
  mod without `Scripts/Generated/MarkerMigrationSystem__System_*.g.cs`. The system
  then logged `marker migration failed` with `Exception: This method should have
  been replaced by codegen`, and `Player.log` lacked `Replacing method
  MapMarkersEnhanced.MarkerMigrationSystem/Pass_T0 …`. Touch the system's `.cs`
  and rebuild, and check the build output for `Adding generated file
  …MarkerMigrationSystem__System_…g.cs`.

**Re-check after the review-gate fixes, 2026-10-06 (CK 1.3.0.4, branch build
with target resolution and per-rule failure isolation):**

- Dedicated server with the new build, client on 1.0.0, world "MME Server Test":
  the server log read `Replacing method
  MapMarkersEnhanced.MarkerMigrationSystem/Scan_T0 with __Scan_…`; twelve
  markers placed on hidden variants each produced one `converted 1 markers to
  vanilla icons` line and became the vanilla icons. No new warning.
- Single-player with the new build on a fresh copy of the 2026-08-16 backup
  ("MME Final Test"): `converted 1 presets`, the game's `Converted 67 old map
  markers`, then `restored 60 legacy markers` — the same count as before the
  fixes; the dialog still hid the five variants. No new warning.

## Icon rework in game (2.0.0)

Six checks, each on a copy of a world, never on a live save; results below.
Build with the shipped sources and check the build output for `Adding generated
file …MarkerMigrationSystem__System_…g.cs` first.

1. **A world placed with 1.0.0.** The world holds markers on all five 1.x
   blocks, including the five that duplicate a vanilla motif (a world that
   already ran 1.1.0 has those converted and cannot show that case). Load it
   with 2.0.0. Expect `converted <n> markers on retired icons` once, in the
   server world's log; the five duplicates are the game's own (yellow question
   mark, yellow cross, white skull, red skull, blue diamond) and every other
   marker shows the same-named, redrawn marker of the new set, names and
   positions kept. No `icon target …` warning. Reload: no further `converted`
   line.
2. **A MapMarkers+ world.** Load a copy of a world that went through the 1.3
   migration. Expect `restored <n> legacy markers` and the restored markers on
   the new set directly, with a MapMarkers+ cross and red skull as the game's
   own; no `converted` line for them.
3. **Presets.** With 1.0.0, set presets on a General, an Ores and a Letters
   marker plus one on `?` and one on `X`. Start 2.0.0 and open a world: expect
   `converted <n> presets`, each preset on the new marker (or the yellow
   vanilla `?` and `X`), names kept; a second launch prints no such line.
4. **Dedicated server.** With the mod on the server, a player joining makes the
   server log (not the client's) print the `converted` line, and a marker a 1.x
   client places on a retired icon is converted on the next pass; the client
   switches to the new icon without reopening the map. On a server without the
   mod (the mod on the client's `disabledMods` for `utils/server.sh start`
   only) nothing converts and 1.x markers show the stand-in diamond; record what
   is observed.
5. **Minimap.** Place one marker from every variant of every icon: each draws
   its own small sprite on the minimap, and Numbers and Letters no longer
   overlap their neighbours.
6. **The dialog.** The icon row reads the vanilla icons, then General, Ores,
   Flags, Tapestry, Orbs, Numbers, Letters, with 18, 11, 14, 15, 19, 10 and 26
   variants, each in its Pixaki layer order and with no gap. `Player.log` holds
   `icons: 7 …` and `icon order: moved <n>, ours at 8,9,10,11,12,13,14 of 15`.

**Result, 2026-10-07 (CK 1.3.0.4, local dedicated server):**

- **Dialog (6): passed.** Seven icons after the vanilla ones; `Player.log` read
  `icon order: moved 15, ours at 8,9,10,11,12,13,14 of 15`; the variant counts
  were 18, 11, 14, 15, 19, 10 and 26, without gaps.
- **Minimap (5): failed with the first cut, passed after the re-cut.** With
  sprites trimmed to their drawn pixels, mostly odd sizes such as 5×5 and 5×7,
  the small icons jittered against the map while the player moved; the large
  ones (8×8) were stable. Vanilla's marker sprites are fixed even boxes: the
  large sheet is 100×90 with 80 sprites of 10×10, the small sheet 60×54 with 80
  sprites of 6×6, 16 pixels per unit, pivot at the centre (checked on every
  sprite asset), and the game assigns them to the renderer unscaled. An odd
  size puts the centre pivot on half a pixel. The fix cuts every sprite as a box
  of the author's 10-pixel grid through the `cells` option of
  `utils/pixaki_to_sheet.py`: large is the 10×10 cell; small is a 6×6 box at
  cell offset (2,2), or 8×8 at (1,1) where the drawing does not fit 6×6. Result:
  113 large sprites of 10×10, 69 small of 6×6 and 44 small of 8×8 (letters,
  numbers, arrows, the flames, StructureStone, StructureWood and Shield). After
  the re-cut the minimap was stable.
- **World placed with 1.1.0 (1):** `converted 72 markers on retired icons`, none
  unresolved, no further line on a second launch. With markers and presets
  placed under 1.0.0, including the five vanilla duplicates: `converted 78
  markers on retired icons` and `converted 2 presets`; the duplicates became the
  game's own, the rest the new art, names and positions kept. Passed.
- **MapMarkers+ world (2):** a CK 1.2 backup loaded under 1.3 with 2.0.0: the
  game's own migration, then `restored 60 legacy markers`; no question marks
  left, none unresolved. Passed.
- **Dedicated server with the mod (4):** the server log read `converted 72
  markers on retired icons`; the client log had no such line, because the
  migration runs in the server world only. Passed.
- **Dedicated server without the mod (4), observed and accepted:** nothing
  converts. A 2.0.0 client shows old mod markers with the prefab's default
  sprite (1.2's blue diamond tile) in a fresh session; in a session whose pooled
  marker elements had shown resolved icons before, they show stale icons of
  other markers, off by one. With the big map open the framerate collapses: the
  client logs `Failed to resolve MapMarkerIconDataBlock at address … for map
  marker entity …` with a full native stack trace for every unresolved visible
  marker every frame, about 12 errors per second with roughly 70 markers
  affected, 6 per second with the map closed. The same world on the server
  with the mod had no such cost. Vanilla markers were unaffected. The owner
  chose to keep the 1.x addresses retired regardless.
- **Not testable locally:** a 1.x client on a 2.0.0 server, because the local
  server mirrors the client's installed build.

## Server without the mod

_Historical: recorded on 1.0.0 and 1.1.0, including the hidden-variant check
of 1.1.0. The 2.0.0 server checks are under "Icon rework in game"._

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

**Result, 2026-09-29 (CK 1.3.0.2), first two checks; the hidden-variant check
did not exist yet and has its own result below:**

Passed. The server log lists 31 loaded mods, none of them MapMarkers — that is
what shows the server ran without the mod. Both joins raised no mod dialog; the
client log shows no unresolved icon and no join error.

**Result, hidden-variant check, 2026-10-06 (CK 1.3.0.4, world "MME Server
Test"):**

Passed. With the server without the mod, the 1.0.0 client placed `?`, `X`, a
skull, a red skull and a diamond; the server log had no `[MapMarkersEnhanced]`
line. With the server still without the mod, the client switched to the new
build: the markers kept their MME icons, and the client log showed no conversion
and no unresolved icon.

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

# Manual tests

This mod has no C# test harness, so behaviour that only the running game can
show is checked here, in game, after a build.

## Task 4 — icon order

Open the map-marker dialog (create a marker on the large map).

- The icon row reads: the vanilla icons (8), then General, Ores and Gems, Flags,
  Numbers, Letters.
- Close and reopen the dialog five times: the order stays the same and no tiles
  are added.
- `Player.log` holds no `[MapMarkersEnhanced] icon order could not be changed;
  icons stay in front` warning.
- `Player.log` holds one `[MapMarkersEnhanced] icon order: moved <n>, ours at
  <indices> of <count>` line per session, and `<indices>` are the last five
  indices of `<count>` (with 13 icons in total: `8,9,10,11,12 of 13`).
- Edit a preset/marker that uses a mod icon deep in the row (e.g. Letters with
  variant Z): on open, both the selected icon and the selected variant are
  visible without scrolling.

## Task 5 — legacy restoration

Only ever on a copy of a world that MapMarkers+ markers went through the 1.3
migration in, never on a live save. Load the copy with the mod enabled.

- Every question mark the migration made of a MapMarkers+ marker shows its
  original icon again, and `Player.log` holds one `[MapMarkersEnhanced] restored
  <n> legacy markers` line.
- A question mark that was renamed before loading becomes its icon and keeps
  its name.
- A marker that was restyled before loading (another icon or variant than the
  question mark) stays exactly as it was.
- Restart the game and load the copy again: every restored marker still shows
  its icon. A scan of the saved copy (method: `docs/ck/savegame-formats.md` in
  the parent repository) shows the restored markers at `Amount` 1 and none left
  at `6000 +` a mapped type. This is the check that settles whether a changed
  `Amount` on an existing entity is persisted.
- Set one restored marker back to the question mark, then restart: it stays a
  question mark (AC5).
- A fresh world, and the copy after its first restored pass, log no further
  `restored` line (Review Focus 2).

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

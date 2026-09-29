# MapMarkersEnhanced — roadmap

Planned, not-yet-built work after 1.0.0. Each point stands on its own; pick the
next one, and let the version number collect whatever has shipped.

## Redraw the small marker buttons

On the minimap, Numbers and Letters currently use their **large** sprite, which
fills the whole cell and overlaps neighbouring markers. moorowl's sheet has a
slot 10 px below each of them, but those slices are blank two-colour placeholder
buttons with no glyph, so they were left unused for 1.0.0.

- **Plan:** redraw the small buttons — borderless, in Core Keeper 1.3's own
  style — for Numbers and Letters, and possibly for every icon so the set looks
  consistent.
- **Wiring once the art exists:** name each slice `markers_<type>_small` in
  `markers.png.meta`, set `small` for those variants in `tools/icons.toml`, and
  extend the small-sprite test so Numbers and Letters require one. No address
  changes, so markers placed with 1.0.0 pick up the new buttons without a
  migration.

## Edit a placed marker

Core Keeper 1.3.0.2 cannot edit a marker once it is placed: the only way to
rename it or change its icon is to delete it and place a new one from a preset.
The game already contains the edit path — `MapUI.ApplyEditToExistingMarker`
(`Pug.Other:345602`) and the `EditCustomMapMarker` command, whose server handler
updates icon, variant and name of an existing marker (`Pug.Other:413849`) — but
nothing calls it.

- **Idea:** open the customization dialog on an existing marker (e.g. from its
  context action on the map) and route the confirm to `ApplyEditToExistingMarker`.
- **Hypothesis, not verified:** that the dead path works as-is once called. It
  may be unfinished, and Pugstorm may ship the feature themselves — check the
  current game version before building anything.
- **Interaction with the legacy restoration:** editing makes the restoration's
  guards reachable for the first time — a question mark renamed or restyled
  before the mod first sees the world. Those guards are designed for it but so
  far only argued from code; test them in game when this lands.

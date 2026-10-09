# MapMarkersEnhanced — roadmap

Planned, not-yet-built work. Each point stands on its own; pick the
next one, and let the version number collect whatever has shipped.

## Edit a placed marker

Core Keeper 1.3.0.2 cannot edit a marker once it is placed: the only way to
rename it or change its icon is to delete it and place a new one from a preset.
The game already contains the edit path — `MapUI.ApplyEditToExistingMarker`
(`Pug.Other:345602`) calls `PlayerCommandSystem.EditCustomMapMarker`
(`Pug.Other:413566`), which sends the same `MapMarkerRpc` as placing a marker,
with a target entity set; the server's edit branch then overwrites that marker's
icon, variant and name (`Pug.Other:413869`) — but nothing calls
`ApplyEditToExistingMarker`.

- **Idea:** open the customization dialog on an existing marker (e.g. from its
  context action on the map) and route the confirm to `ApplyEditToExistingMarker`.
- **Hypothesis, not verified:** that the dead path works as-is once called. It
  may be unfinished, and Pugstorm may ship the feature themselves — check the
  current game version before building anything.
- **Interaction with the legacy restoration:** editing makes the restoration's
  guards reachable for the first time — a question mark renamed or restyled
  before the mod first sees the world. Those guards are designed for it but so
  far only argued from code; test them in game when this lands.

## More than five presets

The marker bar holds five presets. With seven extra icons and up to 26 variants
each, five quick slots run out fast.

- **What the game does:** five is a literal in six places — the preset bar's
  construction (`Pug.Other:344430`), `MapUI.EnsurePresetsInitialized`
  (`345773`), and four range checks in `MapUI` (`345426`, `345440`, `345449`,
  `345457`). The prefs list itself grows on demand
  (`PrefsManager.SetMapMarkerPreset`), so storage needs no change. Presets live in
  the client prefs, not in the world, so this part needs no server.
- **Approach:** a transpiler would need `OpCodes` from `System.Reflection.Emit`,
  which the sandbox denies; whether Harmony helpers outside the deny list avoid
  naming it is untested. The fallback is prefixes that reimplement those six
  methods with the mod's own limit — each one a copy of vanilla code that can
  drift at the next update.
- **Trap:** the bar hides a slot whose preset has no icon, and
  `EnsurePresetsInitialized` only fills slots 0–4, so slots 5 and up must be
  pre-filled or they can never be opened.
- **Unknown:** how many slots the bar can show before it overflows; decide the
  limit from a look at the prefab or in game.

## Make the way into the dialog visible

The marker dialog opens with a right-click on a slot of the big map's preset
bar, and nothing on that bar says so until the cursor hovers a slot and the
game's tooltip appears. A player coming from MapMarkers+, whose own drop-down
arrow sat next to the default icons, did not find the dialog at all and took the
mod for broken (Core Keeper Discord, modding-help channel, 2026-10-08/09); the
log showed it loaded and working.

- **Idea:** a permanent cue on the bar — an arrow or a hint glyph on the slots —
  rather than a change to the dialog itself.
- **Cost:** the bar is the game's prefab, not the mod's data, so this is the
  first piece of UI the mod would touch; until now it only adds data and reorders
  a list.
- **Neighbour, not part of this:** the red slot on the far left of the same bar
  deletes every marker on the map. A cue that draws the eye to the bar also
  draws it there.

## Fewer pages to reach the mod's icons

The dialog's icon row shows the game's icons first and the mod's seven after
them, so every customisation starts with paging right. `IconOrderPatch` puts
them there on purpose — ADR 001's "Icons behind vanilla's". The reason, which
the ADR does not state: the game's own icons come first out of respect for its
developers, and a mod's additions follow them.

- **Not an option:** moving the mod's icons ahead of the game's. Any fix has to
  shorten the way to them while vanilla keeps the front.
- **Check first:** how much paging remains in practice. `ScrollToSelectionPatch`
  already scrolls the icon row to the preset's current icon, so a preset that
  sits on a mod icon opens on the right page; the paging is mainly the first
  time, from a vanilla preset.

## A compact picker with every marker at once

Suggested by the same player: an arrow that opens one panel listing every
marker, the way MapMarkers+ did, instead of the dialog's two linked rows with
back-and-forth between icon and variant.

- **Cost:** a picker of the mod's own beside the game's dialog — prefab, input
  handling, and writing the chosen icon and variant into a preset the way the
  dialog does. ADR 001 rejected exactly this as its "Hybrid" option: the game
  already ships a picker, so a second one is duplicated work to keep alive, and
  the vanilla rows turned out to carry the volume. Building it means revisiting
  that decision, not just adding a feature.
- **Against it, beyond the ADR:** one panel with every marker gets harder to use
  as the set grows, and it grows with every icon added — where two
  linked rows scale by adding a tile. A panel would need its own answer to that
  before it is easier than what it replaces.
- **Overlaps the two points above:** if this lands, it replaces both; if it
  does not, they stand on their own.

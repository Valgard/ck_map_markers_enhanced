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

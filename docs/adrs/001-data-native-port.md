# Ship the markers as game data, not as a ported UI

- Status: accepted
- Date: 2026-09-29

## Context and Problem Statement

MapMarkers+ does not load on Core Keeper 1.3: its code rests on
`UserMapMarkerType` and `UserMapMarkerToggle`, which 1.3 removed along with the
whole four-slot marker system. What replaced it is open-ended. An icon is a
`MapMarkerIconDataBlock` with a list of sprite variants; a marker stores an icon
address, a variant index and an optional name; the player picks from a dialog
with an icon row and a variant row and keeps five presets. MapMarkers+ had built
its own drawer and its own client/server commands to get what the game now does
natively.

A second problem came with the update. MapMarkers+ saved each of its markers in
the vanilla slot `Marker2` and kept its real type in the entity's unused
`Amount` (`6000 + PlusMarkerType`). The 1.3 world migration converts old markers
by slot only, so every one of them became the same question mark, while `Amount`
survived untouched. How should the mod return to 1.3, and what happens to those
markers?

## Decision Drivers

- Survive the next UI rework: the less of the game's UI the mod reproduces, the
  less there is to break.
- Saved markers must keep their icon across restarts, updates of this mod, and
  servers that do not have it.
- A server should not need the mod, so players can keep joining unmodded
  servers.
- Sandbox-clean: no reflection, no `System.IO`.

## Considered Options

1. **Straight port** — rebuild the drawer UI and its networking on 1.3's types.
2. **Hybrid** — native icons, plus a slim picker of the mod's own in case the
   vanilla rows could not hold 83 markers.
3. **Data-native** — ship `MapMarkerIconDataBlock` assets and nothing else of
   the old architecture.

## Decision Outcome

Chosen: **data-native**. A throwaway probe showed the vanilla rows carry the
volume — 26 variants in one row scroll fine — which removed the only reason for
the hybrid. The mod's categories map onto the dialog's two levels without
friction: one icon per category (General, Ores and Gems, Flags, Numbers,
Letters), one variant per marker.

Four decisions follow from it:

- **Assets with pinned addresses.** A marker refers to its icon by address.
  `CreateRuntimeInstance` without an address mints a new one on every launch,
  which orphaned every probe marker at the next restart; the overload that takes
  an address also marks the block as overloading one that does not exist, with
  an effect nobody has tested. An asset carries its address in `m_address` and
  keeps it.
- **One table, generated twice.** `tools/icons.toml` holds every address, sprite
  and legacy type; a script generates the assets and the C# legacy mapping from
  it, and a missing sprite aborts generation. MapMarkers+ resolved sprites by
  name at runtime and fell back to a placeholder silently.
- **Icons behind vanilla's.** In practice the game lists mod blocks before its
  own, for reasons the decompile does not explain. `TryGetDataBlocks` hands out
  its live list, so a Harmony prefix on the dialog's only reader of it moves
  the mod's blocks to the end, stably, and warns if a later version hands out a
  copy instead.
- **Restoration on the server.** An ECS system in the server world restores any
  marker that is a `MapMarker`, carries a known legacy `Amount`, and still shows
  the migration's question mark. It then sets `Amount` to `1`, vanilla's value,
  which makes the pass happen exactly once per marker without any bookkeeping
  of its own.

### Consequences

- **`requiredOn` drops from `3` to `1`.** The mod has no commands of its own
  any more, and vanilla's marker RPC stores an address without checking it, so a
  server works without the mod. Players without it see the marker prefab's
  default sprite and an error per redraw.
- **Uninstalling leaves markers the game cannot draw**, and restoration has
  already discarded the legacy type, so a restored marker cannot become a
  question mark again. Reinstalling brings the icons back, because the addresses
  never change.
- **The icon order rests on an implementation detail.** If the list stops being
  live, the mod's icons move to the front; nothing else breaks.
- Everything else — naming, presets, minimap, networking, saving — is the game's
  own and improves or breaks with it.

### Confirmation

Verified in game on Core Keeper 1.3.0.2, each under its section in
`docs/manual-tests.md`: every icon and variant in the dialog, and one placed
marker per icon keeping its icon on the large map across a restart ("Icons in
the dialog and on the map"); the dialog order and the scroll to a selected mod
icon ("Icon order and scrolling"); restoration of 62 legacy markers on a world
copy, with the changed `Amount` confirmed in the saved file and no second
restoration on the next launch ("Legacy restoration"), and restoration on a
dedicated server ("Legacy restoration on a dedicated server"); a marker
surviving a restart of a dedicated server without the mod ("Server without the
mod"); and the default sprite with an error per redraw on a client without the
mod ("Without the mod on the client"). Not testable on 1.3.0.2: restoration of
a renamed or restyled question mark, because the game cannot edit a placed
marker.

## Pros and Cons of the Options

### 1. Straight port

- Good, because players keep the drawer they know.
- Bad, because it is by far the largest option — a 214 KB prefab, networking
  systems and a marker manager, all rebuilt against new UI types.
- Bad, because it would be exactly as fragile at the next UI rework as it was
  at this one.

### 2. Hybrid

- Good, because a picker of its own could hold any number of markers.
- Bad, because it keeps a second UI to maintain for a volume problem the
  vanilla rows turned out not to have.

### 3. Data-native

- Good, because the mod is data plus two small patches and one system.
- Good, because a server needs nothing.
- Bad, because the minimap needs a small sprite per variant, which Numbers and
  Letters do not have yet.
- Bad, because the icon order depends on the game handing out a live list.

## More Information

The design this record distils is kept in the parent `core_keeper` repository,
deleted in the commit that recorded its findings in the handbook. To read it,
run in `core_keeper`:

~~~bash
git show "$(git rev-list -1 HEAD -- docs/specs/2026-09-28-map-markers-enhanced-design.md)^:docs/specs/2026-09-28-map-markers-enhanced-design.md"
~~~

What the game does underneath — the migration, the data-block order, what a
missing icon block looks like — is in that repository's handbook,
`docs/ck/world-and-mechanics.md`, `docs/ck/savegame-formats.md` and
`docs/ck/database-and-baking.md`.

# Hide the motifs vanilla now draws, do not remove them

- Status: accepted
- Date: 2026-10-06

## Context and Problem Statement

Core Keeper 1.3 ships eight marker icons of its own: cross, dot, flag, home,
pickaxe, question mark, skull and star, each with ten colour variants. Five
variants of this mod draw the same motifs — General's question mark, cross,
skull and red skull, and the ancient crystal in Ores and Gems, which is
vanilla's blue diamond. Offering both is clutter, and a marker with the mod's copy
loses its icon when the mod is uninstalled, while the game's own never does.

A saved marker stores its icon's address and a variant index, so whatever is
done to the duplicates must leave every marker already placed with a valid
icon. How should the mod stop duplicating vanilla?

## Decision Drivers

- No marker may lose its icon, now or after an update of this mod.
- Markers on a server without the mod must keep rendering for clients that have
  it.
- The fewer stored values change meaning, the fewer ways there are to corrupt a
  world.
- Players should end up with the game's own markers where the game has them.

## Considered Options

1. **New icons at new addresses**, the old blocks left in place but hidden.
2. **New icons at new addresses**, the old blocks removed.
3. **Rewrite the variant indices in place**, closing the gaps.
4. **Hide the variants in place** and convert the markers on them to vanilla.

## Decision Outcome

Chosen: **hide in place and convert**. A variant that has a vanilla twin stays
in its block at its index and is simply not offered by the dialog; a marker
sitting on it becomes the vanilla marker wherever the world runs with the mod,
and client presets are rewritten the same way. The hidden set is not a second
list: a variant is hidden exactly when the icon table names a vanilla target for
it, so a hidden variant without a conversion cannot exist.

Options 1 and 2 would leave the visible set right, but every hidden or removed
block still has markers pointing at it. Removing the block orphans them, which
is the failure addresses exist to prevent; keeping it hidden needs the same
hiding logic as the chosen option plus a second set of addresses to maintain, for
no gain. Option 3 changes what a stored index means, so every existing marker on
a shifted variant would silently show another motif.

Two related decisions:

- **Where the world does not run with the mod, nothing converts.** Because no
  block is removed, such markers keep rendering for clients that have the mod,
  and are converted as soon as the world is loaded with it.
- **MapMarkers+'s green flag is not migrated, and the mod's own green flag stays
  a flag of the mod.** MapMarkers+ stored its green flag as vanilla's own marker,
  and 1.2 created that exactly as it created any green flag a player placed, so
  the two cannot be told apart. Moving vanilla green flags to the mod would
  take over flags players placed on purpose, and a mod-icon marker is lost on
  uninstall. All fourteen flags remain.
  MapMarkers+'s cross and red skull, by contrast, were stored with a legacy
  type and now restore straight to vanilla — the red skull was seen doing so in
  game, the cross was not (see Confirmation).

### Consequences

- **Hidden variants still need their sprites**, since a client without the
  conversion — a server without the mod, an unconverted preset — can still show
  them.
- **Indices never shift, hiding included.** Visible positions are not indices:
  the dialog moves a selection to the next visible tile, and keeps the visible
  position, not the index, when the player switches icons.
- **The dialog carries a small patch** that deactivates hidden tiles and rewires
  navigation. If it fails, it puts the row back the way vanilla built it, so
  every variant shows again, and the world conversion cleans up afterwards; if
  the conversion fails, markers keep a mod icon that still renders.
- **Converted markers survive an uninstall**; the mod's own icons still do not.
- A conversion is one-way. A converted marker no longer records that it was
  once the mod's.
- Vanilla's colour variants are read from the sprite sheet and the game's own
  conversion of 1.2 markers, not from fields: the extracted block assets carry
  none. The cross's address rests on a runtime probe alone. So every target is
  looked up in the game's data before anything is written: should an update
  drop or renumber a vanilla block, markers and presets on it are left as they
  are and the log names the address, instead of being rewritten onto an icon
  that shows nothing.

### Confirmation

Verified in game on Core Keeper 1.3.0.4, each under its section in
`docs/manual-tests.md`: the dialog without the five variants and the preview of
the first visible variant ("Hidden variants in the marker dialog"); two presets
rewritten with their names kept ("Presets on hidden variants"); five markers
converted in single-player and on a dedicated server with the mod, converted
markers keeping their icon with the mod uninstalled, and a red skull from
MapMarkers+ restoring to vanilla ("World conversion to vanilla icons"); and no
conversion on a server without the mod ("Server without the mod"). Not tested:
controller navigation across the gaps, a second launch without a preset
conversion, and a MapMarkers+ cross in game, which is covered by the generator
test alone.

## Pros and Cons of the Options

### 1. New addresses, old blocks hidden

- Good, because the old markers keep a valid block.
- Bad, because it needs everything the chosen option needs and a second set of
  addresses besides.

### 2. New addresses, old blocks removed

- Bad, because every marker on a removed block loses its icon.

### 3. Rewriting indices in place

- Good, because the dialog needs no hiding logic.
- Bad, because a stored index changes meaning for markers on a server without
  the mod, and nothing can tell old from new.

### 4. Hiding in place and converting

- Good, because no address, block or index changes.
- Good, because the same table drives the dialog, the conversion and the
  presets.
- Bad, because the dialog needs a patch against the game's own panel.

## More Information

The design this record distils is kept in git history, deleted in the commit
that added this record. To read it, run in this repository:

~~~bash
git show "$(git rev-list -1 HEAD -- docs/specs/2026-10-06-vanilla-icon-migration-design.md)^:docs/specs/2026-10-06-vanilla-icon-migration-design.md"
~~~

The eight vanilla blocks, their addresses and the colour columns are in the
parent `core_keeper` repository's handbook, `docs/ck/world-and-mechanics.md`.

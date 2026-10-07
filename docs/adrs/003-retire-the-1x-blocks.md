# Retire the 1.x icon blocks when the art is redrawn

- Status: accepted
- Date: 2026-10-07
- Supersedes ADR 002 in part: where that record keeps blocks and hides their
  variants, this one retires the blocks.

## Context and Problem Statement

The marker art was redrawn: seven icons instead of five, two of them new
(Tapestry, Orbs), with every variant getting its own minimap sprite. The five
1.x icon blocks hold the old art and the old variant order, and saved markers
refer to them by address and variant index. Shipping the new art means deciding
what happens to those blocks and to the markers on them — including the five
variants that only duplicate a motif the game itself draws.

## Decision Drivers

- A shipped address is never reused for another meaning, and a stored
  (address, index) pair must never silently show another motif.
- Markers should end up on the new art wherever the world runs with the mod,
  without the player doing anything.
- The mod should not carry hidden art and dialog patches it no longer needs.
- The cost to players who do not update must be small, known and stated.

## Considered Options

1. **Keep the 1.x blocks registered, hidden**, and add the new blocks beside
   them.
2. **Redraw in place**: keep the five blocks and swap the art at the same
   indices.
3. **Retire the 1.x blocks**: ship seven new blocks at new addresses, delete the
   old assets, and migrate every marker, preset and legacy restoration onto the
   new set.

## Decision Outcome

Chosen: **retire the 1.x blocks**. The seven new blocks get new addresses; the
five old assets are deleted and their addresses are never used again. The old
addresses and their full variant lists live on in the icon table's retired
section, which is now the only record of what each stored index once meant. A
marker on a retired variant is rewritten to the same-named variant of the new
set, or to the game's own marker for the five duplicates; presets and the
MapMarkers+ restoration use the same table. The rewrite runs in the server world
on every pass, so it also catches a marker a 1.x client places later.

Redrawing in place (option 2) could not work: the new sets differ in order,
count and even meaning at an index, so a stored index would show another motif.
Keeping hidden blocks (option 1) retains the cost this decision removes — hidden
art, hiding code in the dialog — and still needs the same migration to move
markers.

### Consequences

- **The dialog code shrinks.** With nothing hidden, the patches that hid
  variants, kept the visible position across icon switches and previewed
  unselected icons are deleted.
- **Markers not yet migrated show the game's fallback sprite** — a blue diamond
  on a fresh display element, another marker's icon on a reused one — and the
  game logs an error for each, every frame. That applies to a dedicated server
  without the mod, to players still on 1.x looking at markers of the new set,
  and to an uninstall, where markers converted to the game's own are the only
  ones that survive. A server with the mod requires the mod, not a version, so
  nothing prevents the mixed state.
- **That is why this is a major version** and why the release notes tell
  everyone sharing a world to update together.
- A rewritten marker carries an address the retired table does not hold, so the
  rewrite needs no done-flag and cannot match twice. Targets are checked against
  the game's data before anything is written, and an unresolved one is left
  alone and warned about once.
- The generator enforces the rules that keep this sound and refuses to write
  anything when they break: a variant without a sprite in either sheet, a
  variant order that differs from the art's layer order, a retired variant with
  no target, or a retired address reused in a new block.
- The art lives in one Pixaki master cut into a large and a small sheet, so each
  variant has both sprites by construction.

## Pros and Cons of the Options

### 1. Keep the 1.x blocks, hidden

- Good, because markers on a server without the mod keep their old icon.
- Bad, because the old art ships forever and the dialog needs the hiding
  patches, on top of the migration.

### 2. Redraw in place

- Good, because no address changes and no migration.
- Bad, because stored indices would silently change meaning and two icons are
  added with a different layout.

### 3. Retire the 1.x blocks

- Good, because the mod ships only the current art and no hiding logic.
- Good, because one table drives the world migration, the presets and the
  MapMarkers+ restoration.
- Bad, because markers nobody has migrated yet show a fallback sprite.

## More Information

The design this record distils is kept in git history, deleted in the commit
that added this record. To read it, run in this repository:

~~~bash
git show "$(git rev-list -1 HEAD -- docs/specs/2026-10-07-icon-rework-design.md)^:docs/specs/2026-10-07-icon-rework-design.md"
~~~

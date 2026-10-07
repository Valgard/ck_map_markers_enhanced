# CLAUDE.md — MapMarkersEnhanced mod

MapMarkersEnhanced ships a redrawn marker set (after MapMarkers+'s art) as seven native
`MapMarkerIconDataBlock` icons for Core Keeper 1.3, and restores the question
marks the 1.3 world migration made of old MapMarkers+ markers. Parent guidance
(build setup, sandbox rules, macOS/CrossOver workflow, `utils/build.sh`, fake-ID
install) lives in the parent directory's `CLAUDE.md`. This file holds only what
is specific to this mod. Why the mod is built this way, and what was rejected: [`docs/adrs/001-data-native-port.md`](docs/adrs/001-data-native-port.md).

## What runs

| Piece | File | Job |
|---|---|---|
| Seven icon assets | `unity/MapMarkersEnhanced/Data/MapMarkerIconDataBlock/*.asset` | The icons themselves; generated |
| `IconTable` | `Scripts/Generated/IconTable.g.cs` | `ModIconAddresses`, the `Legacy` MapMarkers+ mapping and the `Retired` table of the 1.x blocks; generated |
| `IconOrderPatch` | `Scripts/IconOrderPatch.cs`, `Scripts/IconOrder.cs` | Prefix on `MapMarkerCustomizationPanel.PopulateIconRow`: moves the mod's blocks to the end of the live icon list, stably |
| `ScrollToSelectionPatch` | `Scripts/ScrollToSelectionPatch.cs` | Postfix on the 8-parameter `MapMarkerCustomizationPanel.Open`, carried out from `IMod.Update`: scrolls both rows to the selected tiles |
| `MarkerMigrationSystem` | `Scripts/MarkerMigrationSystem.cs` | Server-world ECS system: restores legacy question marks once per marker, and rewrites markers on a retired 1.x variant to the new set or a vanilla marker, on every pass |
| `RetiredTargets` | `Scripts/RetiredTargets.cs` | Lookup over `IconTable.Retired`: is this (address, variant) a retired 1.x one, what does it convert to, and does the game resolve the target |
| `PresetConversion` | `Scripts/PresetConversion.cs` | Client-side: rewrites the five marker presets that sit on a retired variant, through `Manager.prefs` |
| `MapMarkersEnhancedMod` | `MapMarkersEnhancedMod.cs` | Logs once per session which of the seven addresses the game registered, and runs the preset conversion once per session |

Every log line starts with `[MapMarkersEnhanced]`; `docs/manual-tests.md`
lists the ones a healthy session prints.

## The icon table is the only source

`tools/icons.toml` lists the seven icons with their pinned addresses and the
variants of each in dialog order, plus a `[[retired]]` table: the five 1.x
blocks with their addresses and their full 1.x variant lists in index order —
the only record of which stored index meant which motif — and the vanilla
target on the five that duplicate a vanilla motif. `tools/generate_icons.py`
turns it into the seven `.asset` files with their `.meta`, and into
`IconTable.g.cs`. **Never edit a generated file by hand** —
change the table and regenerate; the next `--check` reports a hand edit as
drift. Before every commit that touches the table, the generator, the Pixaki or the
sheets:

```bash
uv run tools/generate_icons.py            # write the outputs
uv run tools/generate_icons.py --check    # exit 1 if any output differs
uv run --with pytest pytest tools/tests -q
```

The generator refuses to write anything (exit 2) when a variant lacks a sprite in
either sheet, when the variant order differs from the layer order of the icon's
`Large` group in the Pixaki, when a retired variant has neither a same-named new
variant nor a vanilla target, when a retired address reappears in a new block,
or when the table breaks an address rule below. An `.asset` the table no longer
generates — the leftover of a renamed icon, which the game would load beside the
new one at the same address — fails both modes (exit 1); delete it by hand.
The tests check the retired lists against MapMarkers+ 1.1.1's category lists
(copied into the test file as literals), `LEGACY_TYPES` against its
`PlusMarkerType`, the five retired addresses as shipped, and the new blocks
against the Pixaki rather than against themselves.

**Addresses are identities.** A saved marker stores its icon's address, so an
address that has shipped is never reused for anything else, and the variant
indices inside a shipped block never shift. The game never resolves or drops the
address on load, save or network receive; a marker whose address has no
registered block is written back unchanged and merely displays whatever sprite
its display element last had — a blue diamond on a fresh one, another marker's
icon on a reused one — while the client logs an error every frame. So a missing
block costs display, not data, and two cases differ in what brings the icon
back: after an uninstall it is reinstalling the mod; after a block is removed
from the mod it is the migration, since reinstalling registers nothing at that
address. A real redesign (reorder, remove, merge, split) therefore gives the
changed icons new addresses and a migration rewriting old (address, index) to
new — which is what 2.0.0 did, see below. Appending variants and swapping art at
the same index need no new address; reordering or removing variants changes what
existing markers show, since a marker stores the variant's index. Within the
mod, the dialog order is the address order (the game sorts each loader's blocks
by address), so a new icon appended after Letters needs an address greater than
the last one, and every address starts with a hex digit `0`–`7`, which the
generator enforces — `Guid.CompareTo` compares the first field unsigned today,
and the rule keeps the order right should anything ever compare it signed. Mint
one with `uuid4()`, regenerating until both hold.

**The 1.x blocks are retired.** 2.0.0 shipped seven new blocks and deleted the
five 1.x assets; their addresses live only in the `[[retired]]` table and are
never used again. `MarkerMigrationSystem` rule 2 rewrites a marker on a retired
(address, variant) to the same-named new variant, or — for General's question
mark, cross, skull and red skull and Ores' ancient crystal — to the vanilla
marker the table names. It keeps running in the server world on every pass, so a
marker a 1.x client places later is rewritten too; a rewritten marker carries an
address the table does not hold, so it cannot match twice. Nothing is written
before the game data is loaded, a target is resolved before writing, and an
unresolved one is warned about once. `PresetConversion` uses the same table on
the client, and the `Legacy` table points MapMarkers+ restoration straight at
the new targets. The cost, accepted knowingly and the reverse of ADR 002's
choice: markers not yet migrated — a dedicated server without the mod, a 1.x
client — show the fallback sprite, and on a server without the mod the big map's
framerate collapses, because the client logs an error with a native stack trace
per visible unresolved marker every frame (measured, 2026-10-07: about 12 errors
per second with roughly 70 markers; none on a server with the mod). Why: [`docs/adrs/003-retire-the-1x-blocks.md`](docs/adrs/003-retire-the-1x-blocks.md);
what it replaced: [`docs/adrs/002-hide-vanilla-duplicates.md`](docs/adrs/002-hide-vanilla-duplicates.md).

The asset `.meta` GUIDs are derived from the icon names (`uuid5`), so renaming
an icon changes its asset GUID. Nothing references those GUIDs today; the
address is what matters.

## The sprite sheets

The art is one Pixaki master, `sources/mme_markers.pixaki`: group `Rework`, one
sub-group per icon, each with a `Large` and a `Small` group holding the same
layers. **Variant order is the layer order as Pixaki lists it, top layer first**
— not the position on the canvas. Two sprite definitions cut it with the shared
`utils/pixaki_to_sheet.py`: `sources/mme_markers.large.json` into
`Art/markers_large.png` and `sources/mme_markers.small.json` into
`Art/markers_small.png`, each with its pinned GUID and `internalId`s. They
exclude, with `excludeNested`, the other size's group and six layers vanilla
draws or the art does not use (`Question Mark`, `Cross`, `Skull`, `Skull Red`,
`Diamond`, `Ellipse`). A sprite is named after its layer; the generator pairs
large and small by name, and a variant's name is the layer name without spaces
(`Note` → `MusicNote` is the one exception). Both definitions use the sheet
tool's `cells` option, so every sprite is a box of the author's 10-px Pixaki
grid, not the layer's trimmed pixels: large is the 10×10 cell; small is a 6×6
box at cell offset (2,2), or 8×8 at (1,1) where the drawing is taller than 6
(113 large, 69 small 6×6, 44 small 8×8). Why: vanilla's marker sprites are fixed
even boxes (10×10 and 6×6, 16 px per unit, centre pivot), assigned unscaled; an
odd trimmed size puts the pivot on half a pixel, and the 5×5 and 5×7 first cut
jittered on the minimap while the player moved. Where the art sits inside the
grid is the author's and is preserved. Recut with the sheet tool's `--config`,
never by hand; the `Art/*.png` files are generated. `Templates` and `Grid` are
hidden working material, hidden per layer because the tool ignores a group's own
visibility.

## Constants the code relies on

| Constant | Value | Where it comes from |
|---|---|---|
| The eight vanilla icon blocks and the five retired-variant targets | `[vanilla]` table and the `vanilla` fields of the `[[retired]]` blocks in `tools/icons.toml` | addresses read at runtime on 1.3.0.4 with a probe (five of them, Pickaxe included, are also stored in the game's `MapUI.defaultPresets`); each vanilla block has ten variants, variant *n* is colour column *n* of the large marker sheet. Details in `docs/ck/world-and-mechanics.md` in the parent repository |
| Question mark the migration writes | icon `7e09f30c-8838-5604-2b46-8c13b0ef771e`, variant `9` | `ConvertOldMapMarkersSystem.GetDefaultIconForVariation(1)` / `GetDefaultVariantForOldVariation(1)` — MapMarkers+ stored its markers in slot `Marker2`, variation 1 |
| Legacy amount | `6000 + (int)PlusMarkerType` | MapMarkers+ 1.1.1's `PlusMarker.AmountBase`; `LEGACY_TYPES` in the generator is the enum in order (85 entries) |
| Types with no legacy amount | `None`, `Ping`, `AncientCrystal`, `QuestionMark`, `Skull`, `FlagGreen` | MapMarkers+ let the game create these, so they carry `Amount` 1 (`LEGACY_EXCLUDED`) |
| `MapMarkerIconDataBlock` script reference | `{fileID: 1194909520, guid: 5a7e404e57a3ed387bf565f46c30b9c1, type: 3}` | written into every generated asset |
| `requiredOn` | `1` (Client) | the server stores icon addresses without checking them, so a dedicated server does not need the mod; a hosting player does, to see the icons |
| `skipSafetyChecks` | `false` | no `System.IO`, no `System.Reflection` — not even `GetType().Name` — no `AccessTools`/`Traverse` |

Restoration clears `Amount` to `1`, vanilla's value. That is what makes it run
once per marker, and it is also why a restored marker's MapMarkers+ type is gone
for good — the README says so to players. Conversion needs no done-flag of its
own: a converted marker carries an address the retired table does not hold and
cannot match again, so that rule runs on every pass. Each rule's writes run
under a try of their own, so a throw in one never stops the other; only a throw
in the shared read-only scan stops both for that pass. Both rules write a target
only after `ScriptableData` resolves it, and warn instead when it does not; an
unresolved restoration keeps its legacy `Amount`, so it can still happen later.

## Identity

Name, manifest GUID, every block address and every `.meta` GUID are this mod's
own; nothing reuses a MapMarkers+ value, so the two mods can be installed side
by side. The repository is moorowl's history moved into
`unity/MapMarkersEnhanced/` with `git filter-repo`, so his commits keep their
authorship; the MIT `LICENSE` stays at the root, unchanged. The remote
`moorowl` points at the original repository and is not meant to be fetched into
this history — its hashes differ by design.

## Testing

- **Offline:** `tools/tests`, as above.
- **In game:** `docs/manual-tests.md`, written before each piece was built and
  holding the recorded results. Read it before an in-game check.
- **Restoration only ever on a copy of a world**, never on a live save. How the
  copy is made is in the "Legacy restoration" section there; the scan method is
  `docs/ck/savegame-formats.md` in the parent repository.
- **Server without the mod** (its own section there): put the mod on the
  client's `disabledMods` for the duration of `utils/server.sh start` only —
  `relink` mirrors every mod the client has enabled — then switch it back on for
  the client.
- Keep MapMarkers+ disabled in the client: it no longer compiles on 1.3, and
  its load failure would accompany every launch.
- **A rebuild without source changes can drop the generated system code**, and
  the system then throws at runtime (`marker migration failed`, `This method
  should have been replaced by codegen`). `utils/build.sh` now touches the
  system sources and checks the output for the generated file (exit 4), and the
  publish path refuses such a build; mechanism and guard are under "A mod with
  DOTS systems must recompile on every build" in `docs/build-environment.md` of
  the parent repository. If a build ever reports it, rebuild rather than ship.

## Working in a worktree

`.envrc` is gitignored, so a fresh worktree under `.worktrees/<name>/` has none.
Copy the main checkout's, and source the parent `core_keeper/.envrc` before it:

```bash
cp ../../.envrc .envrc
source ../../../.envrc && source .envrc && ../../../utils/build.sh
```

## Logo

`Editor/logo.png` follows the family style: a teal map pin with gold trim in
front of a parchment map, and as the gesture three marker tiles fanned below it
— ore, chest, heart — after the three fanned tiles of moorowl's original
MapMarkers+ logo. It is candidate 4 of `sources/`, generated with the
reusable-cattle-box and caveling-divining-rod logos as references (prompt:
`sources/logo-prompt-white.txt`) and made transparent with the image-generation
skill's `transparify.py` from `logo 4 - white background.jpeg` and `logo 4 -
black background.jpeg`, the black render that registered best with the white one
of three. The other candidates stay in `sources/`.

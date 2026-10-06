# CLAUDE.md — MapMarkersEnhanced mod

MapMarkersEnhanced ships MapMarkers+'s marker art as five native
`MapMarkerIconDataBlock` icons for Core Keeper 1.3, and restores the question
marks the 1.3 world migration made of old MapMarkers+ markers. Parent guidance
(build setup, sandbox rules, macOS/CrossOver workflow, `utils/build.sh`, fake-ID
install) lives in the parent directory's `CLAUDE.md`. This file holds only what
is specific to this mod. Why the mod is built this way, and what was rejected: [`docs/adrs/001-data-native-port.md`](docs/adrs/001-data-native-port.md).

## What runs

| Piece | File | Job |
|---|---|---|
| Five icon assets | `unity/MapMarkersEnhanced/Data/MapMarkerIconDataBlock/*.asset` | The icons themselves; generated |
| `IconTable` | `Scripts/Generated/IconTable.g.cs` | The icon addresses and the legacy mapping; generated |
| `IconOrderPatch` | `Scripts/IconOrderPatch.cs`, `Scripts/IconOrder.cs` | Prefix on `MapMarkerCustomizationPanel.PopulateIconRow`: moves the mod's blocks to the end of the live icon list, stably |
| `ScrollToSelectionPatch` | `Scripts/ScrollToSelectionPatch.cs` | Postfix on the 8-parameter `MapMarkerCustomizationPanel.Open`, carried out from `IMod.Update`: scrolls both rows to the selected tiles |
| `HiddenVariantsPatch`, `IconPreviewPatch` | `Scripts/HiddenVariantsPatch.cs` | Postfixes on `MapMarkerCustomizationPanel`: `BuildVariantRow` deactivates the hidden variant tiles, drops them from the toggle group, rewires left/right navigation over the visible ones and moves a selection off a hidden tile; `PopulateIconRow`/`UpdateIconRowSprites` draw an unselected icon whose variant 0 is hidden with its first visible variant |
| `MarkerMigrationSystem` | `Scripts/MarkerMigrationSystem.cs` | Server-world ECS system: restores legacy question marks once per marker, and converts markers on hidden variants to vanilla |
| `VanillaTargets` | `Scripts/VanillaTargets.cs` | Lookup over `IconTable.ToVanilla`: which variants have a vanilla target (hidden from the dialog) and what it is |
| `PresetConversion` | `Scripts/PresetConversion.cs` | Client-side: rewrites the five marker presets that sit on a hidden variant to the vanilla twin, through `Manager.prefs` |
| `MapMarkersEnhancedMod` | `MapMarkersEnhancedMod.cs` | Logs once per session which of the five addresses the game registered, and runs the preset conversion once per session |

Every log line starts with `[MapMarkersEnhanced]`; `docs/manual-tests.md`
lists the ones a healthy session prints.

## The icon table is the only source

`tools/icons.toml` lists every icon with its pinned address and every variant
with its MapMarkers+ type and, where one exists, its minimap slice.
`tools/generate_icons.py` turns it into the five `.asset` files with their
`.meta`, and into `IconTable.g.cs`. **Never edit a generated file by hand** —
change the table and regenerate; the next `--check` reports a hand edit as
drift. Before every commit that touches the table, the generator or the sprite
sheet:

```bash
uv run tools/generate_icons.py            # write the outputs
uv run tools/generate_icons.py --check    # exit 1 if any output differs
uv run --with pytest pytest tools/tests -q
```

The tests compare the table with MapMarkers+ 1.1.1's category lists, copied
into the test file as literals, so they check the table against upstream rather
than against itself; the same goes for `LEGACY_TYPES` against MapMarkers+'s
`PlusMarkerType`, and for the five shipped addresses. A sprite name the sheet
does not have aborts generation instead of shipping a blank tile, and so does a
table that breaks an address rule below (exit 2). An `.asset` the table no
longer generates — the leftover of a renamed icon, which the game would load
beside the new one at the same address — fails both modes (exit 1); delete it
by hand.

**Addresses are identities.** A saved marker stores its icon's address, so an
address that has shipped never changes, and an icon is never removed: either
leaves every marker using it without its icon. Such a marker shows whatever
sprite its display element last had — a blue diamond on a fresh one, another
marker's icon on a reused one — and logs an error every frame. Within the mod,
the dialog order is the address order (the game sorts each loader's blocks by
address), so a new icon appended after Letters needs an address greater than the
last one, and every address starts with a hex digit `0`–`7`, which the generator
enforces — `Guid.CompareTo` compares the first field unsigned today, and the
rule keeps the order right should anything ever compare it signed. Mint one with
`uuid4()`, regenerating until both hold. Variants can be appended to an icon
freely; reordering or removing them changes what existing markers show, since a
marker stores the variant's index.

The asset `.meta` GUIDs are derived from the icon names (`uuid5`), so renaming
an icon changes its asset GUID. Nothing references those GUIDs today; the
address is what matters.

## The sprite sheet

`unity/MapMarkersEnhanced/Art/markers.png` is moorowl's sheet, unchanged; only
the `guid:` of its `.meta` is new. Sprites are named `markers_<Type>` and
`markers_<Type>_small`, with two exceptions the table spells out:
`markers_skull_small` and `markers_ancient_crystal_small`. Numbers and Letters
have no small slice yet — the slots below them are blank placeholder buttons —
so their minimap sprite is the large one. `docs/roadmap.md` ("Redraw the small
marker buttons") has what to change once the art exists.

## Constants the code relies on

| Constant | Value | Where it comes from |
|---|---|---|
| Question mark the migration writes | icon `7e09f30c-8838-5604-2b46-8c13b0ef771e`, variant `9` | `ConvertOldMapMarkersSystem.GetDefaultIconForVariation(1)` / `GetDefaultVariantForOldVariation(1)` — MapMarkers+ stored its markers in slot `Marker2`, variation 1 |
| Legacy amount | `6000 + (int)PlusMarkerType` | MapMarkers+ 1.1.1's `PlusMarker.AmountBase`; `LEGACY_TYPES` in the generator is the enum in order (85 entries) |
| Types with no legacy amount | `None`, `Ping`, `AncientCrystal`, `QuestionMark`, `Skull`, `FlagGreen` | MapMarkers+ let the game create these, so they carry `Amount` 1 (`LEGACY_EXCLUDED`) |
| `MapMarkerIconDataBlock` script reference | `{fileID: 1194909520, guid: 5a7e404e57a3ed387bf565f46c30b9c1, type: 3}` | written into every generated asset |
| `requiredOn` | `1` (Client) | the server stores icon addresses without checking them, so a dedicated server does not need the mod; a hosting player does, to see the icons |
| `skipSafetyChecks` | `false` | no `System.IO`, no `System.Reflection` — not even `GetType().Name` — no `AccessTools`/`Traverse` |

Restoration clears `Amount` to `1`, vanilla's value. That is what makes it run
once per marker, and it is also why a restored marker's MapMarkers+ type is gone
for good — the README says so to players.

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

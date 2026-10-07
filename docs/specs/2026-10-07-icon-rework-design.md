# Icon rework: a redrawn marker set in new blocks

Status: approved design, not implemented. Target release: **2.0.0**.

## Goal

Replace every marker icon the mod ships with the redrawn set in
`sources/mme_markers.pixaki`, add two new icons (Tapestry, Orbs), give every
variant its own minimap sprite, and move every marker placed with a 1.x icon onto
the new set — or onto vanilla, for the five variants that duplicate a vanilla
motif — wherever the world runs with the mod.

## Acceptance criteria

1. The marker dialog offers exactly seven mod icons, after vanilla's, in this
   order: General, Ores, Flags, Tapestry, Orbs, Numbers, Letters.
2. Each icon offers the variants listed under *The new blocks*, in that order,
   and no other.
3. Every offered variant draws its own large sprite on the map and its own small
   sprite on the minimap.
4. Once a world has been loaded by a server or host running 2.0.0 and its game data
   has loaded, every marker it holds on a 1.x variant — including one a 1.x client
   places later — is rewritten to the same-named variant of the new set or to the
   vanilla marker named under *Migration*, and a 2.0.0 client shows it with that
   icon, never as a missing one (see *Accepted costs* for what a 1.x client sees).
5. MapMarkers+ markers restored by 2.0.0 land directly on the new set or vanilla.
6. Client presets that point at a 1.x variant are rewritten the same way.
7. The five 1.x block addresses are never used again, by any block.
8. The generator refuses to produce output when a variant lacks a sprite in either
   sheet, when the variant order differs from the Pixaki layer order, when a 1.x
   variant has neither a same-named target nor a vanilla target, or when a retired
   address reappears in a new block.

## Source art

`sources/mme_markers.pixaki` (tracked since commit "add the redrawn marker set as
a Pixaki master"), group `Rework`, one sub-group per icon, each with a `Large` and
a `Small` group holding the same layers in the same order. The group `Templates`
and the layer `Grid` are hidden working material and are never cut; that holds
because each of their layers is hidden, since the sheet tool does not look at a
group's own visibility.

**Variant order is the layer order as Pixaki lists it, top layer first** — not the
position on the canvas, which differs for some icons. The file stores layers
bottom-up, so the reader reverses them. The order of the icon groups inside
`Rework` is not the dialog order; criterion 1 fixes that order.

Excluded from the cut, although present in the Pixaki: `Question Mark`, `Cross`,
`Skull`, `Skull Red` (vanilla draws these; the 1.1.0 decision stands),
`Diamond` (the redrawn ancient crystal, which is vanilla's blue diamond), and
`Ellipse`. Each is a layer inside both the `Large` and the `Small` group of its
icon.

## The new blocks

Seven `MapMarkerIconDataBlock`s with new addresses, ascending in dialog order,
since the game sorts a loader's blocks by address. Each address is minted with
`uuid4()`, regenerated until it starts with a hex digit `0`–`7` (the existing
generator rule) and sorts after the previous icon's address; none may equal a
retired address. The five 1.x block assets are deleted.
Variant names follow the 1.x names where a 1.x variant exists; otherwise they are
the layer name without spaces.

| Icon | Variants, in order | Count |
|---|---|---|
| General | ExclamationMark, MusicNote, ArrowLeft, ArrowRight, ArrowUp, ArrowDown, Chest, Sign, Dagger, Axe, StructureWood, Heart, Flames, StructureStone, Leaf, Fish, Shield, Cog | 18 |
| Ores | Copper, Tin, Iron, Gold, Scarlet, Octarine, Galaxite, Solarite, Pandorium, Relucite, RadiationCrystal | 11 |
| Flags | FlagRed, FlagOrange, FlagPeach, FlagYellow, FlagGreen, FlagTeal, FlagCyan, FlagBlue, FlagPurple, FlagPink, FlagBrown, FlagBlack, FlagGray, FlagWhite | 14 |
| Tapestry | TapestryUnpainted, TapestryRed, TapestryOrange, TapestryPeach, TapestryYellow, TapestryGreen, TapestryTeal, TapestryCyan, TapestryBlue, TapestryPurple, TapestryPink, TapestryBrown, TapestryBlack, TapestryGray, TapestryWhite | 15 |
| Orbs | OrbEmpty, OrbRed, OrbOrange, OrbPeach, OrbYellow, OrbGreen, OrbTeal, OrbCyan, OrbBlue, OrbPurple, OrbPink, OrbBrown, OrbBlack, OrbGray, OrbWhite, OrbGold, OrbYellowAlternative, OrbLava, OrbFlower | 19 |
| Numbers | Number1 … Number9, Number0 | 10 |
| Letters | LetterA … LetterZ | 26 |

The only layer name that differs from its variant name by more than its spaces is
`Note` → `MusicNote`.

The Tapestry art is reduced to 8×8 from the fifteen 16×16 fields of Core
Keeper's `tapestry.png`, arranged in the Pixaki in the Flags colour order with
the unpainted field first; the colour in each layer's name is the
`PaintableColor` of its field, verified against `WallTapestry.prefab`
(`colorSprites[color − 1]` lists fields 0–7 and 9–14; field 8 is the unpainted
base sprite). The Orb art comes from Core Keeper's item sprites; the Orb names
are the Pixaki layer names.

## Sprites

Two sheets, cut from the one Pixaki, mirroring vanilla's
`map_marker_large.png` / `map_marker_small.png`:

- `unity/MapMarkersEnhanced/Art/markers_large.png` from every `Large` group,
- `unity/MapMarkersEnhanced/Art/markers_small.png` from every `Small` group,

each with its own `.meta`, a pinned GUID and pinned `internalId`s. A sprite's name
is its layer name; large and small are paired by name, never by position. The 1.x
sheet `Art/markers.png` is removed.

`utils/pixaki_to_sheet.py` (shared, in `core_keeper`) gains two opt-in options
that leave every existing mod's output unchanged:

- `--config <file.json>` — a sprite definition other than the `<name>.json` beside
  the Pixaki, so one Pixaki can feed two sheets;
- `excludeNested` — names of groups **or layers** excluded at any depth. Today's
  `exclude` matches top-level names only (`collect_layers`), which reaches neither
  the `Large`/`Small` groups nor the six excluded layers.

The two definitions are `sources/mme_markers.large.json` (excluding `Small` and
the six layers) and `sources/mme_markers.small.json` (excluding `Large` and the
six layers). They are hand-kept like `icons.toml`, but hold only how the sheets
are cut, never which variants exist.

## Table and generator

`tools/icons.toml` is the one hand-kept table of icons and variants. It lists the
seven blocks with their addresses and variants (with a layer name only where it
differs) and a `[[retired]]` table holding, for each of the five 1.x blocks, its
address and its full variant list in 1.x index order — the only record of which
stored index meant which motif once the 1.x assets are gone — with the vanilla
target on each of the five duplicates. `tools/generate_icons.py` produces the seven block
assets, each variant pointing at its sprite in both sheets, plus the C# migration
table and the MapMarkers+ legacy table.

The generator enforces criterion 8 itself, before writing anything. For the
sprites it checks each variant's sprite name against the sprite names in both
sheets' `.meta` files, as it already does for the one 1.x sheet. For the layer
order it reads the Pixaki with the same loader as the sheet tool, takes each icon's
`Large` group in Pixaki order, drops the excluded layers, maps layer names to
variant names, and compares the result with the table's variant list.

## Migration

| 1.x block (retired) | Address | Target |
|---|---|---|
| General | `0877e397-7e74-4b3f-b822-4d0f052e1b60` | same-named variant in General; QuestionMark, Cross, Skull, SkullRed → the vanilla targets 1.1.0 converts them to |
| OresAndGems | `1d93e76b-8037-44e9-97a9-1c69a3f57156` | same-named variant in Ores; AncientCrystal → the vanilla blue diamond 1.1.0 converts it to |
| Flags | `2e4b6d8c-a19b-476a-b770-8e293827689e` | same-named variant in Flags |
| Numbers | `6152c695-14f2-4344-bee4-a2967b880bd3` | same-named variant in Numbers |
| Letters | `77aea3e9-b732-4217-92f4-1bc153361245` | same-named variant in Letters |

All five vanilla targets are the `vanilla` entries of the 1.1.0 `tools/icons.toml`.

- **Placed markers:** `MarkerMigrationSystem` rule 2 becomes "retired address and
  variant → target", where a target is a new mod variant or a vanilla marker. It
  keeps running in the server world only, on every pass, so a marker a 1.x client
  places on a retired address later is rewritten on the next pass. It keeps every
  existing safeguard: nothing is written before the game data is loaded, targets
  are resolved before writing, and an unresolved target is not written and is
  warned about once — which guards against a game update dropping a vanilla block
  or a mod block failing to register. A rewritten marker carries an address the
  table does not contain, so it cannot match again.
- **MapMarkers+ restoration (rule 1):** the legacy table points at the new targets
  directly.
- **Presets:** `PresetConversion` uses the same table on the client.

### Accepted costs

A marker whose address has no registered block gets no sprite from the game: a
fresh display element shows a blue diamond, a reused one keeps whatever icon it
showed before, and the client logs an error every frame. "Missing icon" below
means that state.

Retiring the 1.x blocks reverses ADR 002's choice to keep blocks, knowingly:

- On a dedicated server without the mod nothing migrates; players with 2.0.0 see
  every 1.x mod-icon marker there with a missing icon.
- Players still on 1.x see every marker migrated to the new set, and every newly
  placed one, with a missing icon until they update; markers converted to
  vanilla show normally. A server with the mod requires the mod, not a version.
- Uninstalling still leaves mod-icon markers with a missing icon; markers converted to
  vanilla keep their icon.

Hence a major version and an explicit "update everyone" note.

## Dialog code

With no hidden variants left, `HiddenVariantsPatch` (with `ExplicitOpenPatch`,
`ExplicitOpenWithPresetPatch`, `ExplicitResetPatch` and `IconPreviewPatch`, which
live in the same file) and the index/visible-position distinction are removed.
`IconOrderPatch` keeps moving the mod's icons behind vanilla's, which is what
places the seven after vanilla in criterion 1; neither it nor
`ScrollToSelectionPatch` uses the hidden-variant machinery, so they only lose prose
that counts the mod's icons (`IconOrderPatch.cs:23` "five", `ScrollToSelectionPatch.cs:188`
"thirteen", meaning eight vanilla and five mod icons, and `CLAUDE.md`). `VanillaTargets`
becomes the lookup over the retired table. The bootstrap's once-per-session log of
registered addresses covers the seven new ones. The DOTS codegen guard and
`requiredOn: 1` are unchanged.

## Documentation

- `CHANGELOG.md` 2.0.0 with the update note; README, `modio-description.md`,
  `steam-description.txt`: new set, new credits, the minimap limitation removed.
- Credits: art redrawn after moorowl's MapMarkers+ (MIT); banners from Core
  Keeper's tapestry sprites; orbs from Core Keeper's item sprites.
- ADR 003 superseding ADR 002 on retiring blocks; the mod's `CLAUDE.md` (its
  sections on hidden variants and the sprite sheet are replaced, the icon count is
  updated, and its note that a rebuild can drop the generated system code now
  points at the guard in `utils/build.sh`, which closed that gap).
- In `core_keeper`: the two `pixaki_to_sheet.py` options, in the tool and in
  `docs/pixaki-format.md`, which also corrects its statement that the layer tree is
  stored top→bottom — it is bottom-up.

## Testing

- **Automated:** generator tests for each case of criterion 8, and a test that every
  1.x variant has exactly one target. The existing tests that compare the table
  with MapMarkers+ 1.1.1's category lists move to the retired table, which is what
  still mirrors MapMarkers+; the new blocks are checked against the Pixaki instead.
  The test of the shipped addresses keeps the five 1.x addresses, now as retired.
  For `pixaki_to_sheet.py`, a regression run over every existing mod's sprite
  definition showing byte-identical output without the new options, alongside its
  existing suite.
- **In game**, recorded in `docs/manual-tests.md`:
  - a world whose markers were placed with 1.0.0, covering all five 1.x blocks and
    the five duplicates (a world that already ran 1.1.0 has its duplicates
    converted and cannot show that case), migrates: the new art for the rest, the
    duplicates vanilla;
  - a MapMarkers+ world restores onto the new targets;
  - presets are rewritten;
  - a dedicated server with 2.0.0 migrates, also a marker a 1.x client places on
    it afterwards; one without the mod leaves 1.x markers with a missing icon
    (observed and documented);
  - every variant's small sprite appears on the minimap;
  - the dialog shows the seven icons in criterion 1's order and each icon's variants
    in its Pixaki layer order.

# Vanilla icon migration — design

Status: approved in conversation, 2026-10-06. Target release: 1.1.0.

## Goal

The mod stops duplicating the vanilla motifs Core Keeper 1.3 draws itself. The
marker dialog no longer offers them, and wherever a world runs with the mod,
markers already using them become their vanilla counterpart. The change takes
no marker's icon away: on a dedicated server without the mod such markers are
simply not converted, and keep rendering for clients that have the mod.

The mod's flags are not part of this: all fourteen stay as they are. The only
flag that ends up vanilla is 1.2's green flag — the game's own, which MapMarkers+
used as well — and the 1.3 world migration already converts it.

A vanilla marker also survives uninstalling the mod, which no MapMarkersEnhanced
icon does.

## Acceptance criteria

Distilled from the owner's statements in the design conversation:

1. The five variants in the table below are no longer offered by the dialog;
   every other variant, the green flag included, still is.
2. No variant changes its index, and no icon block or address is removed.
3. Markers placed with one of the five become the vanilla counterpart where the
   world runs with the mod. Where it does not, they are not converted and keep
   rendering for clients that have the mod.
4. MapMarkers+ markers restore as before, except `Cross` and `SkullRed`, which
   restore to vanilla. MapMarkers+ green flags stay the vanilla flag.
5. An unselected icon whose variant 0 is hidden previews its first visible
   variant.
6. Client presets pointing at one of the five are rewritten to vanilla, keeping
   their name.

## Decisions

| Topic | Decision |
|---|---|
| Duplicates | Five variants: General 0 `QuestionMark`, 3 `Cross`, 16 `Skull`, 17 `SkullRed`; OresAndGems 0 `AncientCrystal` |
| Removal | **Hidden, not removed.** The variants stay in their icon blocks at their indices; the dialog no longer shows them |
| Placed markers | Converted to vanilla on every pass in the server world |
| Legacy restoration | MapMarkers+ `Cross` and `SkullRed` restore to vanilla instead of to the mod; the other 77 restored types are unchanged |
| `FlagGreen` | Stays visible and is not converted. MapMarkers+'s green flag stays the vanilla flag the 1.3 migration made of it |
| Icon-row preview | An unselected icon whose variant 0 is hidden previews its first visible variant |
| Presets | Client presets pointing at a hidden variant are rewritten to vanilla, keeping their name |
| World system | One system with two rules (restoration, conversion) in one read-only scan |

### Targets

| Mod variant | Vanilla block | Address | Variant |
|---|---|---|---|
| General 0 `QuestionMark` | `UserMarker6_Question` | `7e09f30c-8838-5604-2b46-8c13b0ef771e` | 9 (yellow) |
| General 3 `Cross` | `UserMarker1_Cross` | `adbecb0c-1236-bf84-d9ea-0516e188e2d0` | 9 (yellow) |
| General 16 `Skull` | `UserMarker7_Skuill` | `169f71d7-f86d-7234-abf0-0120b015262b` | 0 (white) |
| General 17 `SkullRed` | `UserMarker7_Skuill` | `169f71d7-f86d-7234-abf0-0120b015262b` | 1 (red) |
| OresAndGems 0 `AncientCrystal` | `UserMarker2_Dot` | `f9203606-618b-6384-7a99-a790e5c6de35` | 2 (blue) |

The addresses were read at runtime on 1.3.0.4 with a throwaway log probe that
listed every registered `MapMarkerIconDataBlock`; the block assets in the
extracted resources carry no fields, so they cannot be read there. Every vanilla
block has ten variants, and variant *v* is colour column *v* of
`map_marker_large.png` — white, red, blue, green, light cyan, teal, brown, pink,
lavender, yellow — confirmed by the probe's sprite names against the sprites'
rectangles. Independently, `ConvertOldMapMarkersSystem` hard-codes four pairs
for 1.2's markers (`Pug.Other:175131`, `175151`) — Dot 2 blue, Question 9
yellow, Skull 0 white, Flag 3 green. Their addresses equal the probe's, and with
1.2's sheet showing which motif each was, their variants fit the same column
reading; three of them are targets above. The `Cross` address rests on the
probe alone, the `SkullRed` variant on the column reading.

Why these five: of the eight vanilla motifs, the mod duplicates the question
mark, the cross, the skull (twice, white and red) and the diamond (`Dot`); it
has no home, pickaxe or star. Its flags are out of scope, as the goal says.

### Why MapMarkers+ green flags are not migrated

This is about markers MapMarkers+ placed, not the mod's own `FlagGreen` variant.
MapMarkers+ stored its green flag as vanilla `Marker4` (`PlusMarkerUtility.cs`),
which 1.2 created with `Amount` 1 like any vanilla marker (1.2.1.5
`Pug.Other:397387`), so it was indistinguishable from the game's own green flag
already in 1.2, and the 1.3 migration leaves no trace either. Moving vanilla
green flags to the mod would catch every green flag a player placed
deliberately, and a mod-icon marker loses its icon on uninstall.

## Design

### Table and generator

`tools/icons.toml` gains a `[vanilla]` table naming all eight vanilla blocks
(`Cross`, `Dot`, `Flag`, `Home`, `Pickaxe`, `Question`, `Skull`, `Star`) with
their addresses, and an optional `vanilla = { icon = "<name>", variant = <n> }`
on a variant. **A variant is hidden exactly when it has a vanilla target**;
there is no second field, so a hidden variant without a target cannot exist.

`tools/generate_icons.py` additionally emits into `IconTable.g.cs`:

- `ToVanilla`: (mod icon address, variant index) → (vanilla address, variant).
  The dialog derives the hidden set from it, the world system converts with it,
  the client rewrites presets with it.
- `Legacy`: for a type with a vanilla target, the target is the vanilla address
  and variant. So 6072 (`Cross`) and 6073 (`SkullRed`) point at vanilla; every
  other entry is unchanged.

New validation, aborting with exit 2 like the existing address rules:

- `vanilla.icon` names an entry of `[vanilla]`; `variant` is 0–9.
- No `[vanilla]` address equals a mod address.
- Every icon keeps at least one visible variant.

Tests carry the five mappings and the eight vanilla addresses as literals, the
same way the existing tests carry MapMarkers+'s lists, and check that
`FlagGreen` has no mapping, that 6072 and 6073 point at vanilla, and that each
new rule aborts.

### Dialog — `HiddenVariantsPatch`

Postfixes on `MapMarkerCustomizationPanel`:

- **`BuildVariantRow(iconBlock)`** — for a mod icon with hidden indices: each
  hidden tile is deactivated and removed from `variantToggleGroup.toggleUIElements`.
  Left/right navigation is rewired over the visible tiles **on every call, for
  every icon**: the tile pool is shared between icons and vanilla rewires only
  when it adds tiles, so a gap made for General would otherwise survive a switch
  to Flags. A selection on a hidden tile moves to the next visible one after it,
  or the last one before it if none follows, through `OnLeftClicked` as vanilla
  does. This covers General opening on index 0 and an index carried over from
  another icon. Hidden tiles need no restoring: vanilla reactivates every tile
  below the icon's variant count and rebuilds the toggle group on every call
  (`Pug.Other:345143`–`345150`), so a tile hidden for General is back for Flags.
- **`PopulateIconRow`, `UpdateIconRowSprites`** — an unselected mod icon whose
  variant 0 is hidden previews its first visible variant: General the
  exclamation mark, OresAndGems copper. Vanilla's private `SetSpriteAndColor` is
  reproduced (white when active, 25 % alpha when not): it is a few lines, and a
  `[HarmonyReversePatch]` onto it — not on the sandbox's deny list — has never
  been tried in this setup.

`ScrollToSelectionPatch` is unchanged: its `Open` postfix runs after
`BuildVariantRow` and so sees the moved selection, and it already ignores an
inactive tile.

Whether the row's layout closes the gap left by an inactive tile is an
assumption — vanilla deactivates surplus tiles the same way, but always at the
end. The in-game test checks it.

### Presets

Once per session, at the point in `IMod.Update` where the icon log runs, the mod
reads `Manager.prefs.GetMapMarkerPreset(i)` for the five slots the game uses
(`MapUI.EnsurePresetsInitialized`, `Pug.Other:346760`) and rewrites a preset
found in `ToVanilla` through `SetMapMarkerPreset`, keeping its name. Logs
`converted <n> presets` when n > 0. The rewrite is wrapped in its own try/catch
— `IMod.Update` itself is not guarded, so an exception there would reach the
game. Raising the preset count (roadmap, "More than five presets") has to raise
this bound too.

### World — `MarkerMigrationSystem`

`LegacyRestoreSystem` is renamed, keeping its `.meta`. It still runs in the
server world only, one read-only scan every 60 updates, writing only the
entities a rule matches:

| Rule | Matches | Writes |
|---|---|---|
| 1 Restoration (unchanged) | `Amount` in `Legacy` and icon `7e09f30c…`, variant 9 | target from `Legacy`, `Amount` = 1 |
| 2 Conversion (new) | (icon, variant) in `ToVanilla` | target from `ToVanilla`; `Amount` untouched |

Within a pass the rules are disjoint: rule 1 needs a vanilla address, rule 2 a
mod address. Across passes, rule 2 writes `QuestionMark` onto exactly the icon
and variant rule 1 looks for, so it matters that its markers never carry a
legacy amount: the game creates every placed marker with `Amount` 1
(`Pug.Other:414865`), and restoration writes 1. The server's edit branch
changes icon and variant without touching `Amount` (`414877`); vanilla never
sends an edit (`ApplyEditToExistingMarker` has no caller), but a modded client
could. Should an edit ever put a legacy-amount marker onto a hidden variant,
rule 1 restoring it on the next pass is the right outcome anyway.

Rule 2 needs no marker of its own — once written, a marker carries a vanilla
address and cannot match again — so it may run on every pass, which also catches
hidden-variant markers made later: by an old preset, or on a server without the
mod whose world is later run with it. It converts the `Cross` and `SkullRed`
markers that 1.0.0 already restored to the mod. Logs `converted <n> markers to
vanilla icons` when n > 0; the existing messages keep their wording.

### Failure behaviour

Never throw into the game. Each new piece logs a cause once, the way its
neighbour does: the patch warns once per session, the world system logs an
error once per system instance, the preset rewrite warns once per session. If
hiding fails, the dialog shows the tiles as before and the world conversion
cleans up afterwards; if the conversion fails, markers keep their mod icon,
which still renders; if the preset rewrite fails, presets stay as they are and
the markers they place are converted in the world.

### Boundaries

Conversion and restoration run only where the world runs with the mod. On a
dedicated server without it, mod-icon markers stay as they are and keep
rendering for clients with the mod, since no block is removed.

## Documentation

- Handbook, `docs/ck/world-and-mechanics.md` (parent repository, own commit):
  the eight vanilla blocks with addresses and sprite ranges, variant = colour
  column, and that the extracted block assets carry no fields.
- ADR 002: hide instead of remove, the rejected alternatives (new addresses,
  rewriting indices), why green flags stay vanilla. This spec is replaced by
  the ADR when the work is finished.
- README: four motifs (five variants) are vanilla now; existing markers are
  converted where the world runs with the mod, presets on the client, and both
  then survive an uninstall.
- CLAUDE.md: the notion of a hidden variant, the renamed system, indices never
  shift — hiding included.
- `docs/manual-tests.md`, written before the build: dialog (gap, navigation,
  preview, selection on icon switch), presets, world conversion on a copy of a
  world, restoration of `Cross` and `SkullRed`; once on the dedicated server
  with the mod.
- CHANGELOG: 1.1.0.

## Out of scope

The redrawn icon set in `sources/mme_markers.pixaki` — banners, orbs, the
ellipsis, the radiation crystal and the new art for existing motifs — gets its
own design.

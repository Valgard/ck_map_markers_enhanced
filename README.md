# Map Markers Enhanced

A Core Keeper mod that brings moorowl's MapMarkers+ marker art to Core Keeper
1.3 — ores and gems, coloured flags, arrows, chests, numbers, letters and more —
as native icons in the game's own map-marker dialog. It also gives back the
markers that MapMarkers+ players lost in the 1.3 update, when every one of them
turned into the same yellow question mark.

## Features

- **Five extra icons in the marker dialog**, listed after the game's own:
  General (18 markers), Ores and Gems (10), Flags (14), Numbers (10) and
  Letters (26, A–Z). Pick an icon in the upper row, then the marker in the lower
  one.
- **Four motifs are the game's own now.** The question mark, the cross, the
  skull (white and red) and the blue diamond exist in the game itself since 1.3,
  so the mod no longer offers its copies of them — five markers in all — and
  converts existing ones, see below. The flags, including the green one, are
  unchanged.
- **Everything else is the game's own.** Naming a marker, the five presets, the
  minimap, multiplayer and saving work exactly as they do for vanilla markers:
  the mod adds icons, keeps the dialog scrolled to your selection and restores
  old markers, and leaves the rest to the game.
- **The dialog opens on your selection.** When you open a preset that uses one
  of the mod's icons, the dialog scrolls so the selected icon and marker are in
  view instead of starting at the left end.
- **Old MapMarkers+ markers are restored** — see below.
- **Markers with the retired motifs are converted** — see below.

## Restoring MapMarkers+ markers

MapMarkers+ stored its own markers as one of the game's four marker types and
kept the real type in a spare field. Core Keeper 1.3 converted old markers by
that game type alone, so every marker drawn with MapMarkers+'s own art came out
as the same question mark. The spare field survived the conversion, and that is
what this mod reads.

The first time a world is loaded with the mod on the side that runs the world —
single-player, the host of a multiplayer game, or a dedicated server that has
the mod — each of those question marks gets its original icon back. This
happens once per marker and is saved with the world. Markers you placed with
the game's own icons are not touched, and neither are MapMarkers+'s question
mark, skull, ancient crystal and green flag: those were the game's own markers
all along, and 1.3 converted them correctly. MapMarkers+'s cross and red skull
come back as the game's own cross and red skull, since the mod no longer has
icons of its own for them.

**Back up the world first if you might want the question marks back.** The
restoration replaces the stored MapMarkers+ type with the game's normal value,
so afterwards nothing in the world records which MapMarkers+ marker a restored
marker used to be.

## Markers that now use the game's own icons

Markers you placed with the mod's question mark, cross, skull, red skull or
diamond are converted to the game's own marker with the same motif — a yellow
question mark, a yellow cross, a white skull, a red skull and a blue diamond.
Like the restoration, this happens where the world runs with the mod:
single-player, the host of a multiplayer game, or a dedicated server that has
it. The marker keeps its position and name. Your five presets are rewritten the
same way on your own computer, keeping their names.

A converted marker is the game's own, so it keeps its icon if you uninstall the
mod. On a dedicated server without the mod nothing is converted, and such
markers keep showing the mod's icon to players who have the mod.

## Requirements

- Core Keeper 1.3 (verified on 1.3.0.4)
- No other mods. MapMarkers+ itself is not needed — it does not load on 1.3 —
  and is best disabled.

## Multiplayer

Every player who wants to see the mod's icons needs the mod.

- **On a server that has the mod**, every joining player must have it too.
- **On a server without the mod**, you can join and place markers with the mod's
  icons; they are saved with the world and still show after a server restart.
  Players without the mod see a stand-in where such a marker is: usually a blue
  diamond, but at times the icon of another marker. Old MapMarkers+ markers are
  not restored there, because restoration runs only where the world runs.

## Uninstalling

A marker that still uses one of the mod's icons — one you placed, or one the
mod restored — loses its icon without the mod. It shows a stand-in instead,
usually a blue diamond but at times the icon of another marker, and the game logs an
error for it every time it draws it. Reinstalling brings the icons back: each
icon has a fixed identity that saved markers refer to. What does not come back
is the MapMarkers+ type a restored marker once carried, as described above.

Markers that were converted to the game's own question mark, cross, skull, red
skull or diamond keep their icons, and so do old MapMarkers+ crosses and red
skulls, which the mod restores as the game's own.

## Known limitations

- **Numbers and Letters are too large on the minimap.** They have no small
  minimap sprite yet and use their full-size one, which overlaps neighbouring
  markers. The other three icons have proper small sprites.
- **A placed marker cannot be edited.** This is Core Keeper 1.3's own
  behaviour, not the mod's: to change a marker's icon or name, delete it and
  place a new one.
- **The icon order depends on how the game hands out its icon list.** If a
  later game version changes that, the mod's icons move to the front of the row
  and the mod logs a warning. Nothing else is affected.

## Credits

The marker art and the original mod, [MapMarkers+](https://github.com/moorowl/MapMarkersPlus), are by **moorowl**, released
under the MIT License. Map Markers Enhanced is a fork of it for Core Keeper 1.3:
it keeps moorowl's sprite sheet and commit history, and replaces the rest of the
old implementation with the game's own marker system.

## License

MIT — see [`LICENSE`](LICENSE), MapMarkers+'s licence (© 2026 moorowl), kept
unchanged. Core Keeper modding is subject to Pugstorm's EULA: personal use,
non-commercial.

---

## Development

Built with the official Pugstorm Core Keeper Mod SDK.

- [Mod-internal CLAUDE.md](CLAUDE.md) — the icon generator, the constants the
  code relies on, and how to test
- [ADR 001 — a data-native port](docs/adrs/001-data-native-port.md)
- [ADR 002 — hiding vanilla duplicates](docs/adrs/002-hide-vanilla-duplicates.md)
- [Manual in-game tests](docs/manual-tests.md)
- [Roadmap](docs/roadmap.md)

# Map Markers Enhanced

A Core Keeper mod that adds a redrawn set of 113 map markers to Core Keeper 1.3
— ores and gems, coloured flags, tapestry banners, orbs, arrows, chests,
numbers, letters and more — as native icons in the game's own map-marker
dialog. The art is redrawn after moorowl's MapMarkers+. The mod also gives back
the markers that MapMarkers+ players lost in the 1.3 update, when every one of
them turned into the same yellow question mark.

## Features

- **Seven extra icons in the marker dialog**, listed after the game's own:
  General (18 markers), Ores (11), Flags (14), Tapestry (15), Orbs (19),
  Numbers (10) and Letters (26, A–Z). Pick an icon in the upper row, then the
  marker in the lower one.
- **Tapestry and Orbs are new.** Tapestry is the game's fifteen banners, the
  unpainted one and fourteen colours; Orbs are nineteen of the game's orbs, from
  the empty one through every colour to the gold, lava and flower orbs.
- **Every marker has its own minimap sprite**, so numbers and letters sit
  cleanly beside their neighbours.
- **The game's own question mark, cross, skull and blue diamond** are not
  offered by the mod: the game draws them itself since 1.3. Markers that used
  the mod's older copies are converted, see below.
- **The rest is the game's own.** Naming a marker, the five presets, the
  minimap, multiplayer and saving work exactly as they do for vanilla markers:
  the mod adds icons, keeps the dialog scrolled to your selection, restores old
  markers and moves markers and presets from the older icons to the new set.
- **The dialog opens on your selection.** When you open a preset that uses one
  of the mod's icons, the dialog scrolls so the selected icon and marker are in
  view instead of starting at the left end.
- **Old MapMarkers+ markers are restored** — see below.
- **Markers placed with the mod's 1.x icons move to the new set** — see below.

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

## Markers from version 1.x of this mod

Version 2.0.0 replaces the mod's five 1.x icons with the seven new ones, and
the old icons are never used again. A marker you placed with a 1.x icon is
rewritten to the same-named marker of the new set — the same arrow, ore, flag,
number or letter, redrawn. The question mark, cross, skull, red skull and
diamond become the game's own: a yellow question mark, a yellow cross, a white
skull, a red skull and a blue diamond. Like the restoration, this happens where
the world runs with the mod: single-player, the host of a multiplayer game, or a
dedicated server that has it, and it catches a marker that a 1.x player places
later too. The marker keeps its position and name. Your five presets are
rewritten the same way on your own computer, keeping their names.

A marker that became the game's own keeps its icon if you uninstall the mod.
**Update everyone who shares a world or a server with you:** on a dedicated
server without the mod nothing is converted, and players with 2.0.0 see such
markers as a stand-in; players still on 1.x see every marker of the new set that
way.

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

- **A placed marker cannot be edited.** This is Core Keeper 1.3's own
  behaviour, not the mod's: to change a marker's icon or name, delete it and
  place a new one.
- **The icon order depends on how the game hands out its icon list.** If a
  later game version changes that, the mod's icons move to the front of the row
  and the mod logs a warning. Nothing else is affected.

## Credits

The original mod, [MapMarkers+](https://github.com/moorowl/MapMarkersPlus), is by **moorowl**, released under the MIT
License. Map Markers Enhanced is a fork of it for Core Keeper 1.3: it keeps
moorowl's commit history and replaces the rest of the old implementation with
the game's own marker system.

The art is redrawn by Valgard after moorowl's MapMarkers+ (MIT). The tapestry
banners are drawn from Core Keeper's tapestry sprites and the orbs from its item
sprites.

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
- [ADR 002 — hiding vanilla duplicates](docs/adrs/002-hide-vanilla-duplicates.md) (partly superseded)
- [ADR 003 — retiring the 1.x blocks](docs/adrs/003-retire-the-1x-blocks.md)
- [Manual in-game tests](docs/manual-tests.md)
- [Roadmap](docs/roadmap.md)

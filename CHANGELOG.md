# Changelog

All notable changes to this mod are documented here. The format is loosely based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the topmost `## [x.y.z]` entry is the current published
version.

## [2.0.0] - 2026-10-07

The marker art is redrawn, and two icons are new. **Update everyone who shares a
world or a server with you** — see "Update everyone" below.

### Added

- **A redrawn set of 113 markers in seven icons**, in this order after the
  game's own: General (18), Ores (11), Flags (14), Tapestry (15),
  Orbs (19), Numbers (10) and Letters (26). The art is redrawn after moorowl's
  MapMarkers+ (MIT).
- **Tapestry**: the game's fifteen tapestry banners, the unpainted one and
  fourteen colours, as 8x8 markers.
- **Orbs**: nineteen of the game's orbs, from the empty one through every colour
  to the gold, lava and flower orbs.
- **Every marker has its own minimap sprite.** Numbers and Letters no longer
  overlap their neighbours, and the other icons get redrawn small sprites too.

### Changed

- **The mod's five 1.x icons are gone for good.** The marker dialog offers only
  the seven new ones, with no hidden markers left in the rows, and the five
  1.x icon identities are never used again.
- **Existing markers move to the new set** wherever the world runs with the
  mod: single-player, the host, or a dedicated server with the mod. A marker
  keeps its position and name and gets the same-named marker of the new set; the
  five that the game draws itself (question mark, cross, skull, red skull, blue
  diamond) become the game's own, as in 1.1.0. This also catches a marker that a
  1.x client places later. Restored MapMarkers+ markers land on the new set
  directly, and presets on a 1.x marker are rewritten the same way.
- Ores and Gems is now called Ores and has 11 markers: the radiation crystal is
  new beside the ten that remained.

### Removed

- The tweaks that hid five markers in the dialog. With nothing hidden any more,
  the icon preview and the position-keeping across icon switches that went with
  them are gone.

### Update everyone

- **A dedicated server without the mod does not migrate anything.** Players with
  2.0.0 see every marker placed with a 1.x icon there as a plain blue diamond
  (at times another marker's icon), and the game logs an error for each every
  time it draws it. Put the mod on the server, or accept it.
- **Players still on 1.x see every migrated marker, and every marker placed with
  the new set, the same way**, until they update. Markers that became the game's
  own show normally. A server with the mod only asks for the mod, not for a
  version, so nothing stops a 1.x player from joining.
- **Uninstalling still turns every marker with a mod icon into that stand-in.**
  Markers that became the game's own keep their icon.

### Credits

- The art is redrawn by Valgard after moorowl's MapMarkers+ (MIT); the banners
  come from Core Keeper's tapestry sprites and the orbs from its item sprites.

## [1.1.0] - 2026-10-06

The mod stops duplicating the markers Core Keeper 1.3 draws itself.

### Changed

- **Five markers are the game's own now.** The question mark, cross, skull, red
  skull and blue diamond are no longer offered by the mod: the game has them. The
  marker dialog shows General with 18 markers and Ores and Gems with 10; the
  flags, the green one included, are unchanged.
- **Existing markers with them are converted** to the game's own — a yellow
  question mark, yellow cross, white skull, red skull and blue diamond — wherever
  the world runs with the mod: single-player, the host, or a dedicated server
  with the mod. Converted markers keep their icon if the mod is uninstalled.
- Old MapMarkers+ crosses and red skulls now come back as the game's own cross
  and red skull instead of the mod's icons.
- With the dialog's first marker hidden, an icon you have not selected previews
  its first visible marker, and switching icons keeps your position in the row.

### Added

- **Presets are converted too.** Marker presets that point at one of the five are
  rewritten to the game's own marker, keeping their names.

## [1.0.0] - 2026-09-29

First release, for Core Keeper 1.3: moorowl's MapMarkers+ marker art as native
map-marker icons, and the old MapMarkers+ markers restored.

### Added

- **Five extra icons in the game's marker dialog**, after the game's own:
  General, Ores and Gems, Flags, Numbers and Letters (A–Z) — 83 markers in all,
  from MapMarkers+ by moorowl (MIT). Naming, presets, the minimap, multiplayer
  and saving are the game's own.
- **Old MapMarkers+ markers come back.** The 1.3 update turned every marker
  drawn with MapMarkers+'s own art into the same question mark. Loading such a
  world with this mod on the side that runs it — single-player, the host, or a
  dedicated server with the mod — gives each of them its original icon, once.
  This replaces the MapMarkers+ information stored in the marker, so back the
  world up first if you might want the question marks back.
- The marker dialog scrolls to the selected icon and marker when it opens.

### Good to know

- **Only players need the mod; a server does not.** A server that has it
  requires it of every player who joins. On a server without it, your markers
  with the mod's icons are saved and survive a restart, but players without
  the mod see a plain blue diamond in their place, and old markers are not
  restored there.
- **Uninstalling turns every marker that uses the mod's icons into a plain blue
  diamond**, restored ones included. Reinstalling brings the icons back.
- On the minimap, Numbers and Letters are drawn at full size and overlap
  neighbouring markers until they get small sprites of their own.

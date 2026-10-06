# Changelog

All notable changes to this mod are documented here. The format is loosely based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the topmost `## [x.y.z]` entry is the current published
version.

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

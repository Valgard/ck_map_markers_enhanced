# Changelog

All notable changes to this mod are documented here. The format is loosely based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the topmost `## [x.y.z]` entry is the current published
version.

## [1.0.0] - Unreleased

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

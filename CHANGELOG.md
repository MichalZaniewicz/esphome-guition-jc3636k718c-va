# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.2.6] - 2026-06-25

### Fixed
- Neon watchface: temperature degree sign showed as `Âº` (double-encoded in source); now renders `°` like Classic.

## [2.2.5] - 2026-06-19

### Added
- New **Knobuss** game (optional carousel screen, a knob-steered tube shooter): your ship orbits the rim, you auto-fire inward, foes spiral out from a black-hole core. Turn the knob to aim; every foe that reaches the rim costs a life and bursts in an animated explosion. The ship is a pixel fighter pre-rotated into 16 frames so it always points inward, foes are glowing orbs, a rushing starfield + concentric rings give a cheap 3D-depth tube, and the menu has a "Knobuss" title screen. 3 lives, top-10 scores. Add it to your `screen_order` as `knobuss` (`gyruss` also works). (Art: Lunar Lander pack by Matt Walkden, CC0; see assets/sprites/knobuss/CREDITS.txt.)

### Fixed
- Cool Cars ran choppier than the other games: its per-tick position updates were 8 separate widget actions (now one batched lambda, like Snake/Knobuss), and it ticked at 12.5fps (now 20fps with speeds scaled to keep the same pace) - so the motion is much smoother.

## [2.2.4] - 2026-06-19

### Changed
- Sensors screen: each glance now gets its own accent colour (icon + position dots).
- Added a faint depth ring to the Sensors, Home (Classic) and Weather screens for a consistent framed look.

## [2.2.3] - 2026-06-19

### Changed
- Thermostat screen polished: the whole arc is now colour-coded by action (heating / cooling / idle / off), a white head-dot marks the target on the gauge, and a faint depth ring was added.

## [2.2.2] - 2026-06-19

### Changed
- Timer screen redesigned: colour-coded depleting ring (green → amber → red) with a head-dot, SET / RUNNING / PAUSED status, and tile-styled buttons with a soft glow.
- Alarm screen redesigned: red scrim, a big pulsing bell, "TIME'S UP!" and a tap-to-stop hint.

### Fixed
- Returning to the home screen after music stops/pauses keeps the selected watchface (was forced to Classic).
- The Minecraft watchface now shows the active-timer badge.

## [2.2.1] - 2026-06-19

### Added
- **Minecraft watchface** - a blocky scene with a day/night cycle (sun by day, moon + stars by night), a textured grass/dirt ground, a pixel-font clock, and a heart bar for the battery. Optional, like the other faces.

### Changed
- Watchfaces redraw the clock only when the minute changes (not every second), so they stay light; faces slide in by swipe direction instead of cross-fading.

### Fixed
- Silenced the font "missing glyphs" warnings (pixel font uses an explicit glyph list; the Roboto faces use `ignore_missing_glyphs`).

## [2.2.0] - 2026-06-19

### Added
- **Watchfaces** - the home screen now has selectable looks. Classic is built in; enable the optional **Neon** face (big two-tone digits + neon rings) or copy the heavily-commented **Demo** template to build your own. Pick one in Settings → Home → Watchface with a live full-screen preview (knob switches, tap keeps).

### Changed
- Settings: clearer names (Home screen, LED Ring, Voice Assistant, Show weather / Show climate, Screen auto-off) and the selected row is styled like the swipe-up control tiles.
- The rotary knob now wakes the screen from sleep, just like a tap.

## [2.1.6] - 2026-06-18

### Changed
- Control tiles: the lit tile now has a soft amber glow, and tile names get a little letter spacing.

## [2.1.5] - 2026-06-18

### Changed
- Weather screen redesigned: animated condition icons, colour-coded temperature, and a glow that slides to the selected day.
- Boot splash ring is now an azure comet instead of the rainbow.

### Fixed
- LED ring no longer flashes a stray pixel during screen transitions (RMT now uses DMA).

## [2.1.4] - 2026-06-18

### Added
- **Snake 360** (optional carousel screen). Steer a 360-degree snake with the knob; eat fruit (up to 3 at once) to grow, avoid the ring, your tail and up to two skulls. Keeps a top-10.

### Changed
- In games the knob only changes volume on the menu/scores/how-to screens; while playing and on game-over it steers (no accidental volume changes).

### Fixed
- Clock could stay on UTC: the `timezone` substitution now maps common IANA names (e.g. `Europe/Warsaw`) to the POSIX form the device needs. Use a POSIX string for unlisted zones.

## [2.1.3] - 2026-06-17

### Added
- **Boot splash**. A short "HELLO!" greeting on startup (~5 s) with a spinning arc on the screen
  and the LED ring animating, then it cross-fades to the clock. Touch is ignored until it hands off.
- **Hold to talk** toggle (Settings -> Assistant). Press and hold anywhere on the screen to start
  the assistant; this can now be turned off (the wake word keeps working regardless).

### Fixed
- Clock could show UTC (off by the timezone offset) after a restart until the next time sync. The
  device now re-applies its resolved timezone every second, so the clock never drifts to UTC.
- OTA updates could roll back to the previous firmware if the device was restarted shortly after
  flashing (on esp-idf the bootloader only keeps a new image once the boot is marked good). The
  image is now committed as soon as the boot splash finishes, and the safe-mode window is shortened.

## [2.1.2] - 2026-06-17

### Changed
- Per-screen settings are now declared in each screen's own package via a generic Widgets
  options registry, so a screen is fully self-contained (its options, globals and reset
  logic live in its file). Adding a screen with settings no longer touches the core.
- The games' "Reset scores" is now under separate **Cool Cars** and **Space Wars** groups
  in Settings -> Widgets (previously a single "Games" group); each game owns its high scores.

## [2.1.1] - 2026-06-17

### Added
- **Sensors screen** (optional). A glance of 1-6 configurable Home Assistant entities, shown
  one at a time big and readable; turn the knob to cycle (slider dots show the position).
  Pulls straight from HA (no helper), auto-skips unconfigured slots, and units with a micro
  sign / superscripts are sanitized so they don't render as boxes. New `glanceN_entity` /
  `glanceN_name` / `glanceN_icon` substitutions, plus the icons `air`, `plant`, `plex`,
  `server` and `shield`.

## [2.1.0] - 2026-06-17

### Added
- **Thermostat screen** (optional). A round dial for a Home Assistant `climate.*` entity:
  the knob sets the target temperature (committed ~0.6 s after you stop turning), tap toggles
  on/off, and the accent colour follows the action (heating / cooling / idle). Shows the
  current temperature, humidity and HVAC mode. Set it with the `climate_entity` substitution.
- **Configurable wake word** via a `wake_word` substitution (default `alexa`; built-in:
  `okay_nabu`, `hey_jarvis`, `hey_mycroft`).

## [2.0.0] - 2026-06-17

Modular screens release. The firmware is now split into an always-on core plus optional
screen packages, and you keep a single thin config locally that pulls everything else
from GitHub at compile time.

### Added
- **Modular screens.** Optional carousel screens live as separate packages under
  `base/screens/`. Pick which ones compile in via the `files:` list and set their
  left-to-right order with the `screen_order` substitution, all from one file.
- **Thin local config.** The root `guition-va.yaml` is the only firmware file you keep;
  it pulls `base/core.yaml` and the selected `base/screens/*.yaml` as a remote package.
- **Weather screen.** Today plus a 7-day radial dial (Apple-Watch style); the knob
  highlights a day, the centre shows the day name, temperatures and condition. Includes a
  Celsius/Fahrenheit toggle and a Home Assistant helper sensor that feeds the forecast.
- **Example "demo" screen.** A small, heavily commented screen (TAP ME!) you can copy as a
  starting point for your own screen.
- **Configurable control tiles.** The swipe-up page is now four tiles, each with its own HA
  entity, icon (chosen by name from a 20-icon set, repeatable) and label. Works on any HA
  domain via `homeassistant.toggle`.
- **Configurable clock timezone** via a `timezone` substitution (DST automatic).

### Changed
- **Repository layout.** The core and screens moved into `base/`; the root holds the thin
  `guition-va.yaml` you copy and edit.
- **Settings menu.** "Widgets" is now a per-screen group menu (Widgets -> Demo / Games /
  Weather), each opening that screen's own options. A separate "Home" submenu owns the
  home-screen widget toggles; "Display" keeps global brightness / night / screen-off.
  "System" is always last, and device Restart lives only inside it.

### Fixed
- Clock showing UTC: the timezone is now set explicitly (the Home Assistant time platform
  does not sync the zone to the device).
- Control-tile icons rendering empty, and the "led" icon pointing at map-marker-outline
  (now `led-strip`).
- Settings list collapsing "Restart" and "System" into one entry (a folded YAML newline).
- Demo LED ring staying lit on the home screen after a reboot.

## [1.0.0] - 2026-06-16

### Added
- Initial release: ESPHome voice assistant for the Guition JC3636K718C round knob display.
  Clock, music player (album art + transport), timer, two games (Cool Cars, Space Wars),
  settings menu, WS2812 LED ring, on-device wake word and the Assist voice pipeline.
- Fonts, images and sounds fetched from GitHub at compile time (nothing to copy locally
  except the config and the partition table).

[2.2.5]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.5
[2.2.4]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.4
[2.2.3]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.3
[2.2.2]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.2
[2.2.1]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.1
[2.2.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.2.0
[2.1.6]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.6
[2.1.5]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.5
[2.1.4]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.4
[2.1.3]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.3
[2.1.2]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.2
[2.1.1]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.1
[2.1.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.0
[2.0.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.0.0
[1.0.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v1.0.0

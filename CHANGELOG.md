# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.1.4] - 2026-06-18

### Added
- **Snake 360 screen** (optional). A smooth-steering 360-degree snake: turn the knob to steer the head's heading
  and the body trails behind it, across the whole round screen bounded by a green ring (the snake
  passes under the score). Eat fruit to grow and score - up to 3 fruit (random sprites from a set
  of 12) are kept on the board and replenished over time, sooner when only one is left. Up to two
  skull hazards appear for a while and end the game if eaten; hitting the ring or your own tail also
  ends it. It speeds up as you score and keeps a top-10 (with its own "Reset scores" under Settings
  -> Widgets -> Snake). Full-screen menu logo and a green UI palette to match; How-to uses the same
  numbered-badge layout as the other games. Pick it in the `files:` list and place it via
  `screen_order` like any other screen.

### Changed
- In all games the knob now controls volume on the menu, scores and how-to screens, and is captured
  (no volume change) only while playing and on the game-over screen - so you can't nudge the volume
  mid-game or right after a crash, but the knob is free everywhere else.

### Fixed
- Clock stuck on UTC (off by the timezone offset). The device has no IANA timezone database, so an
  IANA `timezone:` (e.g. `Europe/Warsaw`) depended on a compile-time conversion that fails on some
  build hosts, and the homeassistant time platform didn't apply the zone at runtime either. Core now
  maps common IANA names to their POSIX form itself and forces that into the device environment at
  boot, re-asserting it every second - so a friendly `timezone: "Europe/Warsaw"` just works. A zone
  not in the table can still be given as a POSIX string directly (github.com/nayarsystems/posix_tz_db).

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

[2.1.2]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.2
[2.1.1]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.1
[2.1.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.1.0
[2.0.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v2.0.0
[1.0.0]: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/releases/tag/v1.0.0

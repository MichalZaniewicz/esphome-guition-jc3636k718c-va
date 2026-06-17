# Modular screens (beta)

Goal: pick which carousel screens are compiled in, straight from the YAML - comment a
line in `packages:` and the screen is gone from the firmware (and the flash it used).

This is a **beta** layout on the `beta` branch. It needs to be compiled on a device
(there is no local validation here). Until it is verified, `main` keeps the single-file
config.

## How you choose screens

You keep one thin file locally (`guition-va.yaml`, repo root) that pulls the core and the
screens from GitHub as a remote package. Pick screens in its `files:` list:

```yaml
packages:
  core:
    url: https://github.com/MichalZaniewicz/esphome-guition-jc3636k718c-va
    ref: beta
    files:
      - base/core.yaml                 # always on (clock + controls + settings)
      - base/screens/timer.yaml
      - base/screens/cool-cars.yaml
      - base/screens/space-wars.yaml   # comment out to drop Space Wars
    refresh: 0s
```

Remove/comment a `base/screens/*.yaml` line -> that screen's page, scripts, globals and
game tick are not compiled, and its carousel slot disappears. Nothing else to edit.

## How it stays decoupled (the contract)

ESPHome merges package lists (globals/scripts/interval/lvgl.pages/esphome.on_boot all
concatenate), so each screen file is self-contained and the core never names a screen's
symbols. The glue is a few plain globals in the core:

- `g_base` (int) - id of the current carousel screen. Fixed ids: 0=clock, 1=player,
  2=timer, 3=cars, 4=space (an id never changes, even if a screen is absent).
- `g_order[12]`, `g_order_n` - carousel order, built at boot. Core seeds clock+player;
  each screen package appends its id in an `esphome.on_boot` step (priority sets the
  position). Swipe left/right just steps through `g_order` and wraps.
- `g_nav_req` (bool) + `g_nav_anim` (int: 0=right 1=left 2=top 3=bottom) - core sets
  these on a screen change; each screen package owns a small handler that, when
  `g_base == <my id>`, runs its own `lvgl.page.show` with the matching animation and
  clears `g_nav_req`. Core only `page.show`s its own (clock/player).
- `g_knob_capture` (bool) + `g_knob_delta` (int) - when a screen wants the knob (game
  running, timer idle), it sets `g_knob_capture=true`; the core knob handler then just
  accumulates +/-1 into `g_knob_delta` instead of changing volume. The screen reads and
  zeroes `g_knob_delta` in its own tick. Core never names a game variable.
- `g_scores_reset` (bool) - Settings "reset scores" / factory reset set this; each game
  package clears its own score globals when it sees the flag. Core does not touch game
  score arrays.

So a screen package contributes: its `globals`, its `script`s, its game-tick `interval`,
its `lvgl.pages` entry, one `on_boot` step to register its carousel id, and one nav
handler. It reads/writes only the shared core globals above.

## Status

- [x] core refactor: data-driven carousel (`g_order`), nav via `g_nav_req`, knob via
      `g_knob_capture`/`g_knob_delta`. Score storage (`g_top`/`g_best`/`g_sw_top`/`g_sw_best`)
      stays in the core so reset/factory work without the game screens.
- [x] extract Space Wars -> `base/screens/space-wars.yaml`
- [x] extract Cool Cars -> `base/screens/cool-cars.yaml`
- [x] extract Player -> `base/screens/player.yaml` (volume + overlay stay in core)
- [x] timer carousel-screen toggle -> `base/screens/timer.yaml` (voice timers/alarm/badge stay in core)
- [x] new Weather screen -> `base/screens/weather.yaml` (radial 7-day dial, knob highlights the day;
      forecast from the HA helper `base/screens/weather.ha-helper.yaml`)
- [x] new Thermostat screen -> `base/screens/thermostat.yaml` (climate.* dial; knob sets the target with a
      debounced commit, tap toggles on/off, accent colour by heating/cooling/idle)
- [x] settings ownership: home-screen widget toggles moved to a "Home" submenu (core); "Display"
      keeps only global brightness/night/screen-off
- [x] carousel order via the `screen_order` substitution; screens register `g_present`,
      absent ones are skipped (clock kept as a safety fallback)
- [x] dynamic settings registry: screens add their own entries (label + g_mode) at boot;
      the shared "Games" entry (reset scores) is added once, only when a game is present.
      The roller list is applied at boot with `lv_roller_set_options(id(roller)->obj, ...)`.
- [x] verified on device (compiles; screens toggle from `files:`, order from `screen_order`,
      settings list adapts)
- [ ] consider merging `beta` -> `main` (do NOT until the user says; then update README/wiki)

## Adding a new screen (recipe)

A screen package adds: its `globals` / `script`s / game-tick `interval` / `lvgl.pages`
entry; an `esphome.on_boot` step that sets `id(g_present)[<id>] = true`; a 50ms nav
handler that shows its page when `g_nav_req && g_base == <id>`. To give it a carousel
slot, add its name to the core `name -> id` map in the order builder and to `screen_order`.
To add a settings entry, append a label + g_mode to `g_set_labels`/`g_set_items` in on_boot
(guard it for shared entries).

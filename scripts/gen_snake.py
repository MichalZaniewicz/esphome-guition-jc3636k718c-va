#!/usr/bin/env python3
# Generates base/screens/snake.yaml (modular carousel screen, base id 9). Run from anywhere:
#   python scripts/gen_snake.py
#
# Smooth-steering 360-degree snake. The head glides every tick (knob rotates its heading); the body is a TRAIL
# of dots the head lays down every SEG_DIST of travel. Dots do NOT move once placed - each tick only
# the head moves and (when the head advanced one spacing) one dot is added at the head / dropped at
# the tail. Per-tick render cost is constant regardless of length, which keeps the main loop fast
# enough not to starve the knob input (a chain-follow body that moved every segment every tick made
# turning degrade as the snake grew).
#
# IMPORTANT (why segments are moved from a lambda, not YAML actions): ESPHome plays a sequence of
# synchronous actions by recursion, so a long YAML action list (e.g. a 56-way "if slot==k" dispatch
# or a 56-widget redraw) becomes ~56 nested calls and overflows the task stack. So all body/head
# positioning is done inside ONE lambda via lv_obj_set_pos on an array of lv_obj_t* (indexed at
# runtime). Hidden = parked off-screen (pos 400,400) - avoids any LVGL flag-API version differences.
# Coords: a centre-offset (cx,cy) maps to a top-left lv_obj_set_pos of (180+cx-SEG/2, 180+cy-SEG/2).
import os

POOL = 56          # max body dots = number of body widgets
SEG  = 9           # dot square (px)
SEGR = 4           # dot corner radius
HALF = SEG // 2    # 4
SEG_DIST = 8.0     # spacing between trail dots (px)
R    = 168.0       # max head distance from centre (inside the ring)
RING_D = 344       # ring diameter (radius 172) -> just inside the 360 round display
SPEED0 = 3.2       # head speed px/tick (50ms tick)
TURN = 0.26        # radians turned per knob detent
EAT  = 12.0        # head-to-fruit distance that counts as eating
SKHIT = 13.0       # head-to-skull distance that kills
SELF_SKIP = 6      # newest body dots skipped in self-collision (the neck)
SELF_DIST = 8.0    # head-to-body distance that kills (~ the two 9px sprites touching)
GROW = 3           # body dots added per fruit eaten
START_LEN = 5

NFRUIT = 12        # fruit sprites in the rotation
NFSLOT = 3         # max fruit on the board
NSKULL = 2         # max skulls
FRUIT_WAIT = 90    # ticks between fruit top-ups (~4.5s); halved when only 1 fruit is left
SKULL_WAIT = 200   # ticks between skull spawns (~10s)
SKULL_LIFE = 220   # ticks a skull stays (~11s)

BASE = "https://raw.githubusercontent.com/MichalZaniewicz/esphome-guition-jc3636k718c-va/main/assets/sprites/snake/"

PAGE_BG  = "0x0D1E15"
RING     = "0x3A8C4E"
HEAD     = "0xB8E86A"
BODY     = "0x52A049"
ACCENT   = "0xA6D85F"
ACCENT_TXT = "0x12241A"
BTN2     = "0x244A30"
BTN2_TXT = "0xCFE6C4"
GRAY     = "0x3A3A3D"
TXT      = "0xC6DCC0"
BADGE    = "0x6FB23F"
HUD      = "0xCFEAE4"
WORDMARK = "0x12212D"

M = POOL * 4   # safe positive-modulo offset
# C++ array of the body-segment lv_obj_t* (built locally in each rendering lambda)
SEGINIT = "lv_obj_t *SS[" + str(POOL) + "] = { " + ", ".join(f"id(sn_seg{k})" for k in range(POOL)) + " };"


def body_widgets():
    # no align (top-left origin); parked off-screen until positioned by a lambda
    return "\n".join(
        f"        - obj: {{ id: sn_seg{k}, x: 400, y: 400, width: {SEG}, height: {SEG}, "
        f"radius: {SEGR}, border_width: 0, bg_color: {BODY}, bg_opa: COVER }}"
        for k in range(POOL))


def fruit_widgets():
    return "\n".join(
        f"        - image: {{ id: sn_fruit{s}, align: CENTER, x: 0, y: 0, src: img_sn_fruit0, hidden: true }}"
        for s in range(NFSLOT))


def skull_widgets():
    return "\n".join(
        f"        - image: {{ id: sn_skull{s}, align: CENTER, x: 0, y: 0, src: img_sn_skull, hidden: true }}"
        for s in range(NSKULL))


def fspr_dispatch():
    return "\n".join(
        f"                        - if: {{ condition: {{ lambda: 'return id(g_sn_newfruit) == {s};' }}, "
        f"then: [ script.execute: sn_fspr{s} ] }}"
        for s in range(NFSLOT))


def skull_dispatch():
    return "\n".join(
        f"                        - if: {{ condition: {{ lambda: 'return id(g_sn_newskull) == {s};' }}, "
        f"then: [ lvgl.widget.update: {{ id: sn_skull{s}, hidden: false, "
        f"x: !lambda 'return (int) lroundf(id(g_sn_skx)[{s}]);', "
        f"y: !lambda 'return (int) lroundf(id(g_sn_sky)[{s}]);' }} ] }}"
        for s in range(NSKULL))


def items_hidden():
    out = []
    for s in range(NFSLOT):
        out.append(f"      - lvgl.widget.update: {{ id: sn_fruit{s}, hidden: !lambda 'return !id(g_sn_fon)[{s}];' }}")
    for s in range(NSKULL):
        out.append(f"      - lvgl.widget.update: {{ id: sn_skull{s}, hidden: !lambda 'return !id(g_sn_skon)[{s}];' }}")
    return "\n".join(out)


def item_hides():
    out = [f"      - lvgl.widget.hide: sn_fruit{s}" for s in range(NFSLOT)]
    out += [f"      - lvgl.widget.hide: sn_skull{s}" for s in range(NSKULL)]
    return "\n".join(out)


def fruit_setters():
    blocks = []
    for s in range(NFSLOT):
        lines = [f"  - id: sn_fspr{s}", "    then:",
                 f"      - lvgl.widget.update: {{ id: sn_fruit{s}, hidden: false, "
                 f"x: !lambda 'return (int) lroundf(id(g_sn_fx)[{s}]);', "
                 f"y: !lambda 'return (int) lroundf(id(g_sn_fy)[{s}]);' }}"]
        for k in range(NFRUIT):
            lines.append(
                f"      - if: {{ condition: {{ lambda: 'return id(g_sn_fi)[{s}] == {k};' }}, "
                f"then: [ lvgl.image.update: {{ id: sn_fruit{s}, src: img_sn_fruit{k} }} ] }}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def fruit_images():
    return "\n".join(
f"""  - id: img_sn_fruit{k}
    file: "{BASE}fruit{k}.png"
    type: RGB565
    transparency: alpha_channel""" for k in range(NFRUIT))


YAML = f"""# Snake - optional carousel screen (base id 9). Smooth-steering 360-degree snake steered by the knob.
# Remove it: drop this file from your config's package "files:" list. Nothing else to edit.
# Scores (g_sn_top / g_sn_best) + the "Reset scores" settings action live here - fully self-contained.
#
# GENERATED by scripts/gen_snake.py - edit the generator, not the blocks. Body = a trail of dots
# (ring buffer) rendered from a lambda (lv_obj_set_pos), so per-tick cost is constant + shallow.

esphome:
  on_boot:
    - priority: 655
      then:
        - lambda: 'id(g_present)[9] = true;'
    - priority: 650
      then:
        - lambda: |-
            int g = id(g_wgrp_n)++;
            id(g_wgrp_labels) += (g ? "\\n" : ""); id(g_wgrp_labels) += "Snake";
            int o = id(g_wopt_n)++;
            id(g_wopt_group)[o] = g; id(g_wopt_label)[o] = "Reset scores"; id(g_wopt_kind)[o] = 1; id(g_wopt_ptr)[o] = &id(g_sn_reset);

globals:
  - id: g_sn_best
    type: int
    restore_value: yes
    initial_value: '0'
  - id: g_sn_top
    type: int[10]
    restore_value: yes
  - id: g_sn_reset
    type: bool
    restore_value: no
    initial_value: 'false'
  - id: g_sn_state    # 0=menu 1=playing 2=game over 3=how-to 4=scores
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_len      # body dots in the snake
    type: int
    restore_value: no
    initial_value: '{START_LEN}'
  - id: g_sn_score
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_tx       # body trail dots X (ring buffer; centre coords px)
    type: float[{POOL}]
    restore_value: no
  - id: g_sn_ty
    type: float[{POOL}]
    restore_value: no
  - id: g_sn_head     # ring index of the newest dot
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_hx       # smooth head position (leads the newest dot)
    type: float
    restore_value: no
    initial_value: '0.0'
  - id: g_sn_hy
    type: float
    restore_value: no
    initial_value: '0.0'
  - id: g_sn_ang      # heading (radians)
    type: float
    restore_value: no
    initial_value: '0.0'
  - id: g_sn_grow     # pending growth (appends that won't drop the tail)
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_dead
    type: bool
    restore_value: no
    initial_value: 'false'
  - id: g_sn_add      # ring slot to show/position this tick (-1 none)
    type: int
    restore_value: no
    initial_value: '-1'
  - id: g_sn_del      # ring slot to park off-screen this tick (-1 none)
    type: int
    restore_value: no
    initial_value: '-1'
  - id: g_sn_fx
    type: float[{NFSLOT}]
    restore_value: no
  - id: g_sn_fy
    type: float[{NFSLOT}]
    restore_value: no
  - id: g_sn_fi
    type: int[{NFSLOT}]
    restore_value: no
  - id: g_sn_fon
    type: bool[{NFSLOT}]
    restore_value: no
  - id: g_sn_fclk
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_newfruit
    type: int
    restore_value: no
    initial_value: '-1'
  - id: g_sn_skx
    type: float[{NSKULL}]
    restore_value: no
  - id: g_sn_sky
    type: float[{NSKULL}]
    restore_value: no
  - id: g_sn_skon
    type: bool[{NSKULL}]
    restore_value: no
  - id: g_sn_skage
    type: int[{NSKULL}]
    restore_value: no
  - id: g_sn_skclk
    type: int
    restore_value: no
    initial_value: '0'
  - id: g_sn_newskull
    type: int
    restore_value: no
    initial_value: '-1'

script:
{fruit_setters()}
  - id: sn_hud
    then:
      - lvgl.label.update: {{ id: lbl_sn_score, text: !lambda 'char b[12]; snprintf(b,sizeof(b),"%d",id(g_sn_score)); return std::string(b);' }}
  - id: sn_items
    then:
{items_hidden()}
  # full body redraw - used at start / when (re)entering the play screen (one lambda, not per tick)
  - id: sn_drawfull
    then:
      - lambda: |-
          {SEGINIT}
          for (int k = 0; k < {POOL}; k++) {{
            int d = (id(g_sn_head) - k + {M}) % {POOL};
            if (d < id(g_sn_len)) lv_obj_set_pos(SS[k], 180 + (int) lroundf(id(g_sn_tx)[k]) - {HALF}, 180 + (int) lroundf(id(g_sn_ty)[k]) - {HALF});
            else lv_obj_set_pos(SS[k], 400, 400);
          }}
          lv_obj_set_pos(id(sn_head), 180 + (int) lroundf(id(g_sn_hx)) - {HALF}, 180 + (int) lroundf(id(g_sn_hy)) - {HALF});
      - script.execute: sn_items
  # hide every gameplay widget (park body off-screen + hide fruit/skulls)
  - id: sn_clear
    then:
      - lambda: |-
          {SEGINIT}
          for (int k = 0; k < {POOL}; k++) lv_obj_set_pos(SS[k], 400, 400);
          lv_obj_set_pos(id(sn_head), 400, 400);
{item_hides()}
  - id: sn_start
    then:
      - lambda: |-
          id(g_sn_state) = 1; id(g_sn_score) = 0; id(g_sn_dead) = false;
          id(g_sn_ang) = -1.5708f; id(g_sn_grow) = 0;            // heading up
          id(g_sn_len) = {START_LEN}; id(g_sn_head) = {START_LEN - 1};
          for (int i = 0; i < {POOL}; i++) {{ id(g_sn_tx)[i] = 0.0f; id(g_sn_ty)[i] = 0.0f; }}
          for (int k = 0; k < {START_LEN}; k++) {{ id(g_sn_tx)[k] = 0.0f; id(g_sn_ty)[k] = ({START_LEN - 1} - k) * {SEG_DIST}f; }}
          id(g_sn_hx) = 0.0f; id(g_sn_hy) = 0.0f;
          for (int s = 0; s < {NFSLOT}; s++) id(g_sn_fon)[s] = false;
          for (int s = 0; s < {NSKULL}; s++) {{ id(g_sn_skon)[s] = false; id(g_sn_skage)[s] = 0; }}
          id(g_sn_fclk) = 0; id(g_sn_skclk) = 0;
          id(g_sn_newfruit) = -1; id(g_sn_newskull) = -1; id(g_sn_add) = -1; id(g_sn_del) = -1;
          id(g_knob_capture) = true; id(g_knob_delta) = 0;
          float a = (esp_random() % 62832) / 10000.0f; float rad = 60.0f + (esp_random() % 80);
          id(g_sn_fx)[0] = cosf(a)*rad; id(g_sn_fy)[0] = sinf(a)*rad;
          id(g_sn_fi)[0] = esp_random() % {NFRUIT}; id(g_sn_fon)[0] = true;
      - script.execute: sn_fspr0
      - script.execute: sn_screen
      - script.execute: sn_drawfull
      - script.execute: sn_hud
  - id: sn_over
    then:
      - lambda: |-
          id(g_sn_state) = 2;
          int s = id(g_sn_score);
          if (s > id(g_sn_best)) id(g_sn_best) = s;
          for (int i = 0; i < 10; i++) {{
            if (s > id(g_sn_top)[i]) {{
              for (int j = 9; j > i; j--) id(g_sn_top)[j] = id(g_sn_top)[j-1];
              id(g_sn_top)[i] = s;
              break;
            }}
          }}
      - script.execute: sn_screen
  # screen state + the single knob-capture authority (captured only in play + game over)
  - id: sn_screen
    then:
      - lambda: 'id(g_knob_capture) = (id(g_sn_state) == 1 || id(g_sn_state) == 2);'
      - lvgl.widget.hide: sn_ring
      - script.execute: sn_clear
      - lvgl.widget.hide: lbl_sn_score
      - lvgl.widget.hide: sn_logo
      - lvgl.widget.hide: btn_sn_start
      - lvgl.widget.hide: btn_sn_howto
      - lvgl.widget.hide: btn_sn_scores
      - lvgl.widget.hide: lbl_sn_over
      - lvgl.widget.hide: lbl_sn_rec
      - lvgl.widget.hide: btn_sn_replay
      - lvgl.widget.hide: btn_sn_exit
      - lvgl.widget.hide: lbl_sn_howto_t
      - lvgl.widget.hide: sn_b1
      - lvgl.widget.hide: sn_b2
      - lvgl.widget.hide: sn_b3
      - lvgl.widget.hide: sn_b4
      - lvgl.widget.hide: lbl_sn_howto1
      - lvgl.widget.hide: lbl_sn_howto2
      - lvgl.widget.hide: lbl_sn_howto3
      - lvgl.widget.hide: lbl_sn_howto4
      - lvgl.widget.hide: lbl_sn_scores_t
      - lvgl.widget.hide: lbl_sn_scores1
      - lvgl.widget.hide: lbl_sn_scores2
      - lvgl.widget.hide: btn_sn_back
      - if:   # MENU
          condition: {{ lambda: 'return id(g_sn_state) == 0;' }}
          then:
            - lvgl.widget.show: sn_logo
            - lvgl.widget.show: btn_sn_start
            - lvgl.widget.show: btn_sn_howto
            - lvgl.widget.show: btn_sn_scores
      - if:   # PLAY
          condition: {{ lambda: 'return id(g_sn_state) == 1;' }}
          then:
            - lvgl.widget.show: sn_ring
            - lvgl.widget.show: lbl_sn_score
            - script.execute: sn_drawfull
      - if:   # GAME OVER
          condition: {{ lambda: 'return id(g_sn_state) == 2;' }}
          then:
            - lvgl.widget.show: sn_logo
            - lvgl.widget.show: lbl_sn_over
            - lvgl.widget.show: lbl_sn_rec
            - lvgl.widget.show: btn_sn_replay
            - lvgl.widget.show: btn_sn_exit
            - lvgl.label.update: {{ id: lbl_sn_over, text: !lambda 'char b[24]; snprintf(b,sizeof(b),"Score: %d", id(g_sn_score)); return std::string(b);' }}
            - lvgl.label.update: {{ id: lbl_sn_rec,  text: !lambda 'char b[24]; snprintf(b,sizeof(b),"Best: %d", id(g_sn_best)); return std::string(b);' }}
      - if:   # HOW TO PLAY
          condition: {{ lambda: 'return id(g_sn_state) == 3;' }}
          then:
            - lvgl.widget.show: lbl_sn_howto_t
            - lvgl.widget.show: sn_b1
            - lvgl.widget.show: sn_b2
            - lvgl.widget.show: sn_b3
            - lvgl.widget.show: sn_b4
            - lvgl.widget.show: lbl_sn_howto1
            - lvgl.widget.show: lbl_sn_howto2
            - lvgl.widget.show: lbl_sn_howto3
            - lvgl.widget.show: lbl_sn_howto4
            - lvgl.widget.show: btn_sn_back
      - if:   # SCORES (top 10)
          condition: {{ lambda: 'return id(g_sn_state) == 4;' }}
          then:
            - lvgl.widget.show: lbl_sn_scores_t
            - lvgl.widget.show: lbl_sn_scores1
            - lvgl.widget.show: lbl_sn_scores2
            - lvgl.widget.show: btn_sn_back
            - lvgl.label.update:
                id: lbl_sn_scores1
                text: !lambda |-
                  std::string s; char b[24];
                  for (int i = 0; i < 5; i++) {{ if(i) s += "\\n"; if(id(g_sn_top)[i]>0){{ snprintf(b,sizeof(b),"%d.  %d",i+1,id(g_sn_top)[i]); }} else {{ snprintf(b,sizeof(b),"%d.  -",i+1); }} s += b; }}
                  return s;
            - lvgl.label.update:
                id: lbl_sn_scores2
                text: !lambda |-
                  std::string s; char b[24];
                  for (int i = 5; i < 10; i++) {{ if(i>5) s += "\\n"; if(id(g_sn_top)[i]>0){{ snprintf(b,sizeof(b),"%d.  %d",i+1,id(g_sn_top)[i]); }} else {{ snprintf(b,sizeof(b),"%d.  -",i+1); }} s += b; }}
                  return s;

interval:
  - interval: 250ms
    then:
      - if:
          condition: {{ lambda: 'return id(g_sn_reset) || id(g_factory_reset);' }}
          then:
            - lambda: 'for (int i = 0; i < 10; i++) id(g_sn_top)[i] = 0; id(g_sn_best) = 0; id(g_sn_reset) = false;'
  - interval: 50ms
    then:
      - if:
          condition: {{ lambda: 'return id(g_nav_req) && id(g_base)==9;' }}
          then:
            - lambda: 'id(g_nav_req) = false; id(g_sn_state) = 0; id(g_knob_delta) = 0;'
            - if: {{ condition: {{ lambda: 'return id(g_nav_anim)==0;' }}, then: [lvgl.page.show: {{ id: page_snake, animation: move_left,   time: 250ms }}] }}
            - if: {{ condition: {{ lambda: 'return id(g_nav_anim)==1;' }}, then: [lvgl.page.show: {{ id: page_snake, animation: move_right,  time: 250ms }}] }}
            - if: {{ condition: {{ lambda: 'return id(g_nav_anim)==2;' }}, then: [lvgl.page.show: {{ id: page_snake, animation: move_top,    time: 250ms }}] }}
            - if: {{ condition: {{ lambda: 'return id(g_nav_anim)==3;' }}, then: [lvgl.page.show: {{ id: page_snake, animation: move_bottom, time: 250ms }}] }}
            - script.execute: sn_screen
  # Game tick: steer + glide head; lay/drop one trail dot when the head advanced SEG_DIST.
  # All body/head positioning is done IN this lambda (lv_obj_set_pos) to keep the action chain shallow.
  - interval: 50ms
    then:
      - if:
          condition: {{ lambda: 'return id(g_base) == 9 && id(g_sn_state) == 1;' }}
          then:
            - lambda: |-
                id(g_sn_add) = -1; id(g_sn_del) = -1; id(g_sn_newfruit) = -1; id(g_sn_newskull) = -1;
                int kd = id(g_knob_delta); id(g_knob_delta) = 0;
                id(g_sn_ang) += kd * {TURN}f;
                float spd = {SPEED0}f + id(g_sn_score) / 400.0f; if (spd > 5.5f) spd = 5.5f;
                float hx = id(g_sn_hx) + cosf(id(g_sn_ang)) * spd;
                float hy = id(g_sn_hy) + sinf(id(g_sn_ang)) * spd;
                if (hx*hx + hy*hy > {R}f * {R}f) {{ id(g_sn_dead) = true; }}   // hit the ring
                else {{
                  id(g_sn_hx) = hx; id(g_sn_hy) = hy;
                  int len = id(g_sn_len), head = id(g_sn_head);
                  for (int i = {SELF_SKIP}; i < len; i++) {{
                    int sl = (head - i + {M}) % {POOL};
                    float dx = hx - id(g_sn_tx)[sl], dy = hy - id(g_sn_ty)[sl];
                    if (dx*dx + dy*dy < {SELF_DIST}f * {SELF_DIST}f) {{ id(g_sn_dead) = true; break; }}
                  }}
                  for (int s = 0; s < {NSKULL}; s++) if (id(g_sn_skon)[s]) {{
                    float dx = hx - id(g_sn_skx)[s], dy = hy - id(g_sn_sky)[s];
                    if (dx*dx + dy*dy < {SKHIT}f * {SKHIT}f) {{ id(g_sn_dead) = true; }}
                  }}
                  for (int s = 0; s < {NFSLOT} && !id(g_sn_dead); s++) if (id(g_sn_fon)[s]) {{
                    float dx = hx - id(g_sn_fx)[s], dy = hy - id(g_sn_fy)[s];
                    if (dx*dx + dy*dy < {EAT}f * {EAT}f) {{ id(g_sn_fon)[s] = false; id(g_sn_score) += 10; id(g_sn_grow) += {GROW}; }}
                  }}
                  if (!id(g_sn_dead)) {{
                    float dx = hx - id(g_sn_tx)[head], dy = hy - id(g_sn_ty)[head];
                    if (dx*dx + dy*dy >= {SEG_DIST}f * {SEG_DIST}f) {{
                      int nh = (head + 1) % {POOL};
                      id(g_sn_tx)[nh] = hx; id(g_sn_ty)[nh] = hy;
                      id(g_sn_head) = nh; id(g_sn_add) = nh;
                      if (id(g_sn_grow) > 0 && id(g_sn_len) < {POOL}) {{ id(g_sn_grow)--; id(g_sn_len)++; id(g_sn_del) = -1; }}
                      else {{ if (id(g_sn_grow) > 0) id(g_sn_grow)--; id(g_sn_del) = (head - id(g_sn_len) + 1 + {M}) % {POOL}; }}
                    }}
                  }}
                }}
                if (!id(g_sn_dead)) {{
                  int fc = 0; for (int s = 0; s < {NFSLOT}; s++) if (id(g_sn_fon)[s]) fc++;
                  id(g_sn_fclk)++;
                  int wait = (fc <= 1) ? {FRUIT_WAIT // 2} : {FRUIT_WAIT};
                  if (fc < {NFSLOT} && id(g_sn_fclk) >= wait) {{
                    id(g_sn_fclk) = 0;
                    int sl = -1; for (int s = 0; s < {NFSLOT}; s++) if (!id(g_sn_fon)[s]) {{ sl = s; break; }}
                    if (sl >= 0) {{
                      float a = (esp_random() % 62832) / 10000.0f; float rad = 25.0f + (esp_random() % 140);
                      id(g_sn_fx)[sl] = cosf(a)*rad; id(g_sn_fy)[sl] = sinf(a)*rad;
                      id(g_sn_fi)[sl] = esp_random() % {NFRUIT}; id(g_sn_fon)[sl] = true; id(g_sn_newfruit) = sl;
                    }}
                  }}
                  int sc = 0; for (int s = 0; s < {NSKULL}; s++) if (id(g_sn_skon)[s]) sc++;
                  id(g_sn_skclk)++;
                  if (sc < {NSKULL} && id(g_sn_skclk) >= {SKULL_WAIT}) {{
                    id(g_sn_skclk) = 0;
                    int sl = -1; for (int s = 0; s < {NSKULL}; s++) if (!id(g_sn_skon)[s]) {{ sl = s; break; }}
                    if (sl >= 0) {{
                      float a = (esp_random() % 62832) / 10000.0f; float rad = 30.0f + (esp_random() % 130);
                      id(g_sn_skx)[sl] = cosf(a)*rad; id(g_sn_sky)[sl] = sinf(a)*rad;
                      id(g_sn_skon)[sl] = true; id(g_sn_skage)[sl] = 0; id(g_sn_newskull) = sl;
                    }}
                  }}
                  for (int s = 0; s < {NSKULL}; s++) if (id(g_sn_skon)[s]) {{ id(g_sn_skage)[s]++; if (id(g_sn_skage)[s] >= {SKULL_LIFE}) id(g_sn_skon)[s] = false; }}
                  // render (constant cost): head every tick + the one added/dropped dot
                  lv_obj_set_pos(id(sn_head), 180 + (int) lroundf(id(g_sn_hx)) - {HALF}, 180 + (int) lroundf(id(g_sn_hy)) - {HALF});
                  if (id(g_sn_add) >= 0 || id(g_sn_del) >= 0) {{
                    {SEGINIT}
                    if (id(g_sn_add) >= 0) lv_obj_set_pos(SS[id(g_sn_add)], 180 + (int) lroundf(id(g_sn_tx)[id(g_sn_add)]) - {HALF}, 180 + (int) lroundf(id(g_sn_ty)[id(g_sn_add)]) - {HALF});
                    if (id(g_sn_del) >= 0) lv_obj_set_pos(SS[id(g_sn_del)], 400, 400);
                  }}
                }}
            - if:
                condition: {{ lambda: 'return id(g_sn_dead);' }}
                then:
                  - script.execute: sn_over
                else:
                  - if:
                      condition: {{ lambda: 'return id(g_sn_newfruit) >= 0;' }}
                      then:
{fspr_dispatch()}
                  - if:
                      condition: {{ lambda: 'return id(g_sn_newskull) >= 0;' }}
                      then:
{skull_dispatch()}
                  - script.execute: sn_items
                  - script.execute: sn_hud

image:
  - id: img_sn_logo
    file: "{BASE}snake-logo.png"
    type: RGB565
{fruit_images()}
  - id: img_sn_skull
    file: "{BASE}skull.png"
    type: RGB565
    transparency: alpha_channel

lvgl:
  pages:
    - id: page_snake
      bg_color: {PAGE_BG}
      scrollbar_mode: "off"
      scrollable: false
      widgets:
        - obj: {{ id: sn_ring, align: CENTER, x: 0, y: 0, width: {RING_D}, height: {RING_D}, radius: {RING_D // 2}, bg_opa: TRANSP, border_width: 4, border_color: {RING}, hidden: true }}
{fruit_widgets()}
{skull_widgets()}
{body_widgets()}
        - obj: {{ id: sn_head, x: 400, y: 400, width: {SEG}, height: {SEG}, radius: {SEGR}, border_width: 0, bg_color: {HEAD}, bg_opa: COVER }}
        - label: {{ id: lbl_sn_score, align: CENTER, x: 0, y: -150, text: "0", text_font: font_med, text_color: {HUD}, hidden: true }}
        - image: {{ id: sn_logo, align: CENTER, x: 0, y: 0, src: img_sn_logo, hidden: true }}
        - button:
            id: btn_sn_start
            align: CENTER
            y: 4
            width: 150
            height: 44
            radius: 22
            bg_color: {ACCENT}
            bg_opa: COVER
            border_width: 0
            on_click: [ script.execute: sn_start ]
            widgets:
              - label: {{ align: CENTER, text: "Start", text_font: font_med, text_color: {ACCENT_TXT} }}
        - button:
            id: btn_sn_howto
            align: CENTER
            y: 54
            width: 150
            height: 44
            radius: 22
            bg_color: {BTN2}
            bg_opa: COVER
            border_width: 0
            on_click: [ lambda: 'id(g_sn_state) = 3;', script.execute: sn_screen ]
            widgets:
              - label: {{ align: CENTER, text: "How to play?", text_font: font_med, text_color: {BTN2_TXT} }}
        - button:
            id: btn_sn_scores
            align: CENTER
            y: 104
            width: 150
            height: 44
            radius: 22
            bg_color: {BTN2}
            bg_opa: COVER
            border_width: 0
            on_click: [ lambda: 'id(g_sn_state) = 4;', script.execute: sn_screen ]
            widgets:
              - label: {{ align: CENTER, text: "Scores", text_font: font_med, text_color: {BTN2_TXT} }}
        - label: {{ id: lbl_sn_over, align: CENTER, x: 0, y: -10, text_align: CENTER, text: "", text_font: font_sel, text_color: {WORDMARK}, hidden: true }}
        - label: {{ id: lbl_sn_rec, align: CENTER, x: 0, y: 22, text_align: CENTER, text: "", text_font: font_artist, text_color: {WORDMARK}, hidden: true }}
        - button:
            id: btn_sn_replay
            align: CENTER
            x: -66
            y: 62
            width: 112
            height: 48
            radius: 24
            bg_color: {ACCENT}
            bg_opa: COVER
            border_width: 0
            hidden: true
            on_click: [ script.execute: sn_start ]
            widgets:
              - label: {{ align: CENTER, text: "Play", text_font: font_med, text_color: {ACCENT_TXT} }}
        - button:
            id: btn_sn_exit
            align: CENTER
            x: 66
            y: 62
            width: 112
            height: 48
            radius: 24
            bg_color: {GRAY}
            bg_opa: COVER
            border_width: 0
            hidden: true
            on_click: [ lambda: 'id(g_sn_state) = 0;', script.execute: sn_screen ]
            widgets:
              - label: {{ align: CENTER, text: "Exit", text_font: font_med, text_color: 0xFFFFFF }}
        - label: {{ id: lbl_sn_howto_t, align: CENTER, y: -104, text: "HOW TO PLAY?", text_font: font_sel, text_color: {ACCENT}, hidden: true }}
        - obj: {{ id: sn_b1, align: CENTER, x: -96, y: -52, width: 24, height: 24, radius: 12, bg_color: {BADGE}, bg_opa: COVER, border_width: 0, pad_all: 0, hidden: true, widgets: [ label: {{ align: CENTER, text: "1", text_font: font_artist, text_color: 0xFFFFFF }} ] }}
        - obj: {{ id: sn_b2, align: CENTER, x: -96, y: -16, width: 24, height: 24, radius: 12, bg_color: {BADGE}, bg_opa: COVER, border_width: 0, pad_all: 0, hidden: true, widgets: [ label: {{ align: CENTER, text: "2", text_font: font_artist, text_color: 0xFFFFFF }} ] }}
        - obj: {{ id: sn_b3, align: CENTER, x: -96, y: 20, width: 24, height: 24, radius: 12, bg_color: {BADGE}, bg_opa: COVER, border_width: 0, pad_all: 0, hidden: true, widgets: [ label: {{ align: CENTER, text: "3", text_font: font_artist, text_color: 0xFFFFFF }} ] }}
        - obj: {{ id: sn_b4, align: CENTER, x: -96, y: 56, width: 24, height: 24, radius: 12, bg_color: 0xE05A4A, bg_opa: COVER, border_width: 0, pad_all: 0, hidden: true, widgets: [ label: {{ align: CENTER, text: "!", text_font: font_artist, text_color: 0xFFFFFF }} ] }}
        - label: {{ id: lbl_sn_howto1, align_to: {{ id: sn_b1, align: OUT_RIGHT_MID, x: 8 }}, text: "Turn knob to steer", text_font: font_med, text_color: {TXT}, hidden: true }}
        - label: {{ id: lbl_sn_howto2, align_to: {{ id: sn_b2, align: OUT_RIGHT_MID, x: 8 }}, text: "Eat fruit to grow", text_font: font_med, text_color: {TXT}, hidden: true }}
        - label: {{ id: lbl_sn_howto3, align_to: {{ id: sn_b3, align: OUT_RIGHT_MID, x: 8 }}, text: "Avoid the ring & tail", text_font: font_med, text_color: {TXT}, hidden: true }}
        - label: {{ id: lbl_sn_howto4, align_to: {{ id: sn_b4, align: OUT_RIGHT_MID, x: 8 }}, text: "Skulls kill - avoid!", text_font: font_med, text_color: {TXT}, hidden: true }}
        - label: {{ id: lbl_sn_scores_t, align: CENTER, y: -116, text: "SCORES", text_font: font_sel, text_color: {ACCENT}, hidden: true }}
        - label: {{ id: lbl_sn_scores1, align: CENTER, x: -52, y: 0, text: "", text_align: LEFT, text_font: font_artist, text_color: {TXT}, hidden: true }}
        - label: {{ id: lbl_sn_scores2, align: CENTER, x: 56, y: 0, text: "", text_align: LEFT, text_font: font_artist, text_color: {TXT}, hidden: true }}
        - button:
            id: btn_sn_back
            align: CENTER
            y: 120
            width: 130
            height: 42
            radius: 21
            bg_color: {GRAY}
            bg_opa: COVER
            border_width: 0
            hidden: true
            on_click: [ lambda: 'id(g_sn_state) = 0;', script.execute: sn_screen ]
            widgets:
              - label: {{ align: CENTER, text: "Back", text_font: font_med, text_color: 0xFFFFFF }}
"""

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "..", "base", "screens", "snake.yaml")
out = os.path.normpath(out)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(YAML)
print("wrote", out, "(", len(YAML), "bytes )")

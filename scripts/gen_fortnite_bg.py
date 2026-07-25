#!/usr/bin/env python3
# Builds the background of the "Fortnite" watchface: assets/sprites/fortnite/bg.png
#   python scripts/gen_fortnite_bg.py <your-wallpaper.jpg>
#
# Takes any landscape wallpaper, crops the largest centred square (so as much of the
# scene as possible survives the round 360x360 screen), dims it a touch, and bakes in
# the static parts of the face: a soft scrim behind the clock, a second one under the
# HUD bars, and the purple storm rim. Baking them means the firmware draws ONE image
# instead of a stack of widgets - cheaper to redraw and nothing to keep in sync.
#
# Tweak DIM if the face is too bright/dark on the real panel: lower = darker.
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

S = 360            # panel size
DIM = 0.85         # 1.0 = untouched wallpaper
RIM = (196, 107, 255)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "sprites", "fortnite", "bg.png")


def main(src):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    side = min(W, H)                                   # biggest centred square
    x0, y0 = (W - side) / 2, (H - side) / 2
    im = im.crop((int(x0), int(y0), int(x0 + side), int(y0 + side))).resize((S, S), Image.LANCZOS)
    im = ImageEnhance.Brightness(im).enhance(DIM)

    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))       # scrims, blurred so they read as haze
    od = ImageDraw.Draw(ov)
    od.rectangle([0, 118, S, 205], fill=(8, 6, 30, 105))    # behind the clock
    od.rectangle([0, 236, S, S], fill=(6, 8, 26, 130))      # under the HUD bars
    ov = ov.filter(ImageFilter.GaussianBlur(22))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")

    ImageDraw.Draw(im).ellipse([2, 2, S - 3, S - 3], outline=RIM, width=3)   # storm rim

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/gen_fortnite_bg.py <wallpaper.jpg>")
    main(sys.argv[1])

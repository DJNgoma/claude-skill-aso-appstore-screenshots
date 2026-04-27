#!/usr/bin/env python3
"""
ASO Screenshot Enhancer — local-only Pillow polish on a compose.py scaffold.

Adds the "breakout" pop-out effect by extracting a region of the inner phone
screenshot, scaling it up, applying a soft drop shadow, and pasting it on top
of the scaffold so it overlaps both bezel edges.

No external services — pure Pillow.

Coordinates are given in the *original* simulator screenshot (the input you
fed to compose.py), not the scaffold canvas. The script handles the math to
translate them onto the canvas.

Example:
    python3 enhance.py \
        --scaffold scaffolds/01-today/scaffold-en-US.png \
        --simulator metadata/screenshots/en-US/01-today.png \
        --region 60,840,1085,990 \
        --scale 1.18 \
        --output scaffolds/01-today/v1-en-US.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageFilter

# Must match compose.py
CANVAS_W = 1290
CANVAS_H = 2796
DEVICE_W = 1030
BEZEL = 15
SCREEN_W = DEVICE_W - 2 * BEZEL          # 1000
DEVICE_X = (CANVAS_W - DEVICE_W) // 2    # 130
SCREEN_X = DEVICE_X + BEZEL              # 145
DEVICE_Y = 720                           # matches compose.py


def parse_region(s: str) -> tuple[int, int, int, int]:
    parts = [int(p.strip()) for p in s.split(",")]
    if len(parts) != 4:
        raise ValueError(f"region must be x,y,w,h — got {s!r}")
    return tuple(parts)  # type: ignore


def add_drop_shadow(card: Image.Image, blur: int = 28, offset_y: int = 18,
                    opacity: int = 130) -> Image.Image:
    """Return a new RGBA image: card with a soft drop shadow underneath."""
    pad = blur * 2 + offset_y
    canvas = Image.new("RGBA", (card.width + pad * 2, card.height + pad * 2),
                       (0, 0, 0, 0))

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    # Draw a black silhouette of the card's alpha channel into the shadow layer.
    silhouette = Image.new("RGBA", card.size, (0, 0, 0, opacity))
    silhouette.putalpha(card.split()[-1].point(lambda a: int(a * opacity / 255)))
    shadow_layer.paste(silhouette, (pad, pad + offset_y), silhouette)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))

    canvas = Image.alpha_composite(canvas, shadow_layer)
    canvas.paste(card, (pad, pad), card)
    return canvas


def round_corners(img: Image.Image, radius: int = 28) -> Image.Image:
    """Return a copy with rounded corners on the alpha channel."""
    from PIL import ImageDraw
    rounded = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(rounded)
    draw.rounded_rectangle((0, 0, img.width, img.height), radius=radius, fill=255)
    out = img.copy()
    if out.mode != "RGBA":
        out = out.convert("RGBA")
    alpha = out.split()[-1]
    new_alpha = Image.eval(alpha, lambda v: v).point(lambda v: v)
    # Combine new alpha with rounded mask
    new_alpha = Image.merge("RGBA", (new_alpha, new_alpha, new_alpha, rounded)).split()[-1]
    out.putalpha(new_alpha)
    return out


def enhance(scaffold_path: Path, simulator_path: Path, region: tuple[int, int, int, int],
            scale: float, output_path: Path, breakout_y_canvas: int | None = None) -> None:
    scaffold = Image.open(scaffold_path).convert("RGBA")
    if scaffold.size != (CANVAS_W, CANVAS_H):
        raise ValueError(
            f"scaffold must be {CANVAS_W}x{CANVAS_H}, got {scaffold.size}")

    sim = Image.open(simulator_path).convert("RGBA")
    sim_w, sim_h = sim.size

    rx, ry, rw, rh = region
    # Clamp the region so it stays inside the simulator image.
    rx = max(0, min(rx, sim_w - 1))
    ry = max(0, min(ry, sim_h - 1))
    rw = max(1, min(rw, sim_w - rx))
    rh = max(1, min(rh, sim_h - ry))

    card = sim.crop((rx, ry, rx + rw, ry + rh))

    # The card's vertical position on the device screen — used to anchor the
    # breakout if the caller didn't override.
    if breakout_y_canvas is None:
        # Map the card's y in simulator coords to the device-screen y on canvas.
        # Approximation: assume the simulator image fills the device screen.
        screen_y_top_canvas = DEVICE_Y + BEZEL  # rough; the frame template
        # adds curve at the top, so we leave a small margin.
        breakout_y_canvas = screen_y_top_canvas + int(ry * (SCREEN_W / sim_w))

    # Scale the card UP. We deliberately overshoot the device width so the
    # card extends beyond both bezel edges.
    target_w = int(SCREEN_W * scale)
    new_w = target_w
    new_h = int(rh * (new_w / rw))
    card_big = card.resize((new_w, new_h), Image.LANCZOS)
    card_big = round_corners(card_big, radius=int(28 * (new_w / rw)))

    shadowed = add_drop_shadow(card_big, blur=32, offset_y=22, opacity=140)

    # Centre the breakout horizontally on the canvas, anchored at the
    # original card's vertical position on the device.
    paste_x = (CANVAS_W - shadowed.width) // 2
    paste_y = breakout_y_canvas - (shadowed.height - card_big.height) // 2

    # Don't let the breakout collide with the headline (top ~25% of the canvas).
    min_y = 700  # below headline area; tunable
    if paste_y < min_y:
        paste_y = min_y
    # Don't let it run below the canvas either.
    if paste_y + shadowed.height > CANVAS_H - 60:
        paste_y = CANVAS_H - 60 - shadowed.height

    out = scaffold.copy()
    out.alpha_composite(shadowed, (paste_x, paste_y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.convert("RGB").save(output_path, "PNG")
    print(f"✓ {output_path} ({CANVAS_W}×{CANVAS_H})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scaffold", required=True, type=Path,
                    help="Path to compose.py scaffold (1290x2796 PNG).")
    ap.add_argument("--simulator", required=True, type=Path,
                    help="Path to the original simulator screenshot used to "
                         "build the scaffold.")
    ap.add_argument("--region", required=True,
                    help="Breakout region in simulator coords: 'x,y,w,h'.")
    ap.add_argument("--scale", type=float, default=1.18,
                    help="Breakout width as a multiplier of device screen "
                         "width (default 1.18 — extends ~9%% past each bezel).")
    ap.add_argument("--output", required=True, type=Path,
                    help="Output PNG path.")
    ap.add_argument("--breakout-y", type=int, default=None,
                    help="Optional override: vertical position of the "
                         "breakout on the canvas (in pixels).")
    args = ap.parse_args()

    enhance(
        scaffold_path=args.scaffold,
        simulator_path=args.simulator,
        region=parse_region(args.region),
        scale=args.scale,
        output_path=args.output,
        breakout_y_canvas=args.breakout_y,
    )


if __name__ == "__main__":
    main()

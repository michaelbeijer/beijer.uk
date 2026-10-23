#!/usr/bin/env python3
"""Generate the Beijer.uk social card (Open Graph preview image).

Outputs ``src/assets/social-card.png`` (1200x630) — the default ``og:image``
that ``src/components/BaseHead.astro`` uses for any page that doesn't set its
own ``image`` prop.

Minimalist, in the site's ink on its cream ground. Everything is centred and
sized to fill the middle 630 x 630 square: WhatsApp's small preview is that
square shrunk to about 115 pixels, so a left-aligned card lost the start of
the name and anything small turned to mush. Hence the name on two lines, as
large as the square allows, and one short line under it. Edit the CONTENT
constants below and re-run:

    python scripts/make-social-card.py

Requires Pillow:  pip install pillow
Renders in Arial; falls back to DejaVu Sans (or Arial on macOS) if Arial isn't
found, so it works cross-platform.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Content (edit me) ─────────────────────────────────────────────
NAME    = ["Michael", "Beijer"]  # one line each
ROLE    = "Dutch patent translator"

# ── Style / layout ────────────────────────────────────────────────
SS = 2                       # supersample factor → crisp text after downscale
W, H = 1200 * SS, 630 * SS
SQUARE = 630 * SS            # the middle square a small preview keeps
FIT = 540 * SS               # the widest line may be this wide
INK    = (20, 19, 15)        # global.css --text
GREY   = (74, 74, 74)
GROUND = (240, 238, 230)     # global.css --bg

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "src" / "assets" / "social-card.png"


def _font(bold: bool, pt: int) -> ImageFont.FreeTypeFont:
    names = (
        ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"] if bold
        else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"]
    )
    dirs = [
        r"C:\Windows\Fonts", "/c/Windows/Fonts",
        "/Library/Fonts", "/System/Library/Fonts/Supplemental",
        "/usr/share/fonts/truetype/dejavu",
    ]
    for d in dirs:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), pt * SS)
    raise SystemExit("No sans-serif font found — install Arial or DejaVu Sans.")


def main() -> None:
    # The name as large as the widest of its lines allows.
    pt = 200
    while max(_font(True, pt).getlength(w) for w in NAME) > FIT:
        pt -= 2
    name_f = _font(True, pt)
    role_f = _font(False, 44)

    img = Image.new("RGB", (W, H), GROUND)
    d = ImageDraw.Draw(img)

    # Line boxes from the font's own ascent and descent, so both name lines
    # sit on the same rhythm whatever their letters.
    asc, desc = name_f.getmetrics()
    name_step = int((asc + desc) * 0.92)
    rule_gap, rule_h, role_gap = 22 * SS, 6 * SS, 40 * SS
    ra, rd = role_f.getmetrics()
    total = name_step * (len(NAME) - 1) + asc + desc + rule_gap + rule_h + role_gap + ra + rd
    y = (H - total) // 2

    cx = W // 2
    for i, w in enumerate(NAME):
        d.text((cx, y + i * name_step), w, font=name_f, fill=INK, anchor="ma")
    # below the last line's descenders (the j of Beijer), not its baseline
    y += name_step * (len(NAME) - 1) + asc + desc + rule_gap
    # Short underline accent — echoes the site's nav underline.
    d.rectangle([cx - 66 * SS, y, cx + 66 * SS, y + rule_h], fill=INK)
    y += rule_h + role_gap
    d.text((cx, y), ROLE, font=role_f, fill=GREY, anchor="ma")

    # Refuse a card whose words leave the middle square.
    box = d.textbbox((cx, 0), ROLE, font=role_f, anchor="ma")
    widest = max(max(name_f.getlength(w) for w in NAME), box[2] - box[0])
    if widest > SQUARE or y + ra + rd > H:
        raise SystemExit("The card's text no longer fits the middle square.")

    img = img.resize((1200, 630), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

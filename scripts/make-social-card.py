#!/usr/bin/env python3
"""Generate the Beijer.uk social card (Open Graph preview image).

Outputs ``src/assets/social-card.png`` (1200x630) — the default ``og:image``
that ``src/components/BaseHead.astro`` uses for any page that doesn't set its
own ``image`` prop.

Minimalist black-on-white to match the site. Edit the CONTENT constants below
and re-run:

    python scripts/make-social-card.py

Requires Pillow:  pip install pillow
Renders in Arial; falls back to DejaVu Sans (or Arial on macOS) if Arial isn't
found, so it works cross-platform.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Content (edit me) ─────────────────────────────────────────────
NAME    = "Michael Beijer"
ROLE    = "Dutch patent translator"
TAGLINE = "Patents and technical documentation · Hastings, UK"
DOMAIN  = "Beijer.uk"

# ── Style / layout ────────────────────────────────────────────────
SS = 2                       # supersample factor → crisp text after downscale
W, H = 1200 * SS, 630 * SS
MARGIN = 96 * SS
BLACK  = (17, 17, 17)
GREY   = (74, 74, 74)
GREY2  = (122, 122, 122)
WHITE  = (255, 255, 255)

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
    name_f = _font(True, 98)
    role_f = _font(False, 46)
    tag_f = _font(False, 29)
    domain_f = _font(True, 30)

    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    x, y = MARGIN, 168 * SS
    d.text((x, y), NAME, font=name_f, fill=BLACK)
    y = d.textbbox((x, y), NAME, font=name_f)[3] + 26 * SS

    # Short underline accent — echoes the site's nav underline.
    d.rectangle([x, y, x + 132 * SS, y + 6 * SS], fill=BLACK)
    y += 6 * SS + 40 * SS

    d.text((x, y), ROLE, font=role_f, fill=GREY)
    y = d.textbbox((x, y), ROLE, font=role_f)[3] + 20 * SS

    d.text((x, y), TAGLINE, font=tag_f, fill=GREY2)
    d.text((x, H - MARGIN - 32 * SS), DOMAIN, font=domain_f, fill=BLACK)

    img = img.resize((1200, 630), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

"""Compose FactorFinance demo screenshots into an animated GIF.

Usage:
    python -m scripts.make_gif
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT_GIF = ROOT / "docs" / "factorio.gif"

FRAMES = [
    ("01-home-en.png",              2800),
    ("07-dashboard-en.png",         2400),
    ("08-marketplace-en.png",       3200),
    ("09-marketplace-detail-en.png", 3200),
    ("10-portfolio-en.png",         3200),
    ("11-home-uz.png",              2800),
    ("12-marketplace-uz.png",       2800),
    ("13-home-ru.png",              2800),
    ("14-marketplace-ru.png",       2800),
]

TARGET_W = 1200
TARGET_H = 820
BG = (247, 246, 241)  # parchment (#F7F6F1)


def load_frame(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    ratio = TARGET_W / img.width
    img = img.resize((TARGET_W, int(img.height * ratio)), Image.LANCZOS)
    if img.height > TARGET_H:
        img = img.crop((0, 0, TARGET_W, TARGET_H))
    else:
        canvas = Image.new("RGB", (TARGET_W, TARGET_H), BG)
        canvas.paste(img, (0, 0))
        img = canvas
    return img


def main() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []
    for fname, dur in FRAMES:
        p = SHOTS / fname
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        frames.append(load_frame(p))
        durations.append(dur)
        print(f"  added {fname}  ({dur} ms)")

    if not frames:
        raise SystemExit("No frames found — run scripts/capture_screenshots.py first.")

    OUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=durations,
        loop=0,
        disposal=2,
    )
    print(f"\nWrote {OUT_GIF}  ({OUT_GIF.stat().st_size / 1024:.1f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()

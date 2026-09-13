# -*- coding: utf-8 -*-
"""
Turn the supplied logo artwork into the asset set the app actually uses.

WHY THIS EXISTS AS A SCRIPT

The logo is supplied as flat artwork on an opaque background: no alpha, so
dropped straight into the app it would render as a pale rectangle on the warm
paper canvas. Earlier it arrived as a screenshot of the design, which was also
rotated about 1.4 degrees. Correcting either by hand in an image editor would
have produced files nobody could regenerate or check.

So this does it deterministically instead - measure, correct, un-composite,
cut, size - and a test in tests/test_brand.py rebuilds every output in memory
and compares it byte for byte with what is committed. Re-run it and you get
identical files; drop in a better source and everything regenerates.

    python scripts/prepare_logo.py

Two things here are less obvious than they look, and both are load-bearing:
`skew_degrees` has to be able to REFUSE a measurement, and `cut` erases the
tagline rather than cropping it. See the docstrings on each.

Outputs land in assets/brand/. Do not hand-edit them - edit this and re-run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "source" / "sahulat-logo-source.png"
OUT = ROOT / "assets" / "brand"

# RGB distance from the plate colour at which a pixel is treated as fully
# opaque / fully background. Everything between ramps linearly, which is what
# preserves the anti-aliased edges of the type instead of jagging them.
CORE, EDGE = 90.0, 12.0

# Faint pixels with no strong neighbour are plate residue, not artwork - the
# rotated photo leaves a sliver of its own border behind.
NOISE_ALPHA, NOISE_NEIGHBOUR = 20, 60

# A real text baseline fits a straight line to within a pixel or so. Anything
# looser is not a baseline, and the measured angle must not be acted on.
MAX_BASELINE_RESIDUAL = 2.5
MAX_SKEW = 8.0

# Below this the artwork is treated as straight. Rotating resamples every
# pixel, and a correction of a quarter of a degree is inside the noise of the
# measurement itself - it would trade real sharpness for an imagined fix.
MIN_SKEW = 0.35

# How far above the tagline to look when deciding whether ink in the
# symbol's columns is the bottom of the ribbon or a detached letter.
GAP_PROBE = 6


def _runs(present, minimum: int = 3):
    """Contiguous True runs in a 1-D mask, ignoring specks."""
    out, start = [], None
    for i, value in enumerate(present):
        if value and start is None:
            start = i
        if not value and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(present) - 1))
    return [r for r in out if r[1] - r[0] >= minimum]


# ---------------------------------------------------------------------------
# Measuring the source
# ---------------------------------------------------------------------------

def plate_colour(rgb: np.ndarray) -> np.ndarray:
    """The flat background the artwork was sitting on."""
    return np.median(rgb[rgb.mean(2) > 240], 0)


def skew_degrees(rgb: np.ndarray) -> float:
    """
    Rotation of the artwork, read off the baseline of its bottom text row.

    Evenly-set type has a straight baseline, so the bottom-most dark pixel in
    each column traces a line whose slope is the rotation. That is a far more
    reliable angle than anything derived from the image border, which in a
    screenshot is wherever the screen edge happened to be.

    THE TRAP: a curve traces a convincing slope too. Measured across the whole
    width, the bottom edge of the ribbon reads as -7.7 degrees on artwork that
    is perfectly straight - and acting on that would rotate a clean file into
    a crooked one. Two guards prevent it. The fit is taken only across the
    text block, never the symbol; and it is rejected unless the points really
    do lie on a line, which a curve cannot fake.
    """
    lum = rgb.mean(2)
    dark = lum < 200
    if not dark.any():
        return 0.0

    # Ignore the symbol: measure only where the type is. The widest gap in the
    # column profile separates the two.
    columns = _runs((dark.any(0)))
    text_from = columns[1][0] if len(columns) > 1 else 0
    region = dark[:, text_from:]

    rows = _runs(region.any(1))
    if not rows:
        return 0.0
    band_start, band_end = rows[-1]          # the bottom line of type

    xs, ys = [], []
    for x in range(region.shape[1]):
        column = np.where(region[band_start:band_end + 1, x])[0]
        if len(column):
            xs.append(x)
            ys.append(band_start + column.max())
    if len(xs) < 40:
        return 0.0

    xs, ys = np.array(xs, float), np.array(ys, float)

    # Descenders sit below the baseline - the p's in "Opportunities" alone push
    # a plain least-squares residual to 3px on artwork that is genuinely
    # straight. Fit, drop the worst third, refit: what is left is the baseline
    # proper. A curved edge stays badly fitted even after the trim, which is
    # what keeps the guard meaningful.
    slope, intercept = np.polyfit(xs, ys, 1)
    keep = np.abs(ys - (slope * xs + intercept)) <= np.percentile(
        np.abs(ys - (slope * xs + intercept)), 67)
    if keep.sum() < 20:
        return 0.0
    slope, intercept = np.polyfit(xs[keep], ys[keep], 1)
    residual = float(np.sqrt(np.mean((ys[keep] - (slope * xs[keep] + intercept)) ** 2)))

    # A baseline sits within a pixel of its own fit. A curve does not.
    if residual > MAX_BASELINE_RESIDUAL:
        return 0.0
    angle = float(np.degrees(np.arctan(slope)))
    if not MIN_SKEW <= abs(angle) <= MAX_SKEW:
        return 0.0
    return angle


# ---------------------------------------------------------------------------
# Lifting the artwork off its plate
# ---------------------------------------------------------------------------

def deskew(image: Image.Image, plate: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotate upright, filling new corners with the plate so it stays flat.

    At zero the image is returned untouched rather than rotated by nothing:
    a no-op rotation still resamples every pixel and softens artwork that was
    already straight.
    """
    if angle == 0.0:
        return np.asarray(image).astype(float)
    rotated = image.rotate(angle, resample=Image.BICUBIC, expand=True,
                           fillcolor=tuple(int(v) for v in plate))
    return np.asarray(rotated).astype(float)


def to_rgba(rgb: np.ndarray, plate: np.ndarray) -> np.ndarray:
    """
    Recover colour and coverage from a known flat background.

    Every pixel is plate and artwork mixed: P = a*F + (1-a)*B. B is known and
    a is estimated from how far P has travelled from it, which leaves F
    solvable. Doing it this way - rather than keying out the white - is what
    keeps the grey tagline opaque instead of half-transparent, and stops the
    green ribbon picking up a white rim.
    """
    distance = np.sqrt(((rgb - plate) ** 2).sum(2))
    alpha = np.clip((distance - EDGE) / (CORE - EDGE), 0.0, 1.0)
    safe = np.maximum(alpha, 1e-6)[..., None]
    foreground = np.clip((rgb - (1.0 - alpha)[..., None] * plate) / safe, 0, 255)
    return np.dstack([foreground, alpha * 255.0]).astype(np.uint8)


def drop_residue(rgba: np.ndarray) -> np.ndarray:
    """Zero faint pixels that have no strong neighbour."""
    alpha = rgba[..., 3].astype(int)
    padded = np.pad(alpha, 2, mode="constant")
    neighbourhood = np.zeros_like(alpha)
    for dy in range(5):
        for dx in range(5):
            neighbourhood = np.maximum(
                neighbourhood, padded[dy:dy + alpha.shape[0], dx:dx + alpha.shape[1]])
    residue = (alpha < NOISE_ALPHA) & (neighbourhood < NOISE_NEIGHBOUR)
    rgba = rgba.copy()
    rgba[..., 3][residue] = 0
    return rgba


# ---------------------------------------------------------------------------
# Cutting the variants
# ---------------------------------------------------------------------------

def bands(alpha: np.ndarray, axis: int, threshold: int = 40):
    """Contiguous runs of content along one axis."""
    return _runs((alpha > threshold).any(1 - axis))


def _ink_extent(alpha: np.ndarray, axis: int, floor: float = 0.01):
    """
    First and last index along `axis` that carries real artwork.

    Cropping to "any non-zero pixel" is too literal: the source is a photo, so
    a single faint pixel of its own border can sit hundreds of rows below the
    tagline and stretch the canvas to meet it. Measuring ink per band and
    discarding bands under 1% of the heaviest keeps that from happening while
    staying indifferent to where the artwork actually is.
    """
    ink = alpha.sum(1 - axis).astype(float)
    if not ink.any():
        return 0, alpha.shape[axis] - 1
    keep = np.where(ink >= ink.max() * floor)[0]
    return int(keep.min()), int(keep.max())


def tight(rgba: np.ndarray) -> np.ndarray:
    alpha = rgba[..., 3].astype(float)
    y0, y1 = _ink_extent(alpha, 0)
    x0, x1 = _ink_extent(alpha, 1)
    return rgba[y0:y1 + 1, x0:x1 + 1]


def resize_to_height(rgba: np.ndarray, height: int) -> Image.Image:
    image = Image.fromarray(rgba)
    width = max(1, round(image.width * height / image.height))
    return image.resize((width, height), Image.LANCZOS)


def square_icon(symbol: np.ndarray, size: int, pad_ratio: float = 0.12) -> Image.Image:
    """The symbol centred on a transparent square, with breathing room."""
    inner = max(1, int(round(size * (1 - 2 * pad_ratio))))
    image = Image.fromarray(tight(symbol))
    scale = min(inner / image.width, inner / image.height)
    scaled = image.resize((max(1, round(image.width * scale)),
                           max(1, round(image.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2))
    return canvas


def cut(art: np.ndarray):
    """
    Separate the artwork into symbol, lockup and full.

    The obvious split - crop the tagline off the bottom - is wrong for this
    logo. The ribbon runs the full height of the artwork and the tagline sits
    beside its lower half rather than below it, so a horizontal cut would take
    the bottom off the ribbon with it.

    So the tagline is erased rather than cropped, and only where it is really
    the tagline. Inside the text block that is the whole band. Left of it, in
    the symbol's columns, the same rows may hold either the bottom of the
    ribbon or - in a stacked arrangement, where the tagline runs the full
    width - the first few letters of the tagline. The two are told apart by
    what sits directly above: ribbon is continuous with the artwork above it,
    a letter of the tagline is detached from it.

    The symbol is then taken from the cleaned lockup, never the raw artwork,
    so a stray "More Op" can never end up inside the favicon.
    """
    alpha = art[..., 3]
    columns = bands(alpha, axis=1)
    text_from = columns[1][0] if len(columns) > 1 else alpha.shape[1]
    rows = bands(alpha[:, text_from:], axis=0)

    lockup = art.copy()
    if len(rows) > 1:
        top, bottom = rows[-1]
        lockup[top:bottom + 1, text_from:, 3] = 0

        # Left of the text block: erase only the columns whose ink in this
        # band is detached from whatever is above it.
        gap = alpha[max(0, top - GAP_PROBE):top, :text_from]
        detached = ~(gap > 40).any(0) if gap.size else np.ones(text_from, bool)
        lockup[top:bottom + 1, :text_from, 3][:, detached] = 0

    lockup = tight(lockup)
    symbol_columns = bands(lockup[..., 3], axis=1)
    symbol = tight(lockup[:, symbol_columns[0][0]:symbol_columns[0][1] + 1])
    return symbol, lockup, art


def main() -> int:
    if not SOURCE.exists():
        print(f"missing source artwork: {SOURCE}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    original = Image.open(SOURCE).convert("RGB")
    rgb0 = np.asarray(original).astype(float)
    plate = plate_colour(rgb0)
    angle = skew_degrees(rgb0)
    print(f"source      {original.width}x{original.height}  "
          f"plate #{''.join(f'{int(v):02X}' for v in plate)}  "
          f"skew {angle:+.2f}deg{'  (treated as straight)' if angle == 0 else ''}")

    art = tight(drop_residue(to_rgba(deskew(original, plate, angle), plate)))
    symbol, lockup, full = cut(art)
    print(f"artwork     {full.shape[1]}x{full.shape[0]} with real transparency")
    print(f"  symbol    {symbol.shape[1]}x{symbol.shape[0]}")
    print(f"  lockup    {lockup.shape[1]}x{lockup.shape[0]} (tagline removed)")

    written = []

    def write(name: str, image: Image.Image, inline: bool = False):
        """
        `inline=True` means this file gets base64'd into the page HTML on every
        rerun, so its byte size is a per-interaction cost rather than a
        one-off download. Quantising to 128 colours takes the header lockup
        from 29 KB to under 7 KB for a mean channel error of 1.4 - invisible
        at the 46px it renders at, and four times less HTML on every click.
        """
        if inline:
            image = image.quantize(colors=128, method=Image.FASTOCTREE)
        path = OUT / name
        image.save(path, optimize=True)
        written.append((name, image.width, image.height, path.stat().st_size))

    # Header lockup. 92px is the 2x of the 46px the brand bar renders at;
    # anything larger is bytes the page pays for and no screen can show.
    write("logo-lockup@2x.png", resize_to_height(lockup, 92), inline=True)
    write("logo-lockup.png", resize_to_height(lockup, 46), inline=True)

    # Full artwork with the tagline, for the README and any title card. Capped
    # at the source's own resolution - enlarging past it only ships a bigger
    # file of the same blur.
    full_height = min(320, full.shape[0])
    write("logo-full@2x.png", resize_to_height(full, full_height))
    write("logo-full.png", resize_to_height(full, full_height // 2))

    # The symbol alone.
    write("logo-symbol@2x.png", resize_to_height(symbol, 128), inline=True)
    write("logo-symbol.png", resize_to_height(symbol, 64), inline=True)

    # Icons. 180 is apple-touch; 32 is the favicon.
    for size in (32, 64, 180, 192):
        write(f"icon-{size}.png", square_icon(symbol, size))

    print()
    print(f"wrote {len(written)} files to assets/brand/")
    for name, w, h, size in written:
        print(f"  {name:24s} {w:4d}x{h:<4d} {size/1024:6.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

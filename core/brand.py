"""
The Sahulat AI mark, and the lockups built from it.

One source of truth. Every place the logo appears - the brand bar, the favicon,
the exported files in assets/ - is generated from the geometry below, so a
change to the mark cannot land in one of them and miss the others. A test
asserts the files on disk still match what this module emits.


THE MARK: "The Guided Opportunity Mark" (brand guide section 19)

A single continuous stroke drops into a low bowl, sweeps through it and rises
to a destination point. It is meant to suggest a path, a journey and an
arrival without literally drawing any of them.

The shape was chosen by rendering the alternatives at 16px and looking at
them, which is the only way this kind of question gets answered:

  * The first attempt kept a weighted dot at BOTH ends of a shallow curve. It
    read as a dumbbell at every size. Two ends of equal weight are two
    destinations, and the mark has only one.
  * A plain rising diagonal read as every growth-chart logo ever drawn, which
    is exactly the generic startup pattern the guide warns against (section
    14).
  * The low bowl is what makes it distinctive, and it earns its place: it
    echoes the flowing tail of the Urdu letter س (guide concept D), and it
    says the journey starts below before it rises. A path that only ever goes
    up is not what this product's users are living.

Why the details are what they are:

  * ONE destination point, and it is larger than the stroke is wide. That
    hierarchy is SIZE, never colour - the mark has to survive being printed in
    one ink (section 6), and a destination distinguishable only by being gold
    is a destination that vanishes in black and white.
  * The two cubics share a tangent at the join, so it reads as one continuous
    stroke rather than two arcs stuck together.
  * Colour comes from `currentColor`. One-colour, reversed, grayscale and dark
    mode become a property of where the mark is placed rather than four
    hand-maintained copies of the drawing.
  * NO gold in the symbol. The guide offers it as optional and says the mark
    must work without it; drawn, it was a floating crescent that read as an
    eyebrow over the point and turned to mush below 32px. Gold earns its place
    in the lockup instead, on the Urdu wordmark - the "premium civic"
    combination in section 6.
"""
from __future__ import annotations

# A 32-unit grid - four eight-unit modules - with the artwork inside a 4-unit
# margin. That margin is also the clear-space rule (section 10).
VIEWBOX = 32
MARGIN = 4

# The drawing. Named rather than inlined so the favicon, the web mark, the
# exported files and the tests all describe the same geometry.
#
# Two cubics sharing a tangent at (15.2, 22.4): the outgoing control vector of
# the first and the incoming vector of the second are both (3.2, -4.8), which
# is what makes the join invisible. Move one and you must move the other.
PATH = ("M 6.2 20.4 C 6 26.4 12 27.2 15.2 22.4 "
        "C 18.4 17.6 18.8 12.4 21.2 10.4")
STROKE = 2.45
POINT = (24.0, 8.2)          # the opportunity: where the path arrives
POINT_R = 3.3

GREEN = "#176B55"
DEEP = "#123B32"
GOLD = "#B98227"
INK = "#14211D"
CANVAS = "#F8F8F4"
BORDER = "#DDE4DF"


def mark_svg(size: int = 26, css_class: str = "sahulat-logo-mark",
             title: str = "", animate: bool = False) -> str:
    """
    The symbol on its own, for use inside the app.

    Everything is `currentColor`, so the caller decides the colour by setting
    one CSS property. That is what makes the monochrome, reversed and
    dark-mode versions the same drawing rather than four files to keep in step.
    """
    # A mark standing beside its own wordmark is decorative and must be hidden
    # from a screen reader, or the product name is announced twice. Standing
    # alone it IS the name, and needs a title.
    head = (f' role="img"><title>{title}</title>' if title
            else ' aria-hidden="true">')
    path_class = "sa-logo-path" + (" is-drawn" if animate else "")
    return (
        f'<svg class="{css_class}" viewBox="0 0 {VIEWBOX} {VIEWBOX}" '
        f'width="{size}" height="{size}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg"{head}'
        f'<path class="{path_class}" d="{PATH}" stroke="currentColor" '
        f'stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle class="sa-logo-point" cx="{POINT[0]}" cy="{POINT[1]}" '
        f'r="{POINT_R}" fill="currentColor"/>'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Lockups, exported as standalone files where there is no page CSS to inherit
# ---------------------------------------------------------------------------

def _standalone(body: str, width: float, height: float) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'fill="none" role="img"><title>Sahulat AI</title>{body}</svg>')


def _mark_group(x: float, y: float, scale: float, stroke: str,
                point: str = "") -> str:
    """The mark placed inside a larger lockup, in explicit colours."""
    return (
        f'<g transform="translate({x} {y}) scale({scale})">'
        f'<path d="{PATH}" stroke="{stroke}" stroke-width="{STROKE}" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{POINT[0]}" cy="{POINT[1]}" r="{POINT_R}" '
        f'fill="{point or stroke}"/>'
        f'</g>'
    )


def _wordmark(x: float, baseline: float, colour: str, size: float = 25) -> str:
    return (f'<text x="{x}" y="{baseline}" '
            f'font-family="Georgia,&apos;Source Serif 4&apos;,serif" '
            f'font-size="{size}" font-weight="700" fill="{colour}" '
            f'letter-spacing="-.4">Sahulat AI</text>')


def _urdu(x: float, baseline: float, colour: str, size: float = 20) -> str:
    # Urdu is set on its own optical baseline, not the Latin one. Nastaliq
    # descends well below where a Latin baseline sits, so matching the two
    # mathematically makes the Urdu look like it is sliding off the lockup -
    # which is how a co-equal wordmark ends up looking like an afterthought
    # (guide section 8).
    return (f'<text x="{x}" y="{baseline}" '
            f'font-family="&apos;Noto Nastaliq Urdu&apos;,serif" '
            f'font-size="{size}" fill="{colour}" direction="rtl">سہولت</text>')


def _separator(x: float, y: float, colour: str) -> str:
    return f'<circle cx="{x}" cy="{y}" r="1.5" fill="{colour}"/>'


def lockup_primary(stroke: str = GREEN, point: str = DEEP, word: str = DEEP,
                   urdu: str = GREEN, separator: str = BORDER) -> str:
    """[SYMBOL] Sahulat AI · سہولت - the primary bilingual horizontal logo."""
    body = (_mark_group(3, 5, 1.0, stroke, point)
            + _wordmark(44, 34, word)
            + _separator(172, 28, separator)
            + _urdu(186, 34, urdu))
    return _standalone(body, 250, 48)


def lockup_premium(stroke: str = GREEN, point: str = DEEP,
                   word: str = DEEP) -> str:
    """The "premium civic" combination: the Urdu wordmark in muted gold."""
    return lockup_primary(stroke=stroke, point=point, word=word, urdu=GOLD)


def lockup_compact(stroke: str = GREEN, point: str = DEEP,
                   word: str = DEEP) -> str:
    """[SYMBOL] Sahulat AI - no Urdu, for tight horizontal space."""
    body = _mark_group(3, 5, 1.0, stroke, point) + _wordmark(44, 34, word)
    return _standalone(body, 166, 48)


def lockup_urdu_first(stroke: str = GREEN, point: str = DEEP,
                      urdu: str = DEEP) -> str:
    """[SYMBOL] سہولت - Urdu as the primary wordmark, not a decoration."""
    body = _mark_group(3, 5, 1.0, stroke, point) + _urdu(44, 34, urdu, size=23)
    return _standalone(body, 124, 48)


def lockup_stacked(stroke: str = GREEN, point: str = DEEP, word: str = DEEP,
                   urdu: str = GREEN) -> str:
    """The mark above both wordmarks, for square-ish space."""
    body = (_mark_group(38, 4, 1.35, stroke, point)
            + f'<text x="60" y="78" text-anchor="middle" '
              f'font-family="Georgia,&apos;Source Serif 4&apos;,serif" '
              f'font-size="21" font-weight="700" fill="{word}" '
              f'letter-spacing="-.4">Sahulat AI</text>'
            + f'<text x="60" y="102" text-anchor="middle" '
              f'font-family="&apos;Noto Nastaliq Urdu&apos;,serif" '
              f'font-size="17" fill="{urdu}" direction="rtl">سہولت</text>')
    return _standalone(body, 120, 112)


def symbol_file(stroke: str = GREEN, point: str = DEEP, size: int = 64) -> str:
    """The symbol alone."""
    body = _mark_group(0, 0, 1, stroke, point)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {VIEWBOX} {VIEWBOX}" width="{size}" height="{size}" '
            f'fill="none" role="img"><title>Sahulat AI</title>{body}</svg>')


def favicon_svg() -> str:
    """
    The 16px version: heavier stroke, on the brand canvas, rounded corners.

    A favicon is read at a glance in a crowded tab strip. The stroke is
    thickened because at 16px the drawn width lands near one device pixel and
    a hairline renders as grey rather than green - which is how a green brand
    ends up with a smudge for an icon.
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {VIEWBOX} {VIEWBOX}" width="32" height="32" fill="none" '
        f'role="img"><title>Sahulat AI</title>'
        f'<rect width="{VIEWBOX}" height="{VIEWBOX}" rx="7" fill="{CANVAS}"/>'
        f'<path d="{PATH}" stroke="{GREEN}" stroke-width="3.1" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{POINT[0]}" cy="{POINT[1]}" r="3.5" fill="{DEEP}"/>'
        f'</svg>'
    )


def app_icon_svg() -> str:
    """The app icon and social avatar: the mark reversed out of deep green."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {VIEWBOX} {VIEWBOX}" width="512" height="512" '
        f'fill="none" role="img"><title>Sahulat AI</title>'
        f'<rect width="{VIEWBOX}" height="{VIEWBOX}" fill="{DEEP}"/>'
        f'<path d="{PATH}" stroke="#FFFFFF" stroke-width="2.8" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{POINT[0]}" cy="{POINT[1]}" r="{POINT_R}" fill="#FFFFFF"/>'
        f'</svg>'
    )


# Every file in assets/, under the names the guide asks for (section 9).
EXPORTS = {
    "sahulat-logo-primary.svg": lockup_primary,
    "sahulat-logo-premium.svg": lockup_premium,
    "sahulat-logo-compact.svg": lockup_compact,
    "sahulat-logo-urdu.svg": lockup_urdu_first,
    "sahulat-logo-stacked.svg": lockup_stacked,
    "sahulat-logo-symbol.svg": symbol_file,
    # One ink. Nothing is lost but the colour: the hierarchy was never carried
    # by it.
    "sahulat-logo-monochrome.svg": lambda: lockup_primary(
        stroke=INK, point=INK, word=INK, urdu=INK, separator=INK),
    # For deep-green and photographic backgrounds.
    "sahulat-logo-reversed.svg": lambda: lockup_primary(
        stroke="#FFFFFF", point="#FFFFFF", word="#FFFFFF", urdu="#FFFFFF",
        separator="#FFFFFF"),
    "sahulat-favicon.svg": favicon_svg,
    "sahulat-app-icon.svg": app_icon_svg,
}


def write_exports(directory: str = "assets") -> list:
    """Regenerate every file in assets/. The test calls this too."""
    import io
    import os

    os.makedirs(directory, exist_ok=True)
    written = []
    for name, build in EXPORTS.items():
        path = os.path.join(directory, name)
        io.open(path, "w", encoding="utf-8", newline="\n").write(build() + "\n")
        written.append(path)
    return written

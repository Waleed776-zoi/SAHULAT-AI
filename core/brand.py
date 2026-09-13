# -*- coding: utf-8 -*-
"""
The Sahulat AI brand: the supplied logo, and how the app puts it on a page.

This module used to draw a mark of its own - a placeholder built when the
project had no logo yet. It now serves the real artwork instead. The drawn
mark is gone rather than kept alongside, because two logos in one repository
is precisely how a brand rots: the header gets updated, the favicon and the
press kit keep the old drawing, and nobody notices for months because no
single page shows both at once.

WHERE THE FILES COME FROM

`assets/source/sahulat-logo-source.png` is the master artwork as supplied -
the 2000px export. `sahulat-logo-alt-stacked.png` beside it is the earlier
variant, kept because it is a different arrangement rather than a worse file.
Everything in `assets/brand/` is generated from it by `scripts/prepare_logo.py`
- deskewed, lifted off its background into real transparency, and cut to size.
Never hand-edit those; change the script or the source and re-run it.

HOW IT REACHES THE PAGE

As a base64 data URI, built once per process. Streamlit re-sends the whole
markdown block on every rerun, so the two files that appear in the header are
quantised to 128 colours by the build script - under 7 KB each rather than 29.
A data URI rather than a served file because it cannot 404: there is no static
route to configure, nothing to get wrong behind a proxy, and the logo either
renders or the app never started.

COLOUR

The values below are measured from the artwork, not eyeballed. They are here
so anything that needs to sit beside the logo can match it, and so the drift
between the logo's green and the interface's own green stays a visible fact
rather than a surprise - see PROJECT_TRACKER.md BRAND-02.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "source" / "sahulat-logo-source.png"
BRAND = ROOT / "assets" / "brand"

# -- the artwork -------------------------------------------------------------

LOCKUP = BRAND / "logo-lockup@2x.png"        # symbol + wordmark + Urdu
LOCKUP_1X = BRAND / "logo-lockup.png"
FULL = BRAND / "logo-full@2x.png"            # the above, plus the tagline
FULL_1X = BRAND / "logo-full.png"
SYMBOL = BRAND / "logo-symbol@2x.png"        # the ribbon alone
SYMBOL_1X = BRAND / "logo-symbol.png"
ICON_32 = BRAND / "icon-32.png"
ICON_64 = BRAND / "icon-64.png"
ICON_180 = BRAND / "icon-180.png"            # apple-touch
ICON_192 = BRAND / "icon-192.png"            # browser tab / PWA

#: Every file the build script is expected to produce. Tests read this.
EXPORTS = (
    "logo-lockup@2x.png", "logo-lockup.png",
    "logo-full@2x.png", "logo-full.png",
    "logo-symbol@2x.png", "logo-symbol.png",
    "icon-32.png", "icon-64.png", "icon-180.png", "icon-192.png",
)

#: The two files that get inlined into page HTML on every rerun, so their size
#: is a per-interaction cost. Guarded by a test.
INLINED = ("logo-lockup@2x.png", "logo-symbol@2x.png")
INLINE_BUDGET_BYTES = 12_000

# -- colour, measured from the artwork ---------------------------------------

RIBBON = "#3E965A"          # the ribbon's median green
RIBBON_LIGHT = "#5DB576"    # light end of its gradient
RIBBON_DARK = "#2C8248"     # dark end of its gradient
WORDMARK = "#0B6B4F"        # "Sahulat", deep green
URDU = "#1C6B53"            # the Urdu wordmark
ACCENT = "#14213D"          # the navy ".AI"
TAGLINE = "#798699"         # "More Opportunities. Easier Access."

#: The logo is light-background artwork. Its wordmark is deep green and its
#: ".AI" is navy, both of which drop to almost no contrast on the app's deep
#: green surfaces, so the full lockup must not be placed on them - use
#: `symbol_html()` there, which is light enough to read.
DARK_SAFE = (SYMBOL, SYMBOL_1X, ICON_32, ICON_64, ICON_180, ICON_192)


@lru_cache(maxsize=None)
def data_uri(path: Path) -> str:
    """`path` as a base64 PNG data URI, encoded once per process."""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _img(path: Path, height: int, alt: str, css_class: str, decorative: bool) -> str:
    # An image that sits beside the product name in text is decorative twice
    # over; a screen reader announcing "Sahulat AI logo, Sahulat AI" is noise.
    # Standing alone it is the only thing naming the product, so it needs alt.
    label = (' alt="" aria-hidden="true"' if decorative
             else f' alt="{alt}"')
    return (f'<img src="{data_uri(path)}" class="{css_class}" '
            f'height="{height}"{label} draggable="false">')


def lockup_html(height: int = 46, alt: str = "Sahulat AI",
                css_class: str = "sahulat-logo", decorative: bool = False) -> str:
    """The full horizontal lockup. Light backgrounds only."""
    return _img(LOCKUP, height, alt, css_class, decorative)


def symbol_html(height: int = 24, alt: str = "Sahulat AI",
                css_class: str = "sahulat-symbol", decorative: bool = True) -> str:
    """The ribbon on its own. Safe on dark surfaces as well as light."""
    return _img(SYMBOL, height, alt, css_class, decorative)


def full_html(height: int = 120, alt: str = "Sahulat AI",
              css_class: str = "sahulat-logo-full", decorative: bool = False) -> str:
    """Lockup plus tagline, for title cards. Light backgrounds only."""
    return _img(FULL, height, alt, css_class, decorative)


def page_icon() -> str | None:
    """The browser-tab icon, as a path Streamlit can read. None if missing."""
    return str(ICON_192) if ICON_192.exists() else None


def missing() -> list:
    """Any expected file that is not on disk - run scripts/prepare_logo.py."""
    return [name for name in EXPORTS if not (BRAND / name).exists()]

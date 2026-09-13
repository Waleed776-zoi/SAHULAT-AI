"""
The logo, and the things about it that break silently.

A brand system rots in a particular way: someone adjusts the mark in the
header, the favicon and the exported files keep the old drawing, and nobody
notices for months because no page shows two of them at once. So the first
test here is the anti-drift one - everything in assets/ must still be exactly
what core.brand emits.

The rest guard properties that a screenshot cannot: that the mark survives one
ink, that the drawn stroke length matches the dash length the animation uses,
and that the artwork stays inside its own clear space.
"""
from __future__ import annotations

import io
import math
import os
import re
import unittest

from core import brand

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def _read(name: str) -> str:
    with io.open(os.path.join(ASSETS, name), encoding="utf-8") as handle:
        return handle.read()


def _read_root(*parts: str) -> str:
    with io.open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return handle.read()


class TestExportedFilesMatchTheCode(unittest.TestCase):
    """assets/ is generated, never hand-edited."""

    def test_every_declared_export_exists(self):
        for name in brand.EXPORTS:
            self.assertTrue(os.path.exists(os.path.join(ASSETS, name)),
                            f"{name} is declared but not exported")

    def test_no_file_has_drifted_from_the_generator(self):
        """
        The failure this file exists for. If this breaks, someone edited an
        SVG by hand or changed the geometry without re-running the export -
        and the header, the favicon and the press kit are now three different
        logos.
        """
        for name, build in brand.EXPORTS.items():
            self.assertEqual(_read(name).strip(), build().strip(),
                             f"{name} no longer matches core.brand - "
                             f"run core.brand.write_exports()")

    def test_the_assets_folder_holds_nothing_else(self):
        stray = {f for f in os.listdir(ASSETS) if f.endswith(".svg")} - set(brand.EXPORTS)
        self.assertFalse(stray, f"ungenerated SVGs in assets/: {stray}")


class TestTheMarkSurvivesOneInk(unittest.TestCase):
    """
    Hierarchy must be carried by size, never by colour (guide section 6).
    """

    def test_the_web_mark_is_drawn_in_currentcolor(self):
        """
        One drawing, not four. Monochrome, reversed, grayscale and dark mode
        all become a property of where the mark is placed.
        """
        svg = brand.mark_svg()
        self.assertIn('stroke="currentColor"', svg)
        self.assertIn('fill="currentColor"', svg)
        self.assertNotIn("#", svg, "the web mark hardcodes a colour")

    def test_the_symbol_carries_no_gold(self):
        """
        The guide offers gold as optional and requires the mark to work
        without it. Drawn, the accent was a floating crescent that turned to
        mush below 32px - so it lives on the Urdu wordmark instead.
        """
        self.assertNotIn(brand.GOLD, brand.mark_svg())
        self.assertNotIn(brand.GOLD, brand.symbol_file())
        self.assertNotIn(brand.GOLD, brand.favicon_svg())

    def test_gold_still_has_a_home_in_the_lockup(self):
        self.assertIn(brand.GOLD, brand.lockup_premium())

    def test_the_monochrome_version_is_genuinely_one_colour(self):
        colours = set(re.findall(r'#[0-9A-Fa-f]{6}', _read("sahulat-logo-monochrome.svg")))
        self.assertEqual(colours, {brand.INK}, f"more than one ink: {colours}")

    def test_the_reversed_version_is_genuinely_one_colour(self):
        colours = set(re.findall(r'#[0-9A-Fa-f]{6}', _read("sahulat-logo-reversed.svg")))
        self.assertEqual(colours, {"#FFFFFF"}, f"not purely reversed: {colours}")

    def test_the_destination_reads_without_colour(self):
        """
        The point must be wider than the stroke, or flattening to one ink
        turns the destination into a thicker bit of line.
        """
        self.assertGreater(brand.POINT_R * 2, brand.STROKE * 1.6)


class TestGeometry(unittest.TestCase):
    """Properties of the drawing that a rendered screenshot would not catch."""

    CURVES = (((6.2, 20.4), (6, 26.4), (12, 27.2), (15.2, 22.4)),
              ((15.2, 22.4), (18.4, 17.6), (18.8, 12.4), (21.2, 10.4)))

    def test_the_path_in_the_module_matches_the_curves_tested_here(self):
        numbers = [float(n) for n in re.findall(r'-?\d+\.?\d*', brand.PATH)]
        expected = [v for curve in self.CURVES for point in curve[1:] for v in point]
        expected = list(self.CURVES[0][0]) + expected
        self.assertEqual(numbers, expected,
                         "PATH and the curves in this test have diverged")

    def test_the_two_curves_join_smoothly(self):
        """
        The mark is one continuous stroke. That is only true if the outgoing
        control vector of the first curve equals the incoming vector of the
        second - otherwise there is a visible kink at the join.
        """
        first, second = self.CURVES
        self.assertEqual(first[3], second[0], "the curves do not even meet")
        out_v = (first[3][0] - first[2][0], first[3][1] - first[2][1])
        in_v = (second[1][0] - second[0][0], second[1][1] - second[0][1])
        for a, b in zip(out_v, in_v):
            self.assertAlmostEqual(a, b, places=6,
                                   msg="a kink at the join breaks the stroke")

    def _points(self):
        for curve in self.CURVES:
            for i in range(401):
                t = i / 400
                u = 1 - t
                yield (u**3*curve[0][0] + 3*u*u*t*curve[1][0]
                       + 3*u*t*t*curve[2][0] + t**3*curve[3][0],
                       u**3*curve[0][1] + 3*u*u*t*curve[1][1]
                       + 3*u*t*t*curve[2][1] + t**3*curve[3][1])

    def test_the_artwork_stays_inside_its_clear_space(self):
        """
        The 4-unit margin is also the clear-space rule (section 10). Artwork
        crossing it means the logo touches whatever sits beside it.
        """
        cap = brand.STROKE / 2
        low, high = brand.MARGIN, brand.VIEWBOX - brand.MARGIN
        for x, y in self._points():
            self.assertGreaterEqual(x - cap, low - .05, "stroke crosses the left margin")
            self.assertLessEqual(x + cap, high + .05, "stroke crosses the right margin")
            self.assertGreaterEqual(y - cap, low - .05, "stroke crosses the top margin")
            self.assertLessEqual(y + cap, high + .05, "stroke crosses the bottom margin")

        px, py = brand.POINT
        self.assertLessEqual(px + brand.POINT_R, high + .05)
        self.assertGreaterEqual(py - brand.POINT_R, low - .05)

    def test_the_point_meets_the_end_of_the_stroke(self):
        """
        A gap reads as a broken line; a point sitting on the tip reads as a
        lollipop. It should just touch.
        """
        tip = (21.2, 10.4)
        gap = math.dist(tip, brand.POINT) - brand.POINT_R - brand.STROKE / 2
        self.assertLess(gap, 0, "the destination point is detached")
        self.assertGreater(gap, -2.0, "the point has swallowed the stroke")

    def test_the_dash_length_matches_the_real_stroke_length(self):
        """
        The draw animation uses stroke-dasharray: 27. If the path is longer
        the stroke never finishes drawing; if much shorter the animation ends
        early and the last stretch appears instantly.
        """
        total = 0.0
        previous = None
        for point in self._points():
            if previous is not None and previous != point:
                total += math.dist(previous, point)
            previous = point
        css = _read_root("styles", "animations.css")
        # Two rules share this selector: the animation and the reduced-motion
        # override that sets `dasharray: none`. Take the numeric one.
        lengths = [int(m) for m in re.findall(
            r'\.sa-logo-path\.is-drawn\s*\{[^}]*?stroke-dasharray:\s*(\d+)', css)]
        self.assertEqual(len(lengths), 1,
                         f"expected exactly one numeric dasharray, found {lengths}")
        declared = float(lengths[0])
        self.assertGreaterEqual(declared, total,
                                f"dasharray {declared} < path length {total:.2f}")
        self.assertLess(declared - total, 2.0,
                        f"dasharray {declared} overshoots path length {total:.2f}")


class TestAccessibilityAndLockups(unittest.TestCase):

    def test_the_mark_beside_a_wordmark_is_hidden_from_screen_readers(self):
        """Otherwise the product name is announced twice."""
        self.assertIn('aria-hidden="true"', brand.mark_svg())

    def test_the_mark_standing_alone_is_labelled(self):
        svg = brand.mark_svg(title="Sahulat AI")
        self.assertIn("<title>Sahulat AI</title>", svg)
        self.assertNotIn('aria-hidden', svg)

    def test_every_lockup_carries_the_mark(self):
        for build in (brand.lockup_primary, brand.lockup_compact,
                      brand.lockup_urdu_first, brand.lockup_stacked):
            self.assertIn(brand.PATH, build(), build.__name__)

    def test_the_bilingual_lockups_carry_both_wordmarks(self):
        for build in (brand.lockup_primary, brand.lockup_stacked):
            svg = build()
            self.assertIn("Sahulat AI", svg, build.__name__)
            self.assertIn("سہولت", svg, build.__name__)

    def test_urdu_first_leads_with_urdu_and_drops_the_latin(self):
        """
        "Do not make the Urdu wordmark look like a decorative afterthought."
        The Urdu-first lockup is the one that proves Urdu can stand alone.
        """
        svg = brand.lockup_urdu_first()
        self.assertIn("سہولت", svg)
        self.assertNotIn("Sahulat AI</text>", svg)

    def test_the_urdu_is_set_right_to_left(self):
        self.assertIn('direction="rtl"', brand.lockup_primary())

    def test_the_favicon_is_the_small_size_build(self):
        """
        At 16px the normal stroke lands near one device pixel and renders as
        grey. The favicon thickens it.
        """
        favicon = brand.favicon_svg()
        declared = float(re.search(r'stroke-width="([\d.]+)"', favicon).group(1))
        self.assertGreater(declared, brand.STROKE)
        self.assertIn(brand.PATH, favicon, "the favicon is a different drawing")


class TestTheAppUsesIt(unittest.TestCase):

    APP = _read_root("app.py")

    def test_the_app_draws_the_mark_from_the_brand_module(self):
        self.assertIn("from core.brand import mark_svg", self.APP)

    def test_no_logo_geometry_is_inlined_in_the_app(self):
        """
        The old mark was an SVG string in app.py. That is how drift starts.

        Note 24x24 viewBoxes are fine here - that is the category-icon grid.
        What must not come back is the logo's own geometry.
        """
        self.assertNotIn("LOGO_MARK", self.APP)
        self.assertNotIn("M3 20 C 9 20", self.APP, "the old mark path is back")
        self.assertNotIn("sahulat-logo-mark\" viewBox", self.APP,
                         "the mark is being built in app.py again")

    def test_the_favicon_is_wired_up(self):
        self.assertIn("page_icon", self.APP)
        self.assertIn("sahulat-favicon.svg", self.APP)

    def test_the_draw_animation_plays_once_per_session(self):
        """
        "Do not replay it on every Streamlit rerun." should_animate() is what
        already tracks that, so the mark asks it rather than inventing a
        second mechanism.
        """
        self.assertIn('should_animate("logo")', self.APP)

    def test_reduced_motion_leaves_the_logo_drawn(self):
        """
        Left to the blanket 1ms rule, the dash offset would animate in a
        flicker and the point would pop. Under reduced motion the mark is
        simply present.
        """
        css = _read_root("styles", "animations.css")
        block = css[css.index("prefers-reduced-motion"):]
        self.assertIn("stroke-dasharray: none !important", block)
        self.assertIn(".sa-logo-path.is-drawn ~ .sa-logo-point", block)


if __name__ == "__main__":
    unittest.main()

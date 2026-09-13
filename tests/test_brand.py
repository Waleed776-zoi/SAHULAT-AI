# -*- coding: utf-8 -*-
"""
The brand: the supplied artwork, its generated assets, and how the app uses it.

The headline guard is `test_no_file_has_drifted_from_the_build`. A brand rots
in one specific way - someone touches one file by hand, the rest keep the old
drawing, and nobody notices for months because no single page shows two of
them at once. Regenerating every variant in memory and comparing bytes makes
that impossible to do quietly.
"""
from __future__ import annotations

import base64
import importlib.util
import io
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import brand  # noqa: E402


def _load_build():
    spec = importlib.util.spec_from_file_location(
        "prepare_logo", ROOT / "scripts" / "prepare_logo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load_build()


def _rebuild_in_memory():
    """Everything scripts/prepare_logo.py writes, without writing anything."""
    original = Image.open(build.SOURCE).convert("RGB")
    rgb = np.asarray(original).astype(float)
    plate = build.plate_colour(rgb)
    angle = build.skew_degrees(rgb)
    art = build.tight(build.drop_residue(
        build.to_rgba(build.deskew(original, plate, angle), plate)))
    symbol, lockup, art = build.cut(art)

    full_height = min(320, art.shape[0])
    made = {
        "logo-lockup@2x.png": (build.resize_to_height(lockup, 92), True),
        "logo-lockup.png": (build.resize_to_height(lockup, 46), True),
        "logo-full@2x.png": (build.resize_to_height(art, full_height), False),
        "logo-full.png": (build.resize_to_height(art, full_height // 2), False),
        "logo-symbol@2x.png": (build.resize_to_height(symbol, 128), True),
        "logo-symbol.png": (build.resize_to_height(symbol, 64), True),
    }
    for size in (32, 64, 180, 192):
        made[f"icon-{size}.png"] = (build.square_icon(symbol, size), False)

    out = {}
    for name, (image, inline) in made.items():
        if inline:
            image = image.quantize(colors=128, method=Image.FASTOCTREE)
        buffer = io.BytesIO()
        image.save(buffer, "PNG", optimize=True)
        out[name] = buffer.getvalue()
    return out


class SourceArtwork(unittest.TestCase):

    def test_the_master_artwork_is_in_the_repository(self):
        """Without it nothing downstream can be rebuilt or corrected."""
        self.assertTrue(brand.SOURCE.exists(), f"missing {brand.SOURCE}")

    def test_the_master_is_the_high_resolution_export(self):
        """
        A screenshot of the design was the only file available at first. It
        works, but every icon is sharper from the real export, so the master
        must not quietly regress to the smaller one.
        """
        self.assertGreaterEqual(min(Image.open(brand.SOURCE).size), 1200)

    def test_the_master_is_left_alone_because_it_is_straight(self):
        """
        The current master is a clean export. Reporting any rotation for it
        would mean resampling straight artwork into crookedness.
        """
        rgb = np.asarray(Image.open(brand.SOURCE).convert("RGB")).astype(float)
        self.assertEqual(build.skew_degrees(rgb), 0.0)

    def test_a_tilted_source_is_still_measured_and_corrected(self):
        """
        The earlier artwork was a screenshot, rotated about 1.4 degrees. The
        detector has to keep working on that: the guards added for the clean
        export must not have turned it into a no-op.
        """
        tilted = brand.SOURCE.parent / "sahulat-logo-alt-stacked.png"
        if not tilted.exists():
            self.skipTest("the tilted variant is not kept in this checkout")
        rgb = np.asarray(Image.open(tilted).convert("RGB")).astype(float)
        self.assertAlmostEqual(build.skew_degrees(rgb), -1.41, places=1)

    def test_a_curved_edge_is_not_mistaken_for_a_baseline(self):
        """
        Measured across the whole width, the ribbon's underside fits a line at
        -7.7 degrees on artwork that is perfectly straight. Acting on that
        would rotate a clean logo into a crooked one, which is why the fit is
        rejected unless the points really lie on a line.
        """
        curved = Image.new("RGB", (600, 300), (255, 255, 255))
        pixels = curved.load()
        for x in range(40, 560):
            y = int(240 - 90 * np.sin(np.pi * (x - 40) / 520))
            for dy in range(10):
                pixels[x, y + dy] = (20, 120, 70)
        self.assertEqual(build.skew_degrees(np.asarray(curved).astype(float)), 0.0)

    def test_straight_artwork_would_not_be_rotated(self):
        """A clean source must pass through the deskew untouched."""
        straight = Image.new("RGB", (400, 200), (250, 251, 253))
        for x in range(40, 360, 6):
            for y in range(150, 160):
                straight.putpixel((x, y), (20, 30, 40))
        angle = build.skew_degrees(np.asarray(straight).astype(float))
        self.assertAlmostEqual(angle, 0.0, places=6)


class GeneratedAssets(unittest.TestCase):

    def test_every_declared_export_exists(self):
        self.assertEqual(brand.missing(), [],
                         "run: python scripts/prepare_logo.py")

    def test_no_file_has_drifted_from_the_build(self):
        """
        Each committed asset is byte-identical to what the script produces.

        This is the test that makes the whole arrangement trustworthy: it
        catches a hand-edited file, a stale asset left behind by a changed
        source, and a build parameter changed without regenerating.
        """
        rebuilt = _rebuild_in_memory()
        self.assertEqual(sorted(rebuilt), sorted(brand.EXPORTS),
                         "the build and core.brand.EXPORTS disagree")
        for name in brand.EXPORTS:
            with self.subTest(name):
                on_disk = (brand.BRAND / name).read_bytes()
                self.assertEqual(on_disk, rebuilt[name],
                                 f"{name} differs from scripts/prepare_logo.py "
                                 f"- re-run it rather than editing the file")

    def test_the_brand_folder_holds_nothing_else(self):
        stray = sorted(p.name for p in brand.BRAND.iterdir()
                       if p.name not in brand.EXPORTS)
        self.assertEqual(stray, [], "unexpected files in assets/brand/")

    def test_the_placeholder_mark_is_gone(self):
        """
        The drawn mark this project used before the logo arrived must not
        still be sitting in the repository. Two logos is the rot.
        """
        leftovers = sorted(p.name for p in (ROOT / "assets").rglob("sahulat-logo-*.svg"))
        self.assertEqual(leftovers, [])
        self.assertFalse((ROOT / "assets" / "sahulat-favicon.svg").exists())


class Transparency(unittest.TestCase):
    """The supplied file had no alpha and a near-white plate, not white."""

    def test_every_asset_carries_real_transparency(self):
        """
        Mode is not the thing to assert: the two inlined files are palette
        PNGs, which carry transparency in a tRNS chunk rather than a channel.
        What matters is that it survives being read back.
        """
        for name in brand.EXPORTS:
            with self.subTest(name):
                image = Image.open(brand.BRAND / name)
                self.assertTrue(image.mode == "RGBA" or "transparency" in image.info,
                                f"{name} has no transparency at all")
                self.assertLess(int(np.asarray(image.convert("RGBA"))[..., 3].min()), 8)

    def test_quantising_did_not_flatten_the_edges(self):
        """
        Palette-reducing the inlined files could have left one on/off
        transparent index, which would hard-edge every curve in the ribbon and
        every stem of the type. Graded alpha is what keeps them smooth.
        """
        for name in brand.INLINED:
            with self.subTest(name):
                alpha = np.asarray(Image.open(brand.BRAND / name).convert("RGBA"))[..., 3]
                self.assertGreater(len(np.unique(alpha)), 16,
                                   f"{name} lost its anti-aliasing")

    def test_no_asset_kept_its_background_plate(self):
        """
        The corners must be fully transparent. If the plate survived, the logo
        renders as a pale rectangle on the app's warm paper canvas - which is
        exactly the failure that is invisible on a white mockup.
        """
        for name in brand.EXPORTS:
            with self.subTest(name):
                alpha = np.asarray(Image.open(brand.BRAND / name).convert("RGBA"))[..., 3]
                corners = [alpha[0, 0], alpha[0, -1], alpha[-1, 0], alpha[-1, -1]]
                self.assertEqual(max(int(c) for c in corners), 0)

    def test_the_artwork_reaches_the_edges_of_its_own_box(self):
        """Tightly cropped: no dead transparent margin around the lockup."""
        for name in ("logo-lockup@2x.png", "logo-full@2x.png", "logo-symbol@2x.png"):
            with self.subTest(name):
                alpha = np.asarray(Image.open(brand.BRAND / name).convert("RGBA"))[..., 3]
                self.assertTrue(alpha[0].max() > 0 or alpha[-1].max() > 0)
                self.assertTrue(alpha[:, 0].max() > 0 or alpha[:, -1].max() > 0)

    def test_the_tagline_stayed_opaque(self):
        """
        Keying out the white would have left the grey tagline half
        transparent, because it is closer to the background than the rest.
        Un-compositing from the known plate is what avoids that.
        """
        image = Image.open(brand.BRAND / "logo-full@2x.png").convert("RGBA")
        alpha = np.asarray(image)[..., 3]
        tagline = alpha[int(alpha.shape[0] * 0.86):]
        self.assertGreater(int(tagline.max()), 250)


class Icons(unittest.TestCase):

    def test_icons_are_square(self):
        for size in (32, 64, 180, 192):
            with self.subTest(size):
                image = Image.open(brand.BRAND / f"icon-{size}.png")
                self.assertEqual(image.size, (size, size))

    def test_icons_keep_clear_space_around_the_symbol(self):
        """An icon crammed to its own edge looks wrong beside every other."""
        for size in (64, 180, 192):
            with self.subTest(size):
                alpha = np.asarray(Image.open(brand.BRAND / f"icon-{size}.png"))[..., 3]
                rows = np.where((alpha > 8).any(1))[0]
                cols = np.where((alpha > 8).any(0))[0]
                margin = min(rows.min(), cols.min(),
                             size - 1 - rows.max(), size - 1 - cols.max())
                self.assertGreaterEqual(int(margin), 2)

    def test_the_symbol_survives_on_a_dark_surface(self):
        """
        The green ribbon is the part that may sit on deep green. The full
        lockup may not - its wordmark is navy - which is why the footer uses
        the symbol and core.brand records DARK_SAFE.
        """
        image = Image.open(brand.BRAND / "icon-64.png").convert("RGBA")
        art = np.asarray(image).astype(float)
        opaque = art[..., 3] > 200
        self.assertTrue(opaque.any())
        lit = art[..., :3][opaque].mean(1)
        deep_green_luma = 0.2126 * 0x12 + 0.7152 * 0x3B + 0.0722 * 0x32
        self.assertGreater(float(lit.mean()), deep_green_luma + 20)

    def test_the_lockup_is_not_listed_as_dark_safe(self):
        self.assertNotIn(brand.LOCKUP, brand.DARK_SAFE)
        self.assertIn(brand.SYMBOL, brand.DARK_SAFE)


class Serving(unittest.TestCase):

    def test_the_data_uri_is_a_real_png(self):
        uri = brand.data_uri(brand.LOCKUP)
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        raw = base64.b64decode(uri.split(",", 1)[1])
        self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(raw, brand.LOCKUP.read_bytes())

    def test_the_data_uri_is_built_once(self):
        brand.data_uri.cache_clear()
        brand.data_uri(brand.LOCKUP)
        brand.data_uri(brand.LOCKUP)
        self.assertEqual(brand.data_uri.cache_info().hits, 1)

    def test_inlined_assets_stay_inside_their_budget(self):
        """
        These ship in the page HTML on every rerun, so their size is paid per
        interaction rather than once. Quantising keeps them small; this stops
        a future change quietly making every click heavier.
        """
        for name in brand.INLINED:
            with self.subTest(name):
                size = (brand.BRAND / name).stat().st_size
                self.assertLess(size, brand.INLINE_BUDGET_BYTES,
                                f"{name} is {size} bytes and is inlined on every rerun")

    def test_the_height_is_set_but_never_the_width(self):
        """
        Setting both would let a change to one stretch the artwork. Height
        alone plus the intrinsic ratio cannot distort it.
        """
        markup = brand.lockup_html(height=46)
        self.assertIn('height="46"', markup)
        self.assertNotIn("width=", markup)

    def test_a_logo_standing_alone_is_labelled(self):
        self.assertIn('alt="Sahulat AI"', brand.lockup_html())

    def test_a_logo_beside_the_name_is_hidden_from_screen_readers(self):
        """Announcing "Sahulat AI logo, Sahulat AI" is noise, not access."""
        markup = brand.symbol_html()
        self.assertIn('aria-hidden="true"', markup)
        self.assertIn('alt=""', markup)

    def test_the_page_icon_resolves_to_a_real_file(self):
        icon = brand.page_icon()
        self.assertIsNotNone(icon)
        self.assertTrue(Path(icon).exists())


class Colours(unittest.TestCase):

    def test_recorded_colours_are_valid_hex(self):
        for name in ("RIBBON", "RIBBON_LIGHT", "RIBBON_DARK",
                     "WORDMARK", "URDU", "ACCENT", "TAGLINE"):
            with self.subTest(name):
                value = getattr(brand, name)
                self.assertRegex(value, r"^#[0-9A-F]{6}$")

    def test_the_recorded_colours_are_actually_in_the_artwork(self):
        """
        Measured from the file, not chosen by eye - so this asserts each one
        is close to something really present rather than merely plausible.
        """
        art = np.asarray(Image.open(brand.BRAND / "logo-full@2x.png").convert("RGBA"))
        opaque = art[..., :3][art[..., 3] > 230].astype(int)
        for name in ("RIBBON", "WORDMARK", "URDU", "ACCENT", "TAGLINE"):
            with self.subTest(name):
                target = np.array([int(getattr(brand, name)[i:i + 2], 16)
                                   for i in (1, 3, 5)])
                nearest = np.abs(opaque - target).sum(1).min()
                self.assertLess(int(nearest), 30,
                                f"{name} is not a colour in the artwork")


class AppWiring(unittest.TestCase):

    APP = (ROOT / "app.py").read_text(encoding="utf-8")
    COMPONENTS = (ROOT / "styles" / "components.css").read_text(encoding="utf-8")
    ANIMATIONS = (ROOT / "styles" / "animations.css").read_text(encoding="utf-8")

    def test_the_app_takes_the_logo_from_the_brand_module(self):
        self.assertIn("from core.brand import", self.APP)
        self.assertIn("lockup_html", self.APP)

    def test_no_asset_path_is_spelled_out_in_the_app(self):
        """
        One place resolves paths, so one place has to change. Prose in a
        docstring may name the folder; a string literal naming a file is the
        thing that goes stale.
        """
        for quote in ('"', "'"):
            self.assertNotIn(f".png{quote}", self.APP)
            self.assertNotIn(f"{quote}assets", self.APP)

    def test_the_tab_icon_is_wired_up(self):
        self.assertIn("page_icon=page_icon()", self.APP)

    def test_the_header_does_not_repeat_the_name_beside_the_logo(self):
        """The artwork already contains it, in both scripts."""
        self.assertNotIn("sahulat-logo-name", self.APP)
        self.assertNotIn("sahulat-logo-name", self.COMPONENTS)

    def test_the_footer_uses_the_symbol_not_the_lockup(self):
        """The footer is a dark surface; the navy wordmark disappears there."""
        footer = self.APP.split("def render_footer")[1].split("def render_home")[0]
        self.assertIn("symbol_html", footer)
        self.assertNotIn("lockup_html", footer)

    def test_the_reveal_plays_once_per_session(self):
        self.assertIn('logo_mark(animate=should_animate("logo"))', self.APP)
        self.assertIn("is-new", self.APP)

    def test_reduced_motion_leaves_the_logo_present(self):
        block = self.ANIMATIONS.split("prefers-reduced-motion")[1]
        self.assertIn(".sahulat-logo.is-new", block)
        self.assertIn("opacity: 1 !important", block)

    def test_nothing_still_refers_to_the_placeholder_mark(self):
        for stale in ("mark_svg", "sa-logo-path", "sahulat-logo-mark",
                      "sahulat-favicon.svg"):
            with self.subTest(stale):
                self.assertNotIn(stale, self.APP)
                self.assertNotIn(stale, self.COMPONENTS)
                self.assertNotIn(stale, self.ANIMATIONS)


if __name__ == "__main__":
    unittest.main()

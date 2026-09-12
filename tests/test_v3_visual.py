"""
V3 visual-design spec: the structural changes, tested through the real app.

Three of the spec's items are architectural rather than cosmetic, which means
they can regress silently and a stylesheet cannot catch them:

  45.3  tabs were the product architecture. Three screens with different jobs
        rendered as three panels of one page, and every rerun built all three.
  20    "The eligibility result should not be buried inside an expander."
  13.2  the hero should demonstrate the product rather than decorate it.

The hero is the one with a trap in it. A hand-written example card would
satisfy the spec and be the only fabricated thing on the landing page of a
product whose argument is that it does not fabricate. So the preview is
asserted to match a record that is actually in the catalogue.
"""
from __future__ import annotations

import io
import os
import re
import unittest

from streamlit.testing.v1 import AppTest

from core.data_loader import KNOWN_CATEGORIES, load_all_opportunities
from core.i18n import LANGUAGES, t
from core.models import sample_profile
from core.rules_engine import evaluate_all, top_matches

import app as app_module
from tests.test_app_ui import APP, at_results, launch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _expected_rotation():
    """The best real match in each category - what the hero should cycle."""
    results = evaluate_all(sample_profile(), load_all_opportunities())
    picks = []
    for category in KNOWN_CATEGORIES:
        best = top_matches([r for r in results
                            if r.opportunity.category == category], limit=1)
        if best:
            picks.append(best[0])
    return picks


class TestScreensNotTabs(unittest.TestCase):
    """Spec 45.3: page-like stateful views, not a tab strip."""

    def test_no_top_level_tabs(self):
        app = launch()
        self.assertEqual(len(app.tabs), 0,
                         "the landing screen still renders a tab strip")

    def test_each_section_has_a_nav_control(self):
        app = launch()
        keys = {b.key for b in app.button if b.key}
        for section in ("discover", "read", "how"):
            self.assertIn(f"section_{section}", keys)

    def test_navigation_switches_the_screen(self):
        for section in ("read", "how", "discover"):
            app = launch()
            app.button(key=f"section_{section}").click().run()
            self.assertFalse(app.exception, f"{section}: {app.exception}")
            self.assertEqual(app.session_state["section"], section)

    def test_only_one_screen_renders_at_a_time(self):
        """
        The point of dropping tabs. A tab strip renders every panel and hides
        the inactive ones, so the uploader existed on the landing page and the
        pipeline was built on every rerun whether or not anyone looked at it.
        """
        discover = launch()
        self.assertEqual(len(discover.get("file_uploader")), 0,
                         "the Lens uploader is present on the Discover screen")

        read = launch()
        read.button(key="section_read").click().run()
        self.assertGreater(len(read.get("file_uploader")), 0,
                           "the Lens uploader is missing from its own screen")

    def test_starting_a_journey_carries_the_section(self):
        """
        A deep link into the wizard from another screen has to bring the user
        back to Discover, or they land on a step that is not rendered.
        """
        app = launch()
        app.button(key="section_how").click().run()
        app.button(key="header_restart").click().run()
        self.assertEqual(app.session_state["section"], "discover")
        self.assertFalse(app.exception)

    def test_the_lens_card_navigates_instead_of_naming_a_tab(self):
        app = launch()
        button = [b for b in app.button if b.key == "path_check_ad"]
        self.assertTrue(button, "the Lens card has no action")
        button[0].click().run()
        self.assertEqual(app.session_state["section"], "read")

    def test_no_copy_tells_the_user_to_use_a_tab(self):
        """There are no tabs to point at any more, in any language."""
        for lang in LANGUAGES:
            for key in ("home_upload_hint", "path_check_ad_body"):
                self.assertNotIn("tab", t(key, lang).lower(),
                                 f"{key} ({lang}) still names a tab")


class TestFeaturedMatch(unittest.TestCase):
    """Spec 18.2 / 20: the top match is the decision, not a row in a list."""

    @classmethod
    def setUpClass(cls):
        cls.app = at_results()
        cls.body = " ".join(str(m.value) for m in cls.app.markdown)

    def test_exactly_one_match_is_featured(self):
        # Match the markup, not the stylesheet - the injected CSS names the
        # class too, and counting raw text would find it there as well.
        self.assertEqual(self.body.count('class="sa-featured-marker"'), 1)

    def test_the_featured_scorecard_is_not_behind_a_control(self):
        """
        Spec 20 verbatim: "The eligibility result should not be buried inside
        an expander." One card fewer than the number of results carries a
        disclosure, and the missing one is the featured match.
        """
        cards = self.body.count('class="sa-result-title"')
        disclosures = sum(1 for e in self.app.expander
                          if e.label == t("view_eligibility", "en"))
        self.assertEqual(disclosures, cards - 1,
                         "the featured match still hides its verdict")

    def test_the_verdict_is_visible_on_arrival(self):
        self.assertIn("sa-score-seg", self.body)
        self.assertIn(t("scorecard_heading", "en"), self.body)

    def test_supporting_detail_stays_grouped(self):
        """
        Documents, source and help are reference material consulted one at a
        time, which is what a tab is for. The verdict was not, which is why it
        is no longer one of them.
        """
        labels = {tab.label for tab in self.app.tabs}
        for key in ("tab_documents", "tab_source", "tab_ask"):
            self.assertIn(t(key, "en"), labels)
        self.assertNotIn(t("tab_eligibility", "en"), labels,
                         "eligibility is still a tab beside the reference material")


class TestHeroDemonstratesTheProduct(unittest.TestCase):
    """Spec 13.2, and the honesty constraint it creates."""

    @classmethod
    def setUpClass(cls):
        cls.app = launch()
        cls.body = " ".join(str(m.value) for m in cls.app.markdown)

    def test_the_hero_shows_a_product_preview(self):
        self.assertIn('class="sa-preview"', self.body)
        for part in ("sa-preview-title", "sa-preview-count",
                     "sa-preview-row", "sa-preview-next"):
            self.assertIn(part, self.body, f"the preview has no {part}")

    def test_every_card_is_a_real_record_not_a_mockup(self):
        """
        The load-bearing assertion in this file.

        A fabricated example card would satisfy the spec and quietly contradict
        the product. Every title in the rotation must belong to something
        actually in the catalogue, and must be the match the engine ranks first
        within its own category for the demo profile.
        """
        titles = re.findall(r'sa-preview-title">([^<]+)<', self.body)
        self.assertTrue(titles, "no preview titles rendered")

        catalogue = {o.display_name("en") for o in load_all_opportunities()}
        for title in titles:
            self.assertIn(title, catalogue,
                          f"the hero shows {title!r}, which is not in the catalogue")

        expected = [m.opportunity.display_name("en") for m in _expected_rotation()]
        self.assertEqual(titles, expected,
                         "the hero is not showing the engine's own per-category winners")

    def test_the_preview_counts_agree_with_the_engine(self):
        for match in _expected_rotation():
            score = match.scorecard()
            self.assertIn(t("scorecard_summary", "en",
                            met=score["met"], total=score["total"]),
                          self.body,
                          f"{match.opportunity.opportunity_id} shows a count the "
                          f"engine did not produce")

    def test_the_preview_says_it_is_real(self):
        captions = " ".join(str(c.value) for c in self.app.caption)
        self.assertIn(t("hero_preview_note", "en"), captions)

    def test_the_preview_has_no_deadline_row(self):
        """
        The deadline is a property of the listing, and rendering it as "your
        information: today's date" reads as nonsense at preview size. It has
        its own line.
        """
        from core.i18n import check_title
        from core.models import CHECK_DEADLINE, ConditionCheck, UNKNOWN

        deadline_title = check_title(ConditionCheck(CHECK_DEADLINE, UNKNOWN), "en")
        rows = re.findall(r'sa-preview-req">([^<]+)<', self.body)
        self.assertTrue(rows, "the preview has no condition rows")
        self.assertNotIn(deadline_title, rows)

    def test_the_preview_renders_in_every_language(self):
        for lang in LANGUAGES:
            app = AppTest.from_file(APP, default_timeout=180)
            app.session_state["language"] = lang
            app.run()
            body = " ".join(str(m.value) for m in app.markdown)
            self.assertFalse(app.exception, f"{lang}: {app.exception}")
            self.assertIn('class="sa-preview"', body, lang)
            self.assertIn(t("hero_preview_alt", lang), body, lang)


class TestHeroRotation(unittest.TestCase):
    """
    The hero cycles through one real result per category.

    This is a deliberate exception to the spec's own §40.5 ("avoid
    continuously moving hero graphics") made at the owner's request, so the
    safeguards around it are the part worth testing: no timer, no rerun, no
    JavaScript, and a hard stop under reduced motion.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = launch()
        cls.body = " ".join(str(m.value) for m in cls.app.markdown)
        cls.css = io.open(os.path.join(ROOT, "styles", "animations.css"),
                          encoding="utf-8").read()

    def test_one_card_per_category_that_has_records(self):
        slides = self.body.count('class="sa-preview-slide"')
        self.assertEqual(slides, len(_expected_rotation()))
        self.assertGreater(slides, 1, "nothing to rotate through")

    def test_the_rotation_covers_every_category(self):
        """
        The engine's overall top six for the demo profile is five NAVTTC
        courses. Rotating through those would be accurate and would imply the
        catalogue holds nothing but courses.
        """
        shown = {m.opportunity.category for m in _expected_rotation()}
        self.assertEqual(shown, set(KNOWN_CATEGORIES))

    def test_cards_are_staggered_not_stacked_on_one_beat(self):
        delays = sorted({float(d) for d in
                         re.findall(r'animation-delay:([\d.]+)s', self.body)})
        expected = [i * app_module.PREVIEW_SECONDS_PER_CARD
                    for i in range(len(_expected_rotation()))]
        self.assertEqual(delays, expected)

    def test_a_dot_for_every_card(self):
        self.assertEqual(self.body.count('<i style="animation-delay:'),
                         self.body.count('class="sa-preview-slide"'))

    def test_the_cycle_is_slow_enough_to_read(self):
        """
        The hero is read, not watched. A card has to stay long enough to take
        in a title, a condition count and a next step.
        """
        self.assertGreaterEqual(app_module.PREVIEW_SECONDS_PER_CARD, 3.0)

    def test_keyframes_are_generated_for_the_real_card_count(self):
        css = app_module.preview_cycle_css(4, 4.0)
        self.assertIn("@keyframes sa-preview-cycle", css)
        self.assertIn("25.00%", css, "four cards should each hold a quarter of the cycle")
        self.assertIn("16.0s", css, "four cards at four seconds is a sixteen second cycle")

    def test_a_single_card_does_not_rotate(self):
        """One record in the catalogue is a still hero, not a loop of one."""
        self.assertEqual(app_module.preview_cycle_css(1, 4.0), "")

    def test_nothing_reruns_or_sleeps_to_drive_the_rotation(self):
        """
        A rerun every four seconds would re-screen the catalogue and reset
        every widget on the page. CSS moves the cards; Python renders them once.
        """
        source = io.open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
        for banned in ("time.sleep", "st_autorefresh", "setInterval", "setTimeout"):
            self.assertNotIn(banned, source, f"{banned} is driving the hero")

    def test_reduced_motion_leaves_a_card_on_screen(self):
        """
        The safeguard that actually matters.

        The blanket reduced-motion rule sets every animation to 1ms and one
        iteration, which would park each card on its final keyframe - and that
        keyframe is opacity 0. Without an explicit override the hero would go
        BLANK, not merely still, for exactly the users who asked for less
        movement.
        """
        block = self.css[self.css.index("prefers-reduced-motion"):]
        self.assertIn(".sa-preview-slide", block)
        self.assertIn("opacity: 1 !important", block)
        self.assertIn("animation: none !important", block)
        self.assertIn(":not(:first-child) { display: none; }", block)
        self.assertIn(".sa-preview-dots { display: none !important; }", block)


class TestLanguagePicker(unittest.TestCase):
    """
    Language moved into the brand bar as one dropdown.

    Three always-visible buttons took three of the eight slots on the row that
    carries the navigation, for a setting most people touch once. The property
    that made them worth having is the one these tests protect: every option is
    written in its own script, so a reader who cannot read the other two can
    still recognise theirs.
    """

    def test_the_picker_is_in_the_brand_bar(self):
        app = launch()
        pickers = [s for s in app.selectbox if s.key == "lang_picker"]
        self.assertTrue(pickers, "no language picker")
        body = " ".join(str(m.value) for m in app.markdown)
        self.assertIn('class="sa-brandbar"', body)

    def test_every_language_is_offered(self):
        app = launch()
        picker = app.selectbox(key="lang_picker")
        self.assertEqual(len(picker.options), len(LANGUAGES))

    def test_each_option_is_written_in_its_own_script(self):
        """
        The reason the buttons were always visible. In a menu it survives
        through the labels themselves: someone who reads only Urdu opens the
        picker and sees اردو, not "Urdu".
        """
        from core.i18n import LANGUAGE_NAMES
        app = launch()
        options = app.selectbox(key="lang_picker").options
        self.assertIn(LANGUAGE_NAMES["ur"], options)
        self.assertNotEqual(LANGUAGE_NAMES["ur"], "Urdu",
                            "the Urdu option is labelled in English")

    def test_choosing_a_language_changes_the_page(self):
        for code in LANGUAGES:
            app = launch()
            app.selectbox(key="lang_picker").set_value(code).run()
            self.assertFalse(app.exception, f"{code}: {app.exception}")
            self.assertEqual(app.session_state["language"], code)
            label = [b.label for b in app.button if b.key == "section_discover"]
            self.assertEqual(label, [t("nav_discover", code)],
                             f"{code}: the page did not follow the picker")

    def test_the_nav_row_no_longer_carries_language_buttons(self):
        app = launch()
        keys = {b.key for b in app.button if b.key}
        for code in LANGUAGES:
            self.assertNotIn(f"lang_{code}", keys,
                             "a language button is back on the navigation row")

    def test_the_nav_row_is_screens_and_one_action(self):
        app = launch()
        keys = [b.key for b in app.button
                if b.key and (b.key.startswith("section_") or b.key.startswith("header_"))]
        self.assertEqual(sorted(keys),
                         ["header_cta", "section_discover", "section_how", "section_read"])

    def test_the_bar_is_styled_by_what_it_contains(self):
        """
        `:has(.sa-brandbar)` rather than a positional selector. Streamlit
        rearranging its wrappers would silently unstyle a header matched by
        position, and an unstyled header looks like a rendering bug.
        """
        css = io.open(os.path.join(ROOT, "styles", "components.css"),
                      encoding="utf-8").read()
        self.assertIn(':has(.sa-brandbar)', css)

    def test_the_picker_survives_a_language_the_app_does_not_know(self):
        """
        Stale session state must not crash the header - it is the first thing
        rendered, so an exception there takes the whole page with it.
        """
        app = AppTest.from_file(APP, default_timeout=180)
        app.session_state["language"] = "fr"
        app.run()
        self.assertFalse(app.exception, str(app.exception))


if __name__ == "__main__":
    unittest.main()

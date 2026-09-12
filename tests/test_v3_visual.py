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

import re
import unittest

from streamlit.testing.v1 import AppTest

from core.data_loader import load_all_opportunities
from core.i18n import LANGUAGES, t
from core.models import sample_profile
from core.rules_engine import evaluate_all, top_matches

from tests.test_app_ui import APP, at_results, launch


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

    def test_the_preview_is_a_real_record_not_a_mockup(self):
        """
        The load-bearing assertion in this file.

        A fabricated example card would satisfy the spec and quietly contradict
        the product. The title in the hero must belong to something actually in
        the catalogue, and must be the match the engine actually ranks first
        for the demo profile.
        """
        shown = re.search(r'sa-preview-title">([^<]+)<', self.body)
        self.assertIsNotNone(shown, "no preview title rendered")
        title = shown.group(1)

        catalogue = {o.display_name("en") for o in load_all_opportunities()}
        self.assertIn(title, catalogue,
                      "the hero shows an opportunity that is not in the catalogue")

        ranked = top_matches(evaluate_all(sample_profile(), load_all_opportunities()),
                             limit=1)
        self.assertEqual(title, ranked[0].opportunity.display_name("en"),
                         "the hero is not showing the engine's actual top match")

    def test_the_preview_counts_agree_with_the_engine(self):
        ranked = top_matches(evaluate_all(sample_profile(), load_all_opportunities()),
                             limit=1)
        score = ranked[0].scorecard()
        self.assertIn(t("scorecard_summary", "en",
                        met=score["met"], total=score["total"]),
                      self.body)

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


if __name__ == "__main__":
    unittest.main()

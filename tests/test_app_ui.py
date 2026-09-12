"""
UI regression tests driven through Streamlit's own AppTest harness.

These are slower than the pure-logic tests (each `run()` executes the whole
script), so this file stays deliberately small: it covers behaviour that only
appears once widgets, reruns and render order are involved, and which unit
tests over `core/` therefore cannot catch.
"""
import os
import re
import unittest
from unittest import mock

from streamlit.testing.v1 import AppTest

from core.data_loader import (KNOWN_CATEGORIES, category_counts,
                              load_all_opportunities)
from core.i18n import t

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def launch() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=180)
    app.run()
    return app


def at_results() -> AppTest:
    """Home -> sample profile -> results, in one step."""
    app = launch()
    app.button(key="cta_sample").click().run()
    return app


class TestNoFormSubmitsOnEnter(unittest.TestCase):
    """UX-01: st.form submits on Enter, which is why the wizard uses none."""

    def test_app_renders_no_forms(self):
        self.assertEqual(len(launch().get("form")), 0)

    def test_required_fields_block_progress(self):
        app = launch()
        app.button(key="cta_start").click().run()
        app.button(key="next_0").click().run()      # categories default to selected
        app.button(key="next_1").click().run()      # nothing answered yet
        self.assertEqual(app.session_state["step"], 1)
        self.assertEqual(app.session_state["step_errors"],
                         {"age": "required", "domicile_province": "required"})


class TestDocumentChecklistStaysInSync(unittest.TestCase):
    """
    UX-07 — the reported bug.

    The count and progress bar were written before the checkboxes were read, so
    they rendered the previous run's state: ticking the last box left the bar
    short, and unticking one left it full.
    """

    def setUp(self):
        self.app = at_results()
        keys = [c.key for c in self.app.checkbox
                if c.key and c.key.startswith("doc_")]
        self.assertTrue(keys, "expected a document checklist on the results page")
        prefix = keys[0].rsplit("_", 1)[0]
        self.keys = [k for k in keys if k.startswith(prefix)]
        self.total = len(self.keys)

    def shown(self):
        """
        The count as the page states it.

        P1-1 moved this into the readiness header; the behaviour under test is
        unchanged, so the assertion is not relaxed - it just reads the number
        from where the number now lives. Also picks up the readiness percent so
        a test can check the two never disagree.
        """
        for block in self.app.markdown:
            match = re.search(r'sa-ready-count">(\d+) of (\d+) ready<', str(block.value))
            if match:
                return int(match.group(1)), int(match.group(2))
        return None

    def shown_percent(self):
        for block in self.app.markdown:
            match = re.search(r'sa-ready-num">(\d+)% ready<', str(block.value))
            if match:
                return int(match.group(1))
        return None

    def actual(self):
        return sum(1 for k in self.keys if self.app.checkbox(key=k).value)

    def assert_in_sync(self, label):
        self.assertEqual(self.shown(), (self.actual(), self.total), label)

    def test_starts_at_zero(self):
        self.assert_in_sync("initial render")

    def test_every_tick_updates_immediately(self):
        for index, key in enumerate(self.keys, 1):
            self.app.checkbox(key=key).check().run()
            self.assert_in_sync(f"after ticking {index}")

    def test_all_ticked_reads_full(self):
        """The exact reported failure: all boxes ticked, bar not complete."""
        for key in self.keys:
            self.app.checkbox(key=key).check().run()
        self.assertEqual(self.shown(), (self.total, self.total))

    def test_unticking_updates_immediately(self):
        for key in self.keys:
            self.app.checkbox(key=key).check().run()
        for index, key in enumerate(self.keys, 1):
            self.app.checkbox(key=key).uncheck().run()
            self.assert_in_sync(f"after unticking {index}")


class TestReadinessPercent(unittest.TestCase):
    """
    P1-1: the readiness figure is a count of the checklist, so it must track
    the boxes exactly - including never reading 100% while something is left.
    """

    def setUp(self):
        self.app = at_results()
        keys = [c.key for c in self.app.checkbox
                if c.key and c.key.startswith("doc_")]
        prefix = keys[0].rsplit("_", 1)[0]
        self.keys = [k for k in keys if k.startswith(prefix)]

    def percent(self):
        for block in self.app.markdown:
            match = re.search(r'sa-ready-num">(\d+)% ready<', str(block.value))
            if match:
                return int(match.group(1))
        return None

    def test_starts_at_zero(self):
        self.assertEqual(self.percent(), 0)

    def test_never_reads_full_while_something_is_missing(self):
        for key in self.keys[:-1]:
            self.app.checkbox(key=key).check().run()
        self.assertLess(self.percent(), 100)

    def test_reads_full_only_when_everything_is_ticked(self):
        for key in self.keys:
            self.app.checkbox(key=key).check().run()
        self.assertEqual(self.percent(), 100)

    def test_next_step_follows_the_checklist(self):
        """
        P1-1 connects the checklist to the next action: once some documents
        are gathered, "prepare your documents" is no longer the useful step.
        """
        body = " ".join(str(m.value) for m in self.app.markdown)
        self.assertIn("Prepare the", body)
        self.app.checkbox(key=self.keys[0]).check().run()
        body = " ".join(str(m.value) for m in self.app.markdown)
        self.assertIn("Obtain the next document", body)


class TestMotionDoesNotReplay(unittest.TestCase):
    """
    Spec 17.2: a reveal must fire on a real state change, not on every rerun.
    Streamlit re-executes the script on every interaction, so an ungated CSS
    entrance animation would replay whenever a checkbox was ticked.
    """

    def _reveal_count(self, app):
        """
        Count real uses of the reveal class in markup.

        Matching the bare name would also hit the `.sahulat-reveal` rule inside
        the injected stylesheet, which is present on every run.
        """
        return sum(str(m.value).count('class="sahulat-reveal')
                   for m in app.markdown)

    def test_reveal_classes_are_emitted_once(self):
        app = at_results()
        self.assertGreater(self._reveal_count(app), 0,
                           "results should animate in on first render")
        app.run()
        self.assertEqual(self._reveal_count(app), 0,
                         "animation must not replay on an unrelated rerun")

    def test_new_result_set_animates_again(self):
        app = at_results()
        app.run()
        self.assertEqual(self._reveal_count(app), 0)
        app.button(key="restart").click().run()          # back home
        app.button(key="cta_sample").click().run()       # new result set
        self.assertGreater(self._reveal_count(app), 0)


class TestFieldsAndState(unittest.TestCase):

    def test_gender_uses_a_segmented_control(self):
        """Spec 9.4: clearly separated tappable options, not a dropdown."""
        app = launch()
        app.button(key="cta_start").click().run()
        app.button(key="next_0").click().run()
        self.assertTrue(any(c.key == "w_gender_1"
                            for c in app.segmented_control))

    def test_answers_survive_reruns(self):
        """Spec 17.4: a value must never appear to reset when it has not."""
        app = launch()
        app.button(key="cta_start").click().run()
        app.button(key="next_0").click().run()
        app.number_input(key="w_age_1").set_value(24).run()
        app.selectbox(key="w_domicile_province_1").set_value("Punjab").run()
        for _ in range(3):
            app.run()
        self.assertEqual(app.session_state["answers"]["age"], 24)
        self.assertEqual(app.session_state["answers"]["domicile_province"], "Punjab")

    def test_stylesheet_never_overrides_icon_fonts(self):
        """UX-04: the regression that printed a ligature name as text."""
        css = " ".join(str(m.value) for m in launch().markdown)
        self.assertIn("Material Symbols Rounded", css)
        self.assertNotIn('[class*="st-"] {', css)

    def test_input_instructions_are_hidden(self):
        """UX-05: 'Press Enter to apply' advertised behaviour we removed."""
        css = " ".join(str(m.value) for m in launch().markdown)
        self.assertIn("InputInstructions", css)


UPLOAD_FIXTURE = {
    "name": "Overseas Scholarship for MS/M.Phil leading to Ph.D. (Phase III)",
    "category": "scholarship",
    "provider": "Higher Education Commission (HEC) Pakistan",
    "summary_en": "Overseas scholarships at Top 200 ranked universities.",
    "eligibility_conditions": {
        "max_age": 40,
        "min_education_level": "bachelor",
        "min_marks_percentage": 60,
        "must_not_have_existing_scholarship": True,
        "special_quota_note": "Preference for under-represented districts.",
        "application_deadline": "2026-11-30",
    },
    "required_documents": ["CNIC", "Degree transcripts"],
    "application_steps": ["Register on the portal", "Submit before the deadline"],
    "official_url_if_visible": "https://hec.gov.pk/",
    "extraction_confidence": "high",
}


def bare_app():
    """
    Import app.py as a module to reach its pure helpers.

    Streamlit calls become no-ops without a runtime, which is exactly what we
    want: these tests are about the markup and the call order, not rendering.
    """
    import warnings
    warnings.filterwarnings("ignore")
    import app
    return app


class TestStagePanel(unittest.TestCase):
    """
    UX-10: the staged panel must describe work that has actually happened.
    """

    LABELS = ["Preparing", "Reading", "Structuring", "Screening"]

    def states(self, html):
        return re.findall(r'<div class="sa-stage (is-[a-z]+)"', html)

    def test_exactly_one_stage_is_active(self):
        app = bare_app()
        for active in range(len(self.LABELS)):
            states = self.states(app.stage_markup(self.LABELS, active))
            self.assertEqual(states.count("is-active"), 1, f"active={active}")

    def test_earlier_stages_are_done_and_later_are_pending(self):
        app = bare_app()
        states = self.states(app.stage_markup(self.LABELS, 2))
        self.assertEqual(states, ["is-done", "is-done", "is-active", "is-pending"])

    def test_only_the_running_stage_shows_an_indicator(self):
        """A finished or unstarted step must not appear to still be working."""
        app = bare_app()
        html = app.stage_markup(self.LABELS, 1)
        self.assertEqual(html.count("sa-stage-track"), 1)

    def test_every_stage_is_visible_from_the_start(self):
        """
        Fast steps are never padded to look slow, so they stay readable only
        because the whole list is on screen throughout.
        """
        app = bare_app()
        html = app.stage_markup(self.LABELS, 0)
        for label in self.LABELS:
            self.assertIn(label, html)

    def test_no_percentage_is_ever_claimed(self):
        app = bare_app()
        html = app.stage_markup(self.LABELS, 1)
        self.assertNotIn("%", html)


class TestStagesAdvanceOnRealBoundaries(unittest.TestCase):
    """
    The panel must move because work finished, not because time passed.
    """

    def test_stage_order_brackets_the_real_calls(self):
        app = bare_app()
        log = []

        def fake_stage_markup(labels, active, note=""):
            log.append(("show", active))
            return ""

        def fake_extract(file_bytes, mime_type, language="en"):
            log.append(("model_call", None))
            return dict(UPLOAD_FIXTURE)

        with mock.patch.object(app, "stage_markup", fake_stage_markup), \
                mock.patch.object(app, "extract_raw", fake_extract):
            opportunity, raw, _ = app.read_ad_in_stages(b"x" * 2048, "image/png", False)

        self.assertEqual(log, [("show", 0), ("show", 1), ("model_call", None), ("show", 2)],
                         "the reading stage must be shown BEFORE the model call and the "
                         "structuring stage only AFTER it returns")
        self.assertEqual(opportunity.source_type, "user_uploaded")

    def test_screening_stage_only_when_it_actually_runs(self):
        app = bare_app()
        shown = []

        with mock.patch.object(app, "stage_markup",
                               lambda labels, active, note="": shown.append(len(labels)) or ""), \
                mock.patch.object(app, "extract_raw", lambda *a, **k: dict(UPLOAD_FIXTURE)):
            app.read_ad_in_stages(b"x", "image/png", False)
        self.assertEqual(set(shown), {3}, "no screening stage without answers to screen")


class TestExtractionIsReadable(unittest.TestCase):
    """
    UX-10: the raw JSON dump was the first thing a user met. It is now one
    click away, and the conditions are rendered as prose.
    """

    def setUp(self):
        from core.ad_reader import build_record
        opportunity, raw = build_record(dict(UPLOAD_FIXTURE))
        self.app = AppTest.from_file(APP, default_timeout=180)
        self.app.session_state["uploaded_opportunity"] = opportunity
        self.app.session_state["uploaded_raw"] = raw
        # The Lens lives on its own screen now, so a test that seeds an upload
        # has to be standing on it - which is where a real user would be.
        self.app.session_state["section"] = "read"
        self.app.run()
        self.body = " ".join(str(m.value) for m in self.app.markdown)

    def test_page_renders(self):
        self.assertFalse(self.app.exception)

    def test_conditions_are_rendered_as_prose(self):
        rows = re.findall(r'sa-answer-label">([^<]+)</span>'
                          r'<span class="sa-answer-value">([^<]+)', self.body)
        rendered = {label: value for label, value in rows}
        self.assertIn("Age", rendered)
        self.assertEqual(rendered["Age"], "at most 40")
        self.assertEqual(rendered["Academic marks"], "at least 60%")

    def test_unstated_conditions_are_shown_with_the_caveat(self):
        """
        Silence in a document is not a qualification. The UI has to say so.
        """
        self.assertIn("sa-unstated", self.body)
        captions = " ".join(str(c.value) for c in self.app.caption)
        self.assertIn("not the same as qualifying", captions)

    def test_raw_json_is_behind_a_disclosure(self):
        labels = [e.label for e in self.app.expander]
        self.assertIn("Show exactly what the model returned", labels)


class TestV2ResultsPage(unittest.TestCase):
    """V2 P0-1/2/3/6 reaching the actual page, not just the core modules."""

    @classmethod
    def setUpClass(cls):
        cls.app = at_results()
        cls.body = " ".join(str(m.value) for m in cls.app.markdown)

    def test_page_renders(self):
        self.assertFalse(self.app.exception)

    def test_top_matches_shortlist_is_shown(self):
        self.assertIn("sa-top-name", self.body)
        self.assertIn("sa-top-reason", self.body)

    def test_scorecard_table_is_shown(self):
        self.assertIn("sa-scorecard", self.body)
        for column in ("Requirement", "Your information", "Result"):
            self.assertIn(column, self.body)

    def test_scorecard_rows_carry_a_result_pill(self):
        pills = re.findall(r'sa-pill (pill-[a-z]+)">([^<]+)<', self.body)
        self.assertTrue(pills)
        self.assertTrue(any(label == "Passed" for _, label in pills))

    def test_header_count_matches_the_rows_of_the_first_card(self):
        """
        The summary is a count of the rows below it. Rendering them from
        different places is how they would drift apart.
        """
        shown = re.search(r'sa-score-num">(\d+) of (\d+) stated conditions met', self.body)
        self.assertIsNotNone(shown)
        # Match the markup, not the stylesheet: the injected CSS contains
        # every one of these class names too.
        block = self.body[self.body.index('<div class="sa-scorecard">'):]
        first_table = block[:block.index("</table>")]
        passed = first_table.count('sa-pill pill-good')
        self.assertEqual(int(shown.group(1)), passed)

    def test_no_percentage_match_score_is_claimed(self):
        self.assertNotIn("% match", self.body)
        self.assertNotIn("match score", self.body.lower())

    def test_every_result_offers_a_next_step(self):
        cards = self.body.count('class="sa-result-title"')
        self.assertGreater(cards, 0)
        self.assertEqual(self.body.count('class="sa-next-label"'), cards)

    def test_architecture_statement_is_present(self):
        self.assertIn("AI does not decide your eligibility", self.body)


class TestCorrectingAMisreadExtraction(unittest.TestCase):
    """
    V2 P0-4: reading a photograph is unreliable, and whatever comes out of it
    is treated as fact by the rules engine. The correction path is what stops
    a misread number from silently becoming an eligibility verdict.
    """

    def setUp(self):
        from core.ad_reader import build_record
        # The poster says 60%. The model read 90%.
        self.record, raw = build_record({
            "name": "Test scholarship",
            "category": "scholarship",
            "eligibility_conditions": {"min_marks_percentage": 90,
                                       "min_age": 18, "max_age": 30},
            "extraction_confidence": "medium",
        })
        self.app = AppTest.from_file(APP, default_timeout=240)
        self.app.session_state["uploaded_opportunity"] = self.record
        self.app.session_state["uploaded_raw"] = raw
        # The Lens lives on its own screen now, so a test that seeds an upload
        # has to be standing on it - which is where a real user would be.
        self.app.session_state["section"] = "read"
        self.app.session_state["answers"] = {
            "age": 21, "domicile_province": "Punjab",
            "education_level": "intermediate", "marks_percentage": 72.0}
        self.app.session_state["screen_upload"] = True
        self.app.run()

    def test_correction_changes_the_verdict(self):
        self.assertEqual(self.app.session_state["upload_match"].overall_status,
                         "not_eligible")
        self.app.number_input(key="fix_marks").set_value(60.0).run()
        self.app.button(key="apply_fixes").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["upload_match"].overall_status,
                         "eligible")

    def test_correction_does_not_upgrade_trust(self):
        """
        A user fixing a typo has not verified the opportunity against the
        issuing authority. The record stays user_uploaded (Invariant 4).
        """
        self.app.number_input(key="fix_marks").set_value(60.0).run()
        self.app.button(key="apply_fixes").click().run()
        self.assertEqual(self.record.source_type, "user_uploaded")
        self.assertFalse(self.record.is_verified())

    def test_the_page_says_it_used_the_corrections(self):
        self.app.number_input(key="fix_marks").set_value(60.0).run()
        self.app.button(key="apply_fixes").click().run()
        body = " ".join(str(m.value) for m in self.app.markdown)
        self.assertIn("Screened against your corrections", body)


class TestV2Landing(unittest.TestCase):
    """V2 P0-8."""

    @classmethod
    def setUpClass(cls):
        cls.app = launch()
        cls.body = " ".join(str(m.value) for m in cls.app.markdown)

    def test_every_category_has_a_path_plus_the_lens(self):
        """
        One card per category and one for the Lens. Public assistance joined
        the row when its records landed: a category with data and no way in
        from the landing page is reachable only by someone who already knows
        to go looking for it.
        """
        for label in ("Find a scholarship", "Find a job", "Learn a skill",
                      "Find support", "Check an advertisement"):
            self.assertIn(label, self.body)

    def test_a_path_preselects_its_own_category(self):
        app = launch()
        app.button(key="path_assistance").click().run()
        # AppTest.exception is an (possibly empty) ElementList, never None.
        self.assertFalse(app.exception, [str(e.value) for e in app.exception])
        self.assertEqual(app.session_state["categories"], ["assistance"])

    def test_path_availability_follows_the_catalogue(self):
        """
        A path leads somewhere exactly when its category has records.

        This used to assert that the Jobs path was disabled, which was really
        an assertion about the data of the day rather than about the rule - it
        broke the moment the Jobs catalogue was curated. The rule is the
        relationship between the count and the button, so that is what is
        tested, and it holds whichever categories happen to be filled.
        """
        counts = category_counts(load_all_opportunities())
        for category in KNOWN_CATEGORIES:
            button = [b for b in self.app.button if b.key == f"path_{category}"]
            self.assertTrue(button, f"no landing path rendered for {category}")
            self.assertEqual(
                button[0].disabled, counts[category] == 0,
                f"{category} has {counts[category]} records but disabled="
                f"{button[0].disabled}",
            )

    def test_every_category_is_shown_with_its_real_count(self):
        """
        DATA-03, restated now that no category is empty.

        The original rule was that a category with nothing in it says so
        rather than vanishing, and it was tested against Public Assistance
        because that was the empty one. Filling it (DATA-07) left nothing
        empty, so the assertion is now the general form: every known category
        appears by name, and one that has records advertises the count rather
        than "Coming soon". The count-to-label mapping is the rule; which
        categories happen to be full is data.
        """
        counts = category_counts(load_all_opportunities())
        for category in KNOWN_CATEGORIES:
            self.assertIn(t(f"category_{category}", "en"), self.body,
                          f"{category} is not shown on the landing page")
            if counts[category]:
                self.assertIn(t("available_count", "en", n=counts[category]), self.body,
                              f"{category} has {counts[category]} records but does not "
                              f"advertise them")

    def test_nothing_is_labelled_coming_soon_while_every_category_has_records(self):
        counts = category_counts(load_all_opportunities())
        self.assertTrue(all(counts[c] for c in KNOWN_CATEGORIES),
                        "a category is empty again - restore the 'Coming soon' assertion")
        self.assertNotIn(t("coming_soon", "en"), self.body)

    def test_benefits_row_is_present(self):
        self.assertIn("sa-benefit", self.body)


if __name__ == "__main__":
    unittest.main()

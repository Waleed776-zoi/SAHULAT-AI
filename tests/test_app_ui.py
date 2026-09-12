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
        for caption in self.app.caption:
            match = re.match(r"^(\d+) of (\d+) ready$", str(caption.value).strip())
            if match:
                return int(match.group(1)), int(match.group(2))
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


if __name__ == "__main__":
    unittest.main()

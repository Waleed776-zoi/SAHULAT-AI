"""
Staged progress on the AI calls.

The Lens already showed real stages. The four other places that call a model
showed `st.spinner("")` - a bare grey ring with no text, which told the user
nothing while they waited several seconds for a remote call.

The constraint these tests exist to hold is the same one the Lens work
established: the panel advances because work finished, not because time
passed. There is no timer in the implementation and there must never be one,
so the tests check call ORDER rather than appearance.
"""
from __future__ import annotations

import io
import os
import unittest
from unittest import mock

from core.i18n import LANGUAGES, t

from tests.test_app_ui import bare_app

APP_SOURCE = io.open(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"),
    encoding="utf-8").read()

ASK_LABELS = ("stage_ask_understand", "stage_ask_search",
              "stage_ask_gather", "stage_ask_write")
EXPLAIN_LABELS = ("stage_explain_profile", "stage_explain_decision",
                  "stage_explain_write")
SIMPLIFY_LABELS = ("stage_simplify_read", "stage_simplify_write")
ALL_LABELS = ASK_LABELS + EXPLAIN_LABELS + SIMPLIFY_LABELS


class TestNoBareSpinnersRemain(unittest.TestCase):
    """The regression this work exists to prevent."""

    def test_no_empty_spinner_anywhere(self):
        """
        `st.spinner("")` is a grey ring with no words. Every long call in this
        app talks to a remote model and can take several seconds; a user
        staring at an unlabelled ring cannot tell progress from a hang.
        """
        self.assertNotIn('st.spinner("")', APP_SOURCE,
                         "a bare, wordless spinner is back")

    def test_every_model_call_site_is_staged(self):
        for name in ("answer_followup", "explain_match", "simplify_opportunity"):
            self.assertIn(name, APP_SOURCE)
        self.assertGreaterEqual(APP_SOURCE.count("ai_stages("), 4,
                                "a model call lost its progress panel")


class TestStagesAdvanceOnRealBoundaries(unittest.TestCase):
    """
    The panel is repainted only where real work has genuinely finished.
    """

    def _log_of(self, labels, work):
        """Run `work` against a Stages panel, recording every repaint."""
        app = bare_app()
        log = []

        def fake_markup(labels_, active, note=""):
            log.append(("show", active))
            return ""

        with mock.patch.object(app, "stage_markup", fake_markup):
            with app.Stages(labels) as stages:
                work(stages, log)
        return log

    def test_a_step_is_shown_before_its_work_not_after(self):
        """
        The label has to be on screen while the thing it describes is running.
        Painting it afterwards would describe the past and leave the slow step
        unlabelled - which is the failure mode of a spinner.
        """
        def work(stages, log):
            log.append(("retrieve", None))
            stages.advance()
            log.append(("model_call", None))

        self.assertEqual(
            self._log_of(["a", "b"], work),
            [("show", 0), ("retrieve", None), ("show", 1), ("model_call", None)])

    def test_advance_never_runs_past_the_last_label(self):
        """
        An over-advance would mark every stage done while the model is still
        working - the panel claiming a finished answer that does not exist.
        """
        def work(stages, log):
            for _ in range(6):
                stages.advance()

        shown = [active for kind, active in self._log_of(["a", "b", "c"], work)
                 if kind == "show"]
        self.assertEqual(max(shown), 2, "the panel advanced past its last stage")

    def test_the_panel_is_cleared_even_when_the_call_fails(self):
        """
        A model call that raises must not leave a half-finished progress panel
        frozen on the page pretending to still be working.
        """
        app = bare_app()
        cleared = []

        class FakeSlot:
            def markdown(self, *a, **k):
                pass

            def empty(self):
                cleared.append(True)

        with mock.patch.object(app.st, "empty", lambda: FakeSlot()):
            with self.assertRaises(RuntimeError):
                with app.Stages(["a", "b"]):
                    raise RuntimeError("the model fell over")
        self.assertTrue(cleared, "the progress panel outlived the failure")

    def test_empty_labels_are_dropped_not_rendered_blank(self):
        app = bare_app()
        with mock.patch.object(app, "stage_markup", lambda l, a, note="": ""):
            with app.Stages(["a", "", None, "b"]) as stages:
                self.assertEqual(stages.labels, ["a", "b"])


class TestStageLabelsAreReal(unittest.TestCase):
    """Every label must exist, in every language, and describe real work."""

    def test_every_label_resolves_in_every_language(self):
        for key in ALL_LABELS:
            for lang in LANGUAGES:
                text = t(key, lang)
                self.assertTrue(text.strip(), f"{key} ({lang}) is empty")
                self.assertNotEqual(text, key,
                                    f"{key} ({lang}) fell through to its own key")

    def test_urdu_is_not_an_english_fallback(self):
        for key in ALL_LABELS:
            self.assertNotEqual(t(key, "ur"), t(key, "en"), key)
            self.assertNotEqual(t(key, "ur_roman"), t(key, "en"), key)

    def test_the_ask_flow_has_the_four_the_user_asked_for(self):
        self.assertEqual(len(ASK_LABELS), 4)
        for key in ASK_LABELS:
            self.assertIn(key, APP_SOURCE, f"{key} is defined but never shown")

    def test_no_label_claims_a_percentage_or_a_time(self):
        """
        A progress panel driven by real boundaries cannot know how far along
        it is or how long is left. Saying so would be fabricated progress.
        """
        for key in ALL_LABELS:
            for lang in LANGUAGES:
                text = t(key, lang)
                self.assertNotIn("%", text, f"{key} ({lang})")
                for word in ("second", "minute", "almost", "nearly"):
                    self.assertNotIn(word, text.lower(), f"{key} ({lang})")

    def test_there_is_no_timer_behind_the_panel(self):
        """
        The whole design. If a sleep or a timer ever appears near the staging
        code, the panel has stopped reporting work and started performing it.
        """
        for banned in ("time.sleep", "asyncio.sleep", "threading.Timer"):
            self.assertNotIn(banned, APP_SOURCE,
                             f"{banned} would make the panel fabricate progress")


class TestStageMarkupStates(unittest.TestCase):
    """The rendered panel: done behind, running now, blurred ahead."""

    LABELS = ["one", "two", "three", "four"]

    def test_pending_stages_are_present_but_dimmed(self):
        """
        Every label is on screen from the start, blurred and dimmed, so the
        reader watches a list resolve instead of labels flashing past. That is
        what makes an instant step readable without padding it.
        """
        app = bare_app()
        html = app.stage_markup(self.LABELS, 1)
        for label in self.LABELS:
            self.assertIn(label, html)
        self.assertEqual(html.count("is-done"), 1)
        self.assertEqual(html.count("is-active"), 1)
        self.assertEqual(html.count("is-pending"), 2)

    def test_the_first_paint_claims_nothing_finished(self):
        app = bare_app()
        html = app.stage_markup(self.LABELS, 0)
        self.assertEqual(html.count("is-done"), 0,
                         "the panel claims completed work before any ran")

    def test_the_ai_note_does_not_borrow_the_upload_promise(self):
        """
        The upload panel says "your file is not stored". There is no file in a
        follow-up question, and reusing that line would make a promise about
        something that never existed.
        """
        for lang in LANGUAGES:
            note = t("stage_running_note_ai", lang).lower()
            self.assertTrue(note.strip(), lang)
            for word in ("file", "fayl", "فائل"):
                self.assertNotIn(word, note, f"{lang}: the AI note mentions a file")

    def test_the_note_matches_whether_a_model_is_actually_configured(self):
        """
        Promising "this runs on Google's servers" with no key configured would
        describe work that is not happening.
        """
        app = bare_app()
        for available, expected in ((True, "stage_running_note_ai"),
                                    (False, "stage_running_note_local")):
            with mock.patch.object(app, "is_ai_available", lambda: available),                     mock.patch.object(app, "stage_markup", lambda l, a, note="": ""),                     mock.patch.object(app, "Stages", lambda labels, note="": (labels, note)):
                labels, note = app.ai_stages("stage_ask_write")
            self.assertEqual(note, t(expected, app.lang))

    def test_the_blur_is_reserved_for_what_has_not_happened(self):
        css = io.open(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "styles", "components.css"),
            encoding="utf-8").read()
        self.assertIn(".sa-stage.is-pending", css)
        self.assertIn("blur", css)


if __name__ == "__main__":
    unittest.main()

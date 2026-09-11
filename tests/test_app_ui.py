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


if __name__ == "__main__":
    unittest.main()

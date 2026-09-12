"""
V2 P2: Roman Urdu, impact figures, empty states, degraded-AI behaviour.

The two things worth protecting here are a translation that silently rots and
a failure that silently looks like a success.
"""
import os
import re
import unittest
from unittest import mock

from streamlit.testing.v1 import AppTest

from core import llm_client
from core.data_loader import load_all_opportunities
from core.i18n import (
    LANGUAGES, LANG_EN, LANG_ROMAN, LANG_UR, STRINGS, is_rtl, normalise_lang, t,
)
from core.i18n_roman import ROMAN
from core.impact import MINUTES_PER_LOOKUP, estimate_basis, measure
from core.models import sample_profile
from core.rules_engine import evaluate_all

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
URDU_SCRIPT = re.compile(r"[؀-ۿݐ-ݿ]")
PLACEHOLDERS = re.compile(r"{(\w+)}")


# ===========================================================================
# P2-1 — Roman Urdu
# ===========================================================================
class TestRomanUrduCoverage(unittest.TestCase):
    """
    A half-translated language mode is worse than none: the user gets a page
    that switches script mid-sentence. These tests are what let the mode ship.
    """

    def test_every_string_has_a_roman_translation(self):
        missing = sorted(key for key in STRINGS if key not in ROMAN)
        self.assertEqual(missing, [], f"{len(missing)} strings have no Roman Urdu")

    def test_no_orphan_translations(self):
        """A key that no longer exists is a typo or a leftover."""
        orphans = sorted(key for key in ROMAN if key not in STRINGS)
        self.assertEqual(orphans, [])

    def test_placeholders_survive_translation(self):
        """
        A dropped {placeholder} is not a cosmetic problem: t() formats these,
        so a mismatch renders the wrong number or swallows the value.
        """
        for key, entry in STRINGS.items():
            if key not in ROMAN:
                continue
            self.assertEqual(sorted(set(PLACEHOLDERS.findall(entry["en"]))),
                             sorted(set(PLACEHOLDERS.findall(ROMAN[key]))), key)

    def test_roman_is_written_in_latin_script(self):
        """Roman Urdu that contains Urdu script defeats the entire point."""
        offenders = [key for key, text in ROMAN.items() if URDU_SCRIPT.search(text)]
        self.assertEqual(offenders, [])

    def test_urdu_strings_are_still_urdu(self):
        """P2-1's own warning: not at the expense of the two real languages."""
        for key in ("cta_start", "status_eligible", "next_step_label"):
            self.assertTrue(URDU_SCRIPT.search(STRINGS[key]["ur"]), key)

    def test_three_modes_are_distinct(self):
        for key in ("cta_start", "hero_title", "next_step_label"):
            rendered = {t(key, code) for code in LANGUAGES}
            self.assertEqual(len(rendered), 3, key)

    def test_only_urdu_script_is_right_to_left(self):
        """
        Roman Urdu is Urdu language in Latin script. Mirroring the page for it
        is the obvious mistake, since it is "the other Urdu one".
        """
        self.assertTrue(is_rtl(LANG_UR))
        self.assertFalse(is_rtl(LANG_ROMAN))
        self.assertFalse(is_rtl(LANG_EN))

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(normalise_lang("fr"), LANG_EN)
        self.assertEqual(t("cta_start", "fr"), t("cta_start", LANG_EN))

    def test_a_gap_degrades_to_english_not_to_a_blank(self):
        with mock.patch.dict(ROMAN, clear=False):
            ROMAN.pop("cta_start", None)
            self.assertEqual(t("cta_start", LANG_ROMAN), t("cta_start", LANG_EN))

    def test_model_is_told_not_to_use_urdu_script(self):
        """Asked for "Urdu", a model returns Urdu script - the wrong one."""
        instruction = llm_client._language_instruction(LANG_ROMAN)
        self.assertIn("Latin script", instruction)
        self.assertIn("Do NOT use Urdu script", instruction)
        self.assertNotEqual(instruction, llm_client._language_instruction(LANG_UR))


class TestRomanUrduRenders(unittest.TestCase):

    def test_whole_page_renders_without_urdu_script(self):
        app = AppTest.from_file(APP, default_timeout=300)
        app.session_state["language"] = LANG_ROMAN
        app.run()
        app.button(key="cta_sample").click().run()
        self.assertFalse(app.exception)

        body = " ".join(str(m.value) for m in app.markdown)
        # The switcher labels itself in each script on purpose.
        body = body.replace("اردو", "")
        leaked = URDU_SCRIPT.findall(body)
        self.assertEqual(leaked, [], "Urdu script leaked into the Roman Urdu page")

    def test_roman_page_is_not_mirrored(self):
        app = AppTest.from_file(APP, default_timeout=300)
        app.session_state["language"] = LANG_ROMAN
        app.run()
        body = " ".join(str(m.value) for m in app.markdown)
        self.assertNotIn("direction: rtl", body)


# ===========================================================================
# P2-2 — Impact
# ===========================================================================
class TestImpact(unittest.TestCase):

    def setUp(self):
        self.results = evaluate_all(sample_profile(), load_all_opportunities())

    def test_counts_match_the_work_actually_done(self):
        impact = measure(self.results)
        self.assertEqual(impact.opportunities_screened, len(self.results))
        self.assertEqual(impact.requirements_checked,
                         sum(len(r.applicable_checks()) for r in self.results))
        self.assertEqual(impact.documents_identified,
                         sum(len(r.opportunity.required_documents) for r in self.results))

    def test_counts_only_conditions_that_applied(self):
        """
        A record with two rules must not contribute fourteen. Counting every
        possible condition would inflate the headline figure quietly.
        """
        impact = measure(self.results)
        possible = sum(len(r.checks) for r in self.results)
        self.assertLessEqual(impact.requirements_checked, possible)

    def test_nothing_screened_means_nothing_claimed(self):
        impact = measure([])
        self.assertTrue(impact.is_empty())
        self.assertEqual(impact.estimated_minutes_saved, 0)

    def test_the_estimate_is_derived_from_a_stated_constant(self):
        """
        The one figure that cannot be counted. It must be reproducible from a
        number the UI is able to show, not a hand-tuned impression.
        """
        impact = measure(self.results)
        self.assertEqual(impact.estimated_minutes_saved,
                         impact.opportunities_screened * MINUTES_PER_LOOKUP)
        self.assertEqual(estimate_basis()["minutes_per_lookup"], MINUTES_PER_LOOKUP)

    def test_the_estimate_is_labelled_wherever_it_appears(self):
        note = t("impact_estimate_note", "en", n=3, minutes=MINUTES_PER_LOOKUP)
        self.assertIn("estimate", note.lower())
        self.assertIn("not a measured", note.lower())


# ===========================================================================
# P2-4 / P2-5 — empty states and degraded AI
# ===========================================================================
class TestDegradedAi(unittest.TestCase):
    """
    P2-5: the point of the architecture is that the product works without the
    model. That claim is only worth making if it is tested.
    """

    def test_failed_call_is_marked_not_ok(self):
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", side_effect=RuntimeError("429")):
            out = llm_client.explain_match("p", "r", "en")
        self.assertFalse(out.ok)
        self.assertEqual(out.reason, llm_client.REASON_ERROR)

    def test_offline_answer_is_marked_not_ok(self):
        with mock.patch.object(llm_client, "_client", return_value=None):
            self.assertFalse(llm_client.explain_match("p", "r", "en").ok)

    def test_missing_evidence_is_marked_not_ok(self):
        self.assertEqual(llm_client.answer_followup("q", [], "en").reason,
                         llm_client.REASON_NO_EVIDENCE)

    def test_a_real_answer_is_marked_ok(self):
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", return_value="A real answer."):
            out = llm_client.explain_match("p", "r", "en")
        self.assertTrue(out.ok)
        self.assertEqual(str(out), "A real answer.")

    def test_raw_api_errors_never_reach_the_text(self):
        """"Gemini API error 429" tells an applicant nothing they can act on."""
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate",
                                  side_effect=RuntimeError("429 RESOURCE_EXHAUSTED")):
            out = llm_client.explain_match("p", "r", "en")
        self.assertNotIn("429", str(out))
        self.assertNotIn("RESOURCE_EXHAUSTED", str(out))

    def test_results_page_survives_a_dead_model(self):
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", side_effect=RuntimeError("boom")):
            app = AppTest.from_file(APP, default_timeout=300)
            app.run()
            app.button(key="cta_sample").click().run()
            self.assertFalse(app.exception)
            body = " ".join(str(m.value) for m in app.markdown)

        # The four things P2-5 says must still be there.
        self.assertIn("sa-scorecard", body)          # requirement results
        self.assertIn("sa-next-label", body)         # next step
        self.assertIn("Source", body)                # official source
        self.assertIn("sa-score-num", body)          # deterministic result


class TestEmptyStates(unittest.TestCase):
    """P2-4: a blank screen is a dead end, and invites the wrong conclusion."""

    def test_no_matches_offers_routes_out(self):
        app = AppTest.from_file(APP, default_timeout=300)
        app.run()
        app.button(key="cta_start").click().run()
        app.button(key="next_0").click().run()
        # An age nothing in the catalogue accepts.
        app.number_input(key="w_age_1").set_value(69).run()
        app.selectbox(key="w_domicile_province_1").set_value("Sindh").run()
        # Walk to the results view, answering each step's required fields.
        for _ in range(6):
            nav = [b for b in app.button if b.key and b.key.startswith("next_")]
            if not nav:
                break
            nav[0].click().run()
            education = [w for w in app.selectbox if w.key == "w_education_level_2"]
            if education and app.session_state["step_errors"]:
                education[0].set_value("matric").run()
                nav = [b for b in app.button if b.key and b.key.startswith("next_")]
                if nav:
                    nav[0].click().run()

        labels = [b.label for b in app.button]
        self.assertIn(t("empty_try_answers", "en"), labels)
        self.assertIn(t("empty_try_categories", "en"), labels)

    def test_empty_result_explains_the_catalogue_is_small(self):
        """
        "No matches" reads as "you don't qualify for anything". With three
        records loaded, the likelier explanation is ours, and we should say so.
        """
        note = t("empty_catalogue_note", "en", n=3)
        self.assertIn("prototype", note.lower())
        self.assertIn("not a judgement about you", note.lower())

    def test_no_documents_listed_is_not_read_as_none_required(self):
        note = t("documents_none_listed", "en")
        self.assertIn("gap in our record", note.lower())


if __name__ == "__main__":
    unittest.main()

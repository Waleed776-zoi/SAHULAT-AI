"""
Tests for the modules around the rules engine (TEST-01).

Like the rules-engine tests, these run with no network, no API key and no
chromadb - the app must stay fully testable offline (Invariant 5).
"""
import json
import unittest
from unittest import mock

from core import data_loader, i18n
from core.ad_reader import UPLOAD_DISCLAIMER, read_ad
from core.data_loader import catalogue_health, category_counts, load_all_opportunities
from core.i18n import describe_check, describe_profile, status_label, t
from core.models import (
    CHECK_AGE, CHECK_EXISTING_SCHOLARSHIP, CHECK_INCOME, ConditionCheck,
    MET, NOT_APPLICABLE, Opportunity, STATUS_ELIGIBLE, UNKNOWN, UNMET, UserProfile,
    parse_iso_date,
)
from core.rag_engine import RagIndex


# ---------------------------------------------------------------------------
# data_loader
# ---------------------------------------------------------------------------

class TestDataLoader(unittest.TestCase):

    def test_loads_curated_records(self):
        opportunities = load_all_opportunities()
        self.assertGreater(len(opportunities), 0)
        self.assertTrue(all(isinstance(o, Opportunity) for o in opportunities))

    def test_schema_file_is_not_loaded_as_a_record(self):
        ids = {o.opportunity_id for o in load_all_opportunities()}
        self.assertNotIn("schema", ids)

    def test_placeholder_records_are_skipped(self):
        """A 'REPLACE ME' entry must never reach a live demo."""
        for opportunity in load_all_opportunities():
            self.assertFalse(opportunity.name.upper().startswith("REPLACE ME"))
            self.assertFalse(opportunity.name.upper().startswith("TODO"))

    def test_category_counts_include_empty_categories(self):
        """DATA-03: the UI needs to know a category is empty, not just absent."""
        counts = category_counts(load_all_opportunities())
        for category in data_loader.KNOWN_CATEGORIES:
            self.assertIn(category, counts)

    def test_catalogue_health_adds_up(self):
        opportunities = load_all_opportunities()
        health = catalogue_health(opportunities)
        self.assertEqual(health["total"], len(opportunities))
        self.assertEqual(health["verified"] + health["unverified"], health["total"])

    def test_malformed_json_file_is_skipped_not_fatal(self):
        with mock.patch.object(data_loader.json, "load",
                               side_effect=json.JSONDecodeError("bad", "", 0)):
            self.assertEqual(load_all_opportunities(), [])


# ---------------------------------------------------------------------------
# models - verification state (DATA-01)
# ---------------------------------------------------------------------------

def make_record(**overrides) -> Opportunity:
    payload = {
        "opportunity_id": "x",
        "name": "X",
        "category": "scholarship",
        "provider": "P",
        "eligibility_conditions": {},
        "last_verified": "2026-01-01",
        "confidence_status": "verified",
    }
    payload.update(overrides)
    return Opportunity.from_dict(payload)


class TestVerificationState(unittest.TestCase):

    def test_placeholder_last_verified_is_not_a_date(self):
        record = make_record(last_verified="TODO-VERIFY-BEFORE-DEMO")
        self.assertFalse(record.is_verified())
        self.assertIsNone(record.verified_date())
        self.assertTrue(record.has_placeholder_data())

    def test_real_date_with_verified_status_is_verified(self):
        self.assertTrue(make_record().is_verified())

    def test_needs_recheck_is_not_verified_even_with_a_date(self):
        self.assertFalse(make_record(confidence_status="needs_recheck").is_verified())

    def test_uploaded_records_are_never_verified(self):
        record = make_record(source_type="user_uploaded")
        self.assertFalse(record.is_verified())

    def test_parse_iso_date_never_raises(self):
        self.assertIsNone(parse_iso_date("not a date"))
        self.assertIsNone(parse_iso_date(None))
        self.assertIsNotNone(parse_iso_date("2026-01-01"))

    def test_curated_records_on_disk_do_not_leak_placeholders_as_dates(self):
        for opportunity in load_all_opportunities():
            if opportunity.has_placeholder_data():
                self.assertFalse(
                    opportunity.is_verified(),
                    f"{opportunity.opportunity_id} would render a TODO as a date",
                )


class TestLocalisedRecordFields(unittest.TestCase):
    """I18N-01: the Urdu fields in the data must actually be used."""

    def test_urdu_name_and_summary_are_used(self):
        record = make_record(name="English", name_ur="اردو",
                             summary_en="English summary", summary_ur="اردو خلاصہ")
        self.assertEqual(record.display_name("ur"), "اردو")
        self.assertEqual(record.display_summary("ur"), "اردو خلاصہ")

    def test_falls_back_to_english_when_urdu_missing(self):
        record = make_record(name="English", summary_en="English summary")
        self.assertEqual(record.display_name("ur"), "English")
        self.assertEqual(record.display_summary("ur"), "English summary")

    def test_curated_records_carry_urdu(self):
        for opportunity in load_all_opportunities():
            self.assertNotEqual(opportunity.display_name("ur"), "",
                                f"{opportunity.opportunity_id} has no displayable name")


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

class TestI18n(unittest.TestCase):

    def test_missing_key_returns_the_key(self):
        self.assertEqual(t("definitely_not_a_real_key"), "definitely_not_a_real_key")

    def test_missing_language_falls_back_to_english(self):
        self.assertEqual(t("app_title", "fr"), t("app_title", "en"))

    def test_every_string_has_both_languages(self):
        for key, entry in i18n.STRINGS.items():
            with self.subTest(key=key):
                self.assertIn("en", entry)
                self.assertIn("ur", entry)
                self.assertTrue(entry["ur"].strip(), f"{key} has an empty Urdu string")

    def test_placeholders_are_substituted(self):
        self.assertIn("7", t("sidebar_records", "en", n=7))

    def test_status_labels_differ_by_language(self):
        self.assertNotEqual(status_label(STATUS_ELIGIBLE, "en"),
                            status_label(STATUS_ELIGIBLE, "ur"))


class TestDescribeCheck(unittest.TestCase):
    """I18N-02: prose is composed here, in both languages."""

    def test_renders_in_both_languages(self):
        check = ConditionCheck(CHECK_AGE, MET, required={"min": 18, "max": 30}, actual=25)
        title_en, detail_en = describe_check(check, "en")
        title_ur, detail_ur = describe_check(check, "ur")
        self.assertTrue(detail_en and detail_ur)
        self.assertNotEqual(title_en, title_ur)

    def test_na_check_has_no_detail(self):
        title, detail = describe_check(ConditionCheck(CHECK_AGE, NOT_APPLICABLE), "en")
        self.assertEqual(detail, "")
        self.assertTrue(title)

    def test_unknown_check_says_not_provided(self):
        check = ConditionCheck(CHECK_INCOME, UNKNOWN, required=50000)
        _, detail = describe_check(check, "en")
        self.assertIn("not provided", detail.lower())

    def test_scholarship_detail_is_not_a_contradiction(self):
        """BUG-08: 'already receive a scholarship: False' read as nonsense."""
        check = ConditionCheck(CHECK_EXISTING_SCHOLARSHIP, MET, required=True, actual=False)
        _, detail = describe_check(check, "en")
        self.assertIn("none", detail.lower())

    def test_income_is_formatted_as_money(self):
        check = ConditionCheck(CHECK_INCOME, MET, required=60000, actual=0)
        _, detail = describe_check(check, "en")
        self.assertIn("60,000", detail)

    def test_all_check_keys_render_without_error(self):
        from core.models import (
            CHECK_DEADLINE, CHECK_DOMICILE, CHECK_EDUCATION, CHECK_EMPLOYMENT,
            CHECK_ENROLLMENT, CHECK_EXPERIENCE, CHECK_MARKS,
        )
        samples = [
            ConditionCheck(CHECK_DOMICILE, UNMET, required=["Punjab"], actual="Sindh"),
            ConditionCheck(CHECK_EDUCATION, MET, required="intermediate", actual="bachelor"),
            ConditionCheck(CHECK_MARKS, MET, required=60, actual=72),
            ConditionCheck(CHECK_ENROLLMENT, MET, required=True, actual=True),
            ConditionCheck(CHECK_EMPLOYMENT, MET, required="unemployed", actual="unemployed"),
            ConditionCheck(CHECK_EXPERIENCE, MET, required=2, actual=3),
            ConditionCheck(CHECK_DEADLINE, MET, required="2026-12-31"),
        ]
        for check in samples:
            for language in ("en", "ur"):
                with self.subTest(key=check.key, lang=language):
                    title, detail = describe_check(check, language)
                    self.assertTrue(title)


class TestDescribeProfile(unittest.TestCase):
    """OPS-06: a readable summary, and still no identifying data."""

    def test_summarises_answered_fields(self):
        summary = describe_profile(UserProfile(age=22, domicile_province="Punjab"), "en")
        self.assertIn("22", summary)
        self.assertIn("Punjab", summary)

    def test_names_unanswered_fields_explicitly(self):
        summary = describe_profile(UserProfile(age=22), "en")
        self.assertIn("Not provided", summary)

    def test_empty_profile_does_not_crash(self):
        self.assertTrue(describe_profile(UserProfile(), "en"))

    def test_is_not_a_dataclass_repr(self):
        summary = describe_profile(UserProfile(age=22), "en")
        self.assertNotIn("UserProfile(", summary)


# ---------------------------------------------------------------------------
# ad_reader
# ---------------------------------------------------------------------------

class TestAdReader(unittest.TestCase):

    def _read(self, extracted):
        with mock.patch("core.ad_reader.extract_opportunity_from_file",
                        return_value=extracted):
            return read_ad(b"fake-bytes", "image/png")

    def test_uploaded_record_is_tagged_and_disclaimed(self):
        opportunity, _ = self._read({"name": "Some Ad", "category": "scholarship"})
        self.assertEqual(opportunity.source_type, "user_uploaded")
        self.assertEqual(opportunity.disclaimer, UPLOAD_DISCLAIMER)
        self.assertFalse(opportunity.is_verified())

    def test_missing_fields_get_safe_defaults(self):
        opportunity, _ = self._read({})
        self.assertTrue(opportunity.name)
        self.assertEqual(opportunity.required_documents, [])
        self.assertEqual(opportunity.application_steps, [])

    def test_invalid_category_becomes_unknown(self):
        opportunity, _ = self._read({"category": "not-a-real-category"})
        self.assertEqual(opportunity.category, "unknown")

    def test_null_eligibility_block_is_handled(self):
        opportunity, _ = self._read({"eligibility_conditions": None})
        self.assertIsNone(opportunity.eligibility_conditions.min_age)

    def test_invalid_confidence_falls_back_to_low(self):
        opportunity, _ = self._read({"extraction_confidence": "banana"})
        self.assertEqual(opportunity.confidence_status, "low")

    def test_raw_dict_is_returned_for_display(self):
        payload = {"name": "Ad", "extraction_confidence": "high"}
        _, raw = self._read(payload)
        self.assertEqual(raw, payload)

    def test_uploaded_record_screens_through_the_same_engine(self):
        from core.rules_engine import evaluate
        opportunity, _ = self._read({
            "name": "Ad", "category": "scholarship",
            "eligibility_conditions": {"min_age": 18, "max_age": 25},
        })
        result = evaluate(UserProfile(age=20), opportunity)
        self.assertEqual(result.overall_status, STATUS_ELIGIBLE)


# ---------------------------------------------------------------------------
# llm_client - mock paths (no key configured)
# ---------------------------------------------------------------------------

class TestLlmClientOfflineMode(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch("core.llm_client._client", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_explain_falls_back_without_a_key(self):
        from core.llm_client import explain_match
        out = explain_match("profile", "result summary", "en")
        self.assertIn("result summary", out)

    def test_extraction_falls_back_without_a_key(self):
        from core.llm_client import extract_opportunity_from_file
        out = extract_opportunity_from_file(b"x", "image/png")
        self.assertEqual(out["extraction_confidence"], "low")
        self.assertTrue(out.get("_mock"))

    def test_followup_without_evidence_says_so(self):
        from core.llm_client import answer_followup
        out = answer_followup("anything?", [], "en")
        self.assertEqual(out, t("no_evidence_found", "en"))

    def test_urdu_fallbacks_are_urdu(self):
        from core.llm_client import explain_match
        self.assertNotEqual(explain_match("p", "r", "ur"), explain_match("p", "r", "en"))


class TestLlmClientErrorHandling(unittest.TestCase):
    """OPS-01: a failing model call must not take the page down."""

    def test_explain_returns_message_on_exception(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=("fake", object())), \
             mock.patch.object(llm_client, "_generate", side_effect=RuntimeError("429")):
            out = llm_client.explain_match("p", "r", "en")
        self.assertEqual(out, t("ai_unavailable", "en"))

    def test_extraction_returns_record_on_exception(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=("fake", object())), \
             mock.patch.object(llm_client, "_generate", side_effect=RuntimeError("boom")):
            out = llm_client.extract_opportunity_from_file(b"x", "image/png")
        self.assertEqual(out["extraction_confidence"], "low")
        self.assertIn("_error", out)

    def test_non_json_model_output_is_surfaced_not_raised(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=("fake", object())), \
             mock.patch.object(llm_client, "_generate", return_value="I'm not JSON"):
            out = llm_client.extract_opportunity_from_file(b"x", "image/png")
        self.assertIn("_raw_model_output", out)

    def test_code_fenced_json_is_parsed(self):
        from core import llm_client
        fenced = '```json\n{"name": "Fenced", "extraction_confidence": "high"}\n```'
        with mock.patch.object(llm_client, "_client", return_value=("fake", object())), \
             mock.patch.object(llm_client, "_generate", return_value=fenced):
            out = llm_client.extract_opportunity_from_file(b"x", "image/png")
        self.assertEqual(out["name"], "Fenced")


# ---------------------------------------------------------------------------
# rag_engine - keyword path only (no model download in tests)
# ---------------------------------------------------------------------------

class TestRagKeywordFallback(unittest.TestCase):

    def setUp(self):
        self.index = RagIndex(load_all_opportunities(), allow_semantic=False)

    def test_defaults_to_keyword_mode(self):
        self.assertEqual(self.index.mode, "keyword")
        self.assertIsNotNone(self.index.fallback_reason)

    def test_relevant_query_retrieves_something(self):
        self.assertTrue(self.index.retrieve("scholarship Balochistan domicile"))

    def test_irrelevant_query_returns_nothing(self):
        """BUG-06: never hand the model unrelated text labelled 'Evidence'."""
        self.assertEqual(self.index.retrieve("zebra submarine astrophysics"), [])

    def test_stopword_only_query_returns_nothing(self):
        self.assertEqual(self.index.retrieve("what is the a of"), [])

    def test_empty_query_returns_nothing(self):
        self.assertEqual(self.index.retrieve("   "), [])

    def test_respects_top_k(self):
        self.assertLessEqual(len(self.index.retrieve("scholarship", top_k=1)), 1)


if __name__ == "__main__":
    unittest.main()

"""
V2 P1: readiness, deadlines, scoped retrieval, comparison, freshness, plain
language.

Most of these protect the same boundary the rest of the suite does - the
product may state what it knows, and must not imply what it doesn't. The
recurring trap in this batch is *absence*: no deadline, never verified, no
documents. Each of those has a benign-looking reading ("plenty of time",
"fine", "nothing needed") and each of those readings is wrong.
"""
import unittest
from datetime import date, timedelta
from unittest import mock

from core.comparison import MEANINGFUL_MARGIN, compare
from core.data_loader import load_all_opportunities
from core.i18n import describe_comparison, describe_freshness, describe_urgency
from core.models import (
    EligibilityConditions, Opportunity, UserProfile, sample_profile,
)
from core.next_action import (
    ACTION_APPLY, ACTION_OBTAIN_DOCUMENT, ACTION_PREPARE_DOCUMENTS, next_action,
)
from core.rag_engine import RagIndex
from core.readiness import readiness
from core.rules_engine import evaluate
from core.timeliness import (
    AGING_DAYS, FRESH_AGING, FRESH_NEVER, FRESH_RECENT, FRESH_STALE,
    RECENT_DAYS, URGENCY_IMMINENT, URGENCY_PASSED, URGENCY_PLENTY,
    URGENCY_SOON, URGENCY_UNKNOWN, days_remaining, deadline_urgency,
    is_expired, record_freshness, should_prompt_verification,
)

OPPORTUNITIES = load_all_opportunities()
TODAY = date(2026, 9, 12)


def opportunity(documents=(), deadline=None, **conditions) -> Opportunity:
    return Opportunity(
        opportunity_id="test_op", name="Test opportunity", category="scholarship",
        provider="Test provider", province_scope="", target_group="", summary_en="",
        eligibility_conditions=EligibilityConditions(
            application_deadline=deadline, **conditions),
        required_documents=list(documents), application_steps=[],
        official_url="", source_title="", last_verified="",
    )


def in_days(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


# ===========================================================================
# P1-1 — Application readiness
# ===========================================================================
class TestReadiness(unittest.TestCase):

    def test_splits_into_have_and_missing(self):
        record = opportunity(documents=["CNIC", "Domicile", "Transcript"])
        state = readiness(record, {0, 2})
        self.assertEqual(state.have, ["CNIC", "Transcript"])
        self.assertEqual(state.missing, ["Domicile"])

    def test_percent_tracks_the_checklist(self):
        record = opportunity(documents=["A", "B", "C", "D"])
        self.assertEqual(readiness(record, set()).percent, 0)
        self.assertEqual(readiness(record, {0, 1}).percent, 50)
        self.assertEqual(readiness(record, {0, 1, 2, 3}).percent, 100)

    def test_never_reads_full_while_something_is_missing(self):
        """
        The one output this must never produce. With 199 documents and 198
        ticked, honest rounding would say 100%.
        """
        record = opportunity(documents=[str(i) for i in range(199)])
        state = readiness(record, set(range(198)))
        self.assertEqual(state.percent, 99)
        self.assertFalse(state.is_complete)

    def test_stale_ticks_are_ignored_not_fatal(self):
        """A checklist lives in UI state; the record can change under it."""
        record = opportunity(documents=["A", "B"])
        state = readiness(record, {0, 5, -1})
        self.assertEqual(state.have, ["A"])
        self.assertEqual(state.percent, 50)

    def test_record_with_no_documents_is_not_100_percent(self):
        state = readiness(opportunity(documents=[]), set())
        self.assertEqual(state.percent, 0)
        self.assertFalse(state.is_complete)

    def test_checklist_drives_the_next_action(self):
        record = opportunity(documents=["CNIC", "Domicile"], min_age=18, max_age=40)
        match = evaluate(UserProfile(age=25), record)
        self.assertEqual(next_action(match, set()).key, ACTION_PREPARE_DOCUMENTS)
        partial = next_action(match, {0})
        self.assertEqual(partial.key, ACTION_OBTAIN_DOCUMENT)
        self.assertEqual(partial.subject["document"], "Domicile")
        self.assertEqual(next_action(match, {0, 1}).key, ACTION_APPLY)


# ===========================================================================
# P1-2 — Deadline intelligence
# ===========================================================================
class TestDeadlines(unittest.TestCase):

    def test_urgency_bands(self):
        cases = [(-1, URGENCY_PASSED), (0, URGENCY_IMMINENT), (3, URGENCY_IMMINENT),
                 (4, URGENCY_SOON), (14, URGENCY_SOON), (15, URGENCY_PLENTY)]
        for days, expected in cases:
            self.assertEqual(deadline_urgency(in_days(days), TODAY), expected, days)

    def test_missing_deadline_is_unknown_not_plenty(self):
        """
        The important one. Most curated records carry no deadline, so this is
        the state users meet most often - and "plenty of time" would be a
        reassurance the record does not support.
        """
        self.assertEqual(deadline_urgency(None, TODAY), URGENCY_UNKNOWN)
        self.assertEqual(deadline_urgency("", TODAY), URGENCY_UNKNOWN)

    def test_unparseable_deadline_is_unknown_not_expired(self):
        for bad in ("TODO-VERIFY", "soon", "30 November", "2026-13-45"):
            self.assertEqual(deadline_urgency(bad, TODAY), URGENCY_UNKNOWN, bad)
            self.assertFalse(is_expired(bad, TODAY), bad)

    def test_days_remaining_is_signed(self):
        self.assertEqual(days_remaining(in_days(7), TODAY), 7)
        self.assertEqual(days_remaining(in_days(-7), TODAY), -7)
        self.assertIsNone(days_remaining(None, TODAY))

    def test_unknown_never_renders_as_a_countdown(self):
        label, detail = describe_urgency(URGENCY_UNKNOWN, None, "en")
        self.assertNotIn("remaining", detail)
        self.assertIn("official source", detail)

    def test_expired_listings_are_not_encouraged(self):
        """
        A closed listing must not produce a "go and apply" step, however
        complete the profile and checklist are.
        """
        record = opportunity(documents=["CNIC"], min_age=18, max_age=40,
                             deadline=(date.today() - timedelta(days=3)).isoformat())
        match = evaluate(UserProfile(age=25), record)
        self.assertNotEqual(next_action(match, {0}).key, ACTION_APPLY)

    def test_both_languages(self):
        for urgency in (URGENCY_PASSED, URGENCY_IMMINENT, URGENCY_SOON,
                        URGENCY_PLENTY, URGENCY_UNKNOWN):
            self.assertNotEqual(describe_urgency(urgency, 5, "en")[0],
                                describe_urgency(urgency, 5, "ur")[0], urgency)


# ===========================================================================
# P1-3 — Contextual, scoped retrieval
# ===========================================================================
class TestScopedRetrieval(unittest.TestCase):

    def setUp(self):
        self.index = RagIndex(OPPORTUNITIES, allow_semantic=False)

    def test_returns_only_the_named_record(self):
        target = OPPORTUNITIES[0]
        evidence = self.index.retrieve_for(target.opportunity_id, "what documents?")
        self.assertEqual(len(evidence), 1)
        self.assertIn(target.name, evidence[0])

    def test_never_substitutes_a_different_record(self):
        """
        Returning a near-miss from another scheme, labelled "evidence", is how
        a confident answer about the wrong scholarship gets written.
        """
        evidence = self.index.retrieve_for("no_such_id", "what documents?")
        self.assertEqual(evidence, [])

    def test_empty_question_retrieves_nothing(self):
        self.assertEqual(
            self.index.retrieve_for(OPPORTUNITIES[0].opportunity_id, "   "), [])


# ===========================================================================
# P1-5 — Comparison
# ===========================================================================
class TestComparison(unittest.TestCase):

    def easy_and_hard(self):
        easy = opportunity(documents=["CNIC"], min_age=18, max_age=40)
        easy.opportunity_id, easy.name = "easy", "Easy one"
        hard = opportunity(documents=[f"Doc {i}" for i in range(9)],
                           min_age=18, max_age=40, max_monthly_household_income=50000)
        hard.opportunity_id, hard.name = "hard", "Hard one"
        profile = UserProfile(age=25)
        return [evaluate(profile, easy), evaluate(profile, hard)]

    def test_rows_carry_comparable_facts(self):
        comparison = compare(self.easy_and_hard())
        self.assertEqual(len(comparison.rows), 2)
        by_id = {row.opportunity_id: row for row in comparison.rows}
        self.assertEqual(by_id["easy"].documents_missing, 1)
        self.assertEqual(by_id["hard"].documents_missing, 9)

    def test_names_the_lower_effort_option(self):
        comparison = compare(self.easy_and_hard())
        self.assertEqual(comparison.easiest_id, "easy")
        self.assertTrue(comparison.reasons)

    def test_reflects_documents_already_gathered(self):
        matches = self.easy_and_hard()
        comparison = compare(matches, {"hard": set(range(9))})
        by_id = {row.opportunity_id: row for row in comparison.rows}
        self.assertEqual(by_id["hard"].documents_missing, 0)

    def test_says_nothing_when_it_is_too_close(self):
        """Manufacturing a winner turns a comparison into a recommendation."""
        a = opportunity(documents=["CNIC"], min_age=18, max_age=40)
        a.opportunity_id, a.name = "a", "A"
        b = opportunity(documents=["Domicile"], min_age=18, max_age=40)
        b.opportunity_id, b.name = "b", "B"
        profile = UserProfile(age=25)
        comparison = compare([evaluate(profile, a), evaluate(profile, b)])
        self.assertIsNone(comparison.easiest_id)
        self.assertIn("equally", describe_comparison(comparison, "en"))

    def test_a_blocked_option_is_never_easiest(self):
        blocked = opportunity(documents=[], min_age=40, max_age=60)
        blocked.opportunity_id, blocked.name = "blocked", "Blocked"
        open_one = opportunity(documents=[f"D{i}" for i in range(6)],
                               min_age=18, max_age=40)
        open_one.opportunity_id, open_one.name = "open", "Open"
        profile = UserProfile(age=25)
        comparison = compare([evaluate(profile, blocked), evaluate(profile, open_one)])
        self.assertNotEqual(comparison.easiest_id, "blocked")

    def test_an_expired_option_is_never_easiest(self):
        expired = opportunity(documents=[], min_age=18, max_age=40,
                              deadline=(date.today() - timedelta(days=2)).isoformat())
        expired.opportunity_id, expired.name = "expired", "Expired"
        live = opportunity(documents=[f"D{i}" for i in range(8)],
                           min_age=18, max_age=40)
        live.opportunity_id, live.name = "live", "Live"
        profile = UserProfile(age=25)
        comparison = compare([evaluate(profile, expired), evaluate(profile, live)])
        self.assertNotEqual(comparison.easiest_id, "expired")

    def test_summary_compares_effort_not_worth(self):
        line = describe_comparison(compare(self.easy_and_hard()), "en").lower()
        for claim in ("better", "best", "recommend", "should apply", "worth more"):
            self.assertNotIn(claim, line)


# ===========================================================================
# P1-6 — Freshness
# ===========================================================================
class TestFreshness(unittest.TestCase):

    def verified_record(self, days_ago: int) -> Opportunity:
        record = opportunity()
        record.last_verified = (TODAY - timedelta(days=days_ago)).isoformat()
        record.confidence_status = "verified"
        record.source_type = "curated"
        return record

    def test_bands(self):
        cases = [(0, FRESH_RECENT), (RECENT_DAYS, FRESH_RECENT),
                 (RECENT_DAYS + 1, FRESH_AGING), (AGING_DAYS, FRESH_AGING),
                 (AGING_DAYS + 1, FRESH_STALE)]
        for days, expected in cases:
            self.assertEqual(record_freshness(self.verified_record(days), TODAY),
                             expected, days)

    def test_unverified_is_never_fresh_whatever_date_it_carries(self):
        """
        A date that was never backed by a real check is not evidence. This is
        the DATA-01 failure mode: a placeholder rendering as a verification.
        """
        record = opportunity()
        record.last_verified = TODAY.isoformat()
        record.confidence_status = "needs_recheck"
        self.assertEqual(record_freshness(record, TODAY), FRESH_NEVER)

    def test_uploaded_records_are_never_fresh(self):
        record = opportunity()
        record.source_type = "user_uploaded"
        record.confidence_status = "high"
        record.last_verified = TODAY.isoformat()
        self.assertEqual(record_freshness(record, TODAY), FRESH_NEVER)

    def test_catalogue_records_are_honest_about_themselves(self):
        for record in OPPORTUNITIES:
            if not record.is_verified():
                self.assertEqual(record_freshness(record), FRESH_NEVER,
                                 record.opportunity_id)

    def test_verification_is_prompted_by_default(self):
        """Existing in the database is not evidence of currency."""
        self.assertTrue(should_prompt_verification(opportunity()))
        self.assertFalse(should_prompt_verification(self.verified_record(3), TODAY))
        self.assertTrue(should_prompt_verification(self.verified_record(400), TODAY))

    def test_never_state_explains_itself(self):
        _, detail = describe_freshness(FRESH_NEVER, None, "en")
        self.assertIn("not evidence", detail)


# ===========================================================================
# P1-7 — Plain language
# ===========================================================================
class TestPlainLanguage(unittest.TestCase):

    def test_falls_back_to_a_labelled_mock_without_a_key(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=None):
            result = llm_client.simplify_opportunity("Name: X", "en")
        self.assertTrue(result.get("_mock"))

    def test_model_failure_never_raises(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", side_effect=RuntimeError("429")):
            result = llm_client.simplify_opportunity("Name: X", "en")
        self.assertIn("_error", result)

    def test_non_json_output_is_surfaced_not_rendered(self):
        from core import llm_client
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", return_value="not json at all"):
            result = llm_client.simplify_opportunity("Name: X", "en")
        self.assertIn("_error", result)
        self.assertNotIn("who_can_apply", result)

    def test_unexpected_sections_are_dropped(self):
        """
        Output goes on screen as guidance, so anything not asked for is not
        rendered - including a model volunteering an eligibility verdict.
        """
        from core import llm_client
        payload = ('{"who_can_apply": "Anyone from Punjab.", '
                   '"you_are_eligible": "Yes, you qualify!"}')
        with mock.patch.object(llm_client, "_client", return_value=("x", object())), \
                mock.patch.object(llm_client, "_generate", return_value=payload):
            result = llm_client.simplify_opportunity("Name: X", "en")
        self.assertEqual(result, {"who_can_apply": "Anyone from Punjab."})

    def test_prompt_forbids_adding_or_softening_requirements(self):
        from core.llm_client import SIMPLIFY_SYSTEM_PROMPT
        prompt = SIMPLIFY_SYSTEM_PROMPT.lower()
        self.assertIn("never add a requirement", prompt)
        self.assertIn("never say whether this particular reader is eligible", prompt)


if __name__ == "__main__":
    unittest.main()

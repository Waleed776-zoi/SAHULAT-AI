"""
V2 P0 features: scorecard, explanations, ranking, Lens, trust, next action.

These test the *decisions*, which all live in core/ and are therefore pure.
The rule the whole file exists to protect: structure decides, language
describes. Anything that reads as prose here is rendered from a machine key
by core/i18n.py, and nothing in core/ is allowed to produce a sentence.
"""
import unittest
from datetime import date, timedelta

from core.ad_reader import build_record
from core.data_loader import load_all_opportunities
from core.i18n import (
    describe_gap, describe_next_action, describe_ranking_reason, scorecard_row,
)
from core.models import (
    EligibilityConditions, MET, Opportunity, UNKNOWN, UNMET, UserProfile,
    sample_profile,
)
from core.next_action import (
    ACTION_ANSWER_MISSING, ACTION_APPLY, ACTION_CHECK_SOURCE,
    ACTION_CONFIRM_CONDITION, ACTION_EXPLORE_OTHERS, ACTION_PREPARE_DOCUMENTS,
    ACTION_REVIEW_BLOCKER, is_actionable_now, next_action,
)
from core.rules_engine import evaluate, evaluate_all, ranking_factors, top_matches

OPPORTUNITIES = load_all_opportunities()


def opportunity(**conditions) -> Opportunity:
    return Opportunity(
        opportunity_id="test_op",
        name="Test opportunity",
        category="scholarship",
        provider="Test provider",
        province_scope="",
        target_group="",
        summary_en="",
        eligibility_conditions=EligibilityConditions(**conditions),
        required_documents=[],
        application_steps=[],
        official_url="",
        source_title="",
        last_verified="",
    )


# ===========================================================================
# P0-1 — Eligibility scorecard
# ===========================================================================
class TestScorecard(unittest.TestCase):

    def test_counts_add_up_to_applicable_conditions(self):
        profile = UserProfile(age=20, domicile_province="Punjab")
        for record in OPPORTUNITIES:
            score = evaluate(profile, record).scorecard()
            self.assertEqual(score["met"] + score["unmet"] + score["unknown"],
                             score["total"], record.opportunity_id)

    def test_counts_match_the_rows_shown(self):
        """
        The header is a count of the rows beneath it. If those two can drift,
        the number is worse than no number at all.
        """
        match = evaluate(sample_profile(), OPPORTUNITIES[0])
        score = match.scorecard()
        self.assertEqual(len(match.applicable_checks()), score["total"])
        self.assertEqual(len(match.satisfied()), score["met"])
        self.assertEqual(len(match.blockers()), score["unmet"])
        self.assertEqual(len(match.gaps()), score["unknown"])

    def test_scorecard_is_not_a_percentage(self):
        """A count is checkable against the rows; a 'fit %' is not a thing
        this system computes."""
        score = evaluate(sample_profile(), OPPORTUNITIES[0]).scorecard()
        self.assertNotIn("percent", score)
        self.assertNotIn("score", score)

    def test_row_has_requirement_value_and_result(self):
        match = evaluate(sample_profile(), OPPORTUNITIES[0])
        for check in match.applicable_checks():
            title, required, actual, result = scorecard_row(check, "en")
            self.assertTrue(title and required and result)
            self.assertNotEqual(title, required)

    def test_rows_render_in_both_languages(self):
        match = evaluate(sample_profile(), OPPORTUNITIES[0])
        for check in match.applicable_checks():
            english = scorecard_row(check, "en")
            urdu = scorecard_row(check, "ur")
            self.assertNotEqual(english[0], urdu[0], check.key)

    def test_a_full_scorecard_does_not_override_a_blocker(self):
        """
        The central honesty rule of P0-1: many passes plus one hard failure is
        still a failure. A summary number must never outrank the rules.
        """
        record = opportunity(min_age=18, max_age=30, domicile_provinces=["Punjab"],
                             min_marks_percentage=60)
        profile = UserProfile(age=20, domicile_province="Sindh", marks_percentage=95.0)
        match = evaluate(profile, record)
        self.assertEqual(match.scorecard()["met"], 2)
        self.assertEqual(match.overall_status, "not_eligible")


# ===========================================================================
# P0-2 — Why / why not / what needs verification
# ===========================================================================
class TestExplanations(unittest.TestCase):

    def test_groups_are_disjoint_and_complete(self):
        match = evaluate(UserProfile(age=20, domicile_province="Punjab"),
                         OPPORTUNITIES[0])
        grouped = match.satisfied() + match.blockers() + match.gaps()
        self.assertEqual(len(grouped), len(match.applicable_checks()))
        self.assertEqual(len({id(c) for c in grouped}), len(grouped))

    def test_gap_states_requirement_and_the_profile_value(self):
        record = opportunity(min_marks_percentage=60)
        match = evaluate(UserProfile(marks_percentage=54.0), record)
        line = describe_gap(match.blockers()[0], "en")
        self.assertIn("60", line)
        self.assertIn("54", line)

    def test_gap_never_promises_eligibility(self):
        """
        "Raise your marks and you'll be eligible" is a claim about a decision
        no rule here makes. The line may state facts, never consequences.
        """
        record = opportunity(min_marks_percentage=60)
        match = evaluate(UserProfile(marks_percentage=54.0), record)
        line = describe_gap(match.blockers()[0], "en").lower()
        for promise in ("you will", "you'll", "will be eligible", "would be eligible",
                        "guarantee", "qualify for"):
            self.assertNotIn(promise, line)

    def test_unanswered_is_phrased_differently_from_failed(self):
        record = opportunity(min_marks_percentage=60)
        failed = describe_gap(evaluate(UserProfile(marks_percentage=54.0),
                                       record).blockers()[0], "en")
        unknown = describe_gap(evaluate(UserProfile(), record).gaps()[0], "en")
        self.assertNotEqual(failed, unknown)

    def test_explanations_render_in_urdu(self):
        record = opportunity(min_marks_percentage=60)
        match = evaluate(UserProfile(marks_percentage=54.0), record)
        self.assertNotEqual(describe_gap(match.blockers()[0], "en"),
                            describe_gap(match.blockers()[0], "ur"))


# ===========================================================================
# P0-3 — Personalised top matches
# ===========================================================================
class TestRanking(unittest.TestCase):

    def test_ranking_is_deterministic(self):
        profile = sample_profile()
        first = [r.opportunity.opportunity_id for r in evaluate_all(profile, OPPORTUNITIES)]
        for _ in range(3):
            self.assertEqual(
                [r.opportunity.opportunity_id for r in evaluate_all(profile, OPPORTUNITIES)],
                first)

    def test_eligible_outranks_needs_verification(self):
        statuses = [r.overall_status for r in evaluate_all(sample_profile(), OPPORTUNITIES)]
        order = {"eligible": 0, "needs_verification": 1, "not_eligible": 2}
        self.assertEqual(statuses, sorted(statuses, key=lambda s: order[s]))

    def test_sooner_deadline_ranks_first_among_equals(self):
        soon = (date.today() + timedelta(days=5)).isoformat()
        later = (date.today() + timedelta(days=90)).isoformat()
        a = opportunity(min_age=18, max_age=40, application_deadline=later)
        a.name, a.opportunity_id = "A later", "a"
        b = opportunity(min_age=18, max_age=40, application_deadline=soon)
        b.name, b.opportunity_id = "B sooner", "b"
        ranked = evaluate_all(UserProfile(age=25), [a, b])
        self.assertEqual(ranked[0].opportunity.opportunity_id, "b")

    def test_undated_records_do_not_jump_the_queue(self):
        """'No deadline on record' is its own bucket, not maximum urgency."""
        soon = (date.today() + timedelta(days=5)).isoformat()
        dated = opportunity(min_age=18, max_age=40, application_deadline=soon)
        dated.opportunity_id, dated.name = "dated", "A dated"
        undated = opportunity(min_age=18, max_age=40)
        undated.opportunity_id, undated.name = "undated", "A undated"
        ranked = evaluate_all(UserProfile(age=25), [undated, dated])
        self.assertEqual(ranked[0].opportunity.opportunity_id, "dated")

    def test_top_matches_excludes_closed_and_ineligible(self):
        results = evaluate_all(UserProfile(age=20, domicile_province="Punjab"),
                               OPPORTUNITIES)
        for match in top_matches(results):
            self.assertFalse(match.listing_closed)
            self.assertNotEqual(match.overall_status, "not_eligible")

    def test_top_matches_is_empty_rather_than_padded(self):
        past = (date.today() - timedelta(days=10)).isoformat()
        closed = opportunity(application_deadline=past)
        results = evaluate_all(UserProfile(age=25), [closed])
        self.assertEqual(top_matches(results), [])

    def test_ranking_reason_reports_only_structured_facts(self):
        match = evaluate(sample_profile(), OPPORTUNITIES[0])
        factors = ranking_factors(match)
        self.assertEqual(factors["met"], match.scorecard()["met"])
        reason = describe_ranking_reason(factors, "en")
        self.assertIn(str(factors["total"]), reason)


# ===========================================================================
# P0-4 — Sahulat Lens
# ===========================================================================
class TestLensExtraction(unittest.TestCase):

    def test_unrecognised_gender_value_is_dropped(self):
        """
        A mis-mapped gender becomes a real eligibility gate and wrongly
        excludes people. Unread is recoverable; wrong is not.
        """
        record, _ = build_record({"name": "X", "eligibility_conditions":
                                  {"gender_required": "women preferred"}})
        self.assertIsNone(record.eligibility_conditions.gender_required)

    def test_recognised_values_are_kept(self):
        record, _ = build_record({"name": "X", "province_scope": "Sindh",
                                  "eligibility_conditions": {
                                      "gender_required": "Female",
                                      "fields_of_study": ["computer_science", "nonsense"]}})
        self.assertEqual(record.eligibility_conditions.gender_required, "female")
        self.assertEqual(record.eligibility_conditions.fields_of_study, ["computer_science"])
        self.assertEqual(record.province_scope, "Sindh")

    def test_uploaded_record_screens_through_the_same_engine(self):
        record, _ = build_record({"name": "X", "eligibility_conditions":
                                  {"min_age": 18, "max_age": 30}})
        match = evaluate(UserProfile(age=45), record)
        self.assertEqual(match.overall_status, "not_eligible")
        self.assertEqual(match.blockers()[0].key, "age")

    def test_uploaded_record_still_gets_a_next_action(self):
        record, _ = build_record({"name": "X", "eligibility_conditions": {"min_age": 18}})
        self.assertTrue(next_action(evaluate(UserProfile(age=25), record)).key)


# ===========================================================================
# P0-5 — Trust layer
# ===========================================================================
class TestTrustLevels(unittest.TestCase):

    def test_uploaded_records_are_never_verified(self):
        record, _ = build_record({"name": "X", "extraction_confidence": "high"})
        self.assertEqual(record.source_type, "user_uploaded")
        self.assertFalse(record.is_verified())

    def test_high_extraction_confidence_is_not_verification(self):
        """
        Confidence is about how clearly the model could read the page. It says
        nothing about whether the page is current or true.
        """
        record, _ = build_record({"name": "X", "extraction_confidence": "high"})
        self.assertEqual(record.confidence_status, "high")
        self.assertFalse(record.is_verified())

    def test_corrections_do_not_promote_trust(self):
        record, _ = build_record({"name": "X", "eligibility_conditions": {"min_age": 18}})
        record.eligibility_conditions.min_age = 21      # the user corrects it
        self.assertEqual(record.source_type, "user_uploaded")
        self.assertFalse(record.is_verified())

    def test_curated_unverified_records_are_not_verified_either(self):
        for record in OPPORTUNITIES:
            if record.confidence_status != "verified":
                self.assertFalse(record.is_verified(), record.opportunity_id)


# ===========================================================================
# P0-6 — Next best action
# ===========================================================================
class TestNextAction(unittest.TestCase):

    def test_closed_listing_sends_the_user_elsewhere(self):
        past = (date.today() - timedelta(days=5)).isoformat()
        match = evaluate(UserProfile(age=25), opportunity(application_deadline=past))
        self.assertTrue(match.listing_closed)
        self.assertEqual(next_action(match).key, ACTION_EXPLORE_OTHERS)

    def test_closed_listing_outranks_everything_else(self):
        """A dead application page is not a useful next step, whatever else
        is true about the profile."""
        past = (date.today() - timedelta(days=5)).isoformat()
        record = opportunity(min_age=18, max_age=30, application_deadline=past)
        record.required_documents = ["CNIC"]
        match = evaluate(UserProfile(age=25), record)
        self.assertEqual(next_action(match).key, ACTION_EXPLORE_OTHERS)

    def test_blocker_is_named_rather_than_buried(self):
        record = opportunity(min_marks_percentage=60)
        record.required_documents = ["CNIC"]
        match = evaluate(UserProfile(marks_percentage=40.0), record)
        action = next_action(match)
        self.assertEqual(action.key, ACTION_REVIEW_BLOCKER)
        self.assertEqual(action.subject["check"], "marks")

    def test_unanswered_question_is_asked_before_the_source_is_blamed(self):
        match = evaluate(UserProfile(), opportunity(min_marks_percentage=60))
        self.assertEqual(next_action(match).key, ACTION_ANSWER_MISSING)

    def test_record_gap_asks_the_source(self):
        """
        The user answered; the record is what is incomplete. Only the official
        source can settle that, so do not send the user back to the form.
        """
        check_gap = opportunity(min_marks_percentage=60)
        match = evaluate(UserProfile(marks_percentage=80.0), check_gap)
        match.missing_profile_fields = []
        match.checks = [c for c in match.checks]
        for check in match.checks:
            if check.key == "marks":
                check.status = UNKNOWN
        self.assertEqual(next_action(match).key, ACTION_CONFIRM_CONDITION)

    def test_eligible_with_documents_prepares_them(self):
        record = opportunity(min_age=18, max_age=30)
        record.required_documents = ["CNIC", "Transcript"]
        action = next_action(evaluate(UserProfile(age=25), record))
        self.assertEqual(action.key, ACTION_PREPARE_DOCUMENTS)
        self.assertEqual(action.subject["count"], 2)

    def test_eligible_without_documents_applies(self):
        record = opportunity(min_age=18, max_age=30)
        record.official_url = "https://example.gov.pk/"
        action = next_action(evaluate(UserProfile(age=25), record))
        self.assertEqual(action.key, ACTION_APPLY)

    def test_there_is_always_exactly_one_action(self):
        profiles = [UserProfile(), sample_profile(),
                    UserProfile(age=60, domicile_province="Sindh")]
        for profile in profiles:
            for record in OPPORTUNITIES:
                action = next_action(evaluate(profile, record))
                self.assertTrue(action.key)
                self.assertIsInstance(action.key, str)

    def test_actions_render_in_both_languages(self):
        for record in OPPORTUNITIES:
            action = next_action(evaluate(UserProfile(), record))
            english = describe_next_action(action, "en")
            self.assertTrue(english.strip())
            self.assertNotEqual(english, describe_next_action(action, "ur"))

    def test_only_application_steps_count_as_actionable(self):
        record = opportunity(min_age=18, max_age=30)
        record.required_documents = ["CNIC"]
        self.assertTrue(is_actionable_now(evaluate(UserProfile(age=25), record)))
        self.assertFalse(is_actionable_now(evaluate(UserProfile(), record)))


# ===========================================================================
# The invariant the whole architecture exists to protect
# ===========================================================================
class TestRulesDecideNotLanguage(unittest.TestCase):

    def test_core_modules_emit_no_prose(self):
        """
        core/ decides; core/i18n.py describes. A sentence appearing in a
        decision module is how the two quietly merge.
        """
        import core.next_action as module
        for record in OPPORTUNITIES:
            action = next_action(evaluate(sample_profile(), record))
            self.assertNotIn(" ", action.key)

    def test_status_never_depends_on_the_scorecard_summary(self):
        record = opportunity(min_age=18, max_age=30, domicile_provinces=["Punjab"],
                             min_marks_percentage=60, min_education_level="matric")
        profile = UserProfile(age=20, domicile_province="Punjab", marks_percentage=90.0,
                              education_level="master")
        match = evaluate(profile, record)
        self.assertEqual(match.overall_status, "eligible")
        match.checks[0].status = UNMET          # tamper with a single row
        self.assertEqual(match.overall_status, "eligible",
                         "status is set by the engine, not recomputed from display state")


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for core/rules_engine.py - run with:  python -m pytest tests/
(or just: python -m unittest discover tests)

These tests use zero external dependencies (no Gemini, no chromadb) since
the rules engine must be independently correct - it's the piece the whole
"rules decide, LLM explains" architecture depends on.

Assertions are made against machine keys (STATUS_*, MET/UNMET/UNKNOWN), never
against display prose - the engine is language-free by design (I18N-02).
"""
import unittest
from datetime import date

from core.models import (
    CHECK_COMPUTER, CHECK_DEADLINE, CHECK_ENGLISH, CHECK_EXISTING_SCHOLARSHIP,
    CHECK_EXPERIENCE, CHECK_FIELD_OF_STUDY, CHECK_GENDER, CHECK_INCOME,
    EligibilityConditions, MET, NOT_APPLICABLE, Opportunity,
    STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
    UNKNOWN, UNMET, UserProfile,
)
from core.rules_engine import evaluate, evaluate_all, summarize_counts


def make_opportunity(name: str = "Test Opportunity", **kwargs) -> Opportunity:
    conditions = EligibilityConditions(**kwargs)
    return Opportunity(
        opportunity_id="test_opp",
        name=name,
        category="scholarship",
        provider="Test Provider",
        province_scope="Balochistan",
        target_group="Test group",
        summary_en="A test opportunity.",
        eligibility_conditions=conditions,
        required_documents=[],
        application_steps=[],
        official_url="https://example.gov.pk",
        source_title="Test source",
        last_verified="2026-01-01",
    )


def find(result, key):
    return [c for c in result.checks if c.key == key][0]


class TestRulesEngine(unittest.TestCase):

    def test_fully_eligible_profile(self):
        opp = make_opportunity(
            min_age=17, max_age=25,
            domicile_provinces=["Balochistan"],
            min_education_level="intermediate",
            min_marks_percentage=60,
        )
        profile = UserProfile(
            age=20, domicile_province="Balochistan",
            education_level="bachelor", marks_percentage=72,
        )
        self.assertEqual(evaluate(profile, opp).overall_status, STATUS_ELIGIBLE)

    def test_hard_fail_on_domicile(self):
        opp = make_opportunity(domicile_provinces=["Balochistan"])
        result = evaluate(UserProfile(domicile_province="Punjab"), opp)
        self.assertEqual(result.overall_status, STATUS_NOT_ELIGIBLE)

    def test_domicile_match_is_case_insensitive(self):
        opp = make_opportunity(domicile_provinces=["Balochistan"])
        result = evaluate(UserProfile(domicile_province="  balochistan "), opp)
        self.assertEqual(result.overall_status, STATUS_ELIGIBLE)

    def test_needs_verification_on_missing_data(self):
        opp = make_opportunity(min_marks_percentage=60)
        result = evaluate(UserProfile(age=20), opp)  # marks not provided
        self.assertEqual(result.overall_status, STATUS_NEEDS_VERIFICATION)
        self.assertIn("marks_percentage", result.missing_profile_fields)

    def test_income_ceiling_respected(self):
        opp = make_opportunity(max_monthly_household_income=60000)
        under = evaluate(UserProfile(monthly_household_income=40000), opp)
        over = evaluate(UserProfile(monthly_household_income=80000), opp)
        self.assertEqual(under.overall_status, STATUS_ELIGIBLE)
        self.assertEqual(over.overall_status, STATUS_NOT_ELIGIBLE)

    def test_income_boundary_is_inclusive(self):
        opp = make_opportunity(max_monthly_household_income=60000)
        exact = evaluate(UserProfile(monthly_household_income=60000), opp)
        self.assertEqual(exact.overall_status, STATUS_ELIGIBLE)

    def test_education_rank_comparison(self):
        opp = make_opportunity(min_education_level="intermediate")
        below = evaluate(UserProfile(education_level="matric"), opp)
        above = evaluate(UserProfile(education_level="bachelor"), opp)
        self.assertEqual(below.overall_status, STATUS_NOT_ELIGIBLE)
        self.assertEqual(above.overall_status, STATUS_ELIGIBLE)

    def test_existing_scholarship_exclusivity(self):
        opp = make_opportunity(must_not_have_existing_scholarship=True)
        has_one = evaluate(UserProfile(has_existing_scholarship=True), opp)
        has_none = evaluate(UserProfile(has_existing_scholarship=False), opp)
        self.assertEqual(has_one.overall_status, STATUS_NOT_ELIGIBLE)
        self.assertEqual(has_none.overall_status, STATUS_ELIGIBLE)
        self.assertEqual(find(has_none, CHECK_EXISTING_SCHOLARSHIP).status, MET)

    def test_no_conditions_means_always_eligible(self):
        opp = make_opportunity()  # every condition null
        self.assertEqual(evaluate(UserProfile(), opp).overall_status, STATUS_ELIGIBLE)

    def test_age_range_boundaries(self):
        opp = make_opportunity(min_age=18, max_age=35)
        for age, expected in ((17, STATUS_NOT_ELIGIBLE), (18, STATUS_ELIGIBLE),
                              (35, STATUS_ELIGIBLE), (36, STATUS_NOT_ELIGIBLE)):
            with self.subTest(age=age):
                self.assertEqual(evaluate(UserProfile(age=age), opp).overall_status, expected)


class TestZeroValuesAreRealAnswers(unittest.TestCase):
    """BUG-03: 0 is a valid answer, not a missing one."""

    def test_zero_income_is_met_not_unknown(self):
        opp = make_opportunity(max_monthly_household_income=60000)
        result = evaluate(UserProfile(monthly_household_income=0), opp)
        self.assertEqual(find(result, CHECK_INCOME).status, MET)
        self.assertEqual(result.overall_status, STATUS_ELIGIBLE)
        self.assertNotIn("monthly_household_income", result.missing_profile_fields)

    def test_unanswered_income_is_unknown(self):
        opp = make_opportunity(max_monthly_household_income=60000)
        result = evaluate(UserProfile(monthly_household_income=None), opp)
        self.assertEqual(find(result, CHECK_INCOME).status, UNKNOWN)
        self.assertEqual(result.overall_status, STATUS_NEEDS_VERIFICATION)

    def test_zero_experience_is_a_real_answer(self):
        opp = make_opportunity(min_experience_years=0)
        result = evaluate(UserProfile(years_experience=0), opp)
        self.assertEqual(find(result, CHECK_EXPERIENCE).status, MET)


class TestDeadlineIsAboutTheListing(unittest.TestCase):
    """BUG-04: an expired listing is not the user being ineligible."""

    def setUp(self):
        self.today = date(2026, 6, 15)

    def test_expired_deadline_flagged_as_closed(self):
        opp = make_opportunity(application_deadline="2020-01-01")
        result = evaluate(UserProfile(), opp, today=self.today)
        self.assertTrue(result.listing_closed)
        self.assertEqual(find(result, CHECK_DEADLINE).status, UNMET)

    def test_expired_deadline_does_not_make_user_ineligible(self):
        opp = make_opportunity(application_deadline="2020-01-01",
                               min_age=18, max_age=30)
        result = evaluate(UserProfile(age=25), opp, today=self.today)
        # The person qualifies; only the listing is closed.
        self.assertEqual(result.overall_status, STATUS_ELIGIBLE)
        self.assertTrue(result.listing_closed)

    def test_future_deadline_is_open(self):
        opp = make_opportunity(application_deadline="2026-12-31")
        result = evaluate(UserProfile(), opp, today=self.today)
        self.assertFalse(result.listing_closed)
        self.assertEqual(find(result, CHECK_DEADLINE).status, MET)

    def test_unparseable_deadline_is_unknown_not_closed(self):
        opp = make_opportunity(application_deadline="REPLACE ME: YYYY-MM-DD")
        result = evaluate(UserProfile(), opp, today=self.today)
        self.assertFalse(result.listing_closed)
        self.assertEqual(find(result, CHECK_DEADLINE).status, UNKNOWN)

    def test_absent_deadline_emits_na_check(self):
        """BUG-07: the checks list has a consistent shape for every record."""
        result = evaluate(UserProfile(), make_opportunity(), today=self.today)
        self.assertEqual(find(result, CHECK_DEADLINE).status, NOT_APPLICABLE)


class TestNoUserFacingProse(unittest.TestCase):
    """I18N-02: the engine must stay language-free."""

    def test_checks_carry_keys_and_structured_values_only(self):
        opp = make_opportunity(min_age=18, max_age=30,
                               domicile_provinces=["Punjab"],
                               max_monthly_household_income=50000)
        result = evaluate(UserProfile(age=25, domicile_province="Punjab",
                                      monthly_household_income=10000), opp)
        for check in result.checks:
            self.assertIsInstance(check.key, str)
            self.assertFalse(hasattr(check, "detail"),
                             "ConditionCheck must not carry prose")
            self.assertFalse(hasattr(check, "label"),
                             "ConditionCheck must not carry prose")


class TestEvaluateAll(unittest.TestCase):

    def test_sorted_best_match_first(self):
        eligible = make_opportunity(name="B eligible")
        ineligible = make_opportunity(name="A ineligible", min_age=99)
        results = evaluate_all(UserProfile(age=20), [ineligible, eligible])
        self.assertEqual(results[0].overall_status, STATUS_ELIGIBLE)
        self.assertEqual(results[-1].overall_status, STATUS_NOT_ELIGIBLE)

    def test_open_listings_rank_above_closed_at_same_status(self):
        today = date(2026, 6, 15)
        closed = make_opportunity(name="A closed", application_deadline="2020-01-01")
        open_one = make_opportunity(name="Z open", application_deadline="2026-12-31")
        results = evaluate_all(UserProfile(), [closed, open_one], today=today)
        self.assertFalse(results[0].listing_closed)

    def test_summarize_counts(self):
        results = evaluate_all(
            UserProfile(age=20),
            [make_opportunity(name="ok"), make_opportunity(name="no", min_age=99)],
        )
        totals = summarize_counts(results)
        self.assertEqual(totals["total"], 2)
        self.assertEqual(totals[STATUS_ELIGIBLE], 1)
        self.assertEqual(totals[STATUS_NOT_ELIGIBLE], 1)


class TestNewEligibilityGates(unittest.TestCase):
    """Gates added 2026-09-11 for finer shortlisting."""

    def test_gender_gate(self):
        opp = make_opportunity(gender_required="female")
        self.assertEqual(evaluate(UserProfile(gender="female"), opp).overall_status,
                         STATUS_ELIGIBLE)
        self.assertEqual(evaluate(UserProfile(gender="male"), opp).overall_status,
                         STATUS_NOT_ELIGIBLE)

    def test_gender_any_is_not_a_gate(self):
        opp = make_opportunity(gender_required="any")
        result = evaluate(UserProfile(), opp)
        self.assertEqual(find(result, CHECK_GENDER).status, NOT_APPLICABLE)

    def test_unanswered_gender_is_unknown_not_excluded(self):
        opp = make_opportunity(gender_required="female")
        result = evaluate(UserProfile(), opp)
        self.assertEqual(find(result, CHECK_GENDER).status, UNKNOWN)
        self.assertEqual(result.overall_status, STATUS_NEEDS_VERIFICATION)

    def test_english_level_is_ranked(self):
        opp = make_opportunity(min_english_level="intermediate")
        for level, expected in (("none", UNMET), ("basic", UNMET),
                                ("intermediate", MET), ("fluent", MET)):
            with self.subTest(level=level):
                result = evaluate(UserProfile(english_level=level), opp)
                self.assertEqual(find(result, CHECK_ENGLISH).status, expected)

    def test_english_none_is_an_answer_not_a_blank(self):
        """"none" means 'I have no English' - it must screen, not read as unknown."""
        opp = make_opportunity(min_english_level="basic")
        result = evaluate(UserProfile(english_level="none"), opp)
        self.assertEqual(find(result, CHECK_ENGLISH).status, UNMET)
        self.assertNotIn("english_level", result.missing_profile_fields)

    def test_computer_skills_are_ranked(self):
        opp = make_opportunity(min_computer_skills="intermediate")
        self.assertEqual(
            find(evaluate(UserProfile(computer_skills="advanced"), opp),
                 CHECK_COMPUTER).status, MET)
        self.assertEqual(
            find(evaluate(UserProfile(computer_skills="basic"), opp),
                 CHECK_COMPUTER).status, UNMET)

    def test_field_of_study_membership(self):
        opp = make_opportunity(fields_of_study=["engineering", "computer_science"])
        self.assertEqual(
            find(evaluate(UserProfile(field_of_study="engineering"), opp),
                 CHECK_FIELD_OF_STUDY).status, MET)
        self.assertEqual(
            find(evaluate(UserProfile(field_of_study="law"), opp),
                 CHECK_FIELD_OF_STUDY).status, UNMET)

    def test_new_gates_are_na_when_unused(self):
        result = evaluate(UserProfile(), make_opportunity())
        for key in (CHECK_GENDER, CHECK_ENGLISH, CHECK_COMPUTER, CHECK_FIELD_OF_STUDY):
            with self.subTest(key=key):
                self.assertEqual(find(result, key).status, NOT_APPLICABLE)


class TestPriorityGroupsAreAdvantagesOnly(unittest.TestCase):
    """Priority groups must never exclude anyone."""

    def test_matching_group_is_reported(self):
        opp = make_opportunity(priority_groups=["female", "orphan"])
        result = evaluate(UserProfile(gender="female"), opp)
        self.assertEqual(result.matched_priority_groups, ["female"])

    def test_not_matching_does_not_reduce_eligibility(self):
        opp = make_opportunity(priority_groups=["orphan"])
        result = evaluate(UserProfile(gender="male", is_orphan=False), opp)
        self.assertEqual(result.matched_priority_groups, [])
        self.assertEqual(result.overall_status, STATUS_ELIGIBLE)

    def test_priority_groups_add_no_conditions(self):
        with_groups = evaluate(UserProfile(), make_opportunity(priority_groups=["female"]))
        without = evaluate(UserProfile(), make_opportunity())
        self.assertEqual(len(with_groups.checks), len(without.checks))

    def test_disability_and_orphan_are_detected(self):
        opp = make_opportunity(priority_groups=["disability", "orphan", "minority"])
        result = evaluate(UserProfile(has_disability=True, is_orphan=True), opp)
        self.assertEqual(set(result.matched_priority_groups), {"disability", "orphan"})

    def test_priority_matches_rank_higher(self):
        plain = make_opportunity(name="A plain")
        priority = make_opportunity(name="B priority", priority_groups=["female"])
        results = evaluate_all(UserProfile(gender="female"), [plain, priority])
        self.assertEqual(results[0].opportunity.name, "B priority")


if __name__ == "__main__":
    unittest.main()

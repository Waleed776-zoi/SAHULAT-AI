"""
Unit tests for core/rules_engine.py - run with:  python -m pytest tests/
(or just: python -m unittest discover tests)

These tests use zero external dependencies (no Gemini, no chromadb) since
the rules engine must be independently correct - it's the piece the whole
"rules decide, LLM explains" architecture depends on.
"""
import unittest

from core.models import UserProfile, Opportunity, EligibilityConditions
from core.rules_engine import evaluate


def make_opportunity(**kwargs) -> Opportunity:
    conditions = EligibilityConditions(**kwargs)
    return Opportunity(
        opportunity_id="test_opp",
        name="Test Opportunity",
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
        result = evaluate(profile, opp)
        self.assertEqual(result.overall_status, "Likely Eligible")

    def test_hard_fail_on_domicile(self):
        opp = make_opportunity(domicile_provinces=["Balochistan"])
        profile = UserProfile(domicile_province="Punjab")
        result = evaluate(profile, opp)
        self.assertEqual(result.overall_status, "Likely Not Eligible")

    def test_needs_verification_on_missing_data(self):
        opp = make_opportunity(min_marks_percentage=60)
        profile = UserProfile(age=20)  # marks not provided
        result = evaluate(profile, opp)
        self.assertEqual(result.overall_status, "Needs Verification")
        self.assertIn("marks_percentage", result.missing_profile_fields)

    def test_income_ceiling_respected(self):
        opp = make_opportunity(max_monthly_household_income=60000)
        under = evaluate(UserProfile(monthly_household_income=40000), opp)
        over = evaluate(UserProfile(monthly_household_income=80000), opp)
        self.assertEqual(under.overall_status, "Likely Eligible")
        self.assertEqual(over.overall_status, "Likely Not Eligible")

    def test_education_rank_comparison(self):
        opp = make_opportunity(min_education_level="intermediate")
        below = evaluate(UserProfile(education_level="matric"), opp)
        above = evaluate(UserProfile(education_level="bachelor"), opp)
        self.assertEqual(below.overall_status, "Likely Not Eligible")
        self.assertEqual(above.overall_status, "Likely Eligible")

    def test_existing_scholarship_exclusivity(self):
        opp = make_opportunity(must_not_have_existing_scholarship=True)
        already_has_one = evaluate(UserProfile(has_existing_scholarship=True), opp)
        does_not_have_one = evaluate(UserProfile(has_existing_scholarship=False), opp)
        self.assertEqual(already_has_one.overall_status, "Likely Not Eligible")
        self.assertEqual(does_not_have_one.overall_status, "Likely Eligible")

    def test_no_conditions_means_always_eligible(self):
        opp = make_opportunity()  # every condition null
        result = evaluate(UserProfile(), opp)
        self.assertEqual(result.overall_status, "Likely Eligible")

    def test_expired_job_deadline_flagged(self):
        opp = make_opportunity(application_deadline="2020-01-01")
        result = evaluate(UserProfile(), opp)
        deadline_check = [c for c in result.checks if c.label == "Application deadline"][0]
        self.assertEqual(deadline_check.status, "unmet")


if __name__ == "__main__":
    unittest.main()

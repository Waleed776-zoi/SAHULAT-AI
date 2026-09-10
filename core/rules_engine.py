"""
Deterministic eligibility rules engine.

DESIGN PRINCIPLE (do not violate): this module decides eligibility.
The LLM layer (core/llm_client.py) only ever EXPLAINS the output of this
module in natural language - it never re-derives or overrides a match
decision. If you're tempted to "let the model double check," don't -
that reintroduces the exact hallucination risk this architecture exists
to avoid.

Each condition is checked independently and classified as:
  - "met"     -> profile satisfies the condition
  - "unmet"   -> profile fails the condition (hard fact, not a guess)
  - "unknown" -> profile is missing the data needed to check it
  - "n/a"     -> this opportunity doesn't use this condition at all

Overall status:
  - "Likely Not Eligible" -> at least one condition is "unmet"
  - "Needs Verification"  -> no "unmet", but at least one "unknown"
  - "Likely Eligible"     -> every applicable condition is "met"
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List

from core.models import UserProfile, Opportunity, ConditionCheck, MatchResult

EDUCATION_RANK = {
    "matric": 1,
    "intermediate": 2,
    "bachelor": 3,
    "master": 4,
}


def _rank(level: str) -> int:
    return EDUCATION_RANK.get((level or "").lower(), 0)


def evaluate(profile: UserProfile, opportunity: Opportunity) -> MatchResult:
    ec = opportunity.eligibility_conditions
    checks: List[ConditionCheck] = []
    missing: List[str] = []

    # --- age ---
    if ec.min_age is None and ec.max_age is None:
        checks.append(ConditionCheck("Age", "n/a"))
    elif profile.age is None:
        checks.append(ConditionCheck("Age", "unknown", "Age not provided"))
        missing.append("age")
    else:
        ok = True
        detail_parts = []
        if ec.min_age is not None:
            ok = ok and profile.age >= ec.min_age
            detail_parts.append(f"min {ec.min_age}")
        if ec.max_age is not None:
            ok = ok and profile.age <= ec.max_age
            detail_parts.append(f"max {ec.max_age}")
        checks.append(ConditionCheck(
            "Age", "met" if ok else "unmet",
            f"Required: {', '.join(detail_parts)} | You: {profile.age}"
        ))

    # --- domicile ---
    if not ec.domicile_provinces:
        checks.append(ConditionCheck("Domicile", "n/a"))
    elif not profile.domicile_province:
        checks.append(ConditionCheck("Domicile", "unknown", "Domicile province not provided"))
        missing.append("domicile_province")
    else:
        ok = profile.domicile_province.strip().lower() in [
            p.strip().lower() for p in ec.domicile_provinces
        ]
        checks.append(ConditionCheck(
            "Domicile", "met" if ok else "unmet",
            f"Required: {', '.join(ec.domicile_provinces)} | You: {profile.domicile_province}"
        ))

    # --- education level ---
    if not ec.min_education_level:
        checks.append(ConditionCheck("Education level", "n/a"))
    elif not profile.education_level:
        checks.append(ConditionCheck("Education level", "unknown", "Education level not provided"))
        missing.append("education_level")
    else:
        ok = _rank(profile.education_level) >= _rank(ec.min_education_level)
        checks.append(ConditionCheck(
            "Education level", "met" if ok else "unmet",
            f"Required: at least {ec.min_education_level} | You: {profile.education_level}"
        ))

    # --- marks percentage ---
    if ec.min_marks_percentage is None:
        checks.append(ConditionCheck("Academic marks", "n/a"))
    elif profile.marks_percentage is None:
        checks.append(ConditionCheck("Academic marks", "unknown", "Marks percentage not provided"))
        missing.append("marks_percentage")
    else:
        ok = profile.marks_percentage >= ec.min_marks_percentage
        checks.append(ConditionCheck(
            "Academic marks", "met" if ok else "unmet",
            f"Required: at least {ec.min_marks_percentage}% | You: {profile.marks_percentage}%"
        ))

    # --- income ceiling ---
    if ec.max_monthly_household_income is None:
        checks.append(ConditionCheck("Household income", "n/a"))
    elif profile.monthly_household_income is None:
        checks.append(ConditionCheck("Household income", "unknown", "Income not provided"))
        missing.append("monthly_household_income")
    else:
        ok = profile.monthly_household_income <= ec.max_monthly_household_income
        checks.append(ConditionCheck(
            "Household income", "met" if ok else "unmet",
            f"Required: at most Rs. {ec.max_monthly_household_income:,.0f}/month | "
            f"You: Rs. {profile.monthly_household_income:,.0f}/month"
        ))

    # --- currently enrolled ---
    if ec.must_be_currently_enrolled is None:
        checks.append(ConditionCheck("Current enrollment", "n/a"))
    elif profile.currently_enrolled is None:
        checks.append(ConditionCheck("Current enrollment", "unknown", "Enrollment status not provided"))
        missing.append("currently_enrolled")
    else:
        ok = profile.currently_enrolled == ec.must_be_currently_enrolled
        checks.append(ConditionCheck(
            "Current enrollment", "met" if ok else "unmet",
            f"Required: currently enrolled = {ec.must_be_currently_enrolled} | You: {profile.currently_enrolled}"
        ))

    # --- existing scholarship exclusivity ---
    if ec.must_not_have_existing_scholarship is None:
        checks.append(ConditionCheck("No existing scholarship", "n/a"))
    elif profile.has_existing_scholarship is None:
        checks.append(ConditionCheck("No existing scholarship", "unknown", "Not provided"))
        missing.append("has_existing_scholarship")
    else:
        ok = not (ec.must_not_have_existing_scholarship and profile.has_existing_scholarship)
        checks.append(ConditionCheck(
            "No existing scholarship", "met" if ok else "unmet",
            f"You already receive a scholarship: {profile.has_existing_scholarship}"
        ))

    # --- employment status ---
    if not ec.employment_status_required or ec.employment_status_required == "any":
        checks.append(ConditionCheck("Employment status", "n/a"))
    elif not profile.employment_status:
        checks.append(ConditionCheck("Employment status", "unknown", "Not provided"))
        missing.append("employment_status")
    else:
        ok = profile.employment_status.lower() == ec.employment_status_required.lower()
        checks.append(ConditionCheck(
            "Employment status", "met" if ok else "unmet",
            f"Required: {ec.employment_status_required} | You: {profile.employment_status}"
        ))

    # --- experience (jobs) ---
    if ec.min_experience_years is None:
        checks.append(ConditionCheck("Experience", "n/a"))
    elif profile.years_experience is None:
        checks.append(ConditionCheck("Experience", "unknown", "Not provided"))
        missing.append("years_experience")
    else:
        ok = profile.years_experience >= ec.min_experience_years
        checks.append(ConditionCheck(
            "Experience", "met" if ok else "unmet",
            f"Required: at least {ec.min_experience_years} years | You: {profile.years_experience}"
        ))

    # --- application deadline (jobs) - informational, not a profile-based match ---
    if ec.application_deadline:
        try:
            deadline = datetime.strptime(ec.application_deadline, "%Y-%m-%d").date()
            if deadline < date.today():
                checks.append(ConditionCheck(
                    "Application deadline", "unmet",
                    f"Deadline {ec.application_deadline} has already passed - this listing is stale, remove/replace it."
                ))
            else:
                checks.append(ConditionCheck("Application deadline", "met", f"Open until {ec.application_deadline}"))
        except ValueError:
            checks.append(ConditionCheck("Application deadline", "unknown", "Deadline not in YYYY-MM-DD format"))

    # --- roll up overall status ---
    statuses = [c.status for c in checks]
    if "unmet" in statuses:
        overall = "Likely Not Eligible"
    elif "unknown" in statuses:
        overall = "Needs Verification"
    else:
        overall = "Likely Eligible"

    return MatchResult(
        opportunity=opportunity,
        overall_status=overall,
        checks=checks,
        missing_profile_fields=missing,
    )


def evaluate_all(profile: UserProfile, opportunities: List[Opportunity]) -> List[MatchResult]:
    """Evaluate a profile against every opportunity, sorted best-match-first."""
    results = [evaluate(profile, o) for o in opportunities]

    rank_order = {"Likely Eligible": 0, "Needs Verification": 1, "Likely Not Eligible": 2}
    results.sort(key=lambda r: rank_order.get(r.overall_status, 3))
    return results

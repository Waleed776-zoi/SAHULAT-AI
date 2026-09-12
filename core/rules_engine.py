"""
Deterministic eligibility rules engine.

DESIGN PRINCIPLE (do not violate): this module decides eligibility.
The LLM layer (core/llm_client.py) only ever EXPLAINS the output of this
module in natural language - it never re-derives or overrides a match
decision. If you're tempted to "let the model double check," don't -
that reintroduces the exact hallucination risk this architecture exists
to avoid.

LANGUAGE POLICY (I18N-02): this module emits NO user-facing prose. Each
ConditionCheck carries a stable machine `key` plus structured `required` /
`actual` values. core/i18n.describe_check() renders them in English or Urdu.
Keeping this module language-free is what lets it stay independently testable.

Each condition is checked independently and classified as:
  - "met"     -> profile satisfies the condition
  - "unmet"   -> profile fails the condition (hard fact, not a guess)
  - "unknown" -> profile is missing the data needed to check it
  - "n/a"     -> this opportunity doesn't use this condition at all

Overall status (profile-based conditions only):
  - "not_eligible"       -> at least one condition is "unmet"
  - "needs_verification" -> no "unmet", but at least one "unknown"
  - "eligible"           -> every applicable condition is "met"

The application deadline is deliberately NOT part of that roll-up. A closed
listing is a property of the listing, not of the user (BUG-04); it is reported
separately via MatchResult.listing_closed.
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from core.models import (
    UserProfile, Opportunity, ConditionCheck, MatchResult, parse_iso_date,
    STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
    MET, UNMET, UNKNOWN, NOT_APPLICABLE,
    CHECK_AGE, CHECK_DOMICILE, CHECK_EDUCATION, CHECK_MARKS, CHECK_INCOME,
    CHECK_ENROLLMENT, CHECK_EXISTING_SCHOLARSHIP, CHECK_EMPLOYMENT,
    CHECK_EXPERIENCE, CHECK_DEADLINE, CHECK_GENDER, CHECK_ENGLISH,
    CHECK_COMPUTER, CHECK_FIELD_OF_STUDY,
    EDUCATION_RANK, ENGLISH_RANK, COMPUTER_RANK, rank_in,
)


def _rank(level: str) -> int:
    return EDUCATION_RANK.get((level or "").strip().lower(), 0)


def _ranked_check(key, required_level, actual_level, rank_table,
                  checks, missing, missing_field_name):
    """
    Shared 'at least this level' comparison for the ordered vocabularies
    (English, computer skills). Note that the string "none" is a real answer
    meaning the user has none of that skill - only Python None is unanswered.
    """
    if not required_level:
        checks.append(ConditionCheck(key, NOT_APPLICABLE))
        return
    if actual_level is None:
        checks.append(ConditionCheck(key, UNKNOWN, required=required_level))
        missing.append(missing_field_name)
        return
    ok = rank_in(rank_table, actual_level) >= rank_in(rank_table, required_level)
    checks.append(ConditionCheck(key, MET if ok else UNMET,
                                 required=required_level, actual=actual_level))


def _outcome(ok: bool) -> str:
    return MET if ok else UNMET


def evaluate(profile: UserProfile, opportunity: Opportunity,
             today: Optional[date] = None) -> MatchResult:
    """
    Screen one profile against one opportunity.

    `today` is injectable so deadline behaviour is testable without freezing
    the system clock.
    """
    today = today or date.today()
    ec = opportunity.eligibility_conditions
    checks: List[ConditionCheck] = []
    missing: List[str] = []

    # --- age ---
    if ec.min_age is None and ec.max_age is None:
        checks.append(ConditionCheck(CHECK_AGE, NOT_APPLICABLE))
    elif profile.age is None:
        checks.append(ConditionCheck(CHECK_AGE, UNKNOWN,
                                     required={"min": ec.min_age, "max": ec.max_age}))
        missing.append("age")
    else:
        ok = True
        if ec.min_age is not None:
            ok = ok and profile.age >= ec.min_age
        if ec.max_age is not None:
            ok = ok and profile.age <= ec.max_age
        checks.append(ConditionCheck(
            CHECK_AGE, _outcome(ok),
            required={"min": ec.min_age, "max": ec.max_age},
            actual=profile.age,
        ))

    # --- domicile ---
    if not ec.domicile_provinces:
        checks.append(ConditionCheck(CHECK_DOMICILE, NOT_APPLICABLE))
    elif not profile.domicile_province:
        checks.append(ConditionCheck(CHECK_DOMICILE, UNKNOWN,
                                     required=list(ec.domicile_provinces)))
        missing.append("domicile_province")
    else:
        ok = profile.domicile_province.strip().lower() in [
            p.strip().lower() for p in ec.domicile_provinces
        ]
        checks.append(ConditionCheck(
            CHECK_DOMICILE, _outcome(ok),
            required=list(ec.domicile_provinces),
            actual=profile.domicile_province,
        ))

    # --- education level ---
    if not ec.min_education_level:
        checks.append(ConditionCheck(CHECK_EDUCATION, NOT_APPLICABLE))
    elif not profile.education_level:
        checks.append(ConditionCheck(CHECK_EDUCATION, UNKNOWN,
                                     required=ec.min_education_level))
        missing.append("education_level")
    else:
        ok = _rank(profile.education_level) >= _rank(ec.min_education_level)
        checks.append(ConditionCheck(
            CHECK_EDUCATION, _outcome(ok),
            required=ec.min_education_level,
            actual=profile.education_level,
        ))

    # --- marks percentage ---
    if ec.min_marks_percentage is None:
        checks.append(ConditionCheck(CHECK_MARKS, NOT_APPLICABLE))
    elif profile.marks_percentage is None:
        checks.append(ConditionCheck(CHECK_MARKS, UNKNOWN,
                                     required=ec.min_marks_percentage))
        missing.append("marks_percentage")
    else:
        ok = profile.marks_percentage >= ec.min_marks_percentage
        checks.append(ConditionCheck(
            CHECK_MARKS, _outcome(ok),
            required=ec.min_marks_percentage,
            actual=profile.marks_percentage,
        ))

    # --- income ceiling ---
    if ec.max_monthly_household_income is None:
        checks.append(ConditionCheck(CHECK_INCOME, NOT_APPLICABLE))
    elif profile.monthly_household_income is None:
        checks.append(ConditionCheck(CHECK_INCOME, UNKNOWN,
                                     required=ec.max_monthly_household_income))
        missing.append("monthly_household_income")
    else:
        # NOTE: a household income of exactly 0 is a real, valid answer and
        # must screen as "met", not "unknown" - see BUG-03.
        ok = profile.monthly_household_income <= ec.max_monthly_household_income
        checks.append(ConditionCheck(
            CHECK_INCOME, _outcome(ok),
            required=ec.max_monthly_household_income,
            actual=profile.monthly_household_income,
        ))

    # --- currently enrolled ---
    if ec.must_be_currently_enrolled is None:
        checks.append(ConditionCheck(CHECK_ENROLLMENT, NOT_APPLICABLE))
    elif profile.currently_enrolled is None:
        checks.append(ConditionCheck(CHECK_ENROLLMENT, UNKNOWN,
                                     required=ec.must_be_currently_enrolled))
        missing.append("currently_enrolled")
    else:
        ok = profile.currently_enrolled == ec.must_be_currently_enrolled
        checks.append(ConditionCheck(
            CHECK_ENROLLMENT, _outcome(ok),
            required=ec.must_be_currently_enrolled,
            actual=profile.currently_enrolled,
        ))

    # --- existing scholarship exclusivity ---
    if ec.must_not_have_existing_scholarship is None:
        checks.append(ConditionCheck(CHECK_EXISTING_SCHOLARSHIP, NOT_APPLICABLE))
    elif profile.has_existing_scholarship is None:
        checks.append(ConditionCheck(CHECK_EXISTING_SCHOLARSHIP, UNKNOWN,
                                     required=ec.must_not_have_existing_scholarship))
        missing.append("has_existing_scholarship")
    else:
        ok = not (ec.must_not_have_existing_scholarship and profile.has_existing_scholarship)
        checks.append(ConditionCheck(
            CHECK_EXISTING_SCHOLARSHIP, _outcome(ok),
            required=ec.must_not_have_existing_scholarship,
            actual=profile.has_existing_scholarship,
        ))

    # --- employment status ---
    if not ec.employment_status_required or ec.employment_status_required == "any":
        checks.append(ConditionCheck(CHECK_EMPLOYMENT, NOT_APPLICABLE))
    elif not profile.employment_status:
        checks.append(ConditionCheck(CHECK_EMPLOYMENT, UNKNOWN,
                                     required=ec.employment_status_required))
        missing.append("employment_status")
    else:
        ok = profile.employment_status.lower() == ec.employment_status_required.lower()
        checks.append(ConditionCheck(
            CHECK_EMPLOYMENT, _outcome(ok),
            required=ec.employment_status_required,
            actual=profile.employment_status,
        ))

    # --- experience (jobs) ---
    if ec.min_experience_years is None:
        checks.append(ConditionCheck(CHECK_EXPERIENCE, NOT_APPLICABLE))
    elif profile.years_experience is None:
        checks.append(ConditionCheck(CHECK_EXPERIENCE, UNKNOWN,
                                     required=ec.min_experience_years))
        missing.append("years_experience")
    else:
        # As with income, 0 years is a real answer (entry-level) - BUG-03.
        ok = profile.years_experience >= ec.min_experience_years
        checks.append(ConditionCheck(
            CHECK_EXPERIENCE, _outcome(ok),
            required=ec.min_experience_years,
            actual=profile.years_experience,
        ))

    # --- gender (real women-only / men-only programmes) ---
    if not ec.gender_required or ec.gender_required == "any":
        checks.append(ConditionCheck(CHECK_GENDER, NOT_APPLICABLE))
    elif not profile.gender:
        checks.append(ConditionCheck(CHECK_GENDER, UNKNOWN, required=ec.gender_required))
        missing.append("gender")
    else:
        ok = profile.gender.strip().lower() == ec.gender_required.strip().lower()
        checks.append(ConditionCheck(CHECK_GENDER, _outcome(ok),
                                     required=ec.gender_required, actual=profile.gender))

    # --- English proficiency ---
    _ranked_check(CHECK_ENGLISH, ec.min_english_level, profile.english_level,
                  ENGLISH_RANK, checks, missing, "english_level")

    # --- computer / digital skills ---
    _ranked_check(CHECK_COMPUTER, ec.min_computer_skills, profile.computer_skills,
                  COMPUTER_RANK, checks, missing, "computer_skills")

    # --- field of study ---
    if not ec.fields_of_study:
        checks.append(ConditionCheck(CHECK_FIELD_OF_STUDY, NOT_APPLICABLE))
    elif not profile.field_of_study:
        checks.append(ConditionCheck(CHECK_FIELD_OF_STUDY, UNKNOWN,
                                     required=list(ec.fields_of_study)))
        missing.append("field_of_study")
    else:
        ok = profile.field_of_study.strip().lower() in [
            f.strip().lower() for f in ec.fields_of_study
        ]
        checks.append(ConditionCheck(CHECK_FIELD_OF_STUDY, _outcome(ok),
                                     required=list(ec.fields_of_study),
                                     actual=profile.field_of_study))

    # --- roll up the PROFILE-BASED status (deadline excluded on purpose) ---
    statuses = [c.status for c in checks]
    if UNMET in statuses:
        overall = STATUS_NOT_ELIGIBLE
    elif UNKNOWN in statuses:
        overall = STATUS_NEEDS_VERIFICATION
    else:
        overall = STATUS_ELIGIBLE

    # --- application deadline: a property of the LISTING, not of the user ---
    # BUG-04: an expired listing must not make a qualified person read as
    # "Likely Not Eligible". BUG-07: emit an n/a check when unused, so the
    # checks list has a consistent shape for every opportunity.
    listing_closed = False
    deadline_value = ec.application_deadline
    if not deadline_value:
        checks.append(ConditionCheck(CHECK_DEADLINE, NOT_APPLICABLE))
    else:
        deadline = parse_iso_date(deadline_value)
        if deadline is None:
            # Unparseable date - can't claim it's open, can't claim it's closed.
            checks.append(ConditionCheck(CHECK_DEADLINE, UNKNOWN, required=deadline_value))
        elif deadline < today:
            listing_closed = True
            checks.append(ConditionCheck(CHECK_DEADLINE, UNMET,
                                         required=deadline_value, actual=today.isoformat()))
        else:
            checks.append(ConditionCheck(CHECK_DEADLINE, MET,
                                         required=deadline_value, actual=today.isoformat()))

    # --- priority groups -------------------------------------------------
    # An ADVANTAGE, never a gate: belonging to one of these can help an
    # application, but not belonging to one never excludes anybody. These come
    # from the record's explicit `priority_groups` list - they are never
    # inferred from free-text prose.
    matched_groups = []
    if ec.priority_groups:
        stated = {g.strip().lower() for g in ec.priority_groups}
        matched_groups = [g for g in profile.priority_group_memberships() if g in stated]

    return MatchResult(
        opportunity=opportunity,
        overall_status=overall,
        checks=checks,
        missing_profile_fields=missing,
        listing_closed=listing_closed,
        deadline=deadline_value,
        matched_priority_groups=matched_groups,
    )


# Best-match-first ordering. Open listings outrank closed ones at the same
# eligibility level, so a stale entry never crowds out a live one.
_RANK_ORDER = {
    STATUS_ELIGIBLE: 0,
    STATUS_NEEDS_VERIFICATION: 1,
    STATUS_NOT_ELIGIBLE: 2,
}


def evaluate_all(profile: UserProfile, opportunities: List[Opportunity],
                 today: Optional[date] = None) -> List[MatchResult]:
    """Evaluate a profile against every opportunity, sorted best-match-first."""
    results = [evaluate(profile, o, today=today) for o in opportunities]
    results.sort(key=lambda r: (
        _RANK_ORDER.get(r.overall_status, 3),
        r.listing_closed,                     # open before closed
        -len(r.matched_priority_groups),      # priority-group matches first
        -r.confidence_ratio(),                # more confirmed conditions first
        -r.count(MET),
        r.opportunity.name.lower(),           # stable, predictable tie-break
    ))
    return results


def summarize_counts(results: List[MatchResult]) -> dict:
    """Small aggregate used by the results header. No prose - keys only."""
    return {
        STATUS_ELIGIBLE: sum(1 for r in results if r.overall_status == STATUS_ELIGIBLE),
        STATUS_NEEDS_VERIFICATION: sum(
            1 for r in results if r.overall_status == STATUS_NEEDS_VERIFICATION),
        STATUS_NOT_ELIGIBLE: sum(1 for r in results if r.overall_status == STATUS_NOT_ELIGIBLE),
        "closed": sum(1 for r in results if r.listing_closed),
        "total": len(results),
    }

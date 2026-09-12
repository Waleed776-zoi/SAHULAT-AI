"""
Wizard step definitions and profile validation.

Kept out of app.py so the rules that decide "can this person move to the next
step" are unit-testable without Streamlit, exactly like the eligibility rules.

Validation returns machine keys, never prose - core/i18n.py renders the
messages (I18N-02).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from core.models import (
    COMPUTER_LEVELS, EDUCATION_LEVELS, ENGLISH_LEVELS, FIELDS_OF_STUDY,
    GENDERS, PROVINCES, UserProfile,
)

# Sensible human bounds. Anything outside these is a typo, not an answer.
AGE_MIN, AGE_MAX = 14, 70
MARKS_MIN, MARKS_MAX = 0.0, 100.0
INCOME_MAX = 10_000_000.0
EXPERIENCE_MAX = 50.0

# Error codes -> rendered by i18n.validation_message()
ERR_REQUIRED = "required"
ERR_AGE_RANGE = "age_range"
ERR_MARKS_RANGE = "marks_range"
ERR_INCOME_RANGE = "income_range"
ERR_EXPERIENCE_RANGE = "experience_range"
ERR_NO_CATEGORY = "no_category"
ERR_INVALID_CHOICE = "invalid_choice"


@dataclass(frozen=True)
class Step:
    key: str
    title_key: str
    caption_key: str
    fields: Tuple[str, ...]
    required_fields: Tuple[str, ...] = ()


# The wizard. Ordered, and deliberately short - four input steps then results.
STEPS: Tuple[Step, ...] = (
    Step(
        key="focus",
        title_key="step_focus_title",
        caption_key="step_focus_caption",
        fields=("categories",),
        required_fields=("categories",),
    ),
    Step(
        key="about",
        title_key="step_about_title",
        caption_key="step_about_caption",
        fields=("age", "gender", "domicile_province"),
        required_fields=("age", "domicile_province"),
    ),
    Step(
        key="education",
        title_key="step_education_title",
        caption_key="step_education_caption",
        fields=("education_level", "marks_percentage", "field_of_study",
                "currently_enrolled"),
        required_fields=("education_level",),
    ),
    Step(
        key="circumstances",
        title_key="step_circumstances_title",
        caption_key="step_circumstances_caption",
        fields=("monthly_household_income", "has_existing_scholarship",
                "english_level", "computer_skills", "employment_status",
                "years_experience", "has_disability", "is_orphan"),
        required_fields=(),
    ),
    Step(
        key="results",
        title_key="step_results_title",
        caption_key="step_results_caption",
        fields=(),
        required_fields=(),
    ),
)

RESULTS_STEP_INDEX = len(STEPS) - 1

_ALLOWED_VALUES: Dict[str, Tuple[str, ...]] = {
    "gender": GENDERS,
    "domicile_province": PROVINCES,
    "education_level": EDUCATION_LEVELS,
    "field_of_study": FIELDS_OF_STUDY,
    "english_level": ENGLISH_LEVELS,
    "computer_skills": COMPUTER_LEVELS,
    "employment_status": ("employed", "unemployed"),
}


def step_index(key: str) -> int:
    for index, step in enumerate(STEPS):
        if step.key == key:
            return index
    return 0


def validate_field(field_name: str, value) -> Optional[str]:
    """
    Validate one answered value. Returns an error code, or None if fine.

    An unanswered (None) value is NOT an error here - required-ness is handled
    separately by validate_step, because most fields are legitimately optional.
    """
    if value is None:
        return None

    if field_name == "age":
        if not isinstance(value, (int, float)) or not (AGE_MIN <= value <= AGE_MAX):
            return ERR_AGE_RANGE
    elif field_name == "marks_percentage":
        if not isinstance(value, (int, float)) or not (MARKS_MIN <= value <= MARKS_MAX):
            return ERR_MARKS_RANGE
    elif field_name == "monthly_household_income":
        if not isinstance(value, (int, float)) or not (0 <= value <= INCOME_MAX):
            return ERR_INCOME_RANGE
    elif field_name == "years_experience":
        if not isinstance(value, (int, float)) or not (0 <= value <= EXPERIENCE_MAX):
            return ERR_EXPERIENCE_RANGE
    elif field_name in _ALLOWED_VALUES:
        if str(value) not in _ALLOWED_VALUES[field_name]:
            return ERR_INVALID_CHOICE

    return None


def validate_step(step: Step, profile: UserProfile,
                  selected_categories: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Validate one wizard step.

    Returns {field_name: error_code}. An empty dict means the step is complete
    and the user may continue.
    """
    errors: Dict[str, str] = {}

    for field_name in step.fields:
        if field_name == "categories":
            if not selected_categories:
                errors["categories"] = ERR_NO_CATEGORY
            continue

        value = getattr(profile, field_name, None)

        if field_name in step.required_fields and value is None:
            errors[field_name] = ERR_REQUIRED
            continue

        error = validate_field(field_name, value)
        if error:
            errors[field_name] = error

    return errors


def can_advance(step: Step, profile: UserProfile,
                selected_categories: Optional[List[str]] = None) -> bool:
    return not validate_step(step, profile, selected_categories)


def first_incomplete_step(profile: UserProfile,
                          selected_categories: Optional[List[str]] = None) -> int:
    """Index of the earliest step that is not yet complete."""
    for index, step in enumerate(STEPS[:RESULTS_STEP_INDEX]):
        if validate_step(step, profile, selected_categories):
            return index
    return RESULTS_STEP_INDEX


def completion_percent(profile: UserProfile) -> int:
    """How much of the optional detail has been filled in, for a progress hint."""
    return round(100 * profile.known_field_count() / max(profile.total_field_count(), 1))

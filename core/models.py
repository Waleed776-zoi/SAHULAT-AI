"""
Core data models for Sahulat AI.

Deliberately built on plain stdlib dataclasses (no pydantic/heavy deps) so the
rules engine and its tests can run with zero third-party installs. LLM/RAG
layers are free to convert to/from these shapes as needed.

LANGUAGE POLICY: nothing in this module (or in rules_engine.py) stores
user-facing prose. Checks carry a stable machine `key` plus structured
`required`/`actual` values; `core/i18n.py` turns those into English or Urdu
text at render time. See PROJECT_TRACKER.md I18N-02.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Canonical status constants (machine keys, never shown raw to a user)
# ---------------------------------------------------------------------------

STATUS_ELIGIBLE = "eligible"
STATUS_NEEDS_VERIFICATION = "needs_verification"
STATUS_NOT_ELIGIBLE = "not_eligible"

# Per-condition outcomes
MET = "met"
UNMET = "unmet"
UNKNOWN = "unknown"
NOT_APPLICABLE = "n/a"

# Stable condition keys. Used by the rules engine, the i18n layer, and tests.
CHECK_AGE = "age"
CHECK_DOMICILE = "domicile"
CHECK_EDUCATION = "education"
CHECK_MARKS = "marks"
CHECK_INCOME = "income"
CHECK_ENROLLMENT = "enrollment"
CHECK_EXISTING_SCHOLARSHIP = "existing_scholarship"
CHECK_EMPLOYMENT = "employment"
CHECK_EXPERIENCE = "experience"
CHECK_DEADLINE = "deadline"


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """
    Non-identifying attributes only. NEVER add name, CNIC number, phone
    number, or address to this model - see README "Privacy Rules" and
    PROJECT_TRACKER.md Invariant 2.
    """
    age: Optional[int] = None
    domicile_province: Optional[str] = None
    education_level: Optional[str] = None       # matric | intermediate | bachelor | master
    marks_percentage: Optional[float] = None
    monthly_household_income: Optional[float] = None
    currently_enrolled: Optional[bool] = None
    has_existing_scholarship: Optional[bool] = None
    employment_status: Optional[str] = None      # "employed" | "unemployed"
    years_experience: Optional[float] = None
    language: str = "en"                          # "en" | "ur"

    def is_field_known(self, field_name: str) -> bool:
        return getattr(self, field_name, None) is not None

    def known_field_count(self) -> int:
        """How many screening fields the user has actually answered."""
        screening_fields = (
            "age", "domicile_province", "education_level", "marks_percentage",
            "monthly_household_income", "currently_enrolled",
            "has_existing_scholarship", "employment_status", "years_experience",
        )
        return sum(1 for f in screening_fields if self.is_field_known(f))

    def is_empty(self) -> bool:
        return self.known_field_count() == 0


# ---------------------------------------------------------------------------
# Opportunity (scholarship / job / skills / assistance record)
# ---------------------------------------------------------------------------

@dataclass
class EligibilityConditions:
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    domicile_provinces: Optional[List[str]] = None
    min_education_level: Optional[str] = None
    min_marks_percentage: Optional[float] = None
    max_monthly_household_income: Optional[float] = None
    must_be_currently_enrolled: Optional[bool] = None
    must_not_have_existing_scholarship: Optional[bool] = None
    employment_status_required: Optional[str] = None   # "unemployed" | "employed" | "any"
    special_quota_note: Optional[str] = None
    min_experience_years: Optional[float] = None
    application_deadline: Optional[str] = None          # YYYY-MM-DD


def _is_placeholder(value: Optional[str]) -> bool:
    """True if a data field still holds a curation placeholder (TODO / REPLACE ME)."""
    if not value:
        return True
    upper = str(value).strip().upper()
    return upper.startswith("TODO") or upper.startswith("REPLACE ME")


def parse_iso_date(value: Optional[str]):
    """Return a date for a clean YYYY-MM-DD string, else None. Never raises."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@dataclass
class Opportunity:
    opportunity_id: str
    name: str
    category: str                # scholarship | job | skills | assistance
    provider: str
    province_scope: str
    target_group: str
    summary_en: str
    eligibility_conditions: EligibilityConditions
    required_documents: List[str]
    application_steps: List[str]
    official_url: str
    source_title: str
    last_verified: str
    source_type: str = "curated"        # "curated" | "user_uploaded"
    confidence_status: str = "needs_recheck"
    disclaimer: Optional[str] = None
    name_ur: Optional[str] = None
    summary_ur: Optional[str] = None
    source_date: Optional[str] = None

    # -- verification state (DATA-01) ---------------------------------------

    def verified_date(self):
        """The real verification date, or None if never verified / placeholder."""
        return parse_iso_date(self.last_verified)

    def is_verified(self) -> bool:
        """
        True only when a human recorded a real verification date AND the record
        is not still carrying curation placeholders. A `TODO-VERIFY` string must
        never be presented as if it were a date.
        """
        if self.source_type != "curated":
            return False
        if _is_placeholder(self.last_verified):
            return False
        return self.verified_date() is not None and self.confidence_status == "verified"

    def has_placeholder_data(self) -> bool:
        """True if any curation placeholder is still present in key fields."""
        return any(_is_placeholder(v) for v in (self.last_verified, self.source_date))

    # -- localisation (I18N-01) ---------------------------------------------

    def display_name(self, lang: str = "en") -> str:
        if lang == "ur" and self.name_ur and not _is_placeholder(self.name_ur):
            return self.name_ur
        return self.name

    def display_summary(self, lang: str = "en") -> str:
        if lang == "ur" and self.summary_ur and not _is_placeholder(self.summary_ur):
            return self.summary_ur
        return self.summary_en

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Opportunity":
        ec = d.get("eligibility_conditions", {}) or {}
        conditions = EligibilityConditions(
            min_age=ec.get("min_age"),
            max_age=ec.get("max_age"),
            domicile_provinces=ec.get("domicile_provinces"),
            min_education_level=ec.get("min_education_level"),
            min_marks_percentage=ec.get("min_marks_percentage"),
            max_monthly_household_income=ec.get("max_monthly_household_income"),
            must_be_currently_enrolled=ec.get("must_be_currently_enrolled"),
            must_not_have_existing_scholarship=ec.get("must_not_have_existing_scholarship"),
            employment_status_required=ec.get("employment_status_required"),
            special_quota_note=ec.get("special_quota_note"),
            min_experience_years=ec.get("min_experience_years"),
            application_deadline=ec.get("application_deadline"),
        )
        return Opportunity(
            opportunity_id=d["opportunity_id"],
            name=d["name"],
            name_ur=d.get("name_ur"),
            category=d["category"],
            provider=d["provider"],
            province_scope=d.get("province_scope", ""),
            target_group=d.get("target_group", ""),
            summary_en=d.get("summary_en", ""),
            summary_ur=d.get("summary_ur"),
            eligibility_conditions=conditions,
            required_documents=d.get("required_documents", []),
            application_steps=d.get("application_steps", []),
            official_url=d.get("official_url", ""),
            source_title=d.get("source_title", ""),
            source_date=d.get("source_date"),
            last_verified=d.get("last_verified", ""),
            source_type=d.get("source_type", "curated"),
            confidence_status=d.get("confidence_status", "needs_recheck"),
            disclaimer=d.get("disclaimer"),
        )


# ---------------------------------------------------------------------------
# Match result
# ---------------------------------------------------------------------------

@dataclass
class ConditionCheck:
    """
    One eligibility condition, evaluated.

    Carries NO user-facing prose - `key` is a stable machine identifier and
    `required` / `actual` hold structured values. core/i18n.describe_check()
    renders these into English or Urdu.
    """
    key: str
    status: str                      # met | unmet | unknown | n/a
    required: Any = None
    actual: Any = None


@dataclass
class MatchResult:
    opportunity: Opportunity
    overall_status: str              # eligible | needs_verification | not_eligible
    checks: List[ConditionCheck] = field(default_factory=list)
    missing_profile_fields: List[str] = field(default_factory=list)
    # BUG-04: a closed listing is NOT the same thing as the user being
    # ineligible. Tracked separately so the UI can say so.
    listing_closed: bool = False
    deadline: Optional[str] = None

    def applicable_checks(self) -> List[ConditionCheck]:
        """Checks that actually apply to this opportunity (drops the n/a ones)."""
        return [c for c in self.checks if c.status != NOT_APPLICABLE]

    def count(self, status: str) -> int:
        return sum(1 for c in self.applicable_checks() if c.status == status)

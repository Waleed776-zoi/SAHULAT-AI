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
from datetime import date, datetime
from typing import Any, Dict, List, Optional


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
CHECK_GENDER = "gender"
CHECK_ENGLISH = "english"
CHECK_COMPUTER = "computer"
CHECK_FIELD_OF_STUDY = "field_of_study"
CHECK_REQUIRED_GROUP = "required_group"


# ---------------------------------------------------------------------------
# Ordered vocabularies
#
# Each is ranked so "at least X" comparisons are a simple integer test. The
# string "none" is a real, answered value meaning "I have none of this" - it is
# NOT the same as Python None, which means "not answered".
# ---------------------------------------------------------------------------

EDUCATION_LEVELS = ("matric", "intermediate", "bachelor", "master")
EDUCATION_RANK = {level: index + 1 for index, level in enumerate(EDUCATION_LEVELS)}

ENGLISH_LEVELS = ("none", "basic", "intermediate", "fluent")
ENGLISH_RANK = {level: index for index, level in enumerate(ENGLISH_LEVELS)}

COMPUTER_LEVELS = ("none", "basic", "intermediate", "advanced")
COMPUTER_RANK = {level: index for index, level in enumerate(COMPUTER_LEVELS)}

GENDERS = ("female", "male", "other")

FIELDS_OF_STUDY = (
    "engineering", "computer_science", "medical", "natural_sciences",
    "social_sciences", "business", "arts_humanities", "education",
    "agriculture", "law", "other",
)

PROVINCES = (
    "Balochistan", "Punjab", "Sindh", "Khyber Pakhtunkhwa",
    "Azad Jammu & Kashmir", "Gilgit-Baltistan",
    "Islamabad Capital Territory", "Erstwhile FATA",
)

# Listing status is derived from data, never typed into a component (spec 94).
LISTING_OPEN = "open"            # a real future deadline is on record
LISTING_CLOSED = "closed"        # a real deadline that has passed
LISTING_VERIFY = "verify_cycle"  # no deadline on record - do not claim it is open
# Enrolment never closes: applications are taken any day of the year. This is
# NOT the same as LISTING_VERIFY. Both have no date, but one means "nothing to
# miss" and the other means "we do not know" - opposite instructions to a user,
# so they never share a label.
LISTING_ALWAYS_OPEN = "always_open"

# Groups a programme may give priority to. Data-driven: a record must state
# these explicitly in `priority_groups` - they are never inferred from prose.
PRIORITY_GROUPS = ("female", "disability", "orphan", "minority", "under_served_district")

# Which profile answer decides membership of a group. Only these three can be
# screened: nothing in a non-identifying profile establishes religion or
# district, so `minority` and `under_served_district` stay advantage-only and
# can never be used as a gate.
GROUP_PROFILE_FIELD = {
    "female": "gender",
    "disability": "has_disability",
    "orphan": "is_orphan",
}
GATEABLE_GROUPS = tuple(GROUP_PROFILE_FIELD)


def rank_in(vocabulary_rank: Dict[str, int], value: Optional[str]) -> int:
    return vocabulary_rank.get((value or "").strip().lower(), -1)


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

# Fields the wizard treats as required before results can be shown. Everything
# else stays genuinely optional - an unanswered field becomes "unknown", never
# a guess.
REQUIRED_PROFILE_FIELDS = ("age", "domicile_province", "education_level")

SCREENING_FIELDS = (
    "age", "gender", "domicile_province", "education_level", "marks_percentage",
    "field_of_study", "monthly_household_income", "currently_enrolled",
    "has_existing_scholarship", "english_level", "computer_skills",
    "employment_status", "years_experience", "has_disability", "is_orphan",
)


@dataclass
class UserProfile:
    """
    Non-identifying attributes only. NEVER add name, CNIC number, phone
    number, or address to this model - see README "Privacy Rules" and
    PROJECT_TRACKER.md Invariant 2.

    Every attribute here exists because a real published scheme screens on it.
    """
    # Step: about you
    age: Optional[int] = None
    gender: Optional[str] = None                  # female | male | other
    domicile_province: Optional[str] = None

    # Step: education
    education_level: Optional[str] = None         # matric | intermediate | bachelor | master
    marks_percentage: Optional[float] = None
    field_of_study: Optional[str] = None
    currently_enrolled: Optional[bool] = None

    # Step: circumstances
    monthly_household_income: Optional[float] = None
    has_existing_scholarship: Optional[bool] = None
    has_disability: Optional[bool] = None
    is_orphan: Optional[bool] = None

    # Step: skills and work
    english_level: Optional[str] = None           # none | basic | intermediate | fluent
    computer_skills: Optional[str] = None         # none | basic | intermediate | advanced
    employment_status: Optional[str] = None       # employed | unemployed
    years_experience: Optional[float] = None

    language: str = "en"                          # en | ur

    def is_field_known(self, field_name: str) -> bool:
        return getattr(self, field_name, None) is not None

    def known_field_count(self) -> int:
        return sum(1 for f in SCREENING_FIELDS if self.is_field_known(f))

    def total_field_count(self) -> int:
        return len(SCREENING_FIELDS)

    def is_empty(self) -> bool:
        return self.known_field_count() == 0

    def missing_required_fields(self) -> List[str]:
        return [f for f in REQUIRED_PROFILE_FIELDS if not self.is_field_known(f)]

    def is_screenable(self) -> bool:
        """True once the minimum needed for a meaningful result is answered."""
        return not self.missing_required_fields()

    def group_membership(self, group: str) -> Optional[bool]:
        """
        Whether this profile belongs to `group` - True, False, or None for
        "the question behind it was never answered".

        Three-valued on purpose. priority_group_memberships() below collapses
        None and False together, which is correct for an advantage: a bonus you
        cannot evidence is simply a bonus you do not get. A gate has to tell
        them apart, because "not an orphan" is a rejection and "did not say"
        is a question.
        """
        field_name = GROUP_PROFILE_FIELD.get(group)
        if field_name is None:
            return None                     # nothing in the profile answers it
        value = getattr(self, field_name, None)
        if value is None:
            return None
        if group == "female":
            return value == "female"
        return bool(value)

    def priority_group_memberships(self) -> List[str]:
        """Which priority groups this profile belongs to, from answered fields."""
        memberships = []
        if self.gender == "female":
            memberships.append("female")
        if self.has_disability:
            memberships.append("disability")
        if self.is_orphan:
            memberships.append("orphan")
        return memberships


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
    employment_status_required: Optional[str] = None   # unemployed | employed | any
    special_quota_note: Optional[str] = None
    min_experience_years: Optional[float] = None
    application_deadline: Optional[str] = None          # YYYY-MM-DD
    # True when the programme takes applications all year and there is no
    # closing date to miss - distinct from simply having no date on record.
    enrolment_is_continuous: bool = False
    # True when the date above is a stand-in for a cycle that has not been
    # announced yet, rather than a date an authority has published. A deadline
    # renders as a countdown - the most confident statement on the page - so
    # the difference has to survive all the way to the UI.
    deadline_is_provisional: bool = False
    # Added 2026-09-11 to support finer shortlisting.
    gender_required: Optional[str] = None               # female | male | any
    min_english_level: Optional[str] = None             # none | basic | intermediate | fluent
    min_computer_skills: Optional[str] = None           # none | basic | intermediate | advanced
    fields_of_study: Optional[List[str]] = None
    # Advantages, not gates: never used to exclude anyone.
    priority_groups: Optional[List[str]] = None
    # Gates, unlike the line above. Groups the programme is RESTRICTED to - a
    # disability stipend, an orphans' home. Read as OR: any one of them
    # qualifies. Only GATEABLE_GROUPS can appear here.
    required_groups: Optional[List[str]] = None


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
    source_type: str = "curated"        # curated | user_uploaded
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
            enrolment_is_continuous=bool(ec.get("enrolment_is_continuous", False)),
            deadline_is_provisional=bool(ec.get("deadline_is_provisional", False)),
            gender_required=ec.get("gender_required"),
            min_english_level=ec.get("min_english_level"),
            min_computer_skills=ec.get("min_computer_skills"),
            fields_of_study=ec.get("fields_of_study"),
            priority_groups=ec.get("priority_groups"),
            required_groups=ec.get("required_groups"),
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
    deadline_is_provisional: bool = False
    always_open: bool = False
    # Priority groups this profile matches. Advantages only - never a gate.
    matched_priority_groups: List[str] = field(default_factory=list)

    def applicable_checks(self) -> List[ConditionCheck]:
        """Checks that actually apply to this opportunity (drops the n/a ones)."""
        return [c for c in self.checks if c.status != NOT_APPLICABLE]

    def count(self, status: str) -> int:
        return sum(1 for c in self.applicable_checks() if c.status == status)

    def listing_state(self) -> str:
        """
        Open / closed / unknown, derived from the record.

        Never claims a listing is "Open" unless a real future deadline is on
        record - most curated entries legitimately have none, and pretending
        otherwise is exactly the false precision this product avoids.
        """
        if self.listing_closed:
            return LISTING_CLOSED
        if self.deadline and parse_iso_date(self.deadline):
            return LISTING_OPEN
        if self.always_open:
            # Checked after a real deadline, never before: if a record somehow
            # carries both, the date is the more specific claim and wins.
            return LISTING_ALWAYS_OPEN
        return LISTING_VERIFY

    def confidence_ratio(self) -> float:
        """Share of applicable conditions that are confirmed met (0.0-1.0)."""
        applicable = self.applicable_checks()
        if not applicable:
            return 1.0
        return self.count(MET) / len(applicable)

    # -- V2 P0-1 / P0-2: the scorecard, as structure ------------------------
    # These return ConditionCheck objects, never sentences. core/i18n.py
    # renders them; keeping prose out of here is what lets the engine stay
    # language-free and independently testable.

    def satisfied(self) -> List[ConditionCheck]:
        """Conditions the profile demonstrably meets."""
        return [c for c in self.applicable_checks() if c.status == MET]

    def blockers(self) -> List[ConditionCheck]:
        """
        Conditions the profile demonstrably fails.

        These are decisive: one blocker is what makes the whole result
        "not eligible", regardless of how many others passed.
        """
        return [c for c in self.applicable_checks() if c.status == UNMET]

    def gaps(self) -> List[ConditionCheck]:
        """
        Conditions that could not be checked because the profile is missing
        the answer. NOT failures - unanswered is not the same as unqualified.
        """
        return [c for c in self.applicable_checks() if c.status == UNKNOWN]

    def scorecard(self) -> Dict[str, int]:
        """
        Counts behind the scorecard header (P0-1).

        Deliberately a count of conditions, not a percentage of "fit". The
        spec allows "another clearly defined profile-match representation",
        and "4 of 5 stated conditions met" is checkable against the rows
        immediately below it - a percentage would imply a probability of
        success that no rule in this system computes.
        """
        applicable = self.applicable_checks()
        return {
            "met": self.count(MET),
            "unmet": self.count(UNMET),
            "unknown": self.count(UNKNOWN),
            "total": len(applicable),
        }

    def days_until_deadline(self, today=None) -> Optional[int]:
        """Days remaining, or None when no real deadline is on record."""
        parsed = parse_iso_date(self.deadline)
        if parsed is None:
            return None
        return (parsed - (today or date.today())).days


def sample_profile() -> UserProfile:
    """
    A realistic demo profile, so a live demo never stalls on data entry
    (spec section 59). Clearly labelled as demo wherever it is used.
    """
    return UserProfile(
        age=21,
        gender="female",
        domicile_province="Balochistan",
        education_level="intermediate",
        marks_percentage=72.0,
        field_of_study="computer_science",
        currently_enrolled=True,
        monthly_household_income=35000.0,
        has_existing_scholarship=False,
        english_level="intermediate",
        computer_skills="basic",
        employment_status="unemployed",
        years_experience=0.0,
        has_disability=False,
        is_orphan=False,
    )

"""
Core data models for Sahulat AI.

Deliberately built on plain stdlib dataclasses (no pydantic/heavy deps) so the
rules engine and its tests can run with zero third-party installs. LLM/RAG
layers are free to convert to/from these shapes as needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

@dataclass
class UserProfile:
    """
    Non-identifying attributes only. NEVER add name, CNIC number, phone
    number, or address to this model - see README "Privacy Rules".
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
    label: str
    status: str          # "met" | "unmet" | "unknown" | "n/a"
    detail: str = ""


@dataclass
class MatchResult:
    opportunity: Opportunity
    overall_status: str            # "Likely Eligible" | "Needs Verification" | "Likely Not Eligible"
    checks: List[ConditionCheck] = field(default_factory=list)
    missing_profile_fields: List[str] = field(default_factory=list)

"""
Ties together llm_client.extract_opportunity_from_file() and core.models
to produce an Opportunity object tagged source_type="user_uploaded", which
can then be passed through the exact same rules_engine.evaluate() used for
curated catalog entries.

This module NEVER persists the uploaded file - see README privacy rules and
PROJECT_TRACKER.md Invariant 3. Bytes stay in memory for the request only.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Tuple

from core.llm_client import extract_opportunity_from_file
from core.models import (
    EligibilityConditions, FIELDS_OF_STUDY, GENDERS, Opportunity,
)

VALID_CATEGORIES = ("scholarship", "job", "skills", "assistance")
VALID_CONFIDENCE = ("high", "medium", "low")

UPLOAD_DISCLAIMER = (
    "This record was read automatically from a file you uploaded and has not "
    "been verified by the Sahulat AI team. Always confirm details against the "
    "original document or official source before applying."
)


def _clean_category(value: Any) -> str:
    """Only accept a category the rules engine and UI actually understand."""
    if isinstance(value, str) and value.strip().lower() in VALID_CATEGORIES:
        return value.strip().lower()
    return "unknown"


def _clean_confidence(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in VALID_CONFIDENCE:
        return value.strip().lower()
    return "low"


def _clean_choice(value: Any, allowed: tuple) -> Any:
    """
    Keep an extracted value only when it matches a vocabulary the rules engine
    understands. Anything else becomes None.

    Dropping an unrecognised value is deliberate: a mis-mapped gender or field
    of study would be silently applied as a real eligibility gate, and a wrong
    gate excludes people. Unread is recoverable; wrong is not.
    """
    if isinstance(value, str) and value.strip().lower() in allowed:
        return value.strip().lower()
    return None


def _clean_str_list(value: Any) -> list:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def extract_raw(file_bytes: bytes, mime_type: str,
                language: str = "en") -> Dict[str, Any]:
    """
    Stage 1 of 2: ask the model what the document says. Returns the raw dict.

    Split out from read_ad (UX-10) so the UI can show the model call - the
    only genuinely slow step, several seconds - as its own stage, and advance
    the progress display on a real boundary rather than a timer.
    """
    return extract_opportunity_from_file(file_bytes, mime_type, language=language)


def build_record(extracted: Dict[str, Any]) -> Tuple[Opportunity, Dict[str, Any]]:
    """
    Stage 2 of 2: turn the raw extraction into an Opportunity the rules engine
    can screen. Pure and local - no network, no model.
    """
    ec_raw = extracted.get("eligibility_conditions") or {}
    if not isinstance(ec_raw, dict):
        ec_raw = {}

    conditions = EligibilityConditions(
        min_age=ec_raw.get("min_age"),
        max_age=ec_raw.get("max_age"),
        domicile_provinces=ec_raw.get("domicile_provinces"),
        min_education_level=ec_raw.get("min_education_level"),
        min_marks_percentage=ec_raw.get("min_marks_percentage"),
        max_monthly_household_income=ec_raw.get("max_monthly_household_income"),
        must_be_currently_enrolled=ec_raw.get("must_be_currently_enrolled"),
        must_not_have_existing_scholarship=ec_raw.get("must_not_have_existing_scholarship"),
        employment_status_required=ec_raw.get("employment_status_required"),
        special_quota_note=ec_raw.get("special_quota_note"),
        min_experience_years=ec_raw.get("min_experience_years"),
        application_deadline=ec_raw.get("application_deadline"),
        # V2 P0-4: only values the engine has a vocabulary for.
        gender_required=_clean_choice(ec_raw.get("gender_required"), GENDERS),
        fields_of_study=[f for f in (
            _clean_choice(v, FIELDS_OF_STUDY) for v in _clean_str_list(
                ec_raw.get("fields_of_study"))) if f] or None,
    )

    opportunity = Opportunity(
        opportunity_id=f"uploaded_{uuid.uuid4().hex[:8]}",
        name=extracted.get("name") or "Untitled uploaded opportunity",
        category=_clean_category(extracted.get("category")),
        provider=extracted.get("provider") or "Unknown (from user upload)",
        province_scope=extracted.get("province_scope") or "",
        target_group="",
        summary_en=extracted.get("summary_en") or "",
        eligibility_conditions=conditions,
        required_documents=_clean_str_list(extracted.get("required_documents")),
        application_steps=_clean_str_list(extracted.get("application_steps")),
        official_url=extracted.get("official_url_if_visible") or "",
        source_title="User-uploaded document",
        last_verified="",
        # Invariant 4: an uploaded record must never be able to present itself
        # with the same trust level as a curated one.
        source_type="user_uploaded",
        confidence_status=_clean_confidence(extracted.get("extraction_confidence")),
        disclaimer=UPLOAD_DISCLAIMER,
    )

    return opportunity, extracted


def read_ad(file_bytes: bytes, mime_type: str,
            language: str = "en") -> Tuple[Opportunity, Dict[str, Any]]:
    """
    Returns (Opportunity, raw_extracted_dict).

    The raw dict is returned too so the UI can show the user exactly what was
    read BEFORE any eligibility judgment is made - the extraction and the
    verdict must stay visibly separate.
    """
    return build_record(extract_raw(file_bytes, mime_type, language=language))

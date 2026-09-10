"""
Ties together llm_client.extract_opportunity_from_file() and core.models
to produce an Opportunity object tagged source_type="user_uploaded", which
can then be passed through the exact same rules_engine.evaluate() used for
curated catalog entries.

This module NEVER persists the uploaded file - see README privacy rules.
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, Tuple

from core.models import Opportunity, EligibilityConditions
from core.llm_client import extract_opportunity_from_file


def read_ad(file_bytes: bytes, mime_type: str) -> Tuple[Opportunity, Dict[str, Any]]:
    """
    Returns (Opportunity, raw_extracted_dict).
    The raw dict is returned too so the UI can show the user exactly what
    was read before any eligibility judgment is made (see README Section 6
    of the plan - "show extracted fields before judging").
    """
    extracted = extract_opportunity_from_file(file_bytes, mime_type)
    ec_raw = extracted.get("eligibility_conditions", {}) or {}

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
        min_experience_years=ec_raw.get("min_experience_years"),
        application_deadline=ec_raw.get("application_deadline"),
    )

    opportunity = Opportunity(
        opportunity_id=f"uploaded_{uuid.uuid4().hex[:8]}",
        name=extracted.get("name") or "Untitled uploaded opportunity",
        category=extracted.get("category") or "unknown",
        provider=extracted.get("provider") or "Unknown (from user upload)",
        province_scope="",
        target_group="",
        summary_en=extracted.get("summary_en") or "",
        eligibility_conditions=conditions,
        required_documents=extracted.get("required_documents", []) or [],
        application_steps=extracted.get("application_steps", []) or [],
        official_url=extracted.get("official_url_if_visible") or "",
        source_title="User-uploaded document",
        last_verified="",
        source_type="user_uploaded",
        confidence_status=extracted.get("extraction_confidence", "low"),
        disclaimer=(
            "This record was read automatically from a file you uploaded and has not "
            "been verified by the Sahulat AI team. Always confirm details against the "
            "original document or official source before applying."
        ),
    )

    return opportunity, extracted

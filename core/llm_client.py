"""
Thin wrapper around Google's Gemini API.

DESIGN PRINCIPLE: everything in this module EXPLAINS or EXTRACTS. Nothing
here decides eligibility - that stays in core/rules_engine.py. The prompts
below are written to keep that boundary explicit to the model itself.

Set GEMINI_API_KEY as an environment variable or in .streamlit/secrets.toml
(see README). If no key is configured, every function falls back to a
clearly-labeled mock response so the rest of the app (UI, rules engine)
remains fully testable without a key or network access.

SDK SUPPORT (OPS-02): the legacy `google-generativeai` package is end-of-life
and prints a deprecation notice on import. This module prefers the current
`google-genai` SDK when it is installed and transparently falls back to the
legacy one, so the app keeps working either way. To migrate, just run:
    pip install google-genai

FAILURE POLICY (OPS-01): a network error, rate limit or safety block must
never take the page down. Every call is wrapped; on failure the caller gets a
clearly-labelled message and the rules-based result is unaffected.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import os
from functools import lru_cache
from typing import Optional, Dict, Any, List, Tuple

from core.i18n import t

log = logging.getLogger(__name__)

# Confirmed against the live API on 2026-09-11 (OPS-02): `gemini-2.0-flash` had
# been retired and returned 404 for every call. Of the models actually listed
# for this key, gemini-3.5-flash was the fastest that served BOTH the text and
# the image path reliably; gemini-3.8-flash and gemini-flash-latest returned
# 503 under load, and gemini-2.5-flash is closed to new users.
# Override without a code change via the GEMINI_MODEL env var or secret.
DEFAULT_MODEL_NAME = "gemini-3.5-flash"

# Verified working alternative if the default is ever overloaded (503):
#   GEMINI_MODEL=gemini-3.1-flash-lite

SDK_NEW = "google-genai"
SDK_LEGACY = "google-generativeai"


def _get_secret(name: str) -> Optional[str]:
    """Read a setting from the environment, else from Streamlit secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st  # local import - keeps this module usable outside Streamlit
        return st.secrets.get(name)
    except Exception:
        return None


def _get_api_key() -> Optional[str]:
    return _get_secret("GEMINI_API_KEY")


def model_name() -> str:
    return _get_secret("GEMINI_MODEL") or DEFAULT_MODEL_NAME


@lru_cache(maxsize=2)
def _build_client(api_key: str) -> Optional[Tuple[str, Any]]:
    """
    Build the SDK client once per process (PERF-05).

    Constructing `genai.Client` costs ~1.5s. `is_ai_available()` is called on
    every render to draw the AI status chip, so an uncached build added ~3s to
    every single interaction - but ONLY once a real key was configured, which
    is why it never showed up during development in mock mode. Cached on the
    key itself, so rotating the key still rebuilds.
    """
    try:
        from google import genai  # google-genai (current)
        return SDK_NEW, genai.Client(api_key=api_key)
    except ImportError:
        pass
    except Exception as exc:  # malformed key, etc.
        log.warning("google-genai client init failed: %s", exc)

    try:
        import google.generativeai as genai_legacy  # deprecated, still supported
        genai_legacy.configure(api_key=api_key)
        return SDK_LEGACY, genai_legacy
    except ImportError:
        log.warning("No Gemini SDK installed - falling back to mock mode.")
        return None
    except Exception as exc:
        log.warning("Legacy Gemini client init failed: %s", exc)
        return None


def _client() -> Optional[Tuple[str, Any]]:
    """Returns (sdk_flavour, client_object) or None when no key / no SDK."""
    api_key = _get_api_key()
    if not api_key:
        return None
    return _build_client(api_key)


def is_ai_available() -> bool:
    """
    True when a real model call could be made. Used by the UI status chip.

    Deliberately cheap (PERF-05): a key plus an importable SDK, answered with
    `find_spec`, which touches no module. Building a client to answer this cost
    ~3s of first render, because importing `google.genai` (1.45s) and
    constructing the client (1.45s) both happened before the page could draw.

    The trade-off is that a present-but-malformed key reads as available here.
    That is safe: every call path is wrapped, so a bad key surfaces as a
    labelled failure message at the moment of use rather than a crash, and the
    rules-based result - which is what the product actually promises - is
    unaffected either way.
    """
    if not _get_api_key():
        return False
    return any(importlib.util.find_spec(m) is not None
               for m in ("google.genai", "google.generativeai"))


def active_sdk() -> Optional[str]:
    """Which SDK would be used. Does not build a client."""
    if not _get_api_key():
        return None
    if importlib.util.find_spec("google.genai") is not None:
        return SDK_NEW
    if importlib.util.find_spec("google.generativeai") is not None:
        return SDK_LEGACY
    return None


# ---------------------------------------------------------------------------
# Internal: one generation path for both SDKs
# ---------------------------------------------------------------------------

def _generate(system_prompt: str, parts: List[Any]) -> str:
    """
    Run a generation against whichever SDK is active.

    `parts` items are either plain strings or dicts of
    {"mime_type": str, "data": bytes} for file input.
    Raises on failure - callers are responsible for catching (see OPS-01).
    """
    client = _client()
    if client is None:
        raise RuntimeError("No Gemini client configured")

    flavour, handle = client

    if flavour == SDK_NEW:
        from google.genai import types
        contents: List[Any] = []
        for part in parts:
            if isinstance(part, dict):
                contents.append(types.Part.from_bytes(
                    data=part["data"], mime_type=part["mime_type"]))
            else:
                contents.append(part)
        response = handle.models.generate_content(
            model=model_name(),
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        return (response.text or "").strip()

    # Legacy SDK
    model = handle.GenerativeModel(model_name(), system_instruction=system_prompt)
    response = model.generate_content(parts)
    return (response.text or "").strip()


# ---------------------------------------------------------------------------
# 1. Explanation - turn a rules-engine MatchResult into friendly prose
# ---------------------------------------------------------------------------

EXPLAIN_SYSTEM_PROMPT = """You are Sahulat AI's explanation layer.
You are given a user's profile and the OUTPUT of a deterministic eligibility
check that has ALREADY been decided. Your only job is to explain that result
in warm, clear, plain language (English or Urdu, as instructed).

STRICT RULES:
- Do NOT change, second-guess, or re-derive the eligibility outcome you are given.
- Do NOT invent any eligibility criteria not present in the input.
- Do NOT state or imply the user is definitely approved - use the same
  status language provided to you (e.g. "Likely Eligible").
- If documents or steps are provided, you may summarize them, but do not
  add new ones.
- If a condition is marked unknown, say plainly what the user should provide
  to resolve it. Never guess the missing value.
- Keep it concise: 3-6 sentences plus a short bullet list if useful.
"""


def explain_match(profile_summary: str, match_result_summary: str, language: str = "en") -> str:
    if _client() is None:
        return _mock_explanation(match_result_summary, language)

    lang_instruction = "Respond in Urdu." if language == "ur" else "Respond in English."
    prompt = (
        f"{lang_instruction}\n\n"
        f"User profile:\n{profile_summary}\n\n"
        f"Deterministic eligibility result (already decided - explain, do not change):\n"
        f"{match_result_summary}"
    )
    try:
        return _generate(EXPLAIN_SYSTEM_PROMPT, [prompt])
    except Exception as exc:
        log.warning("explain_match failed: %s", exc)
        return t("ai_unavailable", language)


def _mock_explanation(match_result_summary: str, language: str) -> str:
    return f"{t('ai_mock_notice', language)}\n\n{match_result_summary}"


# ---------------------------------------------------------------------------
# 2. Grounded follow-up chat (RAG-style: evidence chunks passed in explicitly)
# ---------------------------------------------------------------------------

CHAT_SYSTEM_PROMPT = """You are Sahulat AI's follow-up chat assistant.
Answer ONLY using the evidence snippets provided to you below. If the
evidence does not contain the answer, say clearly that you don't have
verified information on that and suggest checking the official source link.
Never invent eligibility criteria, amounts, or dates that are not in the
evidence. Keep answers short and cite which opportunity the evidence came from.
"""


def answer_followup(question: str, evidence_snippets: List[str], language: str = "en") -> str:
    # No evidence means no grounded answer is possible. Say so rather than
    # letting the model improvise (BUG-06).
    if not evidence_snippets:
        return t("no_evidence_found", language)

    if _client() is None:
        return _mock_chat_answer(question, language)

    lang_instruction = "Respond in Urdu." if language == "ur" else "Respond in English."
    evidence_block = "\n---\n".join(evidence_snippets)
    prompt = f"{lang_instruction}\n\nEvidence:\n{evidence_block}\n\nQuestion: {question}"
    try:
        return _generate(CHAT_SYSTEM_PROMPT, [prompt])
    except Exception as exc:
        log.warning("answer_followup failed: %s", exc)
        return t("ai_unavailable", language)


def _mock_chat_answer(question: str, language: str) -> str:
    return f"{t('ai_mock_notice', language)}\n\n> {question}"


# ---------------------------------------------------------------------------
# 3. Ad/document extraction (multimodal) - image or PDF -> structured record
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You read an image or PDF of a Pakistani
scholarship, job, or training advertisement and extract ONLY what is
actually stated in the document into the exact JSON schema given below.

STRICT RULES:
- Every field must come directly from the document. If a field is not
  stated in the document, set it to null. NEVER guess or fill in a
  plausible-sounding value.
- Do not translate or infer eligibility rules that are not explicitly written.
- Return ONLY valid JSON matching this schema, nothing else, no markdown fences:

{
  "name": string or null,
  "category": one of "scholarship" | "job" | "skills" | "assistance" | null,
  "provider": string or null,
  "summary_en": string or null,
  "eligibility_conditions": {
    "min_age": number or null,
    "max_age": number or null,
    "domicile_provinces": [string] or null,
    "min_education_level": one of "matric"|"intermediate"|"bachelor"|"master" or null,
    "min_marks_percentage": number or null,
    "max_monthly_household_income": number or null,
    "must_be_currently_enrolled": boolean or null,
    "must_not_have_existing_scholarship": boolean or null,
    "employment_status_required": one of "unemployed"|"employed"|"any" or null,
    "min_experience_years": number or null,
    "application_deadline": "YYYY-MM-DD" or null
  },
  "required_documents": [string],
  "application_steps": [string],
  "official_url_if_visible": string or null,
  "extraction_confidence": one of "high"|"medium"|"low"
}
"""


def _strip_code_fences(raw: str) -> str:
    """Gemini sometimes wraps JSON in ``` fences despite instructions."""
    text = raw.strip()
    if not text.startswith("```"):
        return text
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_opportunity_from_file(file_bytes: bytes, mime_type: str,
                                  language: str = "en") -> Dict[str, Any]:
    """
    Takes raw bytes of an uploaded image or PDF and returns a dict shaped
    like the schema above. Falls back to a clearly-labeled mock structure
    if no API key is configured, so the rest of the pipeline (UI, rules
    engine comparison) can still be developed/tested without a live key.
    """
    if _client() is None:
        return _mock_extraction(language)

    file_part = {"mime_type": mime_type, "data": file_bytes}
    try:
        raw_text = _generate(EXTRACTION_SYSTEM_PROMPT,
                             [file_part, "Extract the structured record now."])
    except Exception as exc:
        log.warning("extract_opportunity_from_file failed: %s", exc)
        return {
            "name": None,
            "category": None,
            "summary_en": t("ai_unavailable", language),
            "eligibility_conditions": {},
            "required_documents": [],
            "application_steps": [],
            "official_url_if_visible": None,
            "extraction_confidence": "low",
            "_error": str(exc),
        }

    cleaned = _strip_code_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("Top-level JSON value is not an object")
        return parsed
    except (json.JSONDecodeError, ValueError) as exc:
        return {
            "name": None,
            "category": None,
            "eligibility_conditions": {},
            "required_documents": [],
            "application_steps": [],
            "extraction_confidence": "low",
            "_raw_model_output": cleaned,
            "_error": f"Model did not return valid JSON ({exc}) - "
                      f"show raw output to user for manual review.",
        }


def _mock_extraction(language: str = "en") -> Dict[str, Any]:
    return {
        "name": None,
        "category": None,
        "provider": None,
        "summary_en": t("ai_mock_extraction_notice", language),
        "eligibility_conditions": {},
        "required_documents": [],
        "application_steps": [],
        "official_url_if_visible": None,
        "extraction_confidence": "low",
        "_mock": True,
    }

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


# Reasons an answer is not a real model answer. Machine values; i18n words them.
REASON_OFFLINE = "offline"          # no key configured
REASON_ERROR = "error"              # the call failed
REASON_NO_EVIDENCE = "no_evidence"  # nothing grounded to answer from


class AiText(str):
    """
    A model answer that knows whether it actually is one (P2-5).

    A plain string cannot tell the UI the difference between an explanation
    and the sentence we print when the call failed, so both used to render
    identically - in the same blue box, looking equally authoritative. That is
    the failure this class exists to prevent.

    It subclasses `str` deliberately: every existing caller keeps working
    unchanged, and the extra state is additive rather than a migration.
    """
    ok: bool
    reason: str

    def __new__(cls, text: str, ok: bool = True, reason: str = ""):
        value = super().__new__(cls, text)
        value.ok = ok
        value.reason = reason
        return value


def _language_instruction(language: str) -> str:
    """
    How to tell the model which language to answer in (P2-1).

    Roman Urdu needs spelling out: asked for "Urdu", a model returns Urdu
    script, which is precisely what a Roman Urdu reader chose not to have.
    """
    if language == "ur":
        return "Respond in Urdu."
    if language == "ur_roman":
        return ("Respond in Roman Urdu - the Urdu language written in Latin script, "
                "the way Pakistanis type in everyday messages. Do NOT use Urdu script. "
                "Keep common English words (scholarship, documents, deadline) as they are.")
    return "Respond in English."


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


def explain_match(profile_summary: str, match_result_summary: str,
                  language: str = "en") -> AiText:
    """
    Plain-language explanation of a decision the rules engine already made.

    Always returns an AiText. When `.ok` is False the text is a notice, not an
    explanation, and the UI must present it as such - the eligibility result
    itself is rules-based and unaffected either way.
    """
    if _client() is None:
        return AiText(_mock_explanation(match_result_summary, language),
                      ok=False, reason=REASON_OFFLINE)

    lang_instruction = _language_instruction(language)
    prompt = (
        f"{lang_instruction}\n\n"
        f"User profile:\n{profile_summary}\n\n"
        f"Deterministic eligibility result (already decided - explain, do not change):\n"
        f"{match_result_summary}"
    )
    try:
        return AiText(_generate(EXPLAIN_SYSTEM_PROMPT, [prompt]))
    except Exception as exc:
        log.warning("explain_match failed: %s", exc)
        # The exception text is logged, never shown: "Gemini API error 429"
        # tells a scholarship applicant nothing they can act on.
        return AiText(t("ai_unavailable", language), ok=False, reason=REASON_ERROR)


def _mock_explanation(match_result_summary: str, language: str) -> str:
    return f"{t('ai_mock_notice', language)}\n\n{match_result_summary}"


SIMPLIFY_SYSTEM_PROMPT = """You rewrite Pakistani government opportunity
listings into plain, simple language for someone who finds official documents
hard to read. Many readers have limited formal education, so write the way you
would speak to a neighbour.

YOU ARE A TRANSLATOR, NOT AN ADVISOR. Every sentence you write must be
traceable to a fact given to you below.

ABSOLUTE RULES:
- Use ONLY the facts provided. Never add a requirement, amount, date, quota or
  benefit that is not written in them. A reader may miss a real deadline or
  give up on a scholarship they qualify for because of an invented detail.
- Never simplify a condition into something weaker or stronger. "At least 60%
  marks" does not become "good marks". Keep every number exactly as given.
- Never say whether this particular reader is eligible, likely to be selected,
  or should apply. That decision is made elsewhere and is not yours.
- If a section has no facts to draw on, say plainly that the document does not
  state it. Do not fill the gap.
- Short sentences. No jargon. No bureaucratic phrasing.

Return ONLY valid JSON, no markdown fences, exactly this shape:

{
  "who_is_this_for": string,
  "what_you_get": string,
  "who_can_apply": string,
  "what_you_need": string,
  "where_to_apply": string
}
"""

SIMPLIFY_SECTIONS = ("who_is_this_for", "what_you_get", "who_can_apply",
                     "what_you_need", "where_to_apply")


def simplify_opportunity(facts: str, language: str = "en") -> Dict[str, Any]:
    """
    Plain-language version of one opportunity (P1-7).

    `facts` must contain ONLY what the record itself states - the caller builds
    it from structured fields, never from an eligibility result. The model is
    given no profile and no verdict, so it has nothing to reinterpret: it
    cannot tell the reader they qualify because it has not been told.

    Returns a dict of the sections above, plus "_error"/"_mock" markers the UI
    uses to label the output honestly. Never raises.
    """
    if _client() is None:
        return {**_mock_simplification(facts, language), "_mock": True}

    lang_instruction = _language_instruction(language) + " Use simple words."
    try:
        raw = _generate(SIMPLIFY_SYSTEM_PROMPT,
                        [f"{lang_instruction}\n\nFacts from the record:\n{facts}"])
    except Exception as exc:
        log.warning("simplify_opportunity failed: %s", exc)
        return {"_error": str(exc)}

    try:
        parsed = json.loads(_strip_code_fences(raw))
        if not isinstance(parsed, dict):
            raise ValueError("Top-level JSON value is not an object")
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("simplify_opportunity returned non-JSON: %s", exc)
        return {"_error": str(exc), "_raw_model_output": raw}

    # Keep only the sections we asked for, as strings. An unexpected key is
    # not rendered: this output goes on screen as plain guidance, so anything
    # unrecognised is dropped rather than displayed.
    return {section: str(parsed[section]).strip()
            for section in SIMPLIFY_SECTIONS
            if isinstance(parsed.get(section), (str, int, float)) and str(parsed[section]).strip()}


def _mock_simplification(facts: str, language: str) -> Dict[str, Any]:
    """Offline stand-in. Clearly labelled, and invents nothing."""
    return {"who_can_apply": f"{t('ai_mock_notice', language)}\n\n{facts}"}


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


def answer_followup(question: str, evidence_snippets: List[str],
                    language: str = "en") -> AiText:
    """
    Answer a question from supplied evidence only. Always returns an AiText.

    `.ok` is False for all three non-answers - no evidence, no key, failed
    call - because each of them is a notice the UI must present differently
    from an answer, however similar they look as text.
    """
    # No evidence means no grounded answer is possible. Say so rather than
    # letting the model improvise (BUG-06).
    if not evidence_snippets:
        return AiText(t("no_evidence_found", language),
                      ok=False, reason=REASON_NO_EVIDENCE)

    if _client() is None:
        return AiText(_mock_chat_answer(question, language),
                      ok=False, reason=REASON_OFFLINE)

    lang_instruction = _language_instruction(language)
    evidence_block = "\n---\n".join(evidence_snippets)
    prompt = f"{lang_instruction}\n\nEvidence:\n{evidence_block}\n\nQuestion: {question}"
    try:
        return AiText(_generate(CHAT_SYSTEM_PROMPT, [prompt]))
    except Exception as exc:
        log.warning("answer_followup failed: %s", exc)
        return AiText(t("ai_unavailable", language), ok=False, reason=REASON_ERROR)


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
- "gender_required" is ONLY for a document that explicitly restricts applications
  to one gender. A scholarship that merely mentions women, or prioritises them,
  is NOT gender-restricted: leave it null. Getting this wrong wrongly excludes
  people, which is worse than leaving a condition unread.
- "province_scope" is the region the opportunity covers, if the document says so.
- Return ONLY valid JSON matching this schema, nothing else, no markdown fences:

{
  "name": string or null,
  "category": one of "scholarship" | "job" | "skills" | "assistance" | null,
  "provider": string or null,
  "summary_en": string or null,
  "province_scope": string or null,
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
    "gender_required": one of "female"|"male" or null,
    "fields_of_study": [string] or null,
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

"""
Thin wrapper around Google's Gemini API.

DESIGN PRINCIPLE: everything in this module EXPLAINS or EXTRACTS. Nothing
here decides eligibility - that stays in core/rules_engine.py. The prompts
below are written to keep that boundary explicit to the model itself.

Set GEMINI_API_KEY as an environment variable or in .streamlit/secrets.toml
(see README). If no key is configured, every function falls back to a
clearly-labeled mock response so the rest of the app (UI, rules engine)
remains fully testable without a key or network access.
"""
from __future__ import annotations

import json
import os
from typing import Optional, Dict, Any, List

MODEL_NAME = "gemini-2.0-flash"  # confirm current recommended free-tier Flash model name before building


def _get_api_key() -> Optional[str]:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st  # local import - keeps this module usable outside Streamlit too
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _client():
    """Returns a configured genai client, or None if no key is available."""
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        return genai
    except ImportError:
        return None


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
- Keep it concise: 3-6 sentences plus a short bullet list if useful.
"""


def explain_match(profile_summary: str, match_result_summary: str, language: str = "en") -> str:
    client = _client()
    if client is None:
        return _mock_explanation(match_result_summary, language)

    model = client.GenerativeModel(MODEL_NAME, system_instruction=EXPLAIN_SYSTEM_PROMPT)
    lang_instruction = "Respond in Urdu." if language == "ur" else "Respond in English."
    prompt = (
        f"{lang_instruction}\n\n"
        f"User profile:\n{profile_summary}\n\n"
        f"Deterministic eligibility result (already decided - explain, do not change):\n"
        f"{match_result_summary}"
    )
    response = model.generate_content(prompt)
    return response.text


def _mock_explanation(match_result_summary: str, language: str) -> str:
    if language == "ur":
        return f"[مقامی موڈ - کوئی Gemini کلید موجود نہیں]\n\n{match_result_summary}"
    return f"[Local mock mode - no Gemini API key configured]\n\n{match_result_summary}"


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
    client = _client()
    if client is None:
        return _mock_chat_answer(question, language)

    model = client.GenerativeModel(MODEL_NAME, system_instruction=CHAT_SYSTEM_PROMPT)
    lang_instruction = "Respond in Urdu." if language == "ur" else "Respond in English."
    evidence_block = "\n---\n".join(evidence_snippets) if evidence_snippets else "(no evidence retrieved)"
    prompt = f"{lang_instruction}\n\nEvidence:\n{evidence_block}\n\nQuestion: {question}"
    response = model.generate_content(prompt)
    return response.text


def _mock_chat_answer(question: str, language: str) -> str:
    if language == "ur":
        return "[مقامی موڈ] یہ سوال کا جواب دینے کے لیے Gemini API کلید درکار ہے۔"
    return f"[Local mock mode] A configured Gemini API key is needed to answer: '{question}'"


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


def extract_opportunity_from_file(file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """
    Takes raw bytes of an uploaded image or PDF and returns a dict shaped
    like the schema above. Falls back to a clearly-labeled mock structure
    if no API key is configured, so the rest of the pipeline (UI, rules
    engine comparison) can still be developed/tested without a live key.
    """
    client = _client()
    if client is None:
        return _mock_extraction()

    model = client.GenerativeModel(MODEL_NAME, system_instruction=EXTRACTION_SYSTEM_PROMPT)
    file_part = {"mime_type": mime_type, "data": file_bytes}
    response = model.generate_content([file_part, "Extract the structured record now."])

    raw_text = response.text.strip()
    # Gemini sometimes wraps JSON in ``` fences despite instructions - strip defensively.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "name": None,
            "category": None,
            "extraction_confidence": "low",
            "_raw_model_output": raw_text,
            "_error": "Model did not return valid JSON - show raw output to user for manual review.",
        }


def _mock_extraction() -> Dict[str, Any]:
    return {
        "name": "[Local mock mode - no Gemini API key configured]",
        "category": None,
        "provider": None,
        "summary_en": "Configure GEMINI_API_KEY to enable real ad reading.",
        "eligibility_conditions": {},
        "required_documents": [],
        "application_steps": [],
        "official_url_if_visible": None,
        "extraction_confidence": "low",
    }

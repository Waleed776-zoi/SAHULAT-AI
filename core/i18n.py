"""
Bilingual string table and check renderer.

This module owns ALL user-facing prose. core/rules_engine.py and core/models.py
deliberately contain none (see PROJECT_TRACKER.md I18N-02) - they emit stable
machine keys plus structured values, and describe_check() below turns those
into English or Urdu at render time.

Kept as a plain dict rather than a heavy i18n framework: the app needs exactly
two languages and a fixed set of strings.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from core.i18n_roman import ROMAN
from core.models import (
    ConditionCheck,
    STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
    MET, UNMET, UNKNOWN, NOT_APPLICABLE,
    CHECK_AGE, CHECK_DOMICILE, CHECK_EDUCATION, CHECK_MARKS, CHECK_INCOME,
    CHECK_ENROLLMENT, CHECK_EXISTING_SCHOLARSHIP, CHECK_EMPLOYMENT,
    CHECK_EXPERIENCE, CHECK_DEADLINE, CHECK_GENDER, CHECK_ENGLISH,
    CHECK_COMPUTER, CHECK_FIELD_OF_STUDY, CHECK_REQUIRED_GROUP,
)

LANG_EN = "en"
LANG_UR = "ur"
LANG_ROMAN = "ur_roman"          # Urdu written in Latin script
LANGUAGES = (LANG_EN, LANG_UR, LANG_ROMAN)

# What each mode calls itself, in itself.
LANGUAGE_NAMES = {
    LANG_EN: "English",
    LANG_UR: "\u0627\u0631\u062f\u0648",
    LANG_ROMAN: "Roman Urdu",
}


def is_rtl(lang: str) -> bool:
    """
    Only Urdu script is right-to-left.

    Roman Urdu is Urdu *language* in Latin *script*, so it lays out and sets
    type exactly like English. Treating it as RTL - the obvious mistake, since
    it is "the Urdu one" - would mirror the whole page for no reason.
    """
    return lang == LANG_UR


def normalise_lang(lang: str) -> str:
    """Fall back to English for anything we do not ship."""
    return lang if lang in LANGUAGES else LANG_EN


STRINGS: Dict[str, Dict[str, str]] = {
    # -- identity -----------------------------------------------------------
    "app_title": {"en": "Sahulat AI", "ur": "سہولت اے آئی"},
    "app_subtitle": {
        "en": "Pakistan Opportunity & Services Navigator",
        "ur": "پاکستان مواقع اور خدمات نیویگیٹر",
    },
    "app_tagline": {
        "en": "Find scholarships, jobs and training you may qualify for — or upload an ad and ask.",
        "ur": "وہ اسکالرشپ، نوکریاں اور تربیتی پروگرام تلاش کریں جن کے آپ اہل ہو سکتے ہیں — یا کوئی اشتہار اپلوڈ کریں۔",
    },
    "disclaimer_banner": {
        "en": "Sahulat AI is an informational pre-screening tool, not an official government service. "
              "Final eligibility must be verified through the official program channel.",
        "ur": "سہولت اے آئی ایک معلوماتی پری اسکریننگ ٹول ہے، سرکاری سروس نہیں۔ حتمی اہلیت کی تصدیق سرکاری ذریعے سے کریں۔",
    },

    # -- trust chips on the hero -------------------------------------------
    "chip_no_cnic": {"en": "No CNIC or name asked", "ur": "شناختی کارڈ یا نام نہیں پوچھا جاتا"},
    "chip_rules_based": {"en": "Rules-based, not guesswork", "ur": "قواعد پر مبنی، اندازہ نہیں"},
    "chip_official_sources": {"en": "Linked to official sources", "ur": "سرکاری ذرائع سے منسلک"},
    "chip_bilingual": {"en": "English & Urdu", "ur": "انگریزی اور اردو"},

    # -- navigation ---------------------------------------------------------
    "tab_find": {"en": "Find opportunities", "ur": "مواقع تلاش کریں"},
    "tab_upload": {"en": "Read an ad", "ur": "اشتہار پڑھیں"},
    "tab_how": {"en": "How it works", "ur": "یہ کیسے کام کرتا ہے"},

    # -- steps --------------------------------------------------------------
    "step_1_title": {"en": "Choose what you're looking for", "ur": "منتخب کریں کہ آپ کیا تلاش کر رہے ہیں"},
    "step_2_title": {"en": "Tell us about yourself", "ur": "اپنے بارے میں بتائیں"},
    "step_3_title": {"en": "See your results", "ur": "اپنے نتائج دیکھیں"},
    "step_label": {"en": "Step", "ur": "مرحلہ"},

    # -- categories ---------------------------------------------------------
    "select_category": {"en": "What are you looking for?", "ur": "آپ کیا تلاش کر رہے ہیں؟"},
    "category_scholarship": {"en": "Scholarships", "ur": "اسکالرشپس"},
    "category_job": {"en": "Jobs", "ur": "نوکریاں"},
    "category_skills": {"en": "Skills & Training", "ur": "ہنر اور تربیت"},
    "category_assistance": {"en": "Public Assistance", "ur": "سرکاری امداد"},
    "category_unknown": {"en": "Other", "ur": "دیگر"},
    "coming_soon": {"en": "Coming soon", "ur": "جلد آ رہا ہے"},
    "available_count": {"en": "{n} available", "ur": "{n} دستیاب"},
    "no_categories_selected": {
        "en": "Select at least one category above to see matches.",
        "ur": "مماثل مواقع دیکھنے کے لیے اوپر کم از کم ایک زمرہ منتخب کریں۔",
    },
    "category_empty_note": {
        "en": "No verified records in this category yet, so it is switched off. "
              "See PROJECT_TRACKER.md (DATA-03).",
        "ur": "اس زمرے میں ابھی کوئی تصدیق شدہ ریکارڈ موجود نہیں، اس لیے یہ بند ہے۔",
    },

    # -- profile form -------------------------------------------------------
    "profile_heading": {"en": "Tell us a bit about yourself", "ur": "اپنے بارے میں کچھ بتائیں"},
    "profile_privacy_note": {
        "en": "We never ask for your name, CNIC, phone number or address. "
              "Nothing you type here is stored after you close the page.",
        "ur": "ہم کبھی آپ کا نام، شناختی کارڈ نمبر، فون نمبر یا پتہ نہیں پوچھتے۔ "
              "صفحہ بند کرنے کے بعد یہاں لکھی گئی کوئی بھی چیز محفوظ نہیں رہتی۔",
    },
    "optional_hint": {
        "en": "Every field is optional — leave anything blank and we'll mark it "
              "\"needs verification\" instead of guessing.",
        "ur": "ہر خانہ اختیاری ہے — کوئی بھی خانہ خالی چھوڑ دیں، ہم اندازہ لگانے کے بجائے "
              "اسے \"تصدیق درکار\" لکھ دیں گے۔",
    },
    "field_age": {"en": "Age", "ur": "عمر"},
    "field_domicile": {"en": "Domicile province", "ur": "ڈومیسائل صوبہ"},
    "field_education": {"en": "Highest education level", "ur": "اعلیٰ ترین تعلیمی سطح"},
    "field_marks": {"en": "Marks in last exam (%)", "ur": "آخری امتحان میں فیصد نمبر"},
    "field_income": {"en": "Monthly household income (PKR)", "ur": "ماہانہ گھریلو آمدنی (روپے)"},
    "field_enrolled": {"en": "Currently a full-time student?", "ur": "کیا آپ اس وقت فل ٹائم طالب علم ہیں؟"},
    "field_existing_scholarship": {"en": "Already receiving another scholarship?", "ur": "کیا پہلے سے کوئی اور اسکالرشپ مل رہی ہے؟"},
    "field_employment": {"en": "Employment status", "ur": "ملازمت کی صورتحال"},
    "field_experience": {"en": "Years of work experience", "ur": "کام کا تجربہ (سال)"},
    "placeholder_not_answered": {"en": "Prefer not to say", "ur": "بتانا نہیں چاہتے"},
    "option_yes": {"en": "Yes", "ur": "جی ہاں"},
    "option_no": {"en": "No", "ur": "جی نہیں"},
    "option_employed": {"en": "Employed", "ur": "برسرِ روزگار"},
    "option_unemployed": {"en": "Unemployed", "ur": "بے روزگار"},
    "edu_matric": {"en": "Matric", "ur": "میٹرک"},
    "edu_intermediate": {"en": "Intermediate", "ur": "انٹرمیڈیٹ"},
    "edu_bachelor": {"en": "Bachelor's", "ur": "بیچلر"},
    "edu_master": {"en": "Master's", "ur": "ماسٹر"},
    "see_matches": {"en": "See my matches", "ur": "میرے مواقع دکھائیں"},
    "update_matches": {"en": "Update my matches", "ur": "نتائج اپ ڈیٹ کریں"},
    "reset_profile": {"en": "Clear", "ur": "صاف کریں"},
    "profile_completeness": {"en": "{answered} of {total} answered", "ur": "{total} میں سے {answered} مکمل"},

    # -- results ------------------------------------------------------------
    "results_heading": {"en": "Your results", "ur": "آپ کے نتائج"},
    "results_intro": {
        "en": "Screened against {n} record(s). These are informational only — always confirm "
              "with the official source before applying.",
        "ur": "{n} ریکارڈ کے مقابلے میں جانچا گیا۔ یہ صرف معلوماتی ہے — درخواست سے پہلے "
              "سرکاری ذریعے سے تصدیق ضرور کریں۔",
    },
    "status_eligible": {"en": "Likely match", "ur": "غالباً موزوں"},
    "status_needs_verification": {"en": "Needs Verification", "ur": "تصدیق درکار"},
    "status_not_eligible": {"en": "Does not currently match", "ur": "فی الحال موزوں نہیں"},
    "listing_closed": {"en": "Applications closed", "ur": "درخواستیں بند"},
    "listing_closed_explainer": {
        "en": "The deadline for this listing has passed. This is about the listing, "
              "not about you — your eligibility above is unchanged.",
        "ur": "اس اشتہار کی آخری تاریخ گزر چکی ہے۔ اس کا تعلق اشتہار سے ہے، آپ سے نہیں — "
              "آپ کی اہلیت پر کوئی فرق نہیں پڑتا۔",
    },
    "group_eligible_help": {
        "en": "You appear to meet every condition we could check.",
        "ur": "آپ ان تمام شرائط پر پورا اترتے دکھائی دیتے ہیں جو ہم جانچ سکے۔",
    },
    "group_needs_verification_help": {
        "en": "Nothing rules you out — but some details are still missing.",
        "ur": "کوئی چیز آپ کو خارج نہیں کرتی — لیکن کچھ تفصیلات ابھی درکار ہیں۔",
    },
    "group_not_eligible_help": {
        "en": "At least one stated condition does not match your profile.",
        "ur": "کم از کم ایک بیان کردہ شرط آپ کی معلومات سے میل نہیں کھاتی۔",
    },
    "no_results": {
        "en": "No opportunities loaded for the selected categories yet.",
        "ur": "منتخب زمروں کے لیے ابھی کوئی مواقع دستیاب نہیں۔",
    },
    "fill_profile_prompt": {
        "en": "Fill in the form above and select \"See my matches\" to screen your profile.",
        "ur": "اوپر فارم بھریں اور \"میرے مواقع دکھائیں\" منتخب کریں۔",
    },
    "missing_fields_hint": {
        "en": "Answer {fields} to turn this into a clearer result.",
        "ur": "واضح نتیجے کے لیے {fields} کا جواب دیں۔",
    },

    # -- match card ---------------------------------------------------------
    "why_match": {"en": "Why this result?", "ur": "یہ نتیجہ کیوں؟"},
    "ai_explain_button": {"en": "Explain this in plain language", "ur": "آسان زبان میں سمجھائیں"},
    "required_documents": {"en": "Required documents", "ur": "درکار دستاویزات"},
    "document_checklist_heading": {"en": "Document readiness checklist", "ur": "دستاویزات کی تیاری کی فہرست"},
    "documents_ready": {"en": "{have} of {total} ready", "ur": "{total} میں سے {have} تیار"},
    "application_steps": {"en": "How to apply", "ur": "درخواست کیسے دیں"},
    "official_source": {"en": "Official source", "ur": "سرکاری ذریعہ"},
    "open_official_site": {"en": "Open official site", "ur": "سرکاری ویب سائٹ کھولیں"},
    "last_verified": {"en": "Last verified", "ur": "آخری تصدیق"},
    "provider_label": {"en": "Provider", "ur": "ادارہ"},
    "deadline_label": {"en": "Deadline", "ur": "آخری تاریخ"},
    "quota_note_label": {"en": "Special quotas & exemptions", "ur": "خصوصی کوٹہ اور استثنیٰ"},

    # -- trust badges (must never be merged - Invariant 4) ------------------
    "ai_extracted_badge": {
        "en": "AI-read from your upload — verify against the original",
        "ur": "یہ اے آئی نے آپ کی اپلوڈ سے پڑھا ہے — اصل دستاویز سے تصدیق کریں",
    },
    "officially_verified_badge": {"en": "Officially verified", "ur": "سرکاری طور پر تصدیق شدہ"},
    "unverified_badge": {"en": "Not yet verified by our team", "ur": "ہماری ٹیم نے ابھی تصدیق نہیں کی"},
    "unverified_explainer": {
        "en": "This record was researched but a team member has not yet confirmed it against "
              "the official source. Treat the numbers as indicative, not final.",
        "ur": "یہ ریکارڈ تحقیق سے لیا گیا ہے لیکن ابھی تک سرکاری ذریعے سے تصدیق نہیں ہوئی۔ "
              "اعداد و شمار کو حتمی نہ سمجھیں۔",
    },

    # -- upload tab ---------------------------------------------------------
    "upload_ad_heading": {"en": "Upload an ad, poster or PDF", "ur": "اشتہار، پوسٹر یا پی ڈی ایف اپلوڈ کریں"},
    "upload_ad_intro": {
        "en": "Photograph any scholarship, job or training advertisement. Sahulat AI will read "
              "it, show you exactly what it found, and then screen it against your profile "
              "using the same rules as our verified records.",
        "ur": "کسی بھی اسکالرشپ، نوکری یا تربیتی اشتہار کی تصویر لیں۔ سہولت اے آئی اسے پڑھے گا، "
              "جو کچھ ملا وہ دکھائے گا، اور پھر انہی قواعد سے آپ کی معلومات کے ساتھ جانچے گا۔",
    },
    "upload_ad_button": {"en": "Read this ad", "ur": "یہ اشتہار پڑھیں"},
    "upload_clear": {"en": "Remove this upload", "ur": "یہ اپلوڈ ہٹا دیں"},
    "upload_privacy_note": {
        "en": "Your file is processed in memory for this request only. It is never saved to "
              "disk and never shared.",
        "ur": "آپ کی فائل صرف اسی درخواست کے لیے استعمال ہوتی ہے۔ اسے کبھی محفوظ نہیں کیا جاتا۔",
    },
    "extracted_fields_heading": {"en": "What we read from your file", "ur": "ہم نے آپ کی فائل سے کیا پڑھا"},
    "extraction_confidence": {"en": "Extraction confidence", "ur": "استخراج کا اعتماد"},
    "confidence_high": {"en": "High", "ur": "زیادہ"},
    "confidence_medium": {"en": "Medium", "ur": "درمیانہ"},
    "confidence_low": {"en": "Low", "ur": "کم"},
    "screen_uploaded": {"en": "Screen this against my profile", "ur": "میری معلومات کے ساتھ جانچیں"},
    "upload_needs_profile": {
        "en": "Fill in your profile on the \"Find opportunities\" tab first — then come back "
              "and we'll screen this ad against it.",
        "ur": "پہلے \"مواقع تلاش کریں\" ٹیب میں اپنی معلومات بھریں — پھر واپس آئیں۔",
    },
    "raw_extraction_toggle": {"en": "Show exactly what the model returned",
                              "ur": "ماڈل نے بالکل کیا لوٹایا، وہ دیکھیں"},
    "raw_extraction_note": {
        "en": "The unedited JSON, kept so you can audit any field above against the original document.",
        "ur": "غیر ترمیم شدہ JSON، تاکہ آپ اوپر دی گئی ہر تفصیل کو اصل دستاویز سے جانچ سکیں۔"},

    # --- staged reading (UX-10) ---
    "stage_prepare": {"en": "Preparing your file", "ur": "آپ کی فائل تیار کی جا رہی ہے"},
    "stage_read": {"en": "Reading the document with AI", "ur": "دستاویز کو AI سے پڑھا جا رہا ہے"},
    "stage_structure": {"en": "Structuring what it says", "ur": "معلومات کو ترتیب دیا جا رہا ہے"},
    "stage_screen": {"en": "Checking it against your answers",
                     "ur": "آپ کے جوابات سے جانچا جا رہا ہے"},
    # -- staged progress for the AI calls (V3) --
    "stage_ask_understand": {"en": "Understanding your question",
                             "ur": "آپ کا سوال سمجھا جا رہا ہے"},
    "stage_ask_search": {"en": "Searching the records we hold",
                         "ur": "ہمارے پاس موجود اندراجات میں تلاش جاری ہے"},
    "stage_ask_gather": {"en": "Gathering the closest matches",
                         "ur": "قریب ترین اندراجات جمع کیے جا رہے ہیں"},
    "stage_ask_write": {"en": "Writing the answer, with its sources",
                        "ur": "جواب لکھا جا رہا ہے، حوالوں کے ساتھ"},
    "stage_explain_profile": {"en": "Reading your answers",
                              "ur": "آپ کے جوابات پڑھے جا رہے ہیں"},
    "stage_explain_decision": {"en": "Reading the rules engine's decision",
                               "ur": "قواعد کے انجن کا فیصلہ پڑھا جا رہا ہے"},
    "stage_explain_write": {"en": "Putting it in plain words",
                            "ur": "اسے آسان الفاظ میں بیان کیا جا رہا ہے"},
    "stage_simplify_read": {"en": "Reading the official wording",
                            "ur": "سرکاری عبارت پڑھی جا رہی ہے"},
    "stage_simplify_write": {"en": "Rewriting it simply",
                             "ur": "اسے آسان زبان میں دوبارہ لکھا جا رہا ہے"},
    "stage_running_note_ai": {
        "en": "This runs on Google's servers and takes a few seconds. Nothing you type "
              "is stored, and the answer can only use the records shown on this page.",
        "ur": "یہ عمل گوگل کے سرورز پر ہوتا ہے اور چند سیکنڈ لیتا ہے۔ آپ کا لکھا ہوا محفوظ نہیں کیا جاتا، "
              "اور جواب صرف اسی صفحے پر دکھائے گئے اندراجات سے بن سکتا ہے۔"},
    "stage_running_note_local": {
        "en": "Working from the records on this page. No AI key is configured, so the "
              "wording below is a stand-in.",
        "ur": "اسی صفحے کے اندراجات سے کام کیا جا رہا ہے۔ کوئی AI کلید موجود نہیں، اس لیے نیچے کی "
              "عبارت عارضی ہے۔"},
    "stage_running_note": {
        "en": "Reading happens on Google's servers and takes a few seconds. Your file is not stored.",
        "ur": "پڑھنے کا عمل گوگل کے سرورز پر ہوتا ہے اور چند سیکنڈ لیتا ہے۔ آپ کی فائل محفوظ نہیں کی جاتی۔"},

    # --- presenting the extraction (UX-10) ---
    "extracted_requirements": {"en": "Conditions stated in this document",
                               "ur": "اس دستاویز میں بیان کردہ شرائط"},
    "extracted_nothing": {
        "en": "This document did not state any eligibility condition we could read.",
        "ur": "اس دستاویز میں کوئی ایسی شرط نہیں ملی جو ہم پڑھ سکتے۔"},
    "extracted_not_stated": {"en": "Not stated in this document", "ur": "اس دستاویز میں درج نہیں"},
    "extracted_not_stated_note": {
        "en": "Nothing was found about these, so they are not checked against you. That is not the same as qualifying.",
        "ur": "ان کے بارے میں کچھ نہیں ملا، اس لیے یہ آپ پر لاگو نہیں کی جاتیں۔ اس کا مطلب اہلیت نہیں۔"},
    "extracted_documents": {"en": "Documents it asks for", "ur": "مطلوبہ دستاویزات"},
    "extracted_steps": {"en": "How to apply, as stated", "ur": "درخواست کا طریقہ، جیسا درج ہے"},
    "extracted_deadline": {"en": "Deadline stated", "ur": "آخری تاریخ درج ہے"},
    "extracted_quota": {"en": "Preference noted", "ur": "ترجیح درج ہے"},
    "extracted_category": {"en": "Read as", "ur": "کس قسم کے طور پر پڑھا گیا"},

    # ================= V2 P0-1: eligibility scorecard =====================
    "scorecard_heading": {"en": "Eligibility scorecard", "ur": "اہلیت کا تفصیلی جائزہ"},
    "scorecard_summary": {
        "en": "{met} of {total} stated conditions met",
        "ur": "{total} میں سے {met} شرائط پوری"},
    "scorecard_summary_extra": {
        "en": "{unmet} not met · {unknown} need verification",
        "ur": "{unmet} پوری نہیں · {unknown} کی تصدیق درکار"},
    "scorecard_no_score_note": {
        "en": "This is a count of the conditions below, not a percentage chance of success. "
              "The official rules decide, not this number.",
        "ur": "یہ نیچے دی گئی شرائط کی گنتی ہے، کامیابی کے امکان کا تناسب نہیں۔ فیصلہ سرکاری قواعد کرتے ہیں، یہ عدد نہیں۔"},
    "col_requirement": {"en": "Requirement", "ur": "شرط"},
    "col_your_answer": {"en": "Your information", "ur": "آپ کی معلومات"},
    "col_result": {"en": "Result", "ur": "نتیجہ"},
    "result_passed": {"en": "Passed", "ur": "پوری"},
    "result_failed": {"en": "Not met", "ur": "پوری نہیں"},
    "result_verify": {"en": "Verification required", "ur": "تصدیق درکار"},

    # ================= V2 P0-2: why / why not / what changes ==============
    "why_you_match": {"en": "Why you match", "ur": "آپ کیوں اہل ہیں"},
    "why_you_dont": {"en": "Why you don't currently match", "ur": "آپ فی الحال کیوں اہل نہیں"},
    "what_needs_verification": {"en": "What needs verification", "ur": "کس چیز کی تصدیق درکار ہے"},
    "what_would_change": {"en": "What would change this", "ur": "اس میں کیا فرق ڈال سکتا ہے"},
    "gap_line": {
        "en": "This requires {required}. Your profile says {actual}.",
        "ur": "اس کے لیے {required} درکار ہے۔ آپ کی معلومات کے مطابق {actual}۔"},
    "gap_unknown_line": {
        "en": "This requires {required}. Your profile does not answer this yet.",
        "ur": "اس کے لیے {required} درکار ہے۔ آپ نے ابھی اس کا جواب نہیں دیا۔"},
    "what_would_change_caveat": {
        "en": "Meeting this does not by itself make you eligible - the other conditions "
              "still apply, and only the awarding body decides.",
        "ur": "صرف یہ شرط پوری کرنے سے اہلیت ثابت نہیں ہوتی — باقی شرائط بھی لاگو ہیں، اور فیصلہ متعلقہ ادارہ ہی کرتا ہے۔"},
    "decisive_note": {
        "en": "One unmet condition is enough to change the result, however many others passed.",
        "ur": "ایک شرط پوری نہ ہو تو نتیجہ بدل جاتا ہے، چاہے باقی سب پوری ہوں۔"},

    # ================= V2 P0-3: top matches ===============================
    "top_matches_heading": {"en": "Your top opportunities", "ur": "آپ کے لیے بہترین مواقع"},
    "top_matches_lede": {
        "en": "Ranked by structured facts only - status, conditions confirmed, deadline. "
              "No model opinion is involved in this order.",
        "ur": "ترتیب صرف حقائق پر ہے — حیثیت، تصدیق شدہ شرائط، آخری تاریخ۔ اس ترتیب میں ماڈل کی رائے شامل نہیں۔"},
    "top_matches_empty": {
        "en": "Nothing qualifies for this shortlist yet. Your full results are below.",
        "ur": "ابھی کوئی موقع اس فہرست کے لیے موزوں نہیں۔ آپ کے مکمل نتائج نیچے ہیں۔"},
    "rank_reason_all_met": {"en": "All {total} stated conditions met", "ur": "تمام {total} شرائط پوری"},
    "rank_reason_met": {"en": "{met} of {total} conditions met", "ur": "{total} میں سے {met} شرائط پوری"},
    "rank_reason_priority": {"en": "you match the {groups} priority group",
                             "ur": "آپ {groups} ترجیحی زمرے میں آتے ہیں"},
    "rank_reason_deadline": {"en": "closes in {days} days", "ur": "{days} دن میں بند"},
    "rank_reason_verify": {"en": "{unknown} still to confirm", "ur": "{unknown} کی تصدیق باقی"},

    # ================= V2 P0-6: next best action ==========================
    "next_step_label": {"en": "Next step", "ur": "اگلا قدم"},
    "action_explore_others": {
        "en": "Explore your other matching opportunities - this listing has closed.",
        "ur": "اپنے دیگر موزوں مواقع دیکھیں — یہ اشتہار بند ہو چکا ہے۔"},
    "action_review_blocker": {
        "en": "Check the {subject} requirement against the official source before applying.",
        "ur": "درخواست سے پہلے {subject} کی شرط سرکاری ذریعے سے دیکھ لیں۔"},
    "action_answer_missing_one": {
        "en": "Answer one more question so this can be checked - {subject}",
        "ur": "ایک اور سوال کا جواب دیں تاکہ اسے جانچا جا سکے — {subject}"},
    "action_answer_missing_many": {
        "en": "Answer {count} more questions so these conditions can be checked.",
        "ur": "{count} مزید سوالات کے جواب دیں تاکہ یہ شرائط جانچی جا سکیں۔"},
    "action_confirm_condition": {
        "en": "Confirm the {subject} requirement from the official source.",
        "ur": "{subject} کی شرط سرکاری ذریعے سے تصدیق کریں۔"},
    "action_prepare_documents": {
        "en": "Prepare the {subject} documents this opportunity asks for.",
        "ur": "اس موقع کے لیے مطلوبہ {subject} دستاویزات تیار کریں۔"},
    "action_apply": {"en": "Apply through the official source.",
                     "ur": "سرکاری ذریعے سے درخواست دیں۔"},
    "action_check_source": {"en": "Read the official source for the current details.",
                            "ur": "موجودہ تفصیلات کے لیے سرکاری ذریعہ پڑھیں۔"},
    "action_answer_now": {"en": "Answer this now", "ur": "ابھی جواب دیں"},

    # ================= V2 P0-7: responsible AI showcase ===================
    "architecture_heading": {"en": "AI does not decide your eligibility",
                             "ur": "آپ کی اہلیت کا فیصلہ AI نہیں کرتا"},
    "architecture_body": {
        "en": "Eligibility is computed by deterministic rules from the conditions each "
              "authority publishes. The language model only explains a decision that has "
              "already been made, and it cannot change one.",
        "ur": "اہلیت کا تعین متعین قواعد سے ہوتا ہے جو ہر ادارے کی شائع کردہ شرائط پر مبنی ہیں۔ زبان کا ماڈل صرف پہلے سے کیے گئے فیصلے کی وضاحت کرتا ہے، اسے بدل نہیں سکتا۔"},
    "architecture_upload_label": {"en": "Uploaded document", "ur": "اپلوڈ کردہ دستاویز"},
    "architecture_curated_label": {"en": "Curated record", "ur": "ہماری تیار کردہ اندراج"},
    "architecture_same_engine": {
        "en": "Both paths end in the same rules engine. An uploaded poster is screened by "
              "exactly the code that screens a curated record.",
        "ur": "دونوں راستے ایک ہی رولز انجن پر ختم ہوتے ہیں۔ اپلوڈ کردہ اشتہار کو بالکل اسی کوڈ سے جانچا جاتا ہے جو ہمارے اندراجات کو جانچتا ہے۔"},
    "pipeline_extract": {"en": "AI reads the document into structured fields",
                         "ur": "AI دستاویز کو ساختہ خانوں میں پڑھتا ہے"},

    # ================= V2 P0-8: landing ===================================
    "home_paths_heading": {"en": "Choose a path", "ur": "اپنا راستہ منتخب کریں"},
    "path_scholarship": {"en": "Find a scholarship", "ur": "اسکالرشپ تلاش کریں"},
    "path_job": {"en": "Find a job", "ur": "نوکری تلاش کریں"},
    "path_skills": {"en": "Learn a skill", "ur": "ہنر سیکھیں"},
    "path_assistance": {"en": "Find support", "ur": "مدد تلاش کریں"},
    "path_check_ad": {"en": "Check an advertisement", "ur": "اشتہار کی جانچ کریں"},
    "correct_heading": {"en": "Correct what was read", "ur": "پڑھی گئی معلومات درست کریں"},
    "correct_note": {
        "en": "Reading a photo is not perfect. Fix anything that does not match the original "
              "document, and the screening below will be re-run against your corrections.",
        "ur": "تصویر سے پڑھنا ہمیشہ درست نہیں ہوتا۔ جو بات اصل دستاویز سے مطابقت نہ رکھے اسے درست کریں، جانچ دوبارہ کی جائے گی۔"},
    "correct_apply": {"en": "Apply corrections and re-screen", "ur": "درستگی لاگو کریں اور دوبارہ جانچیں"},
    "correct_applied": {
        "en": "Screened against your corrections, not the original reading.",
        "ur": "یہ جانچ آپ کی درست کردہ معلومات پر کی گئی ہے، اصل پڑھائی پر نہیں۔"},
    "correct_deadline_hint": {"en": "Format: YYYY-MM-DD", "ur": "شکل: سال-مہینہ-دن"},
    "correct_none": {"en": "Not stated", "ur": "درج نہیں"},
    "path_start": {"en": "Start here", "ur": "یہاں سے شروع کریں"},
    "hero_preview_alt": {
        "en": "A preview of Sahulat results: an opportunity, the conditions checked, "
              "and the next step.",
        "ur": "سہولت کے نتائج کی جھلک: ایک موقع، جانچی گئی شرائط، اور اگلا قدم۔"},
    "hero_preview_note": {
        "en": "Real results from our catalogue, screened for the demo profile - one from "
              "each category, not an illustration.",
        "ur": "یہ ہماری فہرست سے حقیقی نتائج ہیں، نمونہ پروفائل پر جانچے گئے - ہر زمرے سے ایک، "
              "کوئی تصویری نمونہ نہیں۔"},
    "home_upload_hint": {
        "en": "Opens the Sahulat Lens.",
        "ur": "سہولت لینز کھولتا ہے۔"},
    "path_check_ad_body": {
        "en": "Found a poster, screenshot or PDF elsewhere? Have it read and screened.",
        "ur": "کہیں کوئی اشتہار، اسکرین شاٹ یا PDF ملا؟ اسے پڑھوا کر جانچ لیں۔"},
    "benefits_heading": {"en": "Why Sahulat", "ur": "سہولت کیوں"},
    "benefit_personal_title": {"en": "Personalised", "ur": "ذاتی نوعیت کا"},
    "benefit_personal_body": {"en": "Matched to the profile you enter, not a generic list.",
                              "ur": "آپ کی دی گئی معلومات کے مطابق، عام فہرست نہیں۔"},
    "benefit_evidence_title": {"en": "Evidence-based", "ur": "شواہد پر مبنی"},
    "benefit_evidence_body": {
        "en": "Eligibility comes from structured rules, with the source shown for every record.",
        "ur": "اہلیت متعین قواعد سے نکلتی ہے، اور ہر اندراج کا ماخذ دکھایا جاتا ہے۔"},
    "benefit_bilingual_title": {"en": "Bilingual", "ur": "دو لسانی"},
    "benefit_bilingual_body": {"en": "English and Urdu across the whole journey.",
                               "ur": "پورے سفر میں انگریزی اور اردو۔"},
    "benefit_realworld_title": {"en": "Works with real-world ads", "ur": "اصل اشتہارات پر کام کرتا ہے"},
    "benefit_realworld_body": {"en": "Upload a poster or PDF you found anywhere else.",
                               "ur": "کہیں سے بھی ملا اشتہار یا PDF اپلوڈ کریں۔"},

    # ================= P1-1: application readiness ========================
    "readiness_heading": {"en": "Application readiness", "ur": "درخواست کی تیاری"},
    "readiness_percent": {"en": "{percent}% ready", "ur": "{percent}% تیار"},
    "readiness_none": {"en": "Nothing ticked yet", "ur": "ابھی کچھ منتخب نہیں"},
    "documents_you_have": {"en": "Documents you have", "ur": "آپ کے پاس موجود دستاویزات"},
    "documents_still_needed": {"en": "Still needed", "ur": "ابھی درکار"},
    "readiness_note": {
        "en": "This tracks the checklist you fill in. It does not check that a document "
              "is valid, current or accepted - only the issuing office can do that.",
        "ur": "یہ صرف آپ کی بھری ہوئی فہرست دکھاتا ہے۔ یہ نہیں جانچتا کہ دستاویز درست، موجودہ یا قابلِ قبول ہے — یہ صرف متعلقہ دفتر طے کر سکتا ہے۔"},
    "action_obtain_document": {
        "en": "Obtain the next document you are missing - {subject}",
        "ur": "اگلی درکار دستاویز حاصل کریں — {subject}"},

    # ================= P1-2: deadline intelligence ========================
    "urgency_passed": {"en": "Deadline passed", "ur": "آخری تاریخ گزر چکی"},
    "urgency_imminent": {"en": "Deadline approaching", "ur": "آخری تاریخ قریب"},
    "urgency_soon": {"en": "Apply soon", "ur": "جلد درخواست دیں"},
    "urgency_plenty": {"en": "Plenty of time", "ur": "کافی وقت باقی"},
    "urgency_unknown": {"en": "No deadline on record", "ur": "آخری تاریخ درج نہیں"},
    "days_remaining": {"en": "{days} days remaining", "ur": "{days} دن باقی"},
    "days_remaining_one": {"en": "1 day remaining", "ur": "1 دن باقی"},
    "days_remaining_today": {"en": "Last day today", "ur": "آج آخری دن"},
    "days_since_passed": {"en": "Closed {days} days ago", "ur": "{days} دن پہلے بند ہوا"},
    "urgency_unknown_note": {
        "en": "We have no application deadline for this record. Check the official source "
              "before assuming it is still open.",
        "ur": "اس اندراج کے لیے ہمارے پاس کوئی آخری تاریخ نہیں۔ کھلا ہونے کا اندازہ لگانے سے پہلے سرکاری ذریعہ دیکھیں۔"},
    "urgency_passed_note": {
        "en": "Applications are closed. Nothing here is worth preparing until the next cycle opens.",
        "ur": "درخواستیں بند ہیں۔ اگلا مرحلہ کھلنے تک یہاں کچھ تیار کرنے کی ضرورت نہیں۔"},

    # ================= P1-3: contextual follow-up =========================
    "ask_about_this": {"en": "Ask about this opportunity", "ur": "اس موقع کے بارے میں پوچھیں"},
    "ask_scoped_note": {
        "en": "Answers use only this record's own text as evidence.",
        "ur": "جوابات صرف اسی اندراج کے متن کو بطور شواہد استعمال کرتے ہیں۔"},
    "chip_why_eligible": {"en": "Why am I eligible?", "ur": "میں کیوں اہل ہوں؟"},
    "chip_why_not_eligible": {"en": "Why am I not eligible?", "ur": "میں کیوں اہل نہیں؟"},
    "chip_what_verify": {"en": "What needs verification?", "ur": "کس چیز کی تصدیق درکار ہے؟"},
    "chip_this_deadline": {"en": "What is the deadline?", "ur": "آخری تاریخ کیا ہے؟"},
    "chip_where_apply": {"en": "Where do I apply?", "ur": "درخواست کہاں دوں؟"},
    "chip_this_documents": {"en": "What documents do I need?", "ur": "کون سی دستاویزات چاہئیں؟"},

    # ================= P1-4: opportunity passport =========================
    "passport_heading": {"en": "My opportunity passport", "ur": "میرا مواقع پاسپورٹ"},
    "passport_lede": {
        "en": "Answer once, reuse everywhere. These details are matched against every "
              "opportunity you open, including ads you upload.",
        "ur": "ایک بار جواب دیں، ہر جگہ استعمال کریں۔ یہ تفصیلات ہر موقع پر لاگو ہوتی ہیں، بشمول اپلوڈ کیے گئے اشتہارات۔"},
    "passport_privacy": {
        "en": "No CNIC, name, phone number or address is asked for or stored. Your answers "
              "stay in this browser session and are cleared when you start over.",
        "ur": "شناختی کارڈ، نام، فون نمبر یا پتہ نہ مانگا جاتا ہے نہ محفوظ کیا جاتا ہے۔ آپ کے جوابات صرف اس سیشن میں رہتے ہیں۔"},
    "passport_complete": {"en": "{percent}% complete", "ur": "{percent}% مکمل"},
    "passport_reuse": {"en": "Using your saved answers", "ur": "آپ کے محفوظ جوابات استعمال ہو رہے ہیں"},

    # ================= P1-5: comparison ===================================
    "compare_heading": {"en": "Compare opportunities", "ur": "مواقع کا موازنہ"},
    "compare_hint": {"en": "Pick two or more to compare side by side.",
                     "ur": "موازنے کے لیے دو یا زیادہ منتخب کریں۔"},
    "compare_factor": {"en": "Factor", "ur": "پہلو"},
    "compare_eligibility": {"en": "Eligibility", "ur": "اہلیت"},
    "compare_conditions": {"en": "Conditions met", "ur": "پوری شرائط"},
    "compare_deadline": {"en": "Deadline", "ur": "آخری تاریخ"},
    "compare_documents": {"en": "Documents still needed", "ur": "درکار دستاویزات"},
    "compare_verification": {"en": "Open questions", "ur": "زیرِ التوا سوالات"},
    "compare_apply": {"en": "Official link", "ur": "سرکاری ربط"},
    "compare_easiest": {
        "en": "{name} looks less work to pursue: {reasons}.",
        "ur": "{name} کے لیے نسبتاً کم محنت درکار ہے: {reasons}۔"},
    "compare_reason_fewer_blockers": {"en": "fewer unmet conditions", "ur": "کم غیر پوری شرائط"},
    "compare_reason_fewer_gaps": {"en": "fewer open questions", "ur": "کم زیرِ التوا سوالات"},
    "compare_reason_fewer_documents": {"en": "fewer documents left to gather",
                                       "ur": "کم دستاویزات جمع کرنا باقی"},
    "compare_effort_caveat": {
        "en": "This compares effort, not value. It says nothing about which award is worth "
              "more or which you are more likely to receive.",
        "ur": "یہ محنت کا موازنہ ہے، فائدے کا نہیں۔ یہ نہیں بتاتا کہ کون سا وظیفہ زیادہ بہتر ہے یا ملنے کا امکان زیادہ ہے۔"},
    "compare_too_close": {
        "en": "These look about equally involved. Choose on what the award actually offers.",
        "ur": "دونوں تقریباً برابر محنت طلب ہیں۔ فیصلہ اس بنیاد پر کریں کہ کیا پیشکش ہے۔"},

    # ================= P1-6: freshness ====================================
    "freshness_heading": {"en": "Information freshness", "ur": "معلومات کی تازگی"},
    "freshness_recent": {"en": "Recently verified", "ur": "حال ہی میں تصدیق شدہ"},
    "freshness_aging": {"en": "Verification recommended", "ur": "تصدیق کی سفارش"},
    "freshness_stale": {"en": "Likely out of date", "ur": "غالباً پرانی"},
    "freshness_never": {"en": "Never verified by us", "ur": "ہماری طرف سے کبھی تصدیق نہیں"},
    "freshness_days": {"en": "Checked {days} days ago", "ur": "{days} دن پہلے جانچا گیا"},
    "freshness_today": {"en": "Checked today", "ur": "آج جانچا گیا"},
    "freshness_yesterday": {"en": "Checked yesterday", "ur": "کل جانچا گیا"},
    "freshness_never_note": {
        "en": "Nobody on our team has confirmed this record against the official source. "
              "Being in the catalogue is not evidence that it is current.",
        "ur": "ہماری ٹیم نے اس اندراج کی سرکاری ذریعے سے تصدیق نہیں کی۔ فہرست میں ہونا موجودہ ہونے کا ثبوت نہیں۔"},
    "freshness_prompt": {
        "en": "Confirm the details on the official page before you rely on them.",
        "ur": "ان تفصیلات پر انحصار سے پہلے سرکاری صفحے پر تصدیق کریں۔"},

    # ================= P1-7: explain like I'm new =========================
    "eli5_heading": {"en": "In plain language", "ur": "آسان زبان میں"},
    "eli5_button": {"en": "Explain this simply", "ur": "آسان الفاظ میں سمجھائیں"},
    "eli5_who_is_this_for": {"en": "Who is this for?", "ur": "یہ کس کے لیے ہے؟"},
    "eli5_what_you_get": {"en": "What do you get?", "ur": "آپ کو کیا ملتا ہے؟"},
    "eli5_who_can_apply": {"en": "Who can apply?", "ur": "کون درخواست دے سکتا ہے؟"},
    "eli5_what_you_need": {"en": "What do you need?", "ur": "آپ کو کیا درکار ہے؟"},
    "eli5_where_to_apply": {"en": "Where do you apply?", "ur": "درخواست کہاں دیں؟"},
    "eli5_caveat": {
        "en": "Reworded by AI from this record only. It cannot add or soften a requirement, "
              "and it does not decide your eligibility - the conditions above do.",
        "ur": "یہ صرف اسی اندراج سے AI نے آسان الفاظ میں لکھا ہے۔ یہ کوئی شرط بڑھا یا نرم نہیں کر سکتا، اور اہلیت کا فیصلہ نہیں کرتا — وہ اوپر کی شرائط کرتی ہیں۔"},

    # ================= P1-8: source presentation ==========================
    "source_title_label": {"en": "Source document", "ur": "ماخذ دستاویز"},
    "source_org_label": {"en": "Organisation", "ur": "ادارہ"},
    "source_url_label": {"en": "Official page", "ur": "سرکاری صفحہ"},
    "source_none": {"en": "No official link on record", "ur": "کوئی سرکاری ربط درج نہیں"},

    # ================= P2-4: empty states =================================
    "empty_try_heading": {"en": "What you can try", "ur": "آپ کیا کر سکتے ہیں"},
    "empty_try_categories": {"en": "Choose another category",
                             "ur": "کوئی اور زمرہ منتخب کریں"},
    "empty_try_answers": {"en": "Change your education level or domicile",
                          "ur": "اپنی تعلیمی سطح یا ڈومیسائل تبدیل کریں"},
    "empty_try_upload": {"en": "Upload an advertisement you found elsewhere",
                         "ur": "کہیں اور سے ملا اشتہار اپلوڈ کریں"},
    "empty_catalogue_note": {
        "en": "Our catalogue currently holds {n} verified-source records. A small catalogue "
              "is a limit of this prototype, not a judgement about you.",
        "ur": "ہمارے پاس فی الحال {n} اندراجات ہیں۔ فہرست کا مختصر ہونا اس نمونے کی حد ہے، آپ کے بارے میں کوئی فیصلہ نہیں۔"},
    "documents_none_marked": {
        "en": "You haven't marked any documents as available yet.",
        "ur": "آپ نے ابھی کوئی دستاویز دستیاب کے طور پر نشان زد نہیں کی۔"},
    "documents_none_listed": {
        "en": "This record does not list the documents required. Check the official page "
              "before you apply - that is a gap in our record, not a sign that none are needed.",
        "ur": "اس اندراج میں مطلوبہ دستاویزات درج نہیں۔ درخواست سے پہلے سرکاری صفحہ دیکھیں — یہ ہمارے اندراج کی کمی ہے، اس کا مطلب یہ نہیں کہ کوئی دستاویز درکار نہیں۔"},
    "answer_empty_hint": {
        "en": "Pick a question above to get an answer grounded in this record.",
        "ur": "اوپر سے کوئی سوال منتخب کریں تاکہ اسی اندراج سے جواب مل سکے۔"},

    # ================= P2-5: degraded AI ==================================
    "ai_unavailable_heading": {"en": "AI explanation is temporarily unavailable",
                               "ur": "اے آئی تشریح فی الحال دستیاب نہیں"},
    "ai_unavailable_body": {
        "en": "Everything else on this page is unaffected: your eligibility result, the "
              "conditions checked, the official source and your document checklist are all "
              "produced by rules, not by the AI.",
        "ur": "اس صفحے پر باقی سب کچھ متاثر نہیں ہوا: آپ کا نتیجہ، جانچی گئی شرائط، سرکاری ماخذ اور دستاویزات کی فہرست — سب قواعد سے بنتے ہیں، AI سے نہیں۔"},
    "ai_offline_heading": {"en": "Running without an API key", "ur": "بغیر اے پی آئی کلید کے"},
    "no_evidence_heading": {"en": "We can't answer that from this record",
                            "ur": "اس اندراج سے اس کا جواب نہیں دیا جا سکتا"},
    "ai_retry": {"en": "Try again", "ur": "دوبارہ کوشش کریں"},

    # ================= P2-2: impact ======================================
    "impact_heading": {"en": "Sahulat impact", "ur": "سہولت کا اثر"},
    "impact_screened": {"en": "opportunities screened", "ur": "مواقع جانچے گئے"},
    "impact_requirements": {"en": "requirements checked", "ur": "شرائط جانچی گئیں"},
    "impact_documents": {"en": "documents identified", "ur": "دستاویزات کی نشاندہی"},
    "impact_minutes": {"en": "minutes of searching, estimated",
                       "ur": "منٹ کی تلاش، تخمینہ"},
    "impact_counted_note": {
        "en": "Counted from this session only. Nothing is carried over between users, "
              "and nothing here is stored.",
        "ur": "صرف اسی سیشن سے شمار کیا گیا۔ کچھ بھی صارفین کے درمیان منتقل یا محفوظ نہیں ہوتا۔"},
    "impact_estimate_note": {
        "en": "The time figure is the only estimate: {n} opportunities × {minutes} minutes "
              "assumed per manual lookup. Prototype estimate — not a measured "
              "population-level claim.",
        "ur": "وقت کا عدد ہی واحد تخمینہ ہے: {n} مواقع × {minutes} منٹ فی دستی تلاش۔ یہ نمونے کا تخمینہ ہے، کوئی ماپا گیا دعویٰ نہیں۔"},
    "impact_estimate_badge": {"en": "Estimate", "ur": "تخمینہ"},

    # ================= P2-3: result detail tabs ===========================
    "tab_eligibility": {"en": "Eligibility", "ur": "اہلیت"},
    "tab_documents": {"en": "Documents & steps", "ur": "دستاویزات اور مراحل"},
    "tab_source": {"en": "Source", "ur": "ماخذ"},
    "tab_ask": {"en": "Understand & ask", "ur": "سمجھیں اور پوچھیں"},

    # ================= provisional deadlines (DATA-02) ====================
    "deadline_provisional_badge": {"en": "Provisional date", "ur": "عارضی تاریخ"},

    # ========== always-open enrolment (DATA-07) ==========
    "listing_always_open": {"en": "Always open", "ur": "ہمیشہ کھلا"},
    "urgency_continuous": {"en": "No closing date", "ur": "کوئی آخری تاریخ نہیں"},
    "urgency_continuous_note": {
        "en": "This programme accepts applications all year round. There is no deadline to "
              "miss - but being accepted still depends on the conditions above, and on funds "
              "being available when you apply.",
        "ur": "یہ پروگرام سارا سال درخواستیں قبول کرتا ہے۔ کوئی آخری تاریخ نہیں جو نکل جائے - "
              "لیکن منظوری کا انحصار اوپر دی گئی شرائط اور درخواست کے وقت فنڈز کی دستیابی پر ہے۔"},
    "deadline_provisional_note": {
        "en": "This date is our placeholder for the expected cycle, not a date the authority "
              "has announced. Treat the countdown as indicative and confirm on the official page.",
        "ur": "یہ تاریخ متوقع مرحلے کے لیے ہماری عارضی تاریخ ہے، ادارے کی اعلان کردہ نہیں۔ گنتی کو اندازہ سمجھیں اور سرکاری صفحے پر تصدیق کریں۔"},

    # -- follow-up chat -----------------------------------------------------
    "ask_followup": {"en": "Ask a follow-up question", "ur": "مزید سوال پوچھیں"},
    "ask_followup_hint": {
        "en": "Answers come only from the records above and always cite their source.",
        "ur": "جوابات صرف اوپر دیے گئے ریکارڈ سے آتے ہیں اور ہمیشہ ماخذ کا حوالہ دیتے ہیں۔",
    },
    "ask_placeholder": {
        "en": "e.g. Which documents do I need for the PEEF scholarship?",
        "ur": "مثلاً: پیف اسکالرشپ کے لیے کون سی دستاویزات درکار ہیں؟",
    },
    "ask_button": {"en": "Ask", "ur": "پوچھیں"},
    "no_evidence_found": {
        "en": "We don't have verified information on that in our records. Please check the "
              "official source link for the programme you're asking about.",
        "ur": "ہمارے ریکارڈ میں اس بارے میں تصدیق شدہ معلومات موجود نہیں۔ براہ کرم متعلقہ "
              "پروگرام کے سرکاری لنک سے رجوع کریں۔",
    },

    # -- AI status ----------------------------------------------------------
    "ai_enabled": {"en": "AI features active", "ur": "اے آئی خصوصیات فعال"},
    "ai_mock_mode": {"en": "Offline mode — no API key", "ur": "آف لائن موڈ — کوئی اے پی آئی کلید نہیں"},
    "ai_mock_explainer": {
        "en": "Eligibility screening works fully without an API key — it is rules-based. "
              "Only the plain-language explanations and ad reading need one.",
        "ur": "اہلیت کی جانچ بغیر اے پی آئی کلید کے مکمل کام کرتی ہے کیونکہ یہ قواعد پر مبنی ہے۔ "
              "صرف تشریح اور اشتہار پڑھنے کے لیے کلید درکار ہے۔",
    },
    "ai_unavailable": {
        "en": "The AI explanation is unavailable right now. Your eligibility result above is "
              "rules-based and is completely unaffected.",
        "ur": "اے آئی تشریح اس وقت دستیاب نہیں۔ اوپر دیا گیا نتیجہ قواعد پر مبنی ہے اور "
              "اس پر کوئی اثر نہیں پڑا۔",
    },
    "ai_mock_notice": {
        "en": "Offline mode — add a Gemini API key to get a plain-language explanation here.",
        "ur": "آف لائن موڈ — یہاں آسان تشریح کے لیے Gemini کلید شامل کریں۔",
    },
    "ai_mock_extraction_notice": {
        "en": "Offline mode — reading a real ad needs a Gemini API key. See README Step 5.",
        "ur": "آف لائن موڈ — اصل اشتہار پڑھنے کے لیے Gemini کلید درکار ہے۔",
    },

    # -- sidebar ------------------------------------------------------------
    "sidebar_language": {"en": "Language", "ur": "زبان"},
    "sidebar_status": {"en": "Status", "ur": "صورتحال"},
    "sidebar_catalog": {"en": "Catalogue", "ur": "فہرست"},
    "sidebar_records": {"en": "{n} records loaded", "ur": "{n} ریکارڈ لوڈ ہوئے"},
    "sidebar_verified": {"en": "{n} verified", "ur": "{n} تصدیق شدہ"},
    "sidebar_unverified": {"en": "{n} awaiting verification", "ur": "{n} تصدیق کے منتظر"},
    "sidebar_about": {"en": "About", "ur": "تعارف"},
    "sidebar_about_body": {
        "en": "Sahulat AI screens your profile against official Pakistani opportunity "
              "programmes using a deterministic rules engine. AI is used only to explain "
              "results and to read uploaded ads — never to decide eligibility.",
        "ur": "سہولت اے آئی ایک قواعد پر مبنی نظام سے آپ کی معلومات کو سرکاری پاکستانی "
              "پروگراموں کے ساتھ جانچتا ہے۔ اے آئی صرف تشریح اور اشتہار پڑھنے کے لیے "
              "استعمال ہوتا ہے — اہلیت کا فیصلہ کبھی نہیں کرتا۔",
    },
    "search_mode": {"en": "Search mode", "ur": "تلاش کا طریقہ"},
    "search_mode_semantic": {"en": "Semantic", "ur": "معنوی"},
    "search_mode_keyword": {"en": "Keyword", "ur": "کلیدی الفاظ"},

    # -- how it works -------------------------------------------------------
    "how_heading": {"en": "How Sahulat AI works", "ur": "سہولت اے آئی کیسے کام کرتا ہے"},
    "how_intro": {
        "en": "Most AI tools let a language model decide who qualifies. We don't. Eligibility "
              "is decided by a deterministic rules engine you can read and test. The AI only "
              "explains what that engine already decided.",
        "ur": "زیادہ تر اے آئی ٹولز میں زبان کا ماڈل فیصلہ کرتا ہے کہ کون اہل ہے۔ ہم ایسا نہیں "
              "کرتے۔ اہلیت کا فیصلہ ایک قابلِ جانچ قواعد پر مبنی نظام کرتا ہے۔ اے آئی صرف اس "
              "فیصلے کی وضاحت کرتا ہے۔",
    },
    "how_step1_title": {"en": "1. You describe yourself", "ur": "۱. آپ اپنی معلومات دیتے ہیں"},
    "how_step1_body": {
        "en": "Only screening attributes — age, domicile, education, marks, income. Never your "
              "name, CNIC, phone or address.",
        "ur": "صرف جانچ کے لیے ضروری معلومات — عمر، ڈومیسائل، تعلیم، نمبر، آمدنی۔ کبھی نام، "
              "شناختی کارڈ، فون یا پتہ نہیں۔",
    },
    "how_step2_title": {"en": "2. Rules decide", "ur": "۲. قواعد فیصلہ کرتے ہیں"},
    "how_step2_body": {
        "en": "Each condition is checked independently against the published criteria and "
              "marked met, unmet, or unknown. Missing data is never guessed.",
        "ur": "ہر شرط شائع شدہ معیار کے مطابق الگ الگ جانچی جاتی ہے اور پوری، ادھوری یا "
              "نامعلوم قرار دی جاتی ہے۔ غائب معلومات کا اندازہ نہیں لگایا جاتا۔",
    },
    "how_step3_title": {"en": "3. AI explains", "ur": "۳. اے آئی وضاحت کرتا ہے"},
    "how_step3_body": {
        "en": "The language model receives the decision and puts it in plain words. It cannot "
              "change the outcome or invent a criterion.",
        "ur": "ماڈل کو فیصلہ دیا جاتا ہے اور وہ اسے آسان الفاظ میں بیان کرتا ہے۔ وہ نتیجہ "
              "بدل نہیں سکتا اور نہ کوئی نئی شرط بنا سکتا ہے۔",
    },
    "how_trust_heading": {"en": "How we handle trust", "ur": "ہم اعتماد کو کیسے سنبھالتے ہیں"},
    "how_trust_body": {
        "en": "Records we curated from official sources and records read from your uploads are "
              "never mixed. Each carries its own badge, and an uploaded record always says so.",
        "ur": "سرکاری ذرائع سے مرتب کردہ ریکارڈ اور آپ کی اپلوڈ سے پڑھے گئے ریکارڈ کبھی "
              "آپس میں نہیں ملائے جاتے۔ ہر ایک کا اپنا نشان ہوتا ہے۔",
    },
    "how_privacy_heading": {"en": "What we never collect", "ur": "ہم کیا کبھی جمع نہیں کرتے"},


    # -- wizard -------------------------------------------------------------
    "step_focus_title": {"en": "What are you looking for?", "ur": "آپ کیا تلاش کر رہے ہیں؟"},
    "step_focus_caption": {
        "en": "Choose one or more categories. We will only screen you against these.",
        "ur": "ایک یا زیادہ زمرے منتخب کریں۔ ہم صرف انہی کے مطابق جانچ کریں گے۔",
    },
    "step_about_title": {"en": "About you", "ur": "آپ کے بارے میں"},
    "step_about_caption": {
        "en": "Basic details that almost every programme screens on.",
        "ur": "بنیادی تفصیلات جو تقریباً ہر پروگرام میں درکار ہوتی ہیں۔",
    },
    "step_education_title": {"en": "Education", "ur": "تعلیم"},
    "step_education_caption": {
        "en": "Your highest completed level, and how you performed.",
        "ur": "آپ کی مکمل کردہ اعلیٰ ترین سطح اور کارکردگی۔",
    },
    "step_circumstances_title": {"en": "Skills and circumstances", "ur": "مہارتیں اور حالات"},
    "step_circumstances_caption": {
        "en": "Optional, but each answer sharpens your results and may unlock programmes with reserved places.",
        "ur": "اختیاری، لیکن ہر جواب آپ کے نتائج کو بہتر بناتا ہے اور مخصوص نشستوں والے پروگرام کھول سکتا ہے۔",
    },
    "step_results_title": {"en": "Your results", "ur": "آپ کے نتائج"},
    "step_results_caption": {
        "en": "Screened against every programme in the categories you chose.",
        "ur": "منتخب کردہ زمروں کے تمام پروگراموں کے مطابق جانچ کی گئی۔",
    },
    "nav_back": {"en": "Back", "ur": "واپس"},
    "nav_continue": {"en": "Continue", "ur": "جاری رکھیں"},
    "nav_see_results": {"en": "See my results", "ur": "نتائج دیکھیں"},
    "nav_start_over": {"en": "Start over", "ur": "دوبارہ شروع کریں"},
    "nav_edit_answers": {"en": "Edit my answers", "ur": "جوابات میں ترمیم کریں"},
    "step_counter": {"en": "Step {current} of {total}", "ur": "مرحلہ {current} از {total}"},
    "required_marker": {"en": "Required", "ur": "لازمی"},
    "optional_marker": {"en": "Optional", "ur": "اختیاری"},
    "fix_before_continuing": {
        "en": "Please complete the highlighted fields before continuing.",
        "ur": "جاری رکھنے سے پہلے براہ کرم نشان زد خانے مکمل کریں۔",
    },
    "your_answers": {"en": "Your answers", "ur": "آپ کے جوابات"},
    "detail_completeness": {"en": "{percent}% of optional detail provided",
                            "ur": "{percent}% اختیاری تفصیلات فراہم کی گئیں"},
    "more_detail_hint": {
        "en": "Answering more questions turns \"Needs verification\" results into clear ones.",
        "ur": "مزید سوالات کے جواب دینے سے \"تصدیق درکار\" کے نتائج واضح ہو جاتے ہیں۔",
    },

    # -- validation ---------------------------------------------------------
    "err_required": {"en": "This answer is needed to screen you.",
                     "ur": "جانچ کے لیے یہ جواب ضروری ہے۔"},
    "err_age_range": {"en": "Enter an age between {min} and {max}.",
                      "ur": "{min} سے {max} کے درمیان عمر درج کریں۔"},
    "err_marks_range": {"en": "Marks must be between 0 and 100.",
                        "ur": "نمبر 0 سے 100 کے درمیان ہونے چاہئیں۔"},
    "err_income_range": {"en": "Enter a monthly amount in rupees.",
                         "ur": "ماہانہ رقم روپوں میں درج کریں۔"},
    "err_experience_range": {"en": "Enter years between 0 and 50.",
                             "ur": "0 سے 50 کے درمیان سال درج کریں۔"},
    "err_no_category": {"en": "Choose at least one category.",
                        "ur": "کم از کم ایک زمرہ منتخب کریں۔"},
    "err_invalid_choice": {"en": "Choose one of the listed options.",
                           "ur": "دی گئی فہرست میں سے ایک منتخب کریں۔"},

    # -- new profile fields -------------------------------------------------
    "field_gender": {"en": "Gender", "ur": "جنس"},
    "field_gender_help": {
        "en": "Asked only because some programmes reserve places for women.",
        "ur": "صرف اس لیے پوچھا گیا کہ بعض پروگراموں میں خواتین کے لیے نشستیں مخصوص ہیں۔",
    },
    "gender_female": {"en": "Female", "ur": "خاتون"},
    "gender_male": {"en": "Male", "ur": "مرد"},
    "gender_other": {"en": "Prefer to self-describe", "ur": "خود بیان کرنا چاہوں گا/گی"},
    "field_field_of_study": {"en": "Field of study", "ur": "شعبہ تعلیم"},
    "fos_engineering": {"en": "Engineering", "ur": "انجینئرنگ"},
    "fos_computer_science": {"en": "Computer Science / IT", "ur": "کمپیوٹر سائنس / آئی ٹی"},
    "fos_medical": {"en": "Medical & Health", "ur": "طب و صحت"},
    "fos_natural_sciences": {"en": "Natural Sciences", "ur": "طبیعی علوم"},
    "fos_social_sciences": {"en": "Social Sciences", "ur": "سماجی علوم"},
    "fos_business": {"en": "Business & Commerce", "ur": "کاروبار و تجارت"},
    "fos_arts_humanities": {"en": "Arts & Humanities", "ur": "فنون و علومِ انسانی"},
    "fos_education": {"en": "Education", "ur": "تعلیم"},
    "fos_agriculture": {"en": "Agriculture", "ur": "زراعت"},
    "fos_law": {"en": "Law", "ur": "قانون"},
    "fos_other": {"en": "Other", "ur": "دیگر"},
    "field_english_level": {"en": "English proficiency", "ur": "انگریزی کی استعداد"},
    "eng_none": {"en": "None", "ur": "کوئی نہیں"},
    "eng_basic": {"en": "Basic — simple words and phrases", "ur": "بنیادی — سادہ الفاظ اور جملے"},
    "eng_intermediate": {"en": "Intermediate — can hold a conversation",
                         "ur": "درمیانی — گفتگو کر سکتے ہیں"},
    "eng_fluent": {"en": "Fluent — comfortable reading and writing",
                   "ur": "روانی — پڑھنے لکھنے میں مکمل مہارت"},
    "field_computer_skills": {"en": "Computer & digital skills", "ur": "کمپیوٹر اور ڈیجیٹل مہارت"},
    "comp_none": {"en": "None", "ur": "کوئی نہیں"},
    "comp_basic": {"en": "Basic — email, browsing, typing", "ur": "بنیادی — ای میل، براؤزنگ، ٹائپنگ"},
    "comp_intermediate": {"en": "Intermediate — office software, spreadsheets",
                          "ur": "درمیانی — آفس سافٹ ویئر، اسپریڈ شیٹ"},
    "comp_advanced": {"en": "Advanced — programming, design, data",
                      "ur": "اعلیٰ — پروگرامنگ، ڈیزائن، ڈیٹا"},
    "field_has_disability": {"en": "Do you have a disability?", "ur": "کیا آپ کو کوئی معذوری ہے؟"},
    "field_is_orphan": {"en": "Are you an orphan?", "ur": "کیا آپ یتیم ہیں؟"},
    "special_circumstances": {"en": "Special circumstances", "ur": "خصوصی حالات"},
    "special_circumstances_help": {
        "en": "Several programmes reserve places for these groups. Answering can only help you — it is never used to exclude anyone.",
        "ur": "کئی پروگراموں میں ان گروہوں کے لیے نشستیں مخصوص ہیں۔ جواب دینا صرف فائدہ دے سکتا ہے — اسے کبھی خارج کرنے کے لیے استعمال نہیں کیا جاتا۔",
    },

    # -- priority groups ----------------------------------------------------
    "priority_heading": {"en": "You may qualify for a reserved place",
                         "ur": "آپ مخصوص نشست کے اہل ہو سکتے ہیں"},
    "priority_body": {
        "en": "This programme gives priority to: {groups}. Confirm the current quota rules with the official source.",
        "ur": "یہ پروگرام ان کو ترجیح دیتا ہے: {groups}۔ موجودہ کوٹہ قواعد کی تصدیق سرکاری ذریعے سے کریں۔",
    },
    "pg_female": {"en": "women applicants", "ur": "خواتین امیدوار"},
    "pg_disability": {"en": "applicants with a disability", "ur": "معذور امیدوار"},
    "pg_orphan": {"en": "orphaned applicants", "ur": "یتیم امیدوار"},
    "pg_minority": {"en": "religious minorities", "ur": "مذہبی اقلیتیں"},
    "pg_under_served_district": {"en": "under-served districts", "ur": "پسماندہ اضلاع"},


    # -- navigation / brand -------------------------------------------------
    "brand_urdu": {"en": "سہولت", "ur": "سہولت"},
    "nav_discover": {"en": "Discover", "ur": "دریافت کریں"},
    "nav_read": {"en": "Read an announcement", "ur": "اعلان پڑھیں"},
    "nav_how": {"en": "How it works", "ur": "یہ کیسے کام کرتا ہے"},

    # -- hero ---------------------------------------------------------------
    "hero_eyebrow": {"en": "Pakistan's Opportunity Navigator",
                     "ur": "پاکستان کا مواقع نیویگیٹر"},
    "hero_title": {"en": "Find opportunities that fit your life.",
                   "ur": "ایسے مواقع تلاش کریں جو آپ کی زندگی کے مطابق ہوں۔"},
    "hero_body": {
        "en": "Scholarships, jobs, training and selected public programmes — matched "
              "using clear eligibility rules and explained with official sources.",
        "ur": "اسکالرشپ، نوکریاں، تربیت اور منتخب سرکاری پروگرام — واضح اہلیت کے "
              "قواعد سے جانچے گئے اور سرکاری ذرائع سے سمجھائے گئے۔",
    },
    "cta_start": {"en": "Tell us about yourself", "ur": "اپنے بارے میں بتائیں"},
    "cta_sample": {"en": "Try a sample profile", "ur": "نمونہ پروفائل آزمائیں"},
    "trust_rules": {"en": "Rules-based matching", "ur": "قواعد پر مبنی جانچ"},
    "trust_sources": {"en": "Official-source evidence", "ur": "سرکاری ذرائع کے شواہد"},
    "trust_no_pii": {"en": "No sensitive identifiers", "ur": "کوئی حساس شناخت نہیں"},
    "map_you": {"en": "You", "ur": "آپ"},

    # -- what can you find --------------------------------------------------
    "find_heading": {"en": "What can Sahulat AI help you find?",
                     "ur": "سہولت اے آئی آپ کو کیا تلاش کرنے میں مدد دے سکتا ہے؟"},
    "find_scholarship": {"en": "Financial support for students.",
                         "ur": "طلباء کے لیے مالی معاونت۔"},
    "find_job": {"en": "Government and public-sector roles.",
                 "ur": "سرکاری اور عوامی شعبے کی ملازمتیں۔"},
    "find_skills": {"en": "Skills and professional development.",
                    "ur": "ہنر اور پیشہ ورانہ تربیت۔"},
    "find_assistance": {"en": "Public support programmes.",
                        "ur": "عوامی امدادی پروگرام۔"},

    # -- journey ------------------------------------------------------------
    "journey_heading": {"en": "From profile to opportunity",
                        "ur": "پروفائل سے موقع تک"},
    "journey_line": {"en": "You tell us. Rules check. Sources explain. You decide.",
                     "ur": "آپ بتائیں۔ قواعد جانچیں۔ ذرائع وضاحت کریں۔ فیصلہ آپ کا۔"},
    "journey_1_title": {"en": "Tell us about yourself", "ur": "اپنے بارے میں بتائیں"},
    "journey_1_body": {"en": "Only the attributes needed for matching.",
                       "ur": "صرف وہ معلومات جو جانچ کے لیے درکار ہیں۔"},
    "journey_2_title": {"en": "Rules check the criteria", "ur": "قواعد معیار جانچتے ہیں"},
    "journey_2_body": {"en": "No guessing. Missing information stays unknown.",
                       "ur": "کوئی اندازہ نہیں۔ غائب معلومات نامعلوم رہتی ہیں۔"},
    "journey_3_title": {"en": "Sources provide evidence", "ur": "ذرائع شواہد دیتے ہیں"},
    "journey_3_body": {"en": "We show where important claims come from.",
                       "ur": "ہم بتاتے ہیں کہ اہم باتیں کہاں سے آئیں۔"},
    "journey_4_title": {"en": "You get the next step", "ur": "آپ کو اگلا قدم ملتا ہے"},
    "journey_4_body": {"en": "Documents, status and the official application link.",
                       "ur": "دستاویزات، صورتحال اور سرکاری درخواست کا لنک۔"},

    # -- principles ---------------------------------------------------------
    "principles_heading": {"en": "Built around three principles",
                           "ur": "تین اصولوں پر بنایا گیا"},
    "principle_1_title": {"en": "Rules decide", "ur": "قواعد فیصلہ کرتے ہیں"},
    "principle_1_body": {"en": "Eligibility is evaluated against structured criteria, "
                               "never guessed by a language model.",
                         "ur": "اہلیت منظم معیار کے مطابق جانچی جاتی ہے، کسی ماڈل کے "
                               "اندازے سے نہیں۔"},
    "principle_2_title": {"en": "Sources support", "ur": "ذرائع تائید کرتے ہیں"},
    "principle_2_body": {"en": "Important claims are linked to the published source "
                               "they came from.",
                         "ur": "اہم دعوے اُس شائع شدہ ماخذ سے منسلک ہیں جہاں سے آئے۔"},
    "principle_3_title": {"en": "AI explains", "ur": "اے آئی وضاحت کرتا ہے"},
    "principle_3_body": {"en": "The model turns a decided result into understandable "
                               "guidance — it cannot change the outcome.",
                         "ur": "ماڈل طے شدہ نتیجے کو قابلِ فہم رہنمائی میں بدلتا ہے — "
                               "نتیجہ بدل نہیں سکتا۔"},

    # -- privacy ------------------------------------------------------------
    "privacy_heading": {"en": "Your privacy", "ur": "آپ کی پرائیویسی"},
    "privacy_body": {
        "en": "Sahulat AI does not need your CNIC, name, phone number or address to "
              "suggest opportunities. Nothing you enter is stored after you close the page.",
        "ur": "سہولت اے آئی کو مواقع تجویز کرنے کے لیے آپ کے شناختی کارڈ، نام، فون نمبر "
              "یا پتے کی ضرورت نہیں۔ صفحہ بند کرنے کے بعد کچھ محفوظ نہیں رہتا۔",
    },

    # -- source provenance --------------------------------------------------
    "source_heading": {"en": "Source", "ur": "ماخذ"},
    "source_verified": {"en": "Source verified", "ur": "ماخذ تصدیق شدہ"},
    "source_needs_check": {"en": "Verify current cycle", "ur": "موجودہ سائیکل کی تصدیق کریں"},
    "source_last_checked": {"en": "Last checked", "ur": "آخری جانچ"},
    "source_not_checked": {"en": "Not yet checked by our team",
                           "ur": "ہماری ٹیم نے ابھی جانچ نہیں کی"},
    "source_verify_body": {
        "en": "The eligibility information is published, but the current application "
              "cycle may have changed. Confirm on the official page before applying.",
        "ur": "اہلیت کی معلومات شائع شدہ ہیں، لیکن موجودہ درخواست سائیکل بدل سکتا ہے۔ "
              "درخواست سے پہلے سرکاری صفحے پر تصدیق کریں۔",
    },

    # -- listing status chips -----------------------------------------------
    "listing_open": {"en": "Open", "ur": "کھلا"},
    "listing_verify_cycle": {"en": "Verify current cycle", "ur": "سائیکل کی تصدیق کریں"},

    # -- match labels (spec section 19) -------------------------------------
    "match_likely": {"en": "Likely match", "ur": "غالباً موزوں"},
    "match_needs_verification": {"en": "Needs verification", "ur": "تصدیق درکار"},
    "match_none": {"en": "Does not currently match", "ur": "فی الحال موزوں نہیں"},

    # -- results ------------------------------------------------------------
    "results_found": {"en": "We found {n} opportunities worth checking",
                      "ur": "ہمیں {n} قابلِ توجہ مواقع ملے"},
    "results_found_one": {"en": "We found 1 opportunity worth checking",
                          "ur": "ہمیں 1 قابلِ توجہ موقع ملا"},
    "results_breakdown": {"en": "{strong} strong · {verify} need verification · {no} not a match",
                          "ur": "{strong} مضبوط · {verify} تصدیق درکار · {no} غیر موزوں"},
    "first_card_note": {"en": "This one looks especially relevant to you.",
                        "ur": "یہ آپ کے لیے خاص طور پر موزوں لگتا ہے۔"},
    "why_matches_you": {"en": "Why this matches you", "ur": "یہ آپ کے لیے کیوں موزوں ہے"},
    "view_eligibility": {"en": "View eligibility", "ur": "اہلیت دیکھیں"},
    "how_generated": {"en": "How this match was generated",
                      "ur": "یہ نتیجہ کیسے بنا"},
    "pipeline_profile": {"en": "Your profile", "ur": "آپ کی پروفائل"},
    "pipeline_rules": {"en": "Eligibility rules", "ur": "اہلیت کے قواعد"},
    "pipeline_match": {"en": "Structured match", "ur": "منظم جانچ"},
    "pipeline_retrieval": {"en": "Official-source retrieval", "ur": "سرکاری ماخذ سے حوالہ"},
    "pipeline_explain": {"en": "AI explanation", "ur": "اے آئی وضاحت"},

    # -- application journey -------------------------------------------------
    "timeline_heading": {"en": "Application journey", "ur": "درخواست کا سفر"},

    # -- empty / error states -----------------------------------------------
    "empty_heading": {"en": "We couldn't find a strong match yet.",
                      "ur": "ابھی کوئی مضبوط مماثلت نہیں ملی۔"},
    "empty_body": {"en": "Try changing your education level, the categories you chose, "
                         "or your domicile.",
                   "ur": "اپنی تعلیمی سطح، منتخب زمرے یا ڈومیسائل تبدیل کر کے دیکھیں۔"},
    "error_busy": {"en": "Sahulat AI is temporarily busy. Your profile is safe — "
                         "please try again in a moment.",
                   "ur": "سہولت اے آئی اس وقت مصروف ہے۔ آپ کی معلومات محفوظ ہیں — "
                         "براہ کرم کچھ دیر بعد کوشش کریں۔"},
    "technical_details": {"en": "Technical details", "ur": "تکنیکی تفصیلات"},

    # -- demo profile --------------------------------------------------------
    "demo_badge": {"en": "Demo profile", "ur": "نمونہ پروفائل"},
    "demo_note": {"en": "You are viewing a sample profile. Start over to enter your own.",
                  "ur": "آپ نمونہ پروفائل دیکھ رہے ہیں۔ اپنی معلومات کے لیے دوبارہ شروع کریں۔"},

    # -- prompt chips --------------------------------------------------------
    "chip_what_apply": {"en": "What can I apply for?", "ur": "میں کس چیز کے لیے درخواست دے سکتا ہوں؟"},
    "chip_why_qualify": {"en": "Why do I qualify?", "ur": "میں کیوں اہل ہوں؟"},
    "chip_documents": {"en": "What documents do I need?", "ur": "مجھے کون سی دستاویزات چاہئیں؟"},

    # -- footer --------------------------------------------------------------
    "footer_tagline": {"en": "Opportunity navigation, made simpler.",
                       "ur": "مواقع کی تلاش، آسان بنائی گئی۔"},
    "footer_trust": {"en": "Trust", "ur": "اعتماد"},
    "footer_language": {"en": "Language", "ur": "زبان"},
    "language_help": {"en": "Change the language of the whole page.",
                      "ur": "پورے صفحے کی زبان تبدیل کریں۔"},
    "footer_built": {"en": "Built for Pakistan", "ur": "پاکستان کے لیے بنایا گیا"},
    "footer_disclaimer": {
        "en": "Informational guidance only. Sahulat AI does not make official "
              "eligibility decisions, verify identity, or submit applications on your behalf.",
        "ur": "صرف معلوماتی رہنمائی۔ سہولت اے آئی سرکاری اہلیت کا فیصلہ نہیں کرتا، "
              "شناخت کی تصدیق نہیں کرتا، اور آپ کی طرف سے درخواست جمع نہیں کراتا۔",
    },
    "catalogue_stat": {"en": "curated opportunities", "ur": "مرتب شدہ مواقع"},
    "authorities_stat": {"en": "official authorities", "ur": "سرکاری ادارے"},
    "sourced_stat": {"en": "source-linked records", "ur": "ماخذ سے منسلک ریکارڈ"},
    "identifiers_stat": {"en": "sensitive identifiers required", "ur": "حساس شناختیں درکار"},

    # -- export -------------------------------------------------------------
    "export_heading": {"en": "Save your results", "ur": "اپنے نتائج محفوظ کریں"},
    "export_button": {"en": "Download summary (.txt)", "ur": "خلاصہ ڈاؤن لوڈ کریں"},
    "export_hint": {
        "en": "A plain-text copy of your matches, documents and next steps.",
        "ur": "آپ کے نتائج، دستاویزات اور اگلے اقدامات کی سادہ نقل۔",
    },
}


def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Look up a string. Unknown keys return the key itself (so a missing string
    is visible in testing rather than silently blank). Any **kwargs are used
    as format placeholders.

    Roman Urdu (P2-1) lives in its own table rather than as a third key in
    every literal: it keeps the English/Urdu pairs - the two languages the
    product promises - readable and reviewable side by side, and a gap in the
    Roman table degrades to English rather than breaking a page.
    """
    entry = STRINGS.get(key)
    if not entry:
        return key
    if lang == LANG_ROMAN:
        text = ROMAN.get(key) or entry.get("en") or key
    else:
        text = entry.get(lang) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


# ---------------------------------------------------------------------------
# Value formatting
# ---------------------------------------------------------------------------

_EDUCATION_KEYS = {
    "matric": "edu_matric",
    "intermediate": "edu_intermediate",
    "bachelor": "edu_bachelor",
    "master": "edu_master",
}

_STATUS_KEYS = {
    STATUS_ELIGIBLE: "status_eligible",
    STATUS_NEEDS_VERIFICATION: "status_needs_verification",
    STATUS_NOT_ELIGIBLE: "status_not_eligible",
}

_PROFILE_FIELD_KEYS = {
    "age": "field_age",
    "gender": "field_gender",
    "domicile_province": "field_domicile",
    "education_level": "field_education",
    "marks_percentage": "field_marks",
    "field_of_study": "field_field_of_study",
    "monthly_household_income": "field_income",
    "currently_enrolled": "field_enrolled",
    "has_existing_scholarship": "field_existing_scholarship",
    "english_level": "field_english_level",
    "computer_skills": "field_computer_skills",
    "employment_status": "field_employment",
    "years_experience": "field_experience",
    "has_disability": "field_has_disability",
    "is_orphan": "field_is_orphan",
    "categories": "select_category",
}

_ENGLISH_KEYS = {level: "eng_" + level
                 for level in ("none", "basic", "intermediate", "fluent")}
_COMPUTER_KEYS = {level: "comp_" + level
                  for level in ("none", "basic", "intermediate", "advanced")}
_GENDER_KEYS = {g: "gender_" + g for g in ("female", "male", "other")}
_FIELD_OF_STUDY_KEYS = {
    f: "fos_" + f for f in (
        "engineering", "computer_science", "medical", "natural_sciences",
        "social_sciences", "business", "arts_humanities", "education",
        "agriculture", "law", "other",
    )
}
_PRIORITY_GROUP_KEYS = {
    g: "pg_" + g for g in
    ("female", "disability", "orphan", "minority", "under_served_district")
}


def status_label(status: str, lang: str = "en") -> str:
    return t(_STATUS_KEYS.get(status, status), lang)


def profile_field_label(field_name: str, lang: str = "en") -> str:
    return t(_PROFILE_FIELD_KEYS.get(field_name, field_name), lang)


def education_label(level: Optional[str], lang: str = "en") -> str:
    if not level:
        return "—"
    return t(_EDUCATION_KEYS.get(str(level).lower(), str(level)), lang)


def _short(label: str) -> str:
    """First clause only - dropdown labels carry an explanation, checks don't."""
    for sep in (" — ", " - "):
        if sep in label:
            return label.split(sep, 1)[0]
    return label


def english_label(level: Optional[str], lang: str = "en", short: bool = False) -> str:
    if not level:
        return "\u2014"
    label = t(_ENGLISH_KEYS.get(str(level).lower(), str(level)), lang)
    return _short(label) if short else label


def computer_label(level: Optional[str], lang: str = "en", short: bool = False) -> str:
    if not level:
        return "\u2014"
    label = t(_COMPUTER_KEYS.get(str(level).lower(), str(level)), lang)
    return _short(label) if short else label


def gender_label(value: Optional[str], lang: str = "en") -> str:
    if not value:
        return "\u2014"
    return t(_GENDER_KEYS.get(str(value).lower(), str(value)), lang)


def field_of_study_label(value: Optional[str], lang: str = "en") -> str:
    if not value:
        return "\u2014"
    return t(_FIELD_OF_STUDY_KEYS.get(str(value).lower(), str(value)), lang)


def priority_group_label(value: str, lang: str = "en") -> str:
    return t(_PRIORITY_GROUP_KEYS.get(str(value).lower(), str(value)), lang)


def join_list(values, lang: str = "en") -> str:
    """Join with the correct separator for the language."""
    values = [v for v in values if v]
    return ("\u060c ".join(values)) if lang == "ur" else (", ".join(values))


def validation_message(error_code: str, lang: str = "en") -> str:
    """Render a core.validation error code (I18N-02: codes in, prose out)."""
    from core.validation import AGE_MIN, AGE_MAX
    if error_code == "age_range":
        return t("err_age_range", lang, min=AGE_MIN, max=AGE_MAX)
    return t("err_" + error_code, lang)


def _yes_no(value: Optional[bool], lang: str) -> str:
    if value is None:
        return "—"
    return t("option_yes" if value else "option_no", lang)


def _employment_label(value: Optional[str], lang: str) -> str:
    if not value:
        return "—"
    key = {"employed": "option_employed", "unemployed": "option_unemployed"}.get(
        str(value).lower())
    return t(key, lang) if key else str(value)


def _money(value: Any, lang: str) -> str:
    try:
        return f"Rs. {float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value: Any) -> str:
    try:
        f = float(value)
        return f"{f:g}%"
    except (TypeError, ValueError):
        return str(value)


def _years(value: Any, lang: str) -> str:
    try:
        f = float(value)
        n = f"{f:g}"
    except (TypeError, ValueError):
        n = str(value)
    if lang == LANG_UR:
        return f"{n} سال"
    return f"{n} " + ("saal" if lang == LANG_ROMAN else "yrs")


# ---------------------------------------------------------------------------
# Check rendering  (this is what replaces the old English literals)
# ---------------------------------------------------------------------------

_CHECK_LABEL_KEYS = {
    CHECK_AGE: "field_age",
    CHECK_DOMICILE: "field_domicile",
    CHECK_EDUCATION: "field_education",
    CHECK_MARKS: "field_marks",
    CHECK_INCOME: "field_income",
    CHECK_ENROLLMENT: "field_enrolled",
    CHECK_EXISTING_SCHOLARSHIP: "field_existing_scholarship",
    CHECK_EMPLOYMENT: "field_employment",
    CHECK_EXPERIENCE: "field_experience",
    CHECK_DEADLINE: "deadline_label",
}

_CHECK_TITLES = {
    CHECK_AGE: {"en": "Age", "ur": "عمر",
                   "ur_roman": "Umar"},
    CHECK_DOMICILE: {"en": "Domicile", "ur": "ڈومیسائل",
                   "ur_roman": "Domicile"},
    CHECK_EDUCATION: {"en": "Education level", "ur": "تعلیمی سطح",
                   "ur_roman": "Taleemi darja"},
    CHECK_MARKS: {"en": "Academic marks", "ur": "تعلیمی نمبر",
                   "ur_roman": "Taleemi number"},
    CHECK_INCOME: {"en": "Household income", "ur": "گھریلو آمدنی",
                   "ur_roman": "Ghar ki aamdani"},
    CHECK_ENROLLMENT: {"en": "Current enrollment", "ur": "موجودہ داخلہ",
                   "ur_roman": "Maujooda enrollment"},
    CHECK_EXISTING_SCHOLARSHIP: {"en": "Scholarship exclusivity", "ur": "اسکالرشپ کی شرط",
                   "ur_roman": "Scholarship ki shart"},
    CHECK_EMPLOYMENT: {"en": "Employment status", "ur": "ملازمت کی صورتحال",
                   "ur_roman": "Mulazmat ki soorat-e-haal"},
    CHECK_EXPERIENCE: {"en": "Work experience", "ur": "کام کا تجربہ",
                   "ur_roman": "Kaam ka tajurba"},
    CHECK_DEADLINE: {"en": "Application deadline", "ur": "درخواست کی آخری تاریخ",
                   "ur_roman": "Aakhri tareekh"},
    CHECK_GENDER: {"en": "Gender requirement", "ur": "جنس کی شرط",
                   "ur_roman": "Jins ki shart"},
    CHECK_ENGLISH: {"en": "English proficiency", "ur": "انگریزی کی استعداد",
                   "ur_roman": "English ki mahaarat"},
    CHECK_COMPUTER: {"en": "Computer skills", "ur": "کمپیوٹر مہارت",
                   "ur_roman": "Computer hunar"},
    CHECK_FIELD_OF_STUDY: {"en": "Field of study", "ur": "شعبہ تعلیم",
                   "ur_roman": "Taleemi shoba"},
    CHECK_REQUIRED_GROUP: {"en": "Who this is for", "ur": "یہ کن کے لیے ہے",
                   "ur_roman": "Yeh kin ke liye hai"},
}

_REQUIRED_WORD = {"en": "Required", "ur": "درکار", "ur_roman": "Zaroori"}
_YOU_WORD = {"en": "You", "ur": "آپ", "ur_roman": "Aap"}
_NOT_PROVIDED = {"en": "not provided", "ur": "فراہم نہیں کیا گیا", "ur_roman": "nahi diya gaya"}
_AT_LEAST = {"en": "at least", "ur": "کم از کم", "ur_roman": "kam az kam"}
_AT_MOST = {"en": "at most", "ur": "زیادہ سے زیادہ", "ur_roman": "zyada se zyada"}
_BETWEEN = {"en": "between", "ur": "کے درمیان", "ur_roman": "darmiyan"}
_AND = {"en": "and", "ur": "اور", "ur_roman": "aur"}
_OPEN_UNTIL = {"en": "Open until", "ur": "کھلا ہے", "ur_roman": "Khula hai"}
_CLOSED_ON = {"en": "Closed on", "ur": "بند ہوا", "ur_roman": "Band hua"}
_UNREADABLE_DATE = {"en": "Deadline not in YYYY-MM-DD format", "ur": "آخری تاریخ درست شکل میں نہیں", "ur_roman": "Aakhri tareekh SAAL-MAHINA-DIN ki shakal mein nahi"}
_MUST_BE_ENROLLED = {"en": "must be enrolled", "ur": "داخلہ ضروری ہے", "ur_roman": "zaroori hai ke enrolled hon"}
_MUST_NOT_BE_ENROLLED = {"en": "must not be enrolled", "ur": "داخلہ نہیں ہونا چاہیے", "ur_roman": "enrolled nahi hona chahiye"}
_NO_OTHER_SCHOLARSHIP = {"en": "must not hold another scholarship", "ur": "کوئی اور اسکالرشپ نہیں ہونی چاہیے", "ur_roman": "koi aur scholarship nahi honi chahiye"}
_NO_RESTRICTION = {"en": "no restriction", "ur": "کوئی پابندی نہیں", "ur_roman": "koi pabandi nahi"}
_NONE_OF_THESE = {"en": "none of these", "ur": "ان میں سے کوئی نہیں",
                  "ur_roman": "in mein se koi nahi"}


def _w(table: Dict[str, str], lang: str) -> str:
    return table.get(lang, table["en"])


def check_title(check: ConditionCheck, lang: str = "en") -> str:
    entry = _CHECK_TITLES.get(check.key)
    if entry:
        return _w(entry, lang)
    return t(_CHECK_LABEL_KEYS.get(check.key, check.key), lang)


def _requirement_text(check: ConditionCheck, lang: str) -> str:
    key, req = check.key, check.required

    if key == CHECK_AGE and isinstance(req, dict):
        lo, hi = req.get("min"), req.get("max")
        if lo is not None and hi is not None:
            return f"{_w(_BETWEEN, lang)} {lo} {_w(_AND, lang)} {hi}"
        if lo is not None:
            return f"{_w(_AT_LEAST, lang)} {lo}"
        if hi is not None:
            return f"{_w(_AT_MOST, lang)} {hi}"
        return _w(_NO_RESTRICTION, lang)

    if key == CHECK_DOMICILE and isinstance(req, list):
        return "، ".join(req) if lang == "ur" else ", ".join(req)

    if key == CHECK_EDUCATION:
        return f"{_w(_AT_LEAST, lang)} {education_label(req, lang)}"

    if key == CHECK_MARKS:
        return f"{_w(_AT_LEAST, lang)} {_percent(req)}"

    if key == CHECK_INCOME:
        return f"{_w(_AT_MOST, lang)} {_money(req, lang)}"

    if key == CHECK_ENROLLMENT:
        return _w(_MUST_BE_ENROLLED if req else _MUST_NOT_BE_ENROLLED, lang)

    if key == CHECK_EXISTING_SCHOLARSHIP:
        return _w(_NO_OTHER_SCHOLARSHIP if req else _NO_RESTRICTION, lang)

    if key == CHECK_EMPLOYMENT:
        return _employment_label(req, lang)

    if key == CHECK_EXPERIENCE:
        return f"{_w(_AT_LEAST, lang)} {_years(req, lang)}"

    if key == CHECK_GENDER:
        return gender_label(req, lang)

    if key == CHECK_ENGLISH:
        return f"{_w(_AT_LEAST, lang)} {english_label(req, lang, short=True)}"

    if key == CHECK_COMPUTER:
        return f"{_w(_AT_LEAST, lang)} {computer_label(req, lang, short=True)}"

    if key == CHECK_FIELD_OF_STUDY and isinstance(req, list):
        return join_list([field_of_study_label(f, lang) for f in req], lang)

    if key == CHECK_REQUIRED_GROUP and isinstance(req, list):
        # Several groups are an OR, so they are joined as alternatives rather
        # than as a list of things the person must all be. No "only for"
        # prefix: the check title already says "Who this is for", and the
        # scorecard puts this in a Requirement column where the prefix would
        # read twice.
        return join_list([priority_group_label(g, lang) for g in req], lang)

    return "\u2014" if req is None else str(req)


def _actual_text(check: ConditionCheck, lang: str) -> str:
    key, actual = check.key, check.actual

    if actual is None:
        return _w(_NOT_PROVIDED, lang)
    if key == CHECK_EDUCATION:
        return education_label(actual, lang)
    if key == CHECK_MARKS:
        return _percent(actual)
    if key == CHECK_INCOME:
        return _money(actual, lang)
    if key == CHECK_ENROLLMENT:
        return _yes_no(bool(actual), lang)
    if key == CHECK_EXISTING_SCHOLARSHIP:
        # BUG-08: phrase this as the user's situation, never as a contradiction.
        return _w({"en": "already has one", "ur": "پہلے سے موجود ہے"}, lang) if actual \
            else _w({"en": "none", "ur": "کوئی نہیں"}, lang)
    if key == CHECK_EMPLOYMENT:
        return _employment_label(actual, lang)
    if key == CHECK_EXPERIENCE:
        return _years(actual, lang)
    if key == CHECK_GENDER:
        return gender_label(actual, lang)
    if key == CHECK_ENGLISH:
        return english_label(actual, lang, short=True)
    if key == CHECK_COMPUTER:
        return computer_label(actual, lang, short=True)
    if key == CHECK_FIELD_OF_STUDY:
        return field_of_study_label(actual, lang)
    if key == CHECK_REQUIRED_GROUP:
        # An empty list is a real answer - "you told us, and it is none of
        # them" - which is why it is checked before the falsy-value shortcut.
        if isinstance(actual, list):
            return (join_list([priority_group_label(g, lang) for g in actual], lang)
                    if actual else _w(_NONE_OF_THESE, lang))
        return str(actual)
    return str(actual)


def describe_check(check: ConditionCheck, lang: str = "en") -> Tuple[str, str]:
    """
    Render one ConditionCheck as (title, detail) in the requested language.

    This is the single place English or Urdu prose is attached to a rules-engine
    result. The engine itself stays language-free (I18N-02).
    """
    title = check_title(check, lang)

    if check.status == NOT_APPLICABLE:
        return title, ""

    # The deadline reads as a listing property, not a user comparison (BUG-04).
    if check.key == CHECK_DEADLINE:
        if check.status == UNKNOWN:
            return title, _w(_UNREADABLE_DATE, lang)
        word = _CLOSED_ON if check.status == UNMET else _OPEN_UNTIL
        return title, f"{_w(word, lang)} {check.required}"

    required = _requirement_text(check, lang)

    if check.status == UNKNOWN:
        return title, f"{_w(_REQUIRED_WORD, lang)}: {required} · " \
                      f"{_w(_YOU_WORD, lang)}: {_w(_NOT_PROVIDED, lang)}"

    return title, f"{_w(_REQUIRED_WORD, lang)}: {required} · " \
                  f"{_w(_YOU_WORD, lang)}: {_actual_text(check, lang)}"


_RESULT_LABELS = {
    MET: "result_passed",
    UNMET: "result_failed",
    UNKNOWN: "result_verify",
}


def scorecard_row(check: ConditionCheck, lang: str = "en"):
    """
    One scorecard line (V2 P0-1): (requirement, your information, result).

    Same source of truth as describe_check() - a condition must never read one
    way in the scorecard and another way in the explanation.
    """
    return (check_title(check, lang),
            _requirement_text(check, lang),
            _actual_text(check, lang),
            t(_RESULT_LABELS.get(check.status, "result_verify"), lang))


def describe_gap(check: ConditionCheck, lang: str = "en") -> str:
    """
    What stands between the profile and this condition (V2 P0-2).

    States the requirement and the profile's own value side by side, and
    nothing else. It never says what *would* happen if the value changed:
    that is a claim about a future decision this system does not make.
    """
    required = _requirement_text(check, lang)
    if check.status == UNKNOWN or check.actual is None:
        return t("gap_unknown_line", lang, required=required)
    return t("gap_line", lang, required=required, actual=_actual_text(check, lang))


def describe_next_action(action, lang: str = "en") -> str:
    """
    Render a NextAction (V2 P0-6). The decision of *which* action belongs to
    core/next_action.py; this only puts it into words.
    """
    key = action.key
    if key == "review_blocker" or key == "confirm_condition":
        stub = ConditionCheck(key=action.subject.get("check", ""), status=UNKNOWN)
        return t(f"action_{key}", lang, subject=check_title(stub, lang).lower())
    if key == "answer_missing":
        fields = action.subject.get("fields", [])
        if len(fields) == 1:
            return t("action_answer_missing_one", lang,
                     subject=profile_field_label(fields[0], lang))
        return t("action_answer_missing_many", lang, count=len(fields))
    if key == "prepare_documents":
        return t("action_prepare_documents", lang, subject=action.subject.get("count", ""))
    if key == "obtain_document":
        return t("action_obtain_document", lang, subject=action.subject.get("document", ""))
    return t(f"action_{key}", lang)


def describe_ranking_reason(factors: dict, lang: str = "en") -> str:
    """
    Why this result ranks where it does (V2 P0-3), from structured facts only.

    Kept to at most three clauses: a reason nobody reads is not a reason.
    """
    parts = []
    total, met = factors.get("total", 0), factors.get("met", 0)
    if total and met == total:
        parts.append(t("rank_reason_all_met", lang, total=total))
    elif total:
        parts.append(t("rank_reason_met", lang, met=met, total=total))

    groups = factors.get("priority_groups") or []
    if groups:
        names = join_list([priority_group_label(g, lang) for g in groups], lang)
        parts.append(t("rank_reason_priority", lang, groups=names))

    days = factors.get("days_until_deadline")
    if days is not None and days >= 0:
        parts.append(t("rank_reason_deadline", lang, days=days))
    elif factors.get("unknown"):
        parts.append(t("rank_reason_verify", lang, unknown=factors["unknown"]))

    separator = " · "
    return separator.join(parts[:3])


def describe_urgency(urgency: str, days=None, lang: str = "en"):
    """
    Deadline state as (label, detail) (P1-2).

    "No deadline on record" is returned as its own label, never folded into
    "plenty of time": most curated records carry no deadline, so that is the
    state users meet most often, and it is the one where reassurance would do
    the most harm.
    """
    label = t(f"urgency_{urgency}", lang)
    if days is None:
        if urgency == "unknown":
            return label, t("urgency_unknown_note", lang)
        if urgency == "continuous":
            return label, t("urgency_continuous_note", lang)
        return label, ""
    if days < 0:
        return label, t("days_since_passed", lang, days=abs(days))
    if days == 0:
        return label, t("days_remaining_today", lang)
    if days == 1:
        return label, t("days_remaining_one", lang)
    return label, t("days_remaining", lang, days=days)


def describe_freshness(state: str, days=None, lang: str = "en"):
    """Record freshness as (label, detail) (P1-6)."""
    label = t(f"freshness_{state}", lang)
    if state == "never":
        return label, t("freshness_never_note", lang)
    if days is None:
        return label, ""
    # "Checked 0 days ago" is how a template reads when nobody checked the
    # boundary case. A record verified today is the most common state in a
    # freshly curated catalogue, so it is the one worth phrasing properly.
    if days <= 0:
        return label, t("freshness_today", lang)
    if days == 1:
        return label, t("freshness_yesterday", lang)
    return label, t("freshness_days", lang, days=days)


def describe_comparison(comparison, lang: str = "en") -> str:
    """
    The one-line summary under a comparison (P1-5).

    Returns the "too close to call" line when no option is meaningfully
    easier. Naming a winner where the numbers do not support one would turn a
    comparison into a recommendation.
    """
    if not comparison.easiest_id:
        return t("compare_too_close", lang)
    row = next((r for r in comparison.rows
                if r.opportunity_id == comparison.easiest_id), None)
    if row is None:
        return t("compare_too_close", lang)
    reasons = [t(f"compare_reason_{reason['key']}", lang) for reason in comparison.reasons]
    if not reasons:
        return t("compare_too_close", lang)
    return t("compare_easiest", lang, name=row.name, reasons=join_list(reasons, lang))


def describe_requirements(conditions, lang: str = "en"):
    """
    Render an opportunity's own conditions, with no profile involved (UX-10).

    Returns (stated, unstated):
      stated   - list of (title, requirement) pairs, in reading order
      unstated - list of titles the document said nothing about

    Reuses the same titles and phrasing as describe_check(), so a condition
    reads identically whether it is being explained or evaluated. Building a
    ConditionCheck to do that is deliberate: there is exactly one place that
    turns a machine key plus a structured value into prose.

    An unstated condition is NOT a satisfied condition. The caller must say so
    - see "extracted_not_stated_note".
    """
    age_required = None
    if conditions.min_age is not None or conditions.max_age is not None:
        age_required = {"min": conditions.min_age, "max": conditions.max_age}

    fields = [
        (CHECK_AGE, age_required),
        (CHECK_DOMICILE, conditions.domicile_provinces or None),
        (CHECK_EDUCATION, conditions.min_education_level),
        (CHECK_MARKS, conditions.min_marks_percentage),
        (CHECK_INCOME, conditions.max_monthly_household_income),
        (CHECK_ENROLLMENT, conditions.must_be_currently_enrolled),
        (CHECK_EXISTING_SCHOLARSHIP, conditions.must_not_have_existing_scholarship),
        (CHECK_EMPLOYMENT, conditions.employment_status_required),
        (CHECK_EXPERIENCE, conditions.min_experience_years),
        (CHECK_GENDER, getattr(conditions, "gender_required", None)),
        (CHECK_ENGLISH, getattr(conditions, "min_english_level", None)),
        (CHECK_COMPUTER, getattr(conditions, "min_computer_skills", None)),
        (CHECK_FIELD_OF_STUDY, getattr(conditions, "fields_of_study", None) or None),
    ]

    stated, unstated = [], []
    for key, required in fields:
        check = ConditionCheck(key=key, status=UNKNOWN, required=required)
        title = check_title(check, lang)
        if required is None:
            unstated.append(title)
        else:
            stated.append((title, _requirement_text(check, lang)))
    return stated, unstated


def describe_profile(profile, lang: str = "en") -> str:
    """
    A readable, non-identifying prose summary of the profile, used as context
    for the LLM explanation instead of a raw dataclass repr (OPS-06).
    """
    parts = []
    if profile.age is not None:
        parts.append(f"{t('field_age', lang)}: {profile.age}")
    if profile.domicile_province:
        parts.append(f"{t('field_domicile', lang)}: {profile.domicile_province}")
    if profile.education_level:
        parts.append(f"{t('field_education', lang)}: {education_label(profile.education_level, lang)}")
    if profile.gender:
        parts.append(f"{t('field_gender', lang)}: {gender_label(profile.gender, lang)}")
    if profile.marks_percentage is not None:
        parts.append(f"{t('field_marks', lang)}: {_percent(profile.marks_percentage)}")
    if profile.field_of_study:
        parts.append(f"{t('field_field_of_study', lang)}: "
                     f"{field_of_study_label(profile.field_of_study, lang)}")
    if profile.monthly_household_income is not None:
        parts.append(f"{t('field_income', lang)}: {_money(profile.monthly_household_income, lang)}")
    if profile.currently_enrolled is not None:
        parts.append(f"{t('field_enrolled', lang)}: {_yes_no(profile.currently_enrolled, lang)}")
    if profile.has_existing_scholarship is not None:
        parts.append(f"{t('field_existing_scholarship', lang)}: "
                     f"{_yes_no(profile.has_existing_scholarship, lang)}")
    if profile.employment_status:
        parts.append(f"{t('field_employment', lang)}: "
                     f"{_employment_label(profile.employment_status, lang)}")
    if profile.years_experience is not None:
        parts.append(f"{t('field_experience', lang)}: {_years(profile.years_experience, lang)}")
    if profile.english_level:
        parts.append(f"{t('field_english_level', lang)}: "
                     f"{english_label(profile.english_level, lang)}")
    if profile.computer_skills:
        parts.append(f"{t('field_computer_skills', lang)}: "
                     f"{computer_label(profile.computer_skills, lang)}")
    if profile.has_disability is not None:
        parts.append(f"{t('field_has_disability', lang)}: "
                     f"{_yes_no(profile.has_disability, lang)}")
    if profile.is_orphan is not None:
        parts.append(f"{t('field_is_orphan', lang)}: {_yes_no(profile.is_orphan, lang)}")

    if not parts:
        return t("placeholder_not_answered", lang)

    # Explicitly name what was left blank, so the model doesn't fill the gap.
    unanswered = [profile_field_label(f, lang) for f in _PROFILE_FIELD_KEYS
                  if f != "categories" and not profile.is_field_known(f)]
    summary = "; ".join(parts)
    if unanswered:
        label = "Not provided" if lang != "ur" else "فراہم نہیں کیا گیا"
        summary += f"\n{label}: " + ("، ".join(unanswered) if lang == "ur" else ", ".join(unanswered))
    return summary

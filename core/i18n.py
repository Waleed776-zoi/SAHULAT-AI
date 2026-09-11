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

from core.models import (
    ConditionCheck,
    STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
    MET, UNMET, UNKNOWN, NOT_APPLICABLE,
    CHECK_AGE, CHECK_DOMICILE, CHECK_EDUCATION, CHECK_MARKS, CHECK_INCOME,
    CHECK_ENROLLMENT, CHECK_EXISTING_SCHOLARSHIP, CHECK_EMPLOYMENT,
    CHECK_EXPERIENCE, CHECK_DEADLINE, CHECK_GENDER, CHECK_ENGLISH,
    CHECK_COMPUTER, CHECK_FIELD_OF_STUDY,
)

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
    "status_eligible": {"en": "Likely Eligible", "ur": "غالباً اہل"},
    "status_needs_verification": {"en": "Needs Verification", "ur": "تصدیق درکار"},
    "status_not_eligible": {"en": "Likely Not Eligible", "ur": "غالباً اہل نہیں"},
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
    "raw_extraction_toggle": {"en": "Show raw extracted data", "ur": "خام ڈیٹا دکھائیں"},

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
    """
    entry = STRINGS.get(key)
    if not entry:
        return key
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
    return f"{n} " + ("سال" if lang == "ur" else "yrs")


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
    CHECK_AGE: {"en": "Age", "ur": "عمر"},
    CHECK_DOMICILE: {"en": "Domicile", "ur": "ڈومیسائل"},
    CHECK_EDUCATION: {"en": "Education level", "ur": "تعلیمی سطح"},
    CHECK_MARKS: {"en": "Academic marks", "ur": "تعلیمی نمبر"},
    CHECK_INCOME: {"en": "Household income", "ur": "گھریلو آمدنی"},
    CHECK_ENROLLMENT: {"en": "Current enrollment", "ur": "موجودہ داخلہ"},
    CHECK_EXISTING_SCHOLARSHIP: {"en": "Scholarship exclusivity", "ur": "اسکالرشپ کی شرط"},
    CHECK_EMPLOYMENT: {"en": "Employment status", "ur": "ملازمت کی صورتحال"},
    CHECK_EXPERIENCE: {"en": "Work experience", "ur": "کام کا تجربہ"},
    CHECK_DEADLINE: {"en": "Application deadline", "ur": "درخواست کی آخری تاریخ"},
    CHECK_GENDER: {"en": "Gender requirement", "ur": "جنس کی شرط"},
    CHECK_ENGLISH: {"en": "English proficiency", "ur": "انگریزی کی استعداد"},
    CHECK_COMPUTER: {"en": "Computer skills", "ur": "کمپیوٹر مہارت"},
    CHECK_FIELD_OF_STUDY: {"en": "Field of study", "ur": "شعبہ تعلیم"},
}

_REQUIRED_WORD = {"en": "Required", "ur": "درکار"}
_YOU_WORD = {"en": "You", "ur": "آپ"}
_NOT_PROVIDED = {"en": "not provided", "ur": "فراہم نہیں کیا گیا"}
_AT_LEAST = {"en": "at least", "ur": "کم از کم"}
_AT_MOST = {"en": "at most", "ur": "زیادہ سے زیادہ"}
_BETWEEN = {"en": "between", "ur": "کے درمیان"}
_AND = {"en": "and", "ur": "اور"}
_OPEN_UNTIL = {"en": "Open until", "ur": "کھلا ہے"}
_CLOSED_ON = {"en": "Closed on", "ur": "بند ہوا"}
_UNREADABLE_DATE = {"en": "Deadline not in YYYY-MM-DD format", "ur": "آخری تاریخ درست شکل میں نہیں"}
_MUST_BE_ENROLLED = {"en": "must be enrolled", "ur": "داخلہ ضروری ہے"}
_MUST_NOT_BE_ENROLLED = {"en": "must not be enrolled", "ur": "داخلہ نہیں ہونا چاہیے"}
_NO_OTHER_SCHOLARSHIP = {"en": "must not hold another scholarship", "ur": "کوئی اور اسکالرشپ نہیں ہونی چاہیے"}
_NO_RESTRICTION = {"en": "no restriction", "ur": "کوئی پابندی نہیں"}


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

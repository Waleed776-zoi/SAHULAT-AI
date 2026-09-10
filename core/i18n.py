"""
Minimal bilingual string table. Kept as a plain dict (not a heavy i18n
framework) since the hackathon only needs English + Urdu for a fixed set
of UI strings.
"""

STRINGS = {
    "app_title": {"en": "Sahulat AI", "ur": "سہولت اے آئی"},
    "app_tagline": {
        "en": "Find scholarships, jobs & training you may qualify for - or upload an ad and ask.",
        "ur": "وہ اسکالرشپ، نوکریاں اور تربیتی پروگرام تلاش کریں جن کے آپ اہل ہو سکتے ہیں - یا کوئی اشتہار اپلوڈ کریں۔",
    },
    "disclaimer_banner": {
        "en": "Sahulat AI is an informational pre-screening tool, not an official government service. "
              "Final eligibility must be verified through the official program channel.",
        "ur": "سہولت اے آئی ایک معلوماتی پری اسکریننگ ٹول ہے، سرکاری سروس نہیں۔ حتمی اہلیت کی تصدیق سرکاری ذریعے سے کریں۔",
    },
    "select_category": {"en": "What are you looking for?", "ur": "آپ کیا تلاش کر رہے ہیں؟"},
    "category_scholarship": {"en": "🎓 Scholarships", "ur": "🎓 اسکالرشپس"},
    "category_job": {"en": "💼 Jobs", "ur": "💼 نوکریاں"},
    "category_skills": {"en": "🛠️ Skills & Training", "ur": "🛠️ ہنر اور تربیت"},
    "category_assistance": {"en": "🏛️ Public Assistance (Coming Soon)", "ur": "🏛️ سرکاری امداد (جلد آرہا ہے)"},
    "profile_heading": {"en": "Tell us a bit about yourself", "ur": "اپنے بارے میں کچھ بتائیں"},
    "field_age": {"en": "Age", "ur": "عمر"},
    "field_domicile": {"en": "Domicile province", "ur": "ڈومیسائل صوبہ"},
    "field_education": {"en": "Highest education level", "ur": "تعلیمی سطح"},
    "field_marks": {"en": "Marks percentage in last exam (%)", "ur": "آخری امتحان میں فیصد نمبر"},
    "field_income": {"en": "Monthly household income (PKR)", "ur": "ماہانہ گھریلو آمدنی (روپے)"},
    "field_enrolled": {"en": "Currently enrolled as a full-time student?", "ur": "کیا آپ فل ٹائم طالب علم ہیں؟"},
    "field_existing_scholarship": {"en": "Already receiving another scholarship?", "ur": "کیا پہلے سے کوئی اسکالرشپ مل رہی ہے؟"},
    "field_employment": {"en": "Employment status", "ur": "ملازمت کی صورتحال"},
    "field_experience": {"en": "Years of work experience", "ur": "کام کا تجربہ (سال)"},
    "see_matches": {"en": "See my matches", "ur": "میرے مواقع دکھائیں"},
    "status_eligible": {"en": "Likely Eligible", "ur": "غالباً اہل"},
    "status_needs_verification": {"en": "Needs Verification", "ur": "تصدیق درکار"},
    "status_not_eligible": {"en": "Likely Not Eligible", "ur": "غالباً اہل نہیں"},
    "why_match": {"en": "Why this result?", "ur": "یہ نتیجہ کیوں؟"},
    "required_documents": {"en": "Required documents", "ur": "درکار دستاویزات"},
    "application_steps": {"en": "Application steps", "ur": "درخواست کے مراحل"},
    "official_source": {"en": "Official source", "ur": "سرکاری ذریعہ"},
    "last_verified": {"en": "Last verified", "ur": "آخری تصدیق"},
    "upload_ad_heading": {"en": "Upload an ad, poster or PDF", "ur": "اشتہار، پوسٹر یا پی ڈی ایف اپلوڈ کریں"},
    "upload_ad_button": {"en": "Read this ad", "ur": "یہ اشتہار پڑھیں"},
    "ai_extracted_badge": {
        "en": "⚠️ AI-read from your upload - verify against the original",
        "ur": "⚠️ یہ اے آئی نے آپ کی اپلوڈ سے پڑھا ہے - اصل ماخذ سے تصدیق کریں",
    },
    "officially_verified_badge": {"en": "✅ Officially Verified", "ur": "✅ سرکاری طور پر تصدیق شدہ"},
    "ask_followup": {"en": "Ask a follow-up question", "ur": "مزید سوال پوچھیں"},
    "document_checklist_heading": {"en": "Document readiness checklist", "ur": "دستاویزات کی تیاری کی فہرست"},
}


def t(key: str, lang: str = "en") -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))

"""
Sahulat AI - Pakistan Opportunity & Services Navigator
Main Streamlit application.

Run with:  streamlit run app.py
See README.md for full setup instructions.
"""
import streamlit as st

from core.models import UserProfile
from core.data_loader import load_all_opportunities
from core.rules_engine import evaluate_all, evaluate
from core.i18n import t
from core.llm_client import explain_match, answer_followup
from core.ad_reader import read_ad
from core.rag_engine import RagIndex

st.set_page_config(page_title="Sahulat AI", page_icon="🇵🇰", layout="centered")

# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state.language = "en"
if "profile" not in st.session_state:
    st.session_state.profile = UserProfile()
if "opportunities" not in st.session_state:
    st.session_state.opportunities = load_all_opportunities()
if "rag_index" not in st.session_state:
    st.session_state.rag_index = RagIndex(st.session_state.opportunities)

lang = st.session_state.language

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col1, col2 = st.columns([4, 1])
with col1:
    st.title(t("app_title", lang))
    st.caption(t("app_tagline", lang))
with col2:
    chosen = st.radio("Lang", ["en", "ur"], index=0 if lang == "en" else 1, horizontal=True, label_visibility="collapsed")
    st.session_state.language = chosen
    lang = chosen

st.info(t("disclaimer_banner", lang))

tab_catalog, tab_upload = st.tabs(["📋 " + t("select_category", lang), "📤 " + t("upload_ad_heading", lang)])

# ---------------------------------------------------------------------------
# Shared: profile intake form
# ---------------------------------------------------------------------------
def render_profile_form():
    st.subheader(t("profile_heading", lang))
    p = st.session_state.profile

    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input(t("field_age", lang), min_value=0, max_value=100, value=p.age or 0)
        domicile = st.selectbox(
            t("field_domicile", lang),
            ["", "Balochistan", "Punjab", "Sindh", "KP", "AJK", "GB", "ICT", "Erstwhile FATA"],
            index=0,
        )
        education = st.selectbox(
            t("field_education", lang), ["", "matric", "intermediate", "bachelor", "master"], index=0
        )
        marks = st.number_input(t("field_marks", lang), min_value=0.0, max_value=100.0, value=p.marks_percentage or 0.0)
    with c2:
        income = st.number_input(t("field_income", lang), min_value=0.0, value=p.monthly_household_income or 0.0, step=1000.0)
        enrolled = st.selectbox(t("field_enrolled", lang), ["", "Yes", "No"], index=0)
        existing_scholarship = st.selectbox(t("field_existing_scholarship", lang), ["", "Yes", "No"], index=0)
        employment = st.selectbox(t("field_employment", lang), ["", "employed", "unemployed"], index=0)
        experience = st.number_input(t("field_experience", lang), min_value=0.0, value=p.years_experience or 0.0)

    if st.button(t("see_matches", lang), type="primary"):
        st.session_state.profile = UserProfile(
            age=age or None,
            domicile_province=domicile or None,
            education_level=education or None,
            marks_percentage=marks or None,
            monthly_household_income=income or None,
            currently_enrolled=(enrolled == "Yes") if enrolled else None,
            has_existing_scholarship=(existing_scholarship == "Yes") if existing_scholarship else None,
            employment_status=employment or None,
            years_experience=experience or None,
            language=lang,
        )
        st.session_state.show_results = True


def status_badge(status: str) -> str:
    return {
        "Likely Eligible": "🟢 " + t("status_eligible", lang),
        "Needs Verification": "🟡 " + t("status_needs_verification", lang),
        "Likely Not Eligible": "🔴 " + t("status_not_eligible", lang),
    }.get(status, status)


def render_match_card(match, badge_text: str):
    o = match.opportunity
    with st.expander(f"{status_badge(match.overall_status)} — {o.name}"):
        st.markdown(f"**{badge_text}**")
        st.write(o.summary_en)

        st.markdown(f"**{t('why_match', lang)}**")
        for check in match.checks:
            if check.status == "n/a":
                continue
            icon = {"met": "✅", "unmet": "❌", "unknown": "❔"}.get(check.status, "•")
            st.write(f"{icon} **{check.label}** — {check.detail}")

        if o.required_documents:
            st.markdown(f"**{t('required_documents', lang)}**")
            for doc in o.required_documents:
                st.write(f"- {doc}")

        if o.application_steps:
            st.markdown(f"**{t('application_steps', lang)}**")
            for i, step in enumerate(o.application_steps, 1):
                st.write(f"{i}. {step}")

        if o.official_url:
            st.markdown(f"**{t('official_source', lang)}:** [{o.official_url}]({o.official_url})")
        if o.last_verified:
            st.caption(f"{t('last_verified', lang)}: {o.last_verified}")
        if o.disclaimer:
            st.caption(f"⚠️ {o.disclaimer}")

        if st.button(f"🤖 {t('why_match', lang)} (AI explanation)", key=f"explain_{o.opportunity_id}"):
            profile_summary = str(st.session_state.profile)
            result_summary = "\n".join(f"{c.label}: {c.status} ({c.detail})" for c in match.checks)
            with st.spinner("..."):
                explanation = explain_match(profile_summary, result_summary, lang)
            st.write(explanation)


# ---------------------------------------------------------------------------
# Tab 1: Catalog browsing
# ---------------------------------------------------------------------------
with tab_catalog:
    category_labels = {
        "scholarship": t("category_scholarship", lang),
        "job": t("category_job", lang),
        "skills": t("category_skills", lang),
    }
    chosen_categories = st.multiselect(
        t("select_category", lang),
        list(category_labels.values()),
        default=list(category_labels.values()),
    )
    st.caption(t("category_assistance", lang))

    render_profile_form()

    if st.session_state.get("show_results"):
        st.divider()
        opportunities = st.session_state.opportunities
        # filter by chosen categories
        selected_keys = [k for k, v in category_labels.items() if v in chosen_categories]
        filtered = [o for o in opportunities if o.category in selected_keys]

        results = evaluate_all(st.session_state.profile, filtered)
        if not results:
            st.warning("No opportunities loaded for the selected categories yet.")
        for match in results:
            badge = t("officially_verified_badge", lang) if match.opportunity.source_type == "curated" \
                else t("ai_extracted_badge", lang)
            render_match_card(match, badge)

        st.divider()
        st.subheader(t("ask_followup", lang))
        question = st.text_input(t("ask_followup", lang), label_visibility="collapsed")
        if st.button("→", key="ask_btn") and question:
            evidence = st.session_state.rag_index.retrieve(question, top_k=3)
            with st.spinner("..."):
                answer = answer_followup(question, evidence, lang)
            st.write(answer)

# ---------------------------------------------------------------------------
# Tab 2: Upload an ad
# ---------------------------------------------------------------------------
with tab_upload:
    st.subheader(t("upload_ad_heading", lang))
    uploaded_file = st.file_uploader(
        t("upload_ad_heading", lang), type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"

        st.image(file_bytes, width=300) if mime_type.startswith("image/") else None

        if st.button(t("upload_ad_button", lang), type="primary"):
            with st.spinner("..."):
                opportunity, raw_extracted = read_ad(file_bytes, mime_type)

            st.markdown("#### " + t("ai_extracted_badge", lang))
            st.json(raw_extracted)

            st.divider()
            render_profile_form()

            if st.session_state.get("show_results"):
                match = evaluate(st.session_state.profile, opportunity)
                render_match_card(match, t("ai_extracted_badge", lang))

    st.caption(
        "Note: uploaded files are processed only for this session and are never stored. "
        "This feature requires a configured GEMINI_API_KEY - see README."
    )

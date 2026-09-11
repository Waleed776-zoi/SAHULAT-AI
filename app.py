"""
Sahulat AI - Pakistan Opportunity & Services Navigator
Main Streamlit application.

Run with:  streamlit run app.py
See README.md for setup and PROJECT_TRACKER.md for the work log.

STRUCTURE
  sidebar            language, live status, catalogue health, about
  hero               identity, value proposition, trust chips, disclaimer
  tab: find          step 1 categories -> step 2 profile -> step 3 results
  tab: read an ad    upload -> show what was extracted -> screen it
  tab: how it works  the rules-decide/AI-explains architecture, for judges

PERFORMANCE NOTE (PERF-01): nothing heavy is imported or built at page load.
The retrieval index is created lazily, only when a follow-up question is asked,
and cached per process rather than per session.
"""
from __future__ import annotations

import streamlit as st

from core.ad_reader import read_ad
from core.data_loader import (
    KNOWN_CATEGORIES, catalogue_health, category_counts, load_all_opportunities,
)
from core.i18n import (
    describe_check, describe_profile, education_label, status_label, t,
)
from core.llm_client import answer_followup, explain_match, is_ai_available
from core.models import (
    MET, STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
    UNKNOWN, UNMET, UserProfile,
)
from core.rules_engine import evaluate, evaluate_all, summarize_counts

st.set_page_config(
    page_title="Sahulat AI — Pakistan Opportunity Navigator",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROVINCES = ["Balochistan", "Punjab", "Sindh", "KP", "AJK", "GB", "ICT", "Erstwhile FATA"]
EDUCATION_LEVELS = ["matric", "intermediate", "bachelor", "master"]

CATEGORY_ICONS = {
    "scholarship": "🎓",
    "job": "💼",
    "skills": "🛠️",
    "assistance": "🏛️",
    "unknown": "📄",
}

STATUS_STYLE = {
    STATUS_ELIGIBLE: ("status-eligible", "●"),
    STATUS_NEEDS_VERIFICATION: ("status-partial", "●"),
    STATUS_NOT_ELIGIBLE: ("status-no", "●"),
}

CHECK_ICON = {MET: "✔", UNMET: "✕", UNKNOWN: "?"}
CHECK_CLASS = {MET: "check-met", UNMET: "check-unmet", UNKNOWN: "check-unknown"}


# ---------------------------------------------------------------------------
# Cached resources  (PERF-01)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_opportunities():
    return load_all_opportunities()


@st.cache_resource(show_spinner=False)
def get_rag_index():
    """
    Built on first use only. With semantic search off (the default) this is
    instant; with it on, this is where the model load happens - once per
    process, not once per session.
    """
    from core.rag_engine import RagIndex
    return RagIndex(get_opportunities())


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

def inject_css(lang: str) -> None:
    rtl_block = """
      .stMain .block-container { direction: rtl; text-align: right; }
      .stMain .block-container .sa-checkline { flex-direction: row-reverse; }
      .stMain .block-container code, .stMain .block-container a[href^="http"] {
          direction: ltr; unicode-bidi: embed; display: inline-block;
      }
    """ if lang == "ur" else ""

    st.markdown(
        f"""
        <style>
          :root {{
            --sa-green: #0f6b4f;
            --sa-green-soft: rgba(15, 107, 79, 0.10);
            --sa-border: rgba(128, 128, 128, 0.25);
            --sa-muted: rgba(128, 128, 128, 0.95);
            --sa-ok: #15803d;      --sa-ok-bg: rgba(21, 128, 61, 0.12);
            --sa-warn: #b45309;    --sa-warn-bg: rgba(180, 83, 9, 0.12);
            --sa-no: #b91c1c;      --sa-no-bg: rgba(185, 28, 28, 0.12);
          }}

          /* Hero ---------------------------------------------------------- */
          .sa-hero {{
            background: linear-gradient(135deg, var(--sa-green) 0%, #0b4f3a 100%);
            color: #fff;
            border-radius: 14px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.1rem;
          }}
          .sa-hero h1 {{
            margin: 0; font-size: 2rem; font-weight: 700; color: #fff; line-height: 1.2;
          }}
          .sa-hero .sa-eyebrow {{
            text-transform: uppercase; letter-spacing: .09em; font-size: .72rem;
            opacity: .85; margin-bottom: .35rem; font-weight: 600;
          }}
          .sa-hero p {{ margin: .5rem 0 0; opacity: .94; font-size: 1.02rem; max-width: 60ch; }}
          .sa-chips {{ display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 1rem; }}
          .sa-chip {{
            background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.28);
            padding: .22rem .6rem; border-radius: 999px; font-size: .78rem; font-weight: 500;
          }}

          /* Section headers ------------------------------------------------ */
          .sa-step {{ display: flex; align-items: baseline; gap: .55rem; margin: .3rem 0 .1rem; }}
          .sa-step-num {{
            background: var(--sa-green); color: #fff; border-radius: 999px;
            width: 1.55rem; height: 1.55rem; display: inline-flex;
            align-items: center; justify-content: center;
            font-size: .82rem; font-weight: 700; flex: 0 0 auto;
          }}
          .sa-step-title {{ font-size: 1.12rem; font-weight: 650; }}
          .sa-hint {{ color: var(--sa-muted); font-size: .86rem; margin: .1rem 0 .5rem; }}

          /* Badges --------------------------------------------------------- */
          .sa-badge {{
            display: inline-block; padding: .15rem .55rem; border-radius: 6px;
            font-size: .74rem; font-weight: 600; border: 1px solid transparent;
            white-space: nowrap;
          }}
          .status-eligible {{ background: var(--sa-ok-bg);   color: var(--sa-ok);   border-color: var(--sa-ok); }}
          .status-partial  {{ background: var(--sa-warn-bg); color: var(--sa-warn); border-color: var(--sa-warn); }}
          .status-no       {{ background: var(--sa-no-bg);   color: var(--sa-no);   border-color: var(--sa-no); }}
          .badge-verified  {{ background: var(--sa-ok-bg);   color: var(--sa-ok);   border-color: var(--sa-ok); }}
          .badge-unverified{{ background: var(--sa-warn-bg); color: var(--sa-warn); border-color: var(--sa-warn); }}
          .badge-ai        {{ background: var(--sa-warn-bg); color: var(--sa-warn); border-color: var(--sa-warn); }}
          .badge-closed    {{ background: rgba(120,120,120,.15); color: var(--sa-muted); border-color: var(--sa-border); }}

          /* Condition lines ------------------------------------------------ */
          .sa-checkline {{
            display: flex; align-items: flex-start; gap: .55rem;
            padding: .3rem 0; border-bottom: 1px dashed var(--sa-border);
          }}
          .sa-checkline:last-child {{ border-bottom: none; }}
          .sa-checkicon {{
            flex: 0 0 1.25rem; height: 1.25rem; border-radius: 4px;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: .78rem; font-weight: 700; margin-top: .1rem;
          }}
          .check-met     {{ background: var(--sa-ok-bg);   color: var(--sa-ok); }}
          .check-unmet   {{ background: var(--sa-no-bg);   color: var(--sa-no); }}
          .check-unknown {{ background: var(--sa-warn-bg); color: var(--sa-warn); }}
          .sa-checkbody {{ flex: 1 1 auto; }}
          .sa-checktitle {{ font-weight: 600; font-size: .9rem; }}
          .sa-checkdetail {{ color: var(--sa-muted); font-size: .82rem; }}

          /* Misc ----------------------------------------------------------- */
          .sa-meta {{ color: var(--sa-muted); font-size: .82rem; }}
          .sa-card-title {{ font-size: 1.02rem; font-weight: 650; margin-bottom: .1rem; }}
          .sa-kpi {{ font-size: 1.7rem; font-weight: 700; line-height: 1; }}
          .sa-kpi-label {{ color: var(--sa-muted); font-size: .8rem; }}
          .sa-quota {{
            background: var(--sa-green-soft); border-left: 3px solid var(--sa-green);
            padding: .5rem .7rem; border-radius: 6px; font-size: .85rem; margin-top: .4rem;
          }}
          div[data-testid="stMetricValue"] {{ font-size: 1.6rem; }}
          {rtl_block}
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, css_class: str) -> str:
    return f'<span class="sa-badge {css_class}">{text}</span>'


def step_header(number: int, title: str, hint: str = "") -> None:
    st.markdown(
        f'<div class="sa-step"><span class="sa-step-num">{number}</span>'
        f'<span class="sa-step-title">{title}</span></div>',
        unsafe_allow_html=True,
    )
    if hint:
        st.markdown(f'<div class="sa-hint">{hint}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "language": "en",
        "profile": UserProfile(),
        "show_results": False,
        "selected_categories": [c for c in KNOWN_CATEGORIES],
        "uploaded_opportunity": None,
        "uploaded_raw": None,
        "uploaded_name": None,
        "screen_upload": False,
        "explanations": {},
        "documents_ready": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()
lang = st.session_state.language
inject_css(lang)

opportunities = get_opportunities()
counts = category_counts(opportunities)
health = catalogue_health(opportunities)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(f"### {t('app_title', lang)}")
    st.caption(t("app_subtitle", lang))

    chosen_lang = st.radio(
        t("sidebar_language", lang),
        options=["en", "ur"],
        index=0 if lang == "en" else 1,
        format_func=lambda code: "English" if code == "en" else "اردو",
        horizontal=True,
        key="language_picker",
    )
    if chosen_lang != st.session_state.language:
        st.session_state.language = chosen_lang
        st.rerun()

    st.divider()
    st.markdown(f"**{t('sidebar_status', lang)}**")

    ai_on = is_ai_available()
    if ai_on:
        st.success(t("ai_enabled", lang), icon="✅")
    else:
        st.info(t("ai_mock_mode", lang), icon="🔌")
        st.caption(t("ai_mock_explainer", lang))

    st.divider()
    st.markdown(f"**{t('sidebar_catalog', lang)}**")
    st.markdown(t("sidebar_records", lang, n=health["total"]))
    if health["verified"]:
        st.caption("✅ " + t("sidebar_verified", lang, n=health["verified"]))
    if health["unverified"]:
        st.caption("⚠️ " + t("sidebar_unverified", lang, n=health["unverified"]))

    st.divider()
    with st.expander(t("sidebar_about", lang)):
        st.caption(t("sidebar_about_body", lang))


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

chips = "".join(
    f'<span class="sa-chip">{t(key, lang)}</span>'
    for key in ("chip_no_cnic", "chip_rules_based", "chip_official_sources", "chip_bilingual")
)
st.markdown(
    f"""
    <div class="sa-hero">
      <div class="sa-eyebrow">{t('app_subtitle', lang)}</div>
      <h1>{t('app_title', lang)}</h1>
      <p>{t('app_tagline', lang)}</p>
      <div class="sa-chips">{chips}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.info(t("disclaimer_banner", lang), icon="ℹ️")


# ---------------------------------------------------------------------------
# Shared components
# ---------------------------------------------------------------------------

def render_category_picker() -> list:
    """
    Category selection. A category with zero loaded records is shown but
    disabled and labelled, instead of silently returning nothing (DATA-03).
    """
    step_header(1, t("step_1_title", lang), t("select_category", lang))

    selected = []
    columns = st.columns(len(KNOWN_CATEGORIES))
    for column, category in zip(columns, KNOWN_CATEGORIES):
        available = counts.get(category, 0)
        with column:
            with st.container(border=True):
                st.markdown(
                    f"<div style='font-size:1.5rem;line-height:1'>"
                    f"{CATEGORY_ICONS.get(category, '📄')}</div>"
                    f"<div class='sa-card-title'>{t(f'category_{category}', lang)}</div>",
                    unsafe_allow_html=True,
                )
                if available:
                    checked = st.checkbox(
                        t("available_count", lang, n=available),
                        value=category in st.session_state.selected_categories,
                        key=f"cat_{category}",
                    )
                    if checked:
                        selected.append(category)
                else:
                    st.checkbox(
                        t("coming_soon", lang), value=False, disabled=True,
                        key=f"cat_{category}", help=t("category_empty_note", lang),
                    )

    st.session_state.selected_categories = selected
    return selected


def _as_float(value):
    """
    Seed a float-typed number_input safely.

    Streamlit rejects an int `value` when min/max/step are floats, so a profile
    holding 75 rather than 75.0 would crash the form. None stays None - that is
    how "unanswered" is expressed (BUG-03).
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _tri_state(label: str, current, key: str) -> object:
    """Yes / No / unanswered selector that can express 'not provided'."""
    options = [None, True, False]
    return st.selectbox(
        label,
        options=options,
        index=options.index(current) if current in options else 0,
        format_func=lambda v: t("placeholder_not_answered", lang) if v is None
        else t("option_yes" if v else "option_no", lang),
        key=key,
    )


def render_profile_form() -> None:
    """
    The single profile form for the whole app.

    There is exactly ONE of these (BUG-01): the upload tab reuses this profile
    rather than rendering a second copy, which is both simpler and avoids the
    duplicate-widget-ID crash. Wrapped in st.form so filling it in costs one
    rerun instead of one per keystroke.
    """
    profile: UserProfile = st.session_state.profile
    step_header(2, t("step_2_title", lang), t("optional_hint", lang))
    st.caption("🔒 " + t("profile_privacy_note", lang))

    with st.form("profile_form", border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            # value=None keeps "unanswered" and "zero" as different answers.
            # Using `x or None` here is what made a zero income read as
            # "not provided" (BUG-03).
            age = st.number_input(
                t("field_age", lang), min_value=0, max_value=100, step=1,
                value=_as_int(profile.age),
                placeholder=t("placeholder_not_answered", lang),
            )
            domicile = st.selectbox(
                t("field_domicile", lang),
                options=[None] + PROVINCES,
                index=([None] + PROVINCES).index(profile.domicile_province)
                if profile.domicile_province in PROVINCES else 0,
                format_func=lambda v: t("placeholder_not_answered", lang) if v is None else v,
            )
            education = st.selectbox(
                t("field_education", lang),
                options=[None] + EDUCATION_LEVELS,
                index=([None] + EDUCATION_LEVELS).index(profile.education_level)
                if profile.education_level in EDUCATION_LEVELS else 0,
                format_func=lambda v: t("placeholder_not_answered", lang) if v is None
                else education_label(v, lang),
            )

        with col2:
            marks = st.number_input(
                t("field_marks", lang), min_value=0.0, max_value=100.0, step=1.0,
                value=_as_float(profile.marks_percentage),
                placeholder=t("placeholder_not_answered", lang),
            )
            income = st.number_input(
                t("field_income", lang), min_value=0.0, step=1000.0,
                value=_as_float(profile.monthly_household_income),
                placeholder=t("placeholder_not_answered", lang),
            )
            experience = st.number_input(
                t("field_experience", lang), min_value=0.0, max_value=60.0, step=1.0,
                value=_as_float(profile.years_experience),
                placeholder=t("placeholder_not_answered", lang),
            )

        with col3:
            enrolled = _tri_state(t("field_enrolled", lang),
                                  profile.currently_enrolled, "form_enrolled")
            has_scholarship = _tri_state(t("field_existing_scholarship", lang),
                                         profile.has_existing_scholarship, "form_scholarship")
            employment_options = [None, "employed", "unemployed"]
            employment = st.selectbox(
                t("field_employment", lang),
                options=employment_options,
                index=employment_options.index(profile.employment_status)
                if profile.employment_status in employment_options else 0,
                format_func=lambda v: t("placeholder_not_answered", lang) if v is None
                else t(f"option_{v}", lang),
            )

        submit_col, reset_col = st.columns([3, 1])
        with submit_col:
            submitted = st.form_submit_button(
                t("update_matches", lang) if st.session_state.show_results
                else t("see_matches", lang),
                type="primary", use_container_width=True,
            )
        with reset_col:
            cleared = st.form_submit_button(t("reset_profile", lang),
                                            use_container_width=True)

    if cleared:
        st.session_state.profile = UserProfile(language=lang)
        st.session_state.show_results = False
        st.rerun()

    if submitted:
        st.session_state.profile = UserProfile(
            age=age,
            domicile_province=domicile,
            education_level=education,
            marks_percentage=marks,
            monthly_household_income=income,
            currently_enrolled=enrolled,
            has_existing_scholarship=has_scholarship,
            employment_status=employment,
            years_experience=experience,
            language=lang,
        )
        st.session_state.show_results = True
        st.session_state.explanations = {}


def render_trust_badge(opportunity) -> str:
    """
    Curated and uploaded records never share a badge (Invariant 4), and an
    unverified curated record says so rather than borrowing the verified look.
    """
    if opportunity.source_type == "user_uploaded":
        return badge("⚠ " + t("ai_extracted_badge", lang), "badge-ai")
    if opportunity.is_verified():
        return badge("✅ " + t("officially_verified_badge", lang), "badge-verified")
    return badge("⚠ " + t("unverified_badge", lang), "badge-unverified")


def render_checks(match) -> None:
    st.markdown(f"**{t('why_match', lang)}**")
    rows = []
    for check in match.applicable_checks():
        title, detail = describe_check(check, lang)
        icon = CHECK_ICON.get(check.status, "•")
        css = CHECK_CLASS.get(check.status, "check-unknown")
        rows.append(
            f'<div class="sa-checkline">'
            f'<span class="sa-checkicon {css}">{icon}</span>'
            f'<span class="sa-checkbody"><span class="sa-checktitle">{title}</span><br>'
            f'<span class="sa-checkdetail">{detail}</span></span></div>'
        )
    st.markdown("".join(rows), unsafe_allow_html=True)

    if match.missing_profile_fields:
        from core.i18n import profile_field_label
        names = [profile_field_label(f, lang) for f in match.missing_profile_fields]
        joined = "، ".join(names) if lang == "ur" else ", ".join(names)
        st.caption("💡 " + t("missing_fields_hint", lang, fields=joined))


def render_documents(opportunity) -> None:
    """Interactive readiness checklist rather than a static list (FEAT-01)."""
    if not opportunity.required_documents:
        return

    ready = st.session_state.documents_ready.setdefault(opportunity.opportunity_id, set())
    total = len(opportunity.required_documents)

    st.markdown(f"**{t('document_checklist_heading', lang)}** "
                f'<span class="sa-meta">— {t("documents_ready", lang, have=len(ready), total=total)}</span>',
                unsafe_allow_html=True)
    for index, document in enumerate(opportunity.required_documents):
        checked = st.checkbox(
            document, value=index in ready,
            key=f"doc_{opportunity.opportunity_id}_{index}",
        )
        if checked:
            ready.add(index)
        else:
            ready.discard(index)
    if total:
        st.progress(len(ready) / total)


def render_match_card(match, expanded: bool = False) -> None:
    opportunity = match.opportunity
    css_class, dot = STATUS_STYLE.get(match.overall_status, ("status-partial", "●"))
    title = opportunity.display_name(lang)
    header = f"{dot}  {title}"

    with st.expander(header, expanded=expanded):
        badges = [
            badge(f"{dot} {status_label(match.overall_status, lang)}", css_class),
            render_trust_badge(opportunity),
        ]
        if match.listing_closed:
            badges.append(badge("🕒 " + t("listing_closed", lang), "badge-closed"))
        st.markdown(" ".join(badges), unsafe_allow_html=True)

        st.markdown(
            f'<div class="sa-meta">{CATEGORY_ICONS.get(opportunity.category, "📄")} '
            f'{t(f"category_{opportunity.category}", lang) if opportunity.category in KNOWN_CATEGORIES else opportunity.category}'
            f' · {t("provider_label", lang)}: {opportunity.provider}</div>',
            unsafe_allow_html=True,
        )
        summary = opportunity.display_summary(lang)
        if summary:
            st.write(summary)

        # BUG-04: say plainly that a closed listing is about the listing.
        if match.listing_closed:
            st.warning(t("listing_closed_explainer", lang), icon="🕒")

        # DATA-01: never print a TODO placeholder as if it were a date.
        if opportunity.source_type == "curated" and not opportunity.is_verified():
            st.warning(t("unverified_explainer", lang), icon="⚠️")

        st.divider()
        render_checks(match)

        quota_note = opportunity.eligibility_conditions.special_quota_note
        if quota_note:
            st.markdown(
                f'<div class="sa-quota"><b>{t("quota_note_label", lang)}</b><br>{quota_note}</div>',
                unsafe_allow_html=True,
            )

        st.divider()
        doc_col, step_col = st.columns(2)
        with doc_col:
            render_documents(opportunity)
        with step_col:
            if opportunity.application_steps:
                st.markdown(f"**{t('application_steps', lang)}**")
                for index, step in enumerate(opportunity.application_steps, 1):
                    st.markdown(f"{index}. {step}")

        st.divider()
        meta = []
        if opportunity.official_url:
            meta.append(f"[{t('open_official_site', lang)} ↗]({opportunity.official_url})")
        if opportunity.is_verified():
            meta.append(f"{t('last_verified', lang)}: {opportunity.last_verified}")
        if match.deadline:
            meta.append(f"{t('deadline_label', lang)}: {match.deadline}")
        if meta:
            st.markdown('<span class="sa-meta">' + "  ·  ".join(meta) + "</span>",
                        unsafe_allow_html=True)

        if opportunity.disclaimer:
            st.caption("⚠️ " + opportunity.disclaimer)

        explain_key = f"explain_{opportunity.opportunity_id}"
        if st.button(f"🤖 {t('ai_explain_button', lang)}", key=f"btn_{explain_key}"):
            with st.spinner(""):
                st.session_state.explanations[explain_key] = explain_match(
                    describe_profile(st.session_state.profile, lang),
                    build_result_summary(match),
                    lang,
                )
        if explain_key in st.session_state.explanations:
            st.info(st.session_state.explanations[explain_key])


def build_result_summary(match) -> str:
    """Plain-text rendering of a decided result, handed to the LLM to explain."""
    lines = [
        f"Opportunity: {match.opportunity.name}",
        f"Provider: {match.opportunity.provider}",
        f"Decision (already made by the rules engine): "
        f"{status_label(match.overall_status, 'en')}",
    ]
    if match.listing_closed:
        lines.append("NOTE: this listing's application deadline has passed.")
    for check in match.applicable_checks():
        title, detail = describe_check(check, "en")
        lines.append(f"- {title}: {check.status} ({detail})")
    return "\n".join(lines)


def build_export_text(results) -> str:
    """Plain-text summary for download (FEAT-02). Keeps every trust marker."""
    out = [
        t("app_title", lang) + " — " + t("results_heading", lang),
        t("disclaimer_banner", lang),
        "=" * 68,
        "",
    ]
    for match in results:
        opportunity = match.opportunity
        trust = (t("ai_extracted_badge", lang) if opportunity.source_type == "user_uploaded"
                 else t("officially_verified_badge", lang) if opportunity.is_verified()
                 else t("unverified_badge", lang))
        out.append(f"{opportunity.display_name(lang)}")
        out.append(f"  {status_label(match.overall_status, lang)}  |  {trust}")
        if match.listing_closed:
            out.append(f"  ** {t('listing_closed', lang)} **")
        out.append(f"  {t('provider_label', lang)}: {opportunity.provider}")
        for check in match.applicable_checks():
            title, detail = describe_check(check, lang)
            mark = {MET: "[x]", UNMET: "[ ]", UNKNOWN: "[?]"}.get(check.status, "[-]")
            out.append(f"    {mark} {title} — {detail}")
        if opportunity.required_documents:
            out.append(f"  {t('required_documents', lang)}:")
            out.extend(f"    - {doc}" for doc in opportunity.required_documents)
        if opportunity.application_steps:
            out.append(f"  {t('application_steps', lang)}:")
            out.extend(f"    {i}. {s}" for i, s in enumerate(opportunity.application_steps, 1))
        if opportunity.official_url:
            out.append(f"  {t('official_source', lang)}: {opportunity.official_url}")
        out.append("")
    return "\n".join(out)


def render_results(results) -> None:
    step_header(3, t("step_3_title", lang), t("results_intro", lang, n=len(results)))

    totals = summarize_counts(results)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(t("status_eligible", lang), totals[STATUS_ELIGIBLE])
    kpi2.metric(t("status_needs_verification", lang), totals[STATUS_NEEDS_VERIFICATION])
    kpi3.metric(t("status_not_eligible", lang), totals[STATUS_NOT_ELIGIBLE])
    kpi4.metric(t("listing_closed", lang), totals["closed"])

    groups = [
        (STATUS_ELIGIBLE, "group_eligible_help"),
        (STATUS_NEEDS_VERIFICATION, "group_needs_verification_help"),
        (STATUS_NOT_ELIGIBLE, "group_not_eligible_help"),
    ]
    for status, help_key in groups:
        group = [r for r in results if r.overall_status == status]
        if not group:
            continue
        st.markdown(f"#### {status_label(status, lang)} ({len(group)})")
        st.markdown(f'<div class="sa-hint">{t(help_key, lang)}</div>',
                    unsafe_allow_html=True)
        for match in group:
            render_match_card(match, expanded=(status == STATUS_ELIGIBLE and len(group) <= 2))

    st.divider()
    st.markdown(f"**{t('export_heading', lang)}**")
    st.caption(t("export_hint", lang))
    st.download_button(
        t("export_button", lang),
        data=build_export_text(results).encode("utf-8"),
        file_name="sahulat-ai-results.txt",
        mime="text/plain",
    )


def render_followup() -> None:
    st.divider()
    st.markdown(f"### {t('ask_followup', lang)}")
    st.caption(t("ask_followup_hint", lang))

    question = st.text_input(
        t("ask_followup", lang),
        placeholder=t("ask_placeholder", lang),
        label_visibility="collapsed",
        key="followup_question",
    )
    if st.button(t("ask_button", lang), key="ask_btn") and question.strip():
        # PERF-01: the index is built here, on demand - never at page load.
        with st.spinner(""):
            evidence = get_rag_index().retrieve(question, top_k=3)
            answer = answer_followup(question, evidence, lang)
        if evidence:
            st.info(answer)
        else:
            st.warning(answer, icon="🔎")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_find, tab_upload, tab_how = st.tabs([
    f"🔎 {t('tab_find', lang)}",
    f"📤 {t('tab_upload', lang)}",
    f"ℹ️ {t('tab_how', lang)}",
])


with tab_find:
    selected_categories = render_category_picker()
    st.divider()
    render_profile_form()

    if st.session_state.show_results:
        st.divider()
        if not selected_categories:
            st.warning(t("no_categories_selected", lang), icon="🗂️")
        else:
            filtered = [o for o in opportunities if o.category in selected_categories]
            if not filtered:
                st.warning(t("no_results", lang), icon="📭")
            else:
                results = evaluate_all(st.session_state.profile, filtered)
                render_results(results)
                render_followup()
    else:
        st.info(t("fill_profile_prompt", lang), icon="👆")


with tab_upload:
    st.markdown(f"### {t('upload_ad_heading', lang)}")
    st.caption(t("upload_ad_intro", lang))

    if not is_ai_available():
        st.info(t("ai_mock_extraction_notice", lang), icon="🔌")

    uploaded_file = st.file_uploader(
        t("upload_ad_heading", lang),
        type=["png", "jpg", "jpeg", "pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"

        preview_col, action_col = st.columns([1, 2])
        with preview_col:
            # BUG-09: a plain if, not a conditional expression used as a statement.
            if mime_type.startswith("image/"):
                st.image(file_bytes, use_container_width=True)
            else:
                st.markdown("📄 " + uploaded_file.name)
        with action_col:
            st.caption("🔒 " + t("upload_privacy_note", lang))
            if st.button(t("upload_ad_button", lang), type="primary"):
                with st.spinner(""):
                    opportunity, raw = read_ad(file_bytes, mime_type, language=lang)
                # BUG-02: persist across reruns, or the result vanishes the
                # moment any other widget is touched.
                st.session_state.uploaded_opportunity = opportunity
                st.session_state.uploaded_raw = raw
                st.session_state.uploaded_name = uploaded_file.name
                st.session_state.screen_upload = False

    if st.session_state.uploaded_opportunity is not None:
        st.divider()
        opportunity = st.session_state.uploaded_opportunity
        raw = st.session_state.uploaded_raw or {}

        head_col, clear_col = st.columns([3, 1])
        with head_col:
            st.markdown(f"#### {t('extracted_fields_heading', lang)}")
        with clear_col:
            if st.button(t("upload_clear", lang), use_container_width=True):
                st.session_state.uploaded_opportunity = None
                st.session_state.uploaded_raw = None
                st.session_state.uploaded_name = None
                st.session_state.screen_upload = False
                st.rerun()

        confidence = str(raw.get("extraction_confidence", "low")).lower()
        st.markdown(
            badge("⚠ " + t("ai_extracted_badge", lang), "badge-ai")
            + " "
            + badge(f"{t('extraction_confidence', lang)}: "
                    f"{t('confidence_' + confidence, lang) if confidence in ('high', 'medium', 'low') else confidence}",
                    "badge-closed"),
            unsafe_allow_html=True,
        )

        if raw.get("_error"):
            st.error(raw["_error"])

        st.write(f"**{opportunity.name}**")
        if opportunity.summary_en:
            st.write(opportunity.summary_en)
        st.caption(f"{t('provider_label', lang)}: {opportunity.provider}")

        with st.expander(t("raw_extraction_toggle", lang)):
            st.json(raw)

        st.divider()
        if st.session_state.profile.is_empty():
            st.info(t("upload_needs_profile", lang), icon="📝")
        else:
            if st.button(t("screen_uploaded", lang), type="primary"):
                st.session_state.screen_upload = True
            if st.session_state.screen_upload:
                match = evaluate(st.session_state.profile, opportunity)
                render_match_card(match, expanded=True)

    st.caption("🔒 " + t("upload_privacy_note", lang))


with tab_how:
    st.markdown(f"### {t('how_heading', lang)}")
    st.write(t("how_intro", lang))

    col1, col2, col3 = st.columns(3)
    for column, (title_key, body_key) in zip(
        (col1, col2, col3),
        (("how_step1_title", "how_step1_body"),
         ("how_step2_title", "how_step2_body"),
         ("how_step3_title", "how_step3_body")),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"**{t(title_key, lang)}**")
                st.caption(t(body_key, lang))

    st.divider()
    trust_col, privacy_col = st.columns(2)
    with trust_col:
        st.markdown(f"**{t('how_trust_heading', lang)}**")
        st.caption(t("how_trust_body", lang))
        st.markdown(
            badge("✅ " + t("officially_verified_badge", lang), "badge-verified") + " "
            + badge("⚠ " + t("unverified_badge", lang), "badge-unverified") + " "
            + badge("⚠ " + t("ai_extracted_badge", lang), "badge-ai"),
            unsafe_allow_html=True,
        )
    with privacy_col:
        st.markdown(f"**{t('how_privacy_heading', lang)}**")
        st.caption(t("profile_privacy_note", lang))

    st.divider()
    st.caption(t("disclaimer_banner", lang))

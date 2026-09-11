"""
Sahulat AI - Pakistan Opportunity & Services Navigator
Main Streamlit application.

Run with:  streamlit run app.py
See README.md for setup and PROJECT_TRACKER.md for the work log.

INTERACTION MODEL
  A guided four-step wizard, then results. Steps are validated in
  core/validation.py, so a step cannot be completed until its required fields
  hold sensible values. Deliberately NOT built on st.form: a form submits on
  Enter, which made a half-filled profile jump straight to results.

PERFORMANCE (PERF-01)
  Nothing heavy is imported or built at page load. The retrieval index is
  created lazily, only when a follow-up question is asked, and cached per
  process rather than per session.
"""
from __future__ import annotations

import streamlit as st

from core.ad_reader import read_ad
from core.data_loader import (
    KNOWN_CATEGORIES, catalogue_health, category_counts, load_all_opportunities,
)
from core.i18n import (
    computer_label, describe_check, describe_profile, education_label,
    english_label, field_of_study_label, gender_label, join_list,
    priority_group_label, profile_field_label, status_label, t,
    validation_message,
)
from core.llm_client import answer_followup, explain_match, is_ai_available
from core.models import (
    COMPUTER_LEVELS, EDUCATION_LEVELS, ENGLISH_LEVELS, FIELDS_OF_STUDY, GENDERS,
    MET, PROVINCES, STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION,
    STATUS_NOT_ELIGIBLE, UNKNOWN, UNMET, UserProfile,
)
from core.rules_engine import evaluate, evaluate_all, summarize_counts
from core.validation import (
    AGE_MAX, AGE_MIN, EXPERIENCE_MAX, INCOME_MAX, MARKS_MAX, MARKS_MIN,
    RESULTS_STEP_INDEX, STEPS, completion_percent, validate_step,
)

st.set_page_config(
    page_title="Sahulat AI — Pakistan Opportunity Navigator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Profile fields, in the order they are asked.
PROFILE_FIELDS = (
    "age", "gender", "domicile_province", "education_level", "marks_percentage",
    "field_of_study", "currently_enrolled", "monthly_household_income",
    "has_existing_scholarship", "english_level", "computer_skills",
    "employment_status", "years_experience", "has_disability", "is_orphan",
)

STATUS_CLASS = {
    STATUS_ELIGIBLE: "is-eligible",
    STATUS_NEEDS_VERIFICATION: "is-partial",
    STATUS_NOT_ELIGIBLE: "is-no",
}
CHECK_MARK = {MET: "✓", UNMET: "✕", UNKNOWN: "?"}
CHECK_CLASS = {MET: "mark-met", UNMET: "mark-unmet", UNKNOWN: "mark-unknown"}


# ---------------------------------------------------------------------------
# Cached resources  (PERF-01)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_opportunities():
    return load_all_opportunities()


@st.cache_resource(show_spinner=False)
def get_rag_index():
    from core.rag_engine import RagIndex
    return RagIndex(get_opportunities())


# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&"
    "family=Noto+Naskh+Arabic:wght@400;500;600;700&"
    "family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');"
)


def inject_css(lang: str) -> None:
    urdu = lang == "ur"
    body_font = ("'Noto Naskh Arabic', 'Inter', system-ui, sans-serif" if urdu
                 else "'Inter', system-ui, -apple-system, sans-serif")
    display_font = ("'Noto Nastaliq Urdu', 'Noto Naskh Arabic', serif" if urdu
                    else "'Source Serif 4', Georgia, serif")
    display_line_height = "2.1" if urdu else "1.18"

    rtl = """
      .stMain .block-container { direction: rtl; text-align: right; }
      .sa-checkrow { flex-direction: row-reverse; }
      .sa-stepper { flex-direction: row-reverse; }
      .sa-field-head { flex-direction: row-reverse; }
      a[href^="http"], .sa-mono { direction: ltr; unicode-bidi: embed;
                                  display: inline-block; }
    """ if urdu else ""

    st.markdown(
        f"""
        <style>
          {FONT_IMPORT}

          :root {{
            --ink:        #16211D;
            --ink-soft:   #41514B;
            --muted:      #6B7B75;
            --line:       #E2E8E5;
            --line-soft:  #EEF2F0;
            --canvas:     #F6F8F7;
            --surface:    #FFFFFF;
            --brand:      #0E6B4F;
            --brand-deep: #0A4A36;
            --brand-tint: #EAF2EE;
            --ok:         #1B7A47;  --ok-tint:   #E8F4ED;
            --warn:       #8A6100;  --warn-tint: #FBF2DF;
            --no:         #A03027;  --no-tint:   #FBECEA;
            --radius:     10px;
          }}

          html, body, .stApp, [class*="st-"], button, input, select, textarea {{
            font-family: {body_font};
          }}
          .stApp {{ background: var(--canvas); }}
          .stMain .block-container {{ max-width: 1120px; padding-top: 2.2rem; }}

          h1, h2, h3, .sa-display {{
            font-family: {display_font};
            line-height: {display_line_height};
            color: var(--ink);
            letter-spacing: -0.01em;
          }}

          /* ---------- Masthead ---------- */
          .sa-masthead {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-top: 3px solid var(--brand);
            border-radius: var(--radius);
            padding: 1.5rem 1.75rem 1.35rem;
            margin-bottom: 1rem;
          }}
          .sa-wordmark {{
            font-family: {display_font};
            font-size: 1.85rem; font-weight: 700; color: var(--brand-deep);
            line-height: {display_line_height}; margin: 0;
          }}
          .sa-kicker {{
            font-size: .7rem; font-weight: 600; letter-spacing: .14em;
            text-transform: uppercase; color: var(--muted); margin-bottom: .45rem;
          }}
          .sa-lede {{
            color: var(--ink-soft); font-size: 1rem; max-width: 62ch;
            margin: .45rem 0 0; line-height: 1.6;
          }}
          .sa-assurances {{
            display: flex; flex-wrap: wrap; gap: 1.25rem;
            margin-top: 1.1rem; padding-top: .9rem;
            border-top: 1px solid var(--line-soft);
          }}
          .sa-assurance {{
            font-size: .8rem; color: var(--ink-soft); font-weight: 500;
          }}
          .sa-assurance::before {{
            content: "—"; color: var(--brand); margin-inline-end: .4rem;
            font-weight: 700;
          }}

          /* ---------- Stepper ---------- */
          .sa-stepper {{
            display: flex; gap: .25rem; margin: .25rem 0 1.25rem;
            border: 1px solid var(--line); background: var(--surface);
            border-radius: var(--radius); padding: .5rem;
          }}
          .sa-stepitem {{
            flex: 1 1 0; display: flex; align-items: center; gap: .5rem;
            padding: .5rem .6rem; border-radius: 7px; min-width: 0;
          }}
          .sa-stepitem.current {{ background: var(--brand-tint); }}
          .sa-stepnum {{
            flex: 0 0 auto; width: 1.6rem; height: 1.6rem; border-radius: 50%;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: .78rem; font-weight: 700; border: 1.5px solid var(--line);
            color: var(--muted); background: var(--surface);
          }}
          .sa-stepitem.current .sa-stepnum {{
            background: var(--brand); border-color: var(--brand); color: #fff;
          }}
          .sa-stepitem.done .sa-stepnum {{
            background: var(--ok); border-color: var(--ok); color: #fff;
          }}
          .sa-steplabel {{
            font-size: .82rem; font-weight: 600; color: var(--muted);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
          }}
          .sa-stepitem.current .sa-steplabel {{ color: var(--brand-deep); }}
          .sa-stepitem.done .sa-steplabel {{ color: var(--ink-soft); }}

          /* ---------- Panels ---------- */
          .sa-panel {{
            background: var(--surface); border: 1px solid var(--line);
            border-radius: var(--radius); padding: 1.4rem 1.6rem;
            margin-bottom: 1rem;
          }}
          .sa-panel-title {{
            font-family: {display_font}; font-size: 1.3rem; font-weight: 600;
            color: var(--ink); margin: 0; line-height: {display_line_height};
          }}
          .sa-panel-caption {{
            color: var(--muted); font-size: .88rem; margin: .3rem 0 0;
            line-height: 1.55;
          }}
          .sa-stepcount {{
            font-size: .72rem; font-weight: 600; letter-spacing: .1em;
            text-transform: uppercase; color: var(--brand);
          }}
          .sa-rule {{ height: 1px; background: var(--line-soft); margin: 1.1rem 0; }}

          /* ---------- Field labels ---------- */
          .sa-field-head {{
            display: flex; align-items: baseline; gap: .5rem; margin-bottom: -.55rem;
          }}
          .sa-tag {{
            font-size: .64rem; font-weight: 700; letter-spacing: .07em;
            text-transform: uppercase; padding: .1rem .38rem; border-radius: 4px;
          }}
          .sa-tag.req {{ background: var(--brand-tint); color: var(--brand-deep); }}
          .sa-tag.opt {{ background: var(--line-soft); color: var(--muted); }}
          .sa-fielderror {{
            color: var(--no); font-size: .8rem; font-weight: 500;
            margin: .15rem 0 .6rem;
          }}

          /* ---------- Badges ---------- */
          .sa-badge {{
            display: inline-block; padding: .2rem .55rem; border-radius: 5px;
            font-size: .73rem; font-weight: 600; border: 1px solid;
            white-space: nowrap;
          }}
          .is-eligible {{ background: var(--ok-tint);   color: var(--ok);   border-color: #BFE0CD; }}
          .is-partial  {{ background: var(--warn-tint); color: var(--warn); border-color: #E8D6A8; }}
          .is-no       {{ background: var(--no-tint);   color: var(--no);   border-color: #EFCBC6; }}
          .is-neutral  {{ background: var(--line-soft); color: var(--muted); border-color: var(--line); }}

          /* ---------- Result cards ---------- */
          .sa-result-head {{ display: flex; flex-direction: column; gap: .3rem; }}
          .sa-result-name {{
            font-family: {display_font}; font-size: 1.08rem; font-weight: 600;
            color: var(--ink); line-height: {display_line_height};
          }}
          .sa-result-meta {{ color: var(--muted); font-size: .8rem; }}
          .sa-groupbar {{
            display: flex; align-items: baseline; gap: .6rem;
            margin: 1.4rem 0 .1rem;
          }}
          .sa-grouptitle {{
            font-family: {display_font}; font-size: 1.12rem; font-weight: 600;
            color: var(--ink);
          }}
          .sa-groupnote {{ color: var(--muted); font-size: .84rem; margin-bottom: .5rem; }}

          /* ---------- Condition rows ---------- */
          .sa-checkrow {{
            display: flex; align-items: flex-start; gap: .6rem;
            padding: .45rem 0; border-bottom: 1px solid var(--line-soft);
          }}
          .sa-checkrow:last-child {{ border-bottom: none; }}
          .sa-mark {{
            flex: 0 0 auto; width: 1.2rem; height: 1.2rem; border-radius: 4px;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: .72rem; font-weight: 700; margin-top: .12rem;
          }}
          .mark-met     {{ background: var(--ok-tint);   color: var(--ok); }}
          .mark-unmet   {{ background: var(--no-tint);   color: var(--no); }}
          .mark-unknown {{ background: var(--warn-tint); color: var(--warn); }}
          .sa-checkname {{ font-size: .875rem; font-weight: 600; color: var(--ink); }}
          .sa-checkdetail {{ font-size: .81rem; color: var(--muted); }}

          /* ---------- Callouts ---------- */
          .sa-callout {{
            border-inline-start: 3px solid var(--brand);
            background: var(--brand-tint); padding: .7rem .9rem;
            border-radius: 6px; font-size: .85rem; color: var(--ink-soft);
            margin: .6rem 0;
          }}
          .sa-callout.warn {{ border-color: var(--warn); background: var(--warn-tint); }}
          .sa-callout-title {{ font-weight: 700; color: var(--ink); display: block;
                               margin-bottom: .2rem; }}

          /* ---------- KPIs ---------- */
          .sa-kpi {{
            background: var(--surface); border: 1px solid var(--line);
            border-radius: var(--radius); padding: .85rem 1rem; text-align: center;
          }}
          .sa-kpi-num {{
            font-family: {display_font}; font-size: 1.9rem; font-weight: 700;
            color: var(--ink); line-height: 1.1;
          }}
          .sa-kpi-label {{
            font-size: .75rem; color: var(--muted); font-weight: 600;
            text-transform: uppercase; letter-spacing: .05em;
          }}

          /* ---------- Summary list ---------- */
          .sa-answer {{
            display: flex; justify-content: space-between; gap: 1rem;
            padding: .32rem 0; border-bottom: 1px solid var(--line-soft);
            font-size: .83rem;
          }}
          .sa-answer:last-child {{ border-bottom: none; }}
          .sa-answer-label {{ color: var(--muted); }}
          .sa-answer-value {{ color: var(--ink); font-weight: 600; text-align: end; }}

          /* ---------- Streamlit overrides ---------- */
          .stButton > button {{
            border-radius: 7px; font-weight: 600; font-size: .88rem;
            padding: .5rem 1.1rem; border: 1px solid var(--line);
          }}
          .stButton > button[kind="primary"] {{
            background: var(--brand); border-color: var(--brand);
          }}
          .stButton > button[kind="primary"]:hover {{
            background: var(--brand-deep); border-color: var(--brand-deep);
          }}
          div[data-testid="stExpander"] {{
            border: 1px solid var(--line); border-radius: var(--radius);
            background: var(--surface);
          }}
          section[data-testid="stSidebar"] {{
            background: var(--surface); border-inline-end: 1px solid var(--line);
          }}
          section[data-testid="stSidebar"] h3 {{ font-size: 1.05rem; }}
          .stTabs [data-baseweb="tab-list"] {{ gap: .35rem; }}
          .stTabs [data-baseweb="tab"] {{
            font-weight: 600; font-size: .9rem; padding: .5rem .9rem;
          }}
          [data-testid="stMetricValue"] {{ font-size: 1.6rem; }}
          {rtl}
        </style>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, css_class: str) -> str:
    return f'<span class="sa-badge {css_class}">{text}</span>'


def panel_open(title: str, caption: str = "", counter: str = "") -> None:
    counter_html = f'<div class="sa-stepcount">{counter}</div>' if counter else ""
    caption_html = f'<p class="sa-panel-caption">{caption}</p>' if caption else ""
    st.markdown(
        f'<div class="sa-panel">{counter_html}'
        f'<h2 class="sa-panel-title">{title}</h2>{caption_html}'
        f'<div class="sa-rule"></div></div>',
        unsafe_allow_html=True,
    )


def field_tag(required: bool = False, lang: str = "en") -> None:
    """Small Required / Optional marker rendered just above a widget."""
    tag_class, tag_text = ("req", t("required_marker", lang)) if required \
        else ("opt", t("optional_marker", lang))
    st.markdown(
        f'<div class="sa-field-head"><span class="sa-tag {tag_class}">{tag_text}</span></div>',
        unsafe_allow_html=True,
    )


def field_error(field_name: str, errors: dict, lang: str) -> None:
    if field_name in errors:
        st.markdown(
            f'<div class="sa-fielderror">{validation_message(errors[field_name], lang)}</div>',
            unsafe_allow_html=True,
        )


def callout(body: str, title: str = "", warn: bool = False) -> None:
    title_html = f'<span class="sa-callout-title">{title}</span>' if title else ""
    st.markdown(
        f'<div class="sa-callout{" warn" if warn else ""}">{title_html}{body}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "language": "en",
        "answers": {},
        "categories": [c for c in KNOWN_CATEGORIES],
        "step": 0,
        "step_errors": {},
        "uploaded_opportunity": None,
        "uploaded_raw": None,
        "screen_upload": False,
        "explanations": {},
        "documents_ready": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def current_profile() -> UserProfile:
    """
    Build a UserProfile from the answer store.

    Answers live in a plain dict rather than directly in widget state, because
    Streamlit may drop widget state for widgets that are not currently on
    screen - and a wizard only ever renders one step at a time.
    """
    answers = st.session_state.answers
    return UserProfile(
        **{f: answers.get(f) for f in PROFILE_FIELDS},
        language=st.session_state.language,
    )


def record(field_name: str, value) -> None:
    st.session_state.answers[field_name] = value


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
    if is_ai_available():
        st.success(t("ai_enabled", lang))
    else:
        st.info(t("ai_mock_mode", lang))
        st.caption(t("ai_mock_explainer", lang))

    st.divider()
    st.markdown(f"**{t('sidebar_catalog', lang)}**")
    st.markdown(t("sidebar_records", lang, n=health["total"]))
    if health["verified"]:
        st.caption(t("sidebar_verified", lang, n=health["verified"]))
    if health["unverified"]:
        st.caption(t("sidebar_unverified", lang, n=health["unverified"]))

    st.divider()
    with st.expander(t("sidebar_about", lang)):
        st.caption(t("sidebar_about_body", lang))


# ---------------------------------------------------------------------------
# Masthead
# ---------------------------------------------------------------------------

assurances = "".join(
    f'<span class="sa-assurance">{t(key, lang)}</span>'
    for key in ("chip_no_cnic", "chip_rules_based", "chip_official_sources",
                "chip_bilingual")
)
st.markdown(
    f"""
    <div class="sa-masthead">
      <div class="sa-kicker">{t('app_subtitle', lang)}</div>
      <h1 class="sa-wordmark">{t('app_title', lang)}</h1>
      <p class="sa-lede">{t('app_tagline', lang)}</p>
      <div class="sa-assurances">{assurances}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Wizard chrome
# ---------------------------------------------------------------------------

def render_stepper(active: int) -> None:
    items = []
    for index, step in enumerate(STEPS):
        state = "current" if index == active else ("done" if index < active else "")
        numeral = "✓" if index < active else str(index + 1)
        items.append(
            f'<div class="sa-stepitem {state}">'
            f'<span class="sa-stepnum">{numeral}</span>'
            f'<span class="sa-steplabel">{t(step.title_key, lang)}</span></div>'
        )
    st.markdown(f'<div class="sa-stepper">{"".join(items)}</div>',
                unsafe_allow_html=True)


def go_to(index: int) -> None:
    st.session_state.step = max(0, min(index, RESULTS_STEP_INDEX))
    st.session_state.step_errors = {}
    st.rerun()


def render_nav(step_index: int, errors_on_continue: bool = True) -> None:
    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
    back_col, _, next_col = st.columns([1, 2, 1])

    with back_col:
        if step_index > 0:
            if st.button(t("nav_back", lang), key=f"back_{step_index}",
                         use_container_width=True):
                go_to(step_index - 1)

    with next_col:
        is_last_input = step_index == RESULTS_STEP_INDEX - 1
        label = t("nav_see_results", lang) if is_last_input else t("nav_continue", lang)
        if st.button(label, key=f"next_{step_index}", type="primary",
                     use_container_width=True):
            errors = validate_step(STEPS[step_index], current_profile(),
                                   st.session_state.categories)
            if errors and errors_on_continue:
                st.session_state.step_errors = errors
                st.rerun()
            else:
                go_to(step_index + 1)

    if st.session_state.step_errors:
        st.markdown(
            f'<div class="sa-fielderror">{t("fix_before_continuing", lang)}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------

def optional_select(label: str, field_name: str, options, formatter):
    """A select that can always express 'not answered' as its first option."""
    answers = st.session_state.answers
    choices = [None] + list(options)
    current = answers.get(field_name)
    index = choices.index(current) if current in choices else 0
    value = st.selectbox(
        label, options=choices, index=index,
        format_func=lambda v: t("placeholder_not_answered", lang) if v is None
        else formatter(v),
        key=f"w_{field_name}_{st.session_state.step}",
    )
    record(field_name, value)
    return value


def yes_no_select(label: str, field_name: str, help_text: str = ""):
    answers = st.session_state.answers
    choices = [None, True, False]
    current = answers.get(field_name)
    index = choices.index(current) if current in choices else 0
    value = st.selectbox(
        label, options=choices, index=index,
        format_func=lambda v: t("placeholder_not_answered", lang) if v is None
        else t("option_yes" if v else "option_no", lang),
        key=f"w_{field_name}_{st.session_state.step}",
        help=help_text or None,
    )
    record(field_name, value)
    return value


def number_field(label: str, field_name: str, minimum, maximum, step,
                 as_int: bool = False):
    answers = st.session_state.answers
    current = answers.get(field_name)
    if current is not None:
        current = int(current) if as_int else float(current)
    value = st.number_input(
        label, min_value=minimum, max_value=maximum, step=step, value=current,
        placeholder=t("placeholder_not_answered", lang),
        key=f"w_{field_name}_{st.session_state.step}",
    )
    record(field_name, value)
    return value


def render_step_focus(errors: dict) -> None:
    panel_open(t("step_focus_title", lang), t("step_focus_caption", lang),
               t("step_counter", lang, current=1, total=RESULTS_STEP_INDEX))

    selected = []
    columns = st.columns(len(KNOWN_CATEGORIES))
    for column, category in zip(columns, KNOWN_CATEGORIES):
        available = counts.get(category, 0)
        with column:
            with st.container(border=True):
                st.markdown(f"**{t(f'category_{category}', lang)}**")
                if available:
                    checked = st.checkbox(
                        t("available_count", lang, n=available),
                        value=category in st.session_state.categories,
                        key=f"cat_{category}",
                    )
                    if checked:
                        selected.append(category)
                else:
                    st.checkbox(t("coming_soon", lang), value=False, disabled=True,
                                key=f"cat_{category}",
                                help=t("category_empty_note", lang))
    st.session_state.categories = selected
    field_error("categories", errors, lang)


def render_step_about(errors: dict) -> None:
    panel_open(t("step_about_title", lang), t("step_about_caption", lang),
               t("step_counter", lang, current=2, total=RESULTS_STEP_INDEX))

    col1, col2 = st.columns(2)
    with col1:
        field_tag(required=True, lang=lang)
        number_field(t("field_age", lang), "age", AGE_MIN, AGE_MAX, 1, as_int=True)
        field_error("age", errors, lang)

        field_tag(lang=lang)
        optional_select(t("field_gender", lang), "gender", GENDERS,
                        lambda v: gender_label(v, lang))
        st.caption(t("field_gender_help", lang))

    with col2:
        field_tag(required=True, lang=lang)
        optional_select(t("field_domicile", lang), "domicile_province",
                        PROVINCES, lambda v: v)
        field_error("domicile_province", errors, lang)


def render_step_education(errors: dict) -> None:
    panel_open(t("step_education_title", lang), t("step_education_caption", lang),
               t("step_counter", lang, current=3, total=RESULTS_STEP_INDEX))

    col1, col2 = st.columns(2)
    with col1:
        field_tag(required=True, lang=lang)
        optional_select(t("field_education", lang), "education_level",
                        EDUCATION_LEVELS, lambda v: education_label(v, lang))
        field_error("education_level", errors, lang)

        field_tag(lang=lang)
        number_field(t("field_marks", lang), "marks_percentage",
                     MARKS_MIN, MARKS_MAX, 1.0)
        field_error("marks_percentage", errors, lang)

    with col2:
        field_tag(lang=lang)
        optional_select(t("field_field_of_study", lang), "field_of_study",
                        FIELDS_OF_STUDY, lambda v: field_of_study_label(v, lang))

        field_tag(lang=lang)
        yes_no_select(t("field_enrolled", lang), "currently_enrolled")


def render_step_circumstances(errors: dict) -> None:
    panel_open(t("step_circumstances_title", lang),
               t("step_circumstances_caption", lang),
               t("step_counter", lang, current=4, total=RESULTS_STEP_INDEX))

    col1, col2 = st.columns(2)
    with col1:
        field_tag(lang=lang)
        number_field(t("field_income", lang), "monthly_household_income",
                     0.0, INCOME_MAX, 1000.0)
        field_error("monthly_household_income", errors, lang)

        field_tag(lang=lang)
        yes_no_select(t("field_existing_scholarship", lang), "has_existing_scholarship")

        field_tag(lang=lang)
        optional_select(t("field_english_level", lang), "english_level",
                        ENGLISH_LEVELS, lambda v: english_label(v, lang))

        field_tag(lang=lang)
        optional_select(t("field_computer_skills", lang), "computer_skills",
                        COMPUTER_LEVELS, lambda v: computer_label(v, lang))

    with col2:
        field_tag(lang=lang)
        optional_select(t("field_employment", lang), "employment_status",
                        ("employed", "unemployed"), lambda v: t(f"option_{v}", lang))

        field_tag(lang=lang)
        number_field(t("field_experience", lang), "years_experience",
                     0.0, EXPERIENCE_MAX, 1.0)
        field_error("years_experience", errors, lang)

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        st.markdown(f"**{t('special_circumstances', lang)}**")
        st.caption(t("special_circumstances_help", lang))
        yes_no_select(t("field_has_disability", lang), "has_disability")
        yes_no_select(t("field_is_orphan", lang), "is_orphan")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def answer_value(profile: UserProfile, field_name: str) -> str:
    value = getattr(profile, field_name, None)
    if value is None:
        return "—"
    if field_name == "gender":
        return gender_label(value, lang)
    if field_name == "education_level":
        return education_label(value, lang)
    if field_name == "field_of_study":
        return field_of_study_label(value, lang)
    if field_name == "english_level":
        return english_label(value, lang, short=True)
    if field_name == "computer_skills":
        return computer_label(value, lang, short=True)
    if field_name == "employment_status":
        return t(f"option_{value}", lang)
    if isinstance(value, bool):
        return t("option_yes" if value else "option_no", lang)
    if field_name == "monthly_household_income":
        return f"Rs. {value:,.0f}"
    if field_name == "marks_percentage":
        return f"{value:g}%"
    return str(value)


def render_answer_summary(profile: UserProfile) -> None:
    with st.expander(t("your_answers", lang)):
        rows = [
            f'<div class="sa-answer">'
            f'<span class="sa-answer-label">{profile_field_label(f, lang)}</span>'
            f'<span class="sa-answer-value">{answer_value(profile, f)}</span></div>'
            for f in PROFILE_FIELDS
        ]
        st.markdown("".join(rows), unsafe_allow_html=True)
        st.caption(t("detail_completeness", lang,
                     percent=completion_percent(profile)))
        if st.button(t("nav_edit_answers", lang), key="edit_answers"):
            go_to(1)


def render_checks(match) -> None:
    rows = []
    for check in match.applicable_checks():
        title, detail = describe_check(check, lang)
        rows.append(
            f'<div class="sa-checkrow">'
            f'<span class="sa-mark {CHECK_CLASS.get(check.status, "mark-unknown")}">'
            f'{CHECK_MARK.get(check.status, "-")}</span>'
            f'<span><span class="sa-checkname">{title}</span><br>'
            f'<span class="sa-checkdetail">{detail}</span></span></div>'
        )
    st.markdown(f"**{t('why_match', lang)}**")
    st.markdown("".join(rows), unsafe_allow_html=True)

    if match.missing_profile_fields:
        names = [profile_field_label(f, lang) for f in match.missing_profile_fields]
        st.caption(t("missing_fields_hint", lang, fields=join_list(names, lang)))


def render_documents(opportunity) -> None:
    if not opportunity.required_documents:
        return
    ready = st.session_state.documents_ready.setdefault(opportunity.opportunity_id, set())
    total = len(opportunity.required_documents)
    st.markdown(f"**{t('document_checklist_heading', lang)}**")
    st.caption(t("documents_ready", lang, have=len(ready), total=total))
    for index, document in enumerate(opportunity.required_documents):
        if st.checkbox(document, value=index in ready,
                       key=f"doc_{opportunity.opportunity_id}_{index}"):
            ready.add(index)
        else:
            ready.discard(index)
    st.progress(len(ready) / total)


def trust_badge(opportunity) -> str:
    if opportunity.source_type == "user_uploaded":
        return badge(t("ai_extracted_badge", lang), "is-partial")
    if opportunity.is_verified():
        return badge(t("officially_verified_badge", lang), "is-eligible")
    return badge(t("unverified_badge", lang), "is-partial")


def render_match_card(match, expanded: bool = False) -> None:
    opportunity = match.opportunity
    with st.expander(opportunity.display_name(lang), expanded=expanded):
        badges = [
            badge(status_label(match.overall_status, lang),
                  STATUS_CLASS.get(match.overall_status, "is-neutral")),
            trust_badge(opportunity),
        ]
        if match.listing_closed:
            badges.append(badge(t("listing_closed", lang), "is-neutral"))
        st.markdown(" ".join(badges), unsafe_allow_html=True)

        category_name = (t(f"category_{opportunity.category}", lang)
                         if opportunity.category in KNOWN_CATEGORIES
                         else opportunity.category)
        st.markdown(
            f'<div class="sa-result-meta">{category_name} · '
            f'{t("provider_label", lang)}: {opportunity.provider}</div>',
            unsafe_allow_html=True,
        )

        summary = opportunity.display_summary(lang)
        if summary:
            st.write(summary)

        if match.matched_priority_groups:
            groups = join_list(
                [priority_group_label(g, lang) for g in match.matched_priority_groups],
                lang)
            callout(t("priority_body", lang, groups=groups),
                    title=t("priority_heading", lang))

        if match.listing_closed:
            callout(t("listing_closed_explainer", lang), warn=True)

        if opportunity.source_type == "curated" and not opportunity.is_verified():
            callout(t("unverified_explainer", lang), warn=True)

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        render_checks(match)

        quota_note = opportunity.eligibility_conditions.special_quota_note
        if quota_note:
            callout(quota_note, title=t("quota_note_label", lang))

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        doc_col, step_col = st.columns(2)
        with doc_col:
            render_documents(opportunity)
        with step_col:
            if opportunity.application_steps:
                st.markdown(f"**{t('application_steps', lang)}**")
                for index, step in enumerate(opportunity.application_steps, 1):
                    st.markdown(f"{index}. {step}")

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        meta = []
        if opportunity.official_url:
            meta.append(f"[{t('open_official_site', lang)}]({opportunity.official_url})")
        if opportunity.is_verified():
            meta.append(f"{t('last_verified', lang)}: {opportunity.last_verified}")
        if match.deadline:
            meta.append(f"{t('deadline_label', lang)}: {match.deadline}")
        if meta:
            st.markdown(
                f'<span class="sa-result-meta">{"  ·  ".join(meta)}</span>',
                unsafe_allow_html=True)

        if opportunity.disclaimer:
            st.caption(opportunity.disclaimer)

        explain_key = f"explain_{opportunity.opportunity_id}"
        if st.button(t("ai_explain_button", lang), key=f"btn_{explain_key}"):
            with st.spinner(""):
                st.session_state.explanations[explain_key] = explain_match(
                    describe_profile(current_profile(), lang),
                    build_result_summary(match), lang)
        if explain_key in st.session_state.explanations:
            st.info(st.session_state.explanations[explain_key])


def build_result_summary(match) -> str:
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
    out = [
        f"{t('app_title', lang)} - {t('results_heading', lang)}",
        t("disclaimer_banner", lang),
        "=" * 68, "",
    ]
    for match in results:
        opportunity = match.opportunity
        trust = (t("ai_extracted_badge", lang)
                 if opportunity.source_type == "user_uploaded"
                 else t("officially_verified_badge", lang) if opportunity.is_verified()
                 else t("unverified_badge", lang))
        out.append(opportunity.display_name(lang))
        out.append(f"  {status_label(match.overall_status, lang)}  |  {trust}")
        if match.listing_closed:
            out.append(f"  ** {t('listing_closed', lang)} **")
        out.append(f"  {t('provider_label', lang)}: {opportunity.provider}")
        for check in match.applicable_checks():
            title, detail = describe_check(check, lang)
            mark = {MET: "[x]", UNMET: "[ ]", UNKNOWN: "[?]"}.get(check.status, "[-]")
            out.append(f"    {mark} {title} - {detail}")
        if opportunity.required_documents:
            out.append(f"  {t('required_documents', lang)}:")
            out.extend(f"    - {d}" for d in opportunity.required_documents)
        if opportunity.application_steps:
            out.append(f"  {t('application_steps', lang)}:")
            out.extend(f"    {i}. {s}"
                       for i, s in enumerate(opportunity.application_steps, 1))
        if opportunity.official_url:
            out.append(f"  {t('official_source', lang)}: {opportunity.official_url}")
        out.append("")
    return "\n".join(out)


def render_followup() -> None:
    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
    st.markdown(f"**{t('ask_followup', lang)}**")
    st.caption(t("ask_followup_hint", lang))

    question = st.text_input(t("ask_followup", lang),
                             placeholder=t("ask_placeholder", lang),
                             label_visibility="collapsed", key="followup_question")
    if st.button(t("ask_button", lang), key="ask_btn") and question.strip():
        with st.spinner(""):
            evidence = get_rag_index().retrieve(question, top_k=3)
            answer = answer_followup(question, evidence, lang)
        if evidence:
            st.info(answer)
        else:
            st.warning(answer)


def render_results() -> None:
    profile = current_profile()
    selected = st.session_state.categories
    panel_open(t("step_results_title", lang), t("step_results_caption", lang))

    filtered = [o for o in opportunities if o.category in selected]
    if not filtered:
        st.warning(t("no_results", lang))
        if st.button(t("nav_back", lang), key="back_from_empty"):
            go_to(RESULTS_STEP_INDEX - 1)
        return

    results = evaluate_all(profile, filtered)
    totals = summarize_counts(results)

    kpis = [
        (totals[STATUS_ELIGIBLE], t("status_eligible", lang)),
        (totals[STATUS_NEEDS_VERIFICATION], t("status_needs_verification", lang)),
        (totals[STATUS_NOT_ELIGIBLE], t("status_not_eligible", lang)),
        (totals["closed"], t("listing_closed", lang)),
    ]
    for column, (number, label) in zip(st.columns(4), kpis):
        column.markdown(
            f'<div class="sa-kpi"><div class="sa-kpi-num">{number}</div>'
            f'<div class="sa-kpi-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    render_answer_summary(profile)
    if completion_percent(profile) < 70:
        st.caption(t("more_detail_hint", lang))

    for status, note_key in (
        (STATUS_ELIGIBLE, "group_eligible_help"),
        (STATUS_NEEDS_VERIFICATION, "group_needs_verification_help"),
        (STATUS_NOT_ELIGIBLE, "group_not_eligible_help"),
    ):
        group = [r for r in results if r.overall_status == status]
        if not group:
            continue
        st.markdown(
            f'<div class="sa-groupbar"><span class="sa-grouptitle">'
            f'{status_label(status, lang)}</span>'
            f'<span class="sa-result-meta">{len(group)}</span></div>'
            f'<div class="sa-groupnote">{t(note_key, lang)}</div>',
            unsafe_allow_html=True,
        )
        for match in group:
            render_match_card(match,
                              expanded=(status == STATUS_ELIGIBLE and len(group) <= 2))

    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
    export_col, restart_col = st.columns([1, 1])
    with export_col:
        st.download_button(t("export_button", lang),
                           data=build_export_text(results).encode("utf-8"),
                           file_name="sahulat-ai-results.txt", mime="text/plain",
                           use_container_width=True)
    with restart_col:
        if st.button(t("nav_start_over", lang), key="restart",
                     use_container_width=True):
            st.session_state.answers = {}
            st.session_state.categories = [c for c in KNOWN_CATEGORIES]
            st.session_state.explanations = {}
            go_to(0)

    render_followup()


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_find, tab_upload, tab_how = st.tabs([
    t("tab_find", lang), t("tab_upload", lang), t("tab_how", lang),
])


with tab_find:
    step_index = st.session_state.step
    errors = st.session_state.step_errors
    render_stepper(step_index)

    if step_index == 0:
        render_step_focus(errors)
    elif step_index == 1:
        render_step_about(errors)
    elif step_index == 2:
        render_step_education(errors)
    elif step_index == 3:
        render_step_circumstances(errors)

    if step_index < RESULTS_STEP_INDEX:
        render_nav(step_index)
    else:
        render_results()

    st.caption(t("disclaimer_banner", lang))


with tab_upload:
    panel_open(t("upload_ad_heading", lang), t("upload_ad_intro", lang))

    if not is_ai_available():
        st.info(t("ai_mock_extraction_notice", lang))

    uploaded_file = st.file_uploader(t("upload_ad_heading", lang),
                                     type=["png", "jpg", "jpeg", "pdf"],
                                     label_visibility="collapsed")

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"

        preview_col, action_col = st.columns([1, 2])
        with preview_col:
            if mime_type.startswith("image/"):
                st.image(file_bytes, use_container_width=True)
            else:
                st.markdown(f"`{uploaded_file.name}`")
        with action_col:
            st.caption(t("upload_privacy_note", lang))
            if st.button(t("upload_ad_button", lang), type="primary"):
                with st.spinner(""):
                    extracted_opportunity, raw = read_ad(file_bytes, mime_type,
                                                         language=lang)
                st.session_state.uploaded_opportunity = extracted_opportunity
                st.session_state.uploaded_raw = raw
                st.session_state.screen_upload = False

    if st.session_state.uploaded_opportunity is not None:
        opportunity = st.session_state.uploaded_opportunity
        raw = st.session_state.uploaded_raw or {}

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        head_col, clear_col = st.columns([3, 1])
        with head_col:
            st.markdown(f"**{t('extracted_fields_heading', lang)}**")
        with clear_col:
            if st.button(t("upload_clear", lang), use_container_width=True):
                st.session_state.uploaded_opportunity = None
                st.session_state.uploaded_raw = None
                st.session_state.screen_upload = False
                st.rerun()

        confidence = str(raw.get("extraction_confidence", "low")).lower()
        confidence_text = (t(f"confidence_{confidence}", lang)
                           if confidence in ("high", "medium", "low") else confidence)
        st.markdown(
            badge(t("ai_extracted_badge", lang), "is-partial") + " "
            + badge(f"{t('extraction_confidence', lang)}: {confidence_text}",
                    "is-neutral"),
            unsafe_allow_html=True,
        )

        if raw.get("_error"):
            st.error(raw["_error"])

        st.markdown(f"**{opportunity.name}**")
        if opportunity.summary_en:
            st.write(opportunity.summary_en)
        st.caption(f"{t('provider_label', lang)}: {opportunity.provider}")

        with st.expander(t("raw_extraction_toggle", lang)):
            st.json(raw)

        st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
        if not current_profile().is_screenable():
            st.info(t("upload_needs_profile", lang))
        else:
            if st.button(t("screen_uploaded", lang), type="primary"):
                st.session_state.screen_upload = True
            if st.session_state.screen_upload:
                render_match_card(evaluate(current_profile(), opportunity),
                                  expanded=True)

    st.caption(t("upload_privacy_note", lang))


with tab_how:
    panel_open(t("how_heading", lang), t("how_intro", lang))

    for column, (title_key, body_key) in zip(
        st.columns(3),
        (("how_step1_title", "how_step1_body"),
         ("how_step2_title", "how_step2_body"),
         ("how_step3_title", "how_step3_body")),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"**{t(title_key, lang)}**")
                st.caption(t(body_key, lang))

    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
    trust_col, privacy_col = st.columns(2)
    with trust_col:
        st.markdown(f"**{t('how_trust_heading', lang)}**")
        st.caption(t("how_trust_body", lang))
        st.markdown(
            badge(t("officially_verified_badge", lang), "is-eligible") + " "
            + badge(t("unverified_badge", lang), "is-partial") + " "
            + badge(t("ai_extracted_badge", lang), "is-partial"),
            unsafe_allow_html=True,
        )
    with privacy_col:
        st.markdown(f"**{t('how_privacy_heading', lang)}**")
        st.caption(t("profile_privacy_note", lang))

    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)
    st.caption(t("disclaimer_banner", lang))

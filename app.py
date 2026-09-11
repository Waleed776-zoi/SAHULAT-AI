"""
Sahulat AI - Pakistan Opportunity & Services Navigator
Main Streamlit application.

Run with:  streamlit run app.py
See README.md for setup and PROJECT_TRACKER.md for the work log.

DESIGN DIRECTION ("Civic Intelligence")
  Calm, editorial, bilingual, restrained. Warm paper background, white
  surfaces for content, deep green reserved for actions and positive states,
  gold for verification, blue for information. Green is an accent, never the
  whole interface. No gradients, glassmorphism, robot imagery or decorative
  animation - see PROJECT_TRACKER.md UX-04.

INTERACTION MODEL
  Home -> guided four-step wizard -> ranked results. Steps are validated in
  core/validation.py. Deliberately NOT built on st.form: a form submits on
  Enter, which made a half-filled profile jump straight to results.

PERFORMANCE (PERF-01)
  Nothing heavy is imported or built at page load. The retrieval index is
  created lazily, only when a follow-up question is asked, and cached per
  process rather than per session.
"""
from __future__ import annotations

from pathlib import Path

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
    LISTING_CLOSED, LISTING_OPEN, MET, PROVINCES, STATUS_ELIGIBLE,
    STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE, UNKNOWN, UNMET, UserProfile,
    sample_profile,
)
from core.rules_engine import evaluate, evaluate_all, summarize_counts
from core.validation import (
    AGE_MAX, AGE_MIN, EXPERIENCE_MAX, INCOME_MAX, MARKS_MAX, MARKS_MIN,
    RESULTS_STEP_INDEX, STEPS, completion_percent, validate_step,
)

st.set_page_config(
    page_title="Sahulat AI — Pakistan's Opportunity Navigator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PROFILE_FIELDS = (
    "age", "gender", "domicile_province", "education_level", "marks_percentage",
    "field_of_study", "currently_enrolled", "monthly_household_income",
    "has_existing_scholarship", "english_level", "computer_skills",
    "employment_status", "years_experience", "has_disability", "is_orphan",
)

# Semantic badge system (spec section 19): green / gold / red / grey only.
STATUS_CLASS = {
    STATUS_ELIGIBLE: "tone-good",
    STATUS_NEEDS_VERIFICATION: "tone-verify",
    STATUS_NOT_ELIGIBLE: "tone-no",
}
LISTING_CLASS = {LISTING_OPEN: "tone-good", LISTING_CLOSED: "tone-mute"}
CHECK_MARK = {MET: "✓", UNMET: "✕", UNKNOWN: "!"}
CHECK_CLASS = {MET: "mark-good", UNMET: "mark-no", UNKNOWN: "mark-verify"}


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
# Design tokens and stylesheet
# ---------------------------------------------------------------------------

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&"
    "family=Noto+Naskh+Arabic:wght@400;500;600;700&"
    "family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');"
)

STYLE_DIR = Path(__file__).resolve().parent / "styles"
STYLESHEETS = ("theme.css", "components.css", "animations.css")


@st.cache_data(show_spinner=False)
def load_stylesheets() -> str:
    """Concatenate styles/*.css. Cached - read once per process."""
    parts = []
    for name in STYLESHEETS:
        path = STYLE_DIR / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def inject_css(lang: str) -> None:
    """
    Inject the stylesheet.

    Only the language-dependent bits are generated here - fonts and RTL. All
    static styling lives in styles/*.css (spec 17.1) so it is readable and
    reviewable instead of buried in a Python f-string.
    """
    urdu = lang == "ur"
    body_font = ("'Noto Naskh Arabic','Inter',system-ui,sans-serif" if urdu
                 else "'Inter',system-ui,-apple-system,sans-serif")
    display_font = ("'Noto Nastaliq Urdu','Noto Naskh Arabic',serif" if urdu
                    else "'Source Serif 4',Georgia,serif")
    display_lh = "2.0" if urdu else "1.12"

    rtl = """
      .stMain .block-container { direction: rtl; text-align: right; }
      .sa-checkrow, .sa-stepper, .sa-inline-trust,
      .sahulat-header-inner, .sahulat-logo { flex-direction: row-reverse; }
      a[href^="http"], .sa-ltr { direction: ltr; unicode-bidi: embed;
                                 display: inline-block; }
      .sahulat-nav a::after { left: auto; right: 0; }
    """ if urdu else ""

    st.markdown(
        f"<style>{FONT_IMPORT}\n"
        f":root {{ --sa-font-body: {body_font};"
        f" --sa-font-display: {display_font};"
        f" --sa-display-lh: {display_lh}; }}\n"
        f"{load_stylesheets()}\n{rtl}</style>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Motion gating
#
# Streamlit reruns the script on every interaction. A CSS entrance animation
# would therefore replay every time a checkbox is ticked. These helpers make a
# reveal play once per real state change (spec 17.2/17.3).
# ---------------------------------------------------------------------------

def should_animate(token: str) -> bool:
    seen = st.session_state.setdefault("animated_tokens", set())
    if token in seen:
        return False
    seen.add(token)
    return True


def reveal(token: str, position: int = 1) -> str:
    """CSS classes for a staggered block entrance, or "" if already played."""
    if not should_animate(token):
        return ""
    return f"sahulat-reveal sahulat-stagger-{min(position, 6)}"


def results_token() -> str:
    """Changes whenever the answers or chosen categories change."""
    answers = st.session_state.answers
    return repr(sorted((k, str(v)) for k, v in answers.items())) + \
        repr(sorted(st.session_state.categories))


# ---------------------------------------------------------------------------
# Small render helpers
# ---------------------------------------------------------------------------

def badge(text: str, tone: str) -> str:
    return f'<span class="sa-badge {tone}">{text}</span>'


def section_label(text: str) -> None:
    st.markdown(f'<div class="sa-section-label">{text}</div>', unsafe_allow_html=True)


def section_title(title: str, lede: str = "") -> None:
    lede_html = f'<p class="sa-section-lede">{lede}</p>' if lede else ""
    st.markdown(f'<h2 class="sa-section-title">{title}</h2>{lede_html}',
                unsafe_allow_html=True)


def panel_head(title: str, caption: str = "", counter: str = "") -> None:
    counter_html = f'<div class="sa-stepcount">{counter}</div>' if counter else ""
    caption_html = f'<p class="sa-panel-caption">{caption}</p>' if caption else ""
    st.markdown(f'<div class="sa-panel-head">{counter_html}'
                f'<h2 class="sa-panel-title">{title}</h2>{caption_html}</div>',
                unsafe_allow_html=True)


def rule() -> None:
    st.markdown('<div class="sa-rule"></div>', unsafe_allow_html=True)


def field_tag(required: bool = False, lang: str = "en") -> None:
    css, text = ("req", t("required_marker", lang)) if required \
        else ("opt", t("optional_marker", lang))
    st.markdown(f'<div class="sa-tagrow"><span class="sa-tag {css}">{text}</span></div>',
                unsafe_allow_html=True)


def field_error(field_name: str, errors: dict, lang: str) -> None:
    if field_name in errors:
        st.markdown(f'<div class="sa-fielderror">'
                    f'{validation_message(errors[field_name], lang)}</div>',
                    unsafe_allow_html=True)


def callout(body: str, title: str = "", tone: str = "") -> None:
    title_html = f'<span class="sa-callout-title">{title}</span>' if title else ""
    st.markdown(f'<div class="sa-callout {tone}">{title_html}{body}</div>',
                unsafe_allow_html=True)


def opportunity_map_svg(lang: str) -> str:
    """
    The signature visual: one person, many opportunity paths.

    Inline SVG - no external asset, no animation, and it inherits the palette.
    """
    labels = [t(f"category_{c}", lang) for c in ("scholarship", "job", "skills", "assistance")]
    you = t("map_you", lang)
    return f"""
    <svg viewBox="0 0 420 300" width="100%" height="auto" role="img"
         aria-label="{you}" style="max-width:440px">
      <g stroke="#DDE4DF" stroke-width="1.5" fill="none">
        <path d="M210 150 C 160 150, 150 70, 96 62"/>
        <path d="M210 150 C 260 150, 272 70, 326 62"/>
        <path d="M210 150 C 160 150, 150 232, 96 240"/>
        <path d="M210 150 C 260 150, 272 232, 326 240"/>
      </g>
      <circle cx="210" cy="150" r="30" fill="#123B32"/>
      <text x="210" y="155" text-anchor="middle" fill="#FFFFFF"
            font-size="13" font-weight="600"
            font-family="Inter,system-ui,sans-serif">{you}</text>
      <g font-size="11.5" font-family="Inter,system-ui,sans-serif" fill="#40504A">
        <circle cx="96"  cy="62"  r="7" fill="#198766"/>
        <text x="96"  y="44"  text-anchor="middle">{labels[0]}</text>
        <circle cx="326" cy="62"  r="7" fill="#176B55"/>
        <text x="326" y="44"  text-anchor="middle">{labels[1]}</text>
        <circle cx="96"  cy="240" r="7" fill="#B98227"/>
        <text x="96"  y="266" text-anchor="middle">{labels[2]}</text>
        <circle cx="326" cy="240" r="7" fill="#245B78"/>
        <text x="326" y="266" text-anchor="middle">{labels[3]}</text>
      </g>
    </svg>
    """


# One consistent icon family: thin stroked line marks, no emoji (spec 7).
def _icon(paths: str) -> str:
    return ('<svg class="sahulat-category-icon" width="24" height="24" '
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{paths}</svg>')


CATEGORY_ICONS = {
    "scholarship": _icon('<path d="M22 10 12 5 2 10l10 5 10-5Z"/>'
                         '<path d="M6 12v5c3 2 9 2 12 0v-5"/>'),
    "job": _icon('<rect x="2" y="7" width="20" height="14" rx="2"/>'
                 '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'),
    "skills": _icon('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0'
                    'l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3'
                    'l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76Z"/>'),
    "assistance": _icon('<path d="M3 21h18"/><path d="M5 21V8l7-5 7 5v13"/>'
                        '<path d="M9 21v-6h6v6"/>'),
}


def sahulat_path_svg(lang: str) -> str:
    """
    The Sahulat Path: Profile -> Rules -> Evidence -> Action, drawn once.

    The recurring identity motif. Desktop horizontal; a vertical timeline takes
    over below 640px (spec 6 and 8).
    """
    labels = [t(f"journey_{i}_title", lang) for i in (1, 2, 3, 4)]
    animate = should_animate("sahulat_path")
    line_class = "sahulat-path-line" if animate else ""
    xs = [90, 310, 530, 750]
    nodes = []
    for index, (x, label) in enumerate(zip(xs, labels), start=1):
        node_class = f"sahulat-path-node sahulat-path-node-{index}" if animate else ""
        nodes.append(
            f'<g class="{node_class}">'
            f'<circle cx="{x}" cy="44" r="9" fill="#176B55"/>'
            f'<circle cx="{x}" cy="44" r="3.4" fill="#FFFFFF"/>'
            f'<text x="{x}" y="24" text-anchor="middle" font-size="12"'
            f' font-weight="700" fill="#176B55"'
            f' font-family="Inter,system-ui,sans-serif">0{index}</text>'
            f'<text x="{x}" y="72" text-anchor="middle" font-size="13"'
            f' fill="#14211D" font-family="Inter,system-ui,sans-serif">{label}</text>'
            f'</g>')
    return (f'<svg class="sahulat-path" viewBox="0 0 840 92" role="img" '
            f'aria-label="{t("journey_line", lang)}">'
            f'<line class="{line_class}" x1="90" y1="44" x2="750" y2="44" '
            f'stroke="#DDE4DF" stroke-width="1.5"/>'
            f'{"".join(nodes)}</svg>')


def sahulat_path_vertical(lang: str) -> str:
    """Mobile fallback: the same journey as a vertical timeline (spec 8)."""
    items = "".join(
        f'<div class="sa-tl-item"><div class="sa-tl-step">0{i}</div>'
        f'<div class="sa-item-title">{t(f"journey_{i}_title", lang)}</div>'
        f'<div class="sa-tl-body">{t(f"journey_{i}_body", lang)}</div></div>'
        for i in (1, 2, 3, 4))
    return f'<div class="sahulat-path-mobile sahulat-timeline">{items}</div>'


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "language": "en",
        "view": "home",
        "answers": {},
        "categories": [c for c in KNOWN_CATEGORIES],
        "step": 0,
        "step_errors": {},
        "is_demo": False,
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
    return UserProfile(**{f: answers.get(f) for f in PROFILE_FIELDS},
                       language=st.session_state.language)


def record(field_name: str, value) -> None:
    st.session_state.answers[field_name] = value


def go_to(index: int) -> None:
    st.session_state.step = max(0, min(index, RESULTS_STEP_INDEX))
    st.session_state.step_errors = {}
    st.session_state.view = "wizard"
    st.rerun()


def start_over() -> None:
    st.session_state.answers = {}
    st.session_state.categories = [c for c in KNOWN_CATEGORIES]
    st.session_state.explanations = {}
    st.session_state.is_demo = False
    st.session_state.step = 0
    st.session_state.step_errors = {}
    st.session_state.view = "home"
    st.session_state.documents_ready = {}
    # Starting over is a fresh journey, so let the reveals play again. Without
    # this, re-running the same profile would land on a static page.
    st.session_state.animated_tokens = set()
    st.rerun()


init_state()
lang = st.session_state.language
inject_css(lang)

opportunities = get_opportunities()
counts = category_counts(opportunities)
health = catalogue_health(opportunities)


# ---------------------------------------------------------------------------
# Brand bar  (replaces the sidebar entirely - spec sections 12 and 31)
# ---------------------------------------------------------------------------

LOGO_MARK = (
    '<svg class="sahulat-logo-mark" viewBox="0 0 24 24" fill="none" '
    'stroke="#176B55" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
    '<path d="M3 20 C 9 20, 9 4, 15 4"/><circle cx="3" cy="20" r="1.6" fill="#176B55"/>'
    '<circle cx="15" cy="4" r="1.6" fill="#123B32"/><path d="M18 9 L21 4 L21 9 Z" '
    'fill="#B98227" stroke="none"/></svg>'
)


def render_header() -> None:
    """A distinct navigation layer, not another white block (spec 4)."""
    st.markdown(
        f'<div class="sahulat-header"><div class="sahulat-header-inner">'
        f'<div class="sahulat-logo">{LOGO_MARK}'
        f'<span class="sahulat-logo-name">{t("app_title", lang)}</span>'
        f'<span class="sahulat-logo-sep">·</span>'
        f'<span class="sahulat-logo-ur">{t("brand_urdu", lang)}</span></div>'
        f'<nav class="sahulat-nav">'
        f'<a href="#discover">{t("nav_discover", lang)}</a>'
        f'<a href="#how">{t("nav_how", lang)}</a>'
        f'<a href="#privacy">{t("privacy_heading", lang)}</a>'
        f'</nav></div></div>',
        unsafe_allow_html=True,
    )


render_header()

_, lang_en_col, lang_ur_col, cta_col = st.columns([4, 1, 1, 2])
with lang_en_col:
    if st.button("EN", key="lang_en", use_container_width=True,
                 type="primary" if lang == "en" else "secondary"):
        st.session_state.language = "en"
        st.rerun()
with lang_ur_col:
    if st.button("اردو", key="lang_ur", use_container_width=True,
                 type="primary" if lang == "ur" else "secondary"):
        st.session_state.language = "ur"
        st.rerun()
with cta_col:
    if st.session_state.view == "home":
        if st.button(t("cta_start", lang), key="header_cta",
                     type="primary", use_container_width=True):
            go_to(0)
    else:
        if st.button(t("nav_start_over", lang), key="header_restart",
                     use_container_width=True):
            start_over()


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

def render_footer() -> None:
    st.markdown('<div class="sa-footer">', unsafe_allow_html=True)
    brand, discover, trust, language = st.columns([2, 1, 1, 1])
    with brand:
        st.markdown(
            f'<div class="sa-footer-brand">{t("app_title", lang)} · '
            f'{t("brand_urdu", lang)}</div>'
            f'<div style="margin-top:.4rem;max-width:34ch">{t("footer_tagline", lang)}</div>',
            unsafe_allow_html=True)
    with discover:
        st.markdown(f'<div class="sa-footer-head">{t("nav_discover", lang)}</div>'
                    f'<div>{t("find_heading", lang)}</div>', unsafe_allow_html=True)
    with trust:
        st.markdown(f'<div class="sa-footer-head">{t("footer_trust", lang)}</div>'
                    f'<div>{t("privacy_heading", lang)}<br>{t("source_heading", lang)}</div>',
                    unsafe_allow_html=True)
    with language:
        st.markdown(f'<div class="sa-footer-head">{t("footer_language", lang)}</div>'
                    f'<div>English · اردو<br>{t("footer_built", lang)}</div>',
                    unsafe_allow_html=True)
    st.markdown(f'<div class="sa-footer-note">{t("footer_disclaimer", lang)}</div>'
                f'</div>', unsafe_allow_html=True)


def render_home() -> None:
    hero_text, hero_visual = st.columns([1.15, 1], gap="large")
    with hero_text:
        st.markdown(
            f'<div class="sa-eyebrow">{t("hero_eyebrow", lang)}</div>'
            f'<h1 class="sa-hero-title">{t("hero_title", lang)}</h1>'
            f'<p class="sa-hero-body">{t("hero_body", lang)}</p>',
            unsafe_allow_html=True,
        )
        start_col, sample_col = st.columns([1, 1])
        with start_col:
            if st.button(t("cta_start", lang), type="primary",
                         use_container_width=True, key="cta_start"):
                go_to(0)
        with sample_col:
            if st.button(t("cta_sample", lang), use_container_width=True,
                         key="cta_sample"):
                demo = sample_profile()
                st.session_state.answers = {f: getattr(demo, f) for f in PROFILE_FIELDS}
                st.session_state.is_demo = True
                st.session_state.categories = [c for c in KNOWN_CATEGORIES
                                               if counts.get(c, 0)]
                go_to(RESULTS_STEP_INDEX)
        st.markdown(
            '<div class="sa-inline-trust">'
            + "".join(f'<span class="sa-trust-item">{t(k, lang)}</span>'
                      for k in ("trust_rules", "trust_sources", "trust_no_pii"))
            + "</div>",
            unsafe_allow_html=True,
        )
    with hero_visual:
        st.markdown(opportunity_map_svg(lang), unsafe_allow_html=True)

    # -- what can you find --
    section_label(t("find_heading", lang))
    for position, (column, category) in enumerate(
            zip(st.columns(len(KNOWN_CATEGORIES)), KNOWN_CATEGORIES), start=1):
        available = counts.get(category, 0)
        chip = (badge(t("available_count", lang, n=available), "tone-good") if available
                else badge(t("coming_soon", lang), "tone-mute"))
        with column:
            st.markdown(
                f'<div class="sahulat-category {reveal("home_cat", position)}">'
                f'{CATEGORY_ICONS.get(category, "")}'
                f'<div class="sahulat-category-name">{t(f"category_{category}", lang)}</div>'
                f'<div class="sahulat-category-accent"></div>'
                f'<div class="sahulat-category-body">{t(f"find_{category}", lang)}</div>'
                f'<div style="margin-top:.7rem">{chip}</div></div>',
                unsafe_allow_html=True,
            )

    # -- the Sahulat Path: a connected journey, not four isolated cards --
    section_label(t("journey_heading", lang))
    section_title(t("journey_line", lang))
    st.markdown(sahulat_path_svg(lang), unsafe_allow_html=True)
    st.markdown(sahulat_path_vertical(lang), unsafe_allow_html=True)

    # -- three principles --
    section_label(t("principles_heading", lang))
    principle_cols = st.columns(3)
    for index, column in enumerate(principle_cols, start=1):
        with column:
            st.markdown(
                f'<div class="sa-journey-item"><span class="sa-num">0{index}</span>'
                f'<div class="sa-item-title">{t(f"principle_{index}_title", lang)}</div>'
                f'<div class="sa-item-body">{t(f"principle_{index}_body", lang)}</div></div>',
                unsafe_allow_html=True,
            )

    # -- product-generated statistics (never invented - spec section 53) --
    section_label(t("privacy_heading", lang))
    privacy_col, stats_col = st.columns([1.3, 1], gap="large")
    with privacy_col:
        st.markdown(f'<p class="sa-section-lede">{t("privacy_body", lang)}</p>',
                    unsafe_allow_html=True)
    with stats_col:
        stat_a, stat_b = st.columns(2)
        providers = len({o.provider for o in opportunities})
        sourced = sum(1 for o in opportunities if o.official_url)
        with stat_a:
            st.markdown(f'<div class="sa-stat-num">{health["total"]}</div>'
                        f'<div class="sa-stat-label">{t("catalogue_stat", lang)}</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div style="height:1rem"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-stat-num">{sourced}</div>'
                        f'<div class="sa-stat-label">{t("sourced_stat", lang)}</div>',
                        unsafe_allow_html=True)
        with stat_b:
            st.markdown(f'<div class="sa-stat-num">{providers}</div>'
                        f'<div class="sa-stat-label">{t("authorities_stat", lang)}</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div style="height:1rem"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-stat-num">0</div>'
                        f'<div class="sa-stat-label">{t("identifiers_stat", lang)}</div>',
                        unsafe_allow_html=True)

    render_footer()


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------

def render_stepper(active: int) -> None:
    items = []
    for index, step in enumerate(STEPS):
        state = "current" if index == active else ("done" if index < active else "")
        numeral = "✓" if index < active else str(index + 1)
        items.append(f'<div class="sa-stepitem {state}">'
                     f'<span class="sa-stepnum">{numeral}</span>'
                     f'<span class="sa-steplabel">{t(step.title_key, lang)}</span></div>')
    st.markdown(f'<div class="sa-stepper">{"".join(items)}</div>', unsafe_allow_html=True)


def optional_select(label: str, field_name: str, options, formatter):
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
        key=f"w_{field_name}_{st.session_state.step}", help=help_text or None,
    )
    record(field_name, value)
    return value


def number_field(label: str, field_name: str, minimum, maximum, step, as_int=False):
    current = st.session_state.answers.get(field_name)
    if current is not None:
        current = int(current) if as_int else float(current)
    value = st.number_input(
        label, min_value=minimum, max_value=maximum, step=step, value=current,
        placeholder=t("placeholder_not_answered", lang),
        key=f"w_{field_name}_{st.session_state.step}",
    )
    record(field_name, value)
    return value


def render_nav(step_index: int) -> None:
    rule()
    back_col, _, next_col = st.columns([1, 2, 1])
    with back_col:
        label = t("nav_back", lang)
        if st.button(label, key=f"back_{step_index}", use_container_width=True):
            if step_index == 0:
                st.session_state.view = "home"
                st.rerun()
            else:
                go_to(step_index - 1)
    with next_col:
        is_last = step_index == RESULTS_STEP_INDEX - 1
        label = t("nav_see_results", lang) if is_last else t("nav_continue", lang)
        if st.button(label, key=f"next_{step_index}", type="primary",
                     use_container_width=True):
            errors = validate_step(STEPS[step_index], current_profile(),
                                   st.session_state.categories)
            if errors:
                st.session_state.step_errors = errors
                st.rerun()
            go_to(step_index + 1)

    if st.session_state.step_errors:
        st.markdown(f'<div class="sa-fielderror">{t("fix_before_continuing", lang)}</div>',
                    unsafe_allow_html=True)


def render_step_focus(errors: dict) -> None:
    panel_head(t("step_focus_title", lang), t("step_focus_caption", lang),
               t("step_counter", lang, current=1, total=RESULTS_STEP_INDEX))
    selected = []
    for column, category in zip(st.columns(len(KNOWN_CATEGORIES)), KNOWN_CATEGORIES):
        available = counts.get(category, 0)
        with column:
            with st.container(border=True):
                st.markdown(f"**{t(f'category_{category}', lang)}**")
                st.caption(t(f"find_{category}", lang))
                if available:
                    if st.checkbox(t("available_count", lang, n=available),
                                   value=category in st.session_state.categories,
                                   key=f"cat_{category}"):
                        selected.append(category)
                else:
                    st.checkbox(t("coming_soon", lang), value=False, disabled=True,
                                key=f"cat_{category}",
                                help=t("category_empty_note", lang))
    st.session_state.categories = selected
    field_error("categories", errors, lang)


def render_step_about(errors: dict) -> None:
    panel_head(t("step_about_title", lang), t("step_about_caption", lang),
               t("step_counter", lang, current=2, total=RESULTS_STEP_INDEX))
    col1, col2 = st.columns(2, gap="large")
    with col1:
        field_tag(required=True, lang=lang)
        number_field(t("field_age", lang), "age", AGE_MIN, AGE_MAX, 1, as_int=True)
        field_error("age", errors, lang)

        field_tag(lang=lang)
        # Clearly separated, tappable options rather than an ambiguous
        # dropdown (spec 9.4). Selecting nothing means "prefer not to say".
        current_gender = st.session_state.answers.get("gender")
        chosen_gender = st.segmented_control(
            t("field_gender", lang), options=list(GENDERS),
            format_func=lambda v: gender_label(v, lang),
            default=current_gender if current_gender in GENDERS else None,
            key=f"w_gender_{st.session_state.step}",
        )
        record("gender", chosen_gender)
        st.caption(t("field_gender_help", lang))
    with col2:
        field_tag(required=True, lang=lang)
        optional_select(t("field_domicile", lang), "domicile_province",
                        PROVINCES, lambda v: v)
        field_error("domicile_province", errors, lang)


def render_step_education(errors: dict) -> None:
    panel_head(t("step_education_title", lang), t("step_education_caption", lang),
               t("step_counter", lang, current=3, total=RESULTS_STEP_INDEX))
    col1, col2 = st.columns(2, gap="large")
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
    panel_head(t("step_circumstances_title", lang),
               t("step_circumstances_caption", lang),
               t("step_counter", lang, current=4, total=RESULTS_STEP_INDEX))
    col1, col2 = st.columns(2, gap="large")
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

        rule()
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
        st.markdown(
            "".join(
                f'<div class="sa-answer">'
                f'<span class="sa-answer-label">{profile_field_label(f, lang)}</span>'
                f'<span class="sa-answer-value">{answer_value(profile, f)}</span></div>'
                for f in PROFILE_FIELDS),
            unsafe_allow_html=True)
        st.caption(t("detail_completeness", lang, percent=completion_percent(profile)))
        if st.button(t("nav_edit_answers", lang), key="edit_answers"):
            go_to(1)


def render_checks(match) -> None:
    st.markdown(f"**{t('why_matches_you', lang)}**")
    st.markdown(
        "".join(
            f'<div class="sa-checkrow">'
            f'<span class="sa-mark {CHECK_CLASS.get(c.status, "mark-verify")}">'
            f'{CHECK_MARK.get(c.status, "-")}</span>'
            f'<span><span class="sa-checkname">{describe_check(c, lang)[0]}</span><br>'
            f'<span class="sa-checkdetail">{describe_check(c, lang)[1]}</span></span></div>'
            for c in match.applicable_checks()),
        unsafe_allow_html=True)
    if match.missing_profile_fields:
        names = [profile_field_label(f, lang) for f in match.missing_profile_fields]
        st.caption(t("missing_fields_hint", lang, fields=join_list(names, lang)))


def render_source_card(opportunity) -> None:
    """Provenance as a visible block, not a footnote (spec sections 23 and 54)."""
    verified = opportunity.is_verified()
    status = t("source_verified", lang) if verified else t("source_needs_check", lang)
    meta = (f'{t("source_last_checked", lang)}: {opportunity.last_verified}'
            if verified else t("source_not_checked", lang))
    link = ""
    if opportunity.official_url:
        link = (f'<a class="sa-source-link" href="{opportunity.official_url}"'
                f' target="_blank" rel="noopener">{t("open_official_site", lang)}'
                f' <span class="sa-arrow">↗</span></a>')
    st.markdown(
        f'<div class="sahulat-source{" verified" if verified else ""}">'
        f'<div class="sa-source-label">{t("source_heading", lang)} — {status}</div>'
        f'<div class="sa-source-name">{opportunity.provider}</div>'
        f'<div class="sa-source-meta">{opportunity.source_title or ""}</div>'
        f'<div class="sa-source-meta">{meta}</div>{link}</div>',
        unsafe_allow_html=True)
    if not verified:
        st.caption(t("source_verify_body", lang))


def render_documents(opportunity) -> None:
    """
    Document readiness.

    ORDERING MATTERS (UX-07): the count and the progress bar must be written
    AFTER the checkboxes have been read, otherwise they render the previous
    run's state and lag one interaction behind - ticking the last box left the
    bar short, and unticking one left it full. A container reserved above the
    list lets us write into it once the true count is known.
    """
    if not opportunity.required_documents:
        return

    total = len(opportunity.required_documents)
    st.markdown(f"**{t('document_checklist_heading', lang)}**")
    summary_slot = st.container()          # filled in below, once we know the count

    previously_ready = st.session_state.documents_ready.get(
        opportunity.opportunity_id, set())
    ready = set()
    for index, document in enumerate(opportunity.required_documents):
        if st.checkbox(document, value=index in previously_ready,
                       key=f"doc_{opportunity.opportunity_id}_{index}"):
            ready.add(index)
    st.session_state.documents_ready[opportunity.opportunity_id] = ready

    with summary_slot:
        st.caption(t("documents_ready", lang, have=len(ready), total=total))
        st.progress(len(ready) / total)


def render_timeline(opportunity) -> None:
    if not opportunity.application_steps:
        return
    st.markdown(f"**{t('timeline_heading', lang)}**")
    st.markdown(
        '<div class="sahulat-timeline">'
        + "".join(f'<div class="sa-tl-item"><div class="sa-tl-step">'
                  f'{index:02d}</div><div class="sa-tl-body">{step}</div></div>'
                  for index, step in enumerate(opportunity.application_steps, 1))
        + "</div>",
        unsafe_allow_html=True)


def render_pipeline() -> None:
    """Judge-facing view of how a result was produced (spec section 61)."""
    with st.expander(t("how_generated", lang)):
        steps = ["pipeline_profile", "pipeline_rules", "pipeline_match",
                 "pipeline_retrieval", "pipeline_explain"]
        st.markdown(
            '<div class="sahulat-timeline">'
            + "".join(f'<div class="sa-tl-item"><div class="sa-tl-step">{i:02d}</div>'
                      f'<div class="sa-tl-body">{t(key, lang)}</div></div>'
                      for i, key in enumerate(steps, 1))
            + "</div>", unsafe_allow_html=True)


def trust_badge(opportunity) -> str:
    if opportunity.source_type == "user_uploaded":
        return badge(t("ai_extracted_badge", lang), "tone-verify")
    if opportunity.is_verified():
        return badge(t("officially_verified_badge", lang), "tone-good")
    return badge(t("unverified_badge", lang), "tone-verify")


def listing_badge(match) -> str:
    state = match.listing_state()
    label = {LISTING_OPEN: t("listing_open", lang),
             LISTING_CLOSED: t("listing_closed", lang)}.get(
        state, t("listing_verify_cycle", lang))
    return badge(label, LISTING_CLASS.get(state, "tone-verify"))


def render_match_card(match, rank: int = 0, highlight: bool = False,
                      animation: str = "") -> None:
    opportunity = match.opportunity
    if animation:
        # Information arriving, not cards falling. Plays once per result set.
        st.markdown(f'<div class="{animation}">', unsafe_allow_html=True)
    with st.container(border=True):
        head_col, badge_col = st.columns([3, 2])
        with head_col:
            if highlight:
                st.markdown(f'<div class="sa-first-note">{t("first_card_note", lang)}</div>',
                            unsafe_allow_html=True)
            rank_html = (f'<span class="sa-result-rank">{rank:02d}</span>&nbsp;&nbsp;'
                         if rank else "")
            category_name = (t(f"category_{opportunity.category}", lang)
                             if opportunity.category in KNOWN_CATEGORIES
                             else opportunity.category)
            st.markdown(
                f'<div class="sa-source-label">{category_name}</div>'
                f'<div>{rank_html}<span class="sa-result-title">'
                f'{opportunity.display_name(lang)}</span></div>'
                f'<div class="sa-result-authority">{opportunity.provider}</div>',
                unsafe_allow_html=True)
        with badge_col:
            st.markdown(
                " ".join([badge(status_label(match.overall_status, lang),
                                STATUS_CLASS.get(match.overall_status, "tone-mute")),
                          listing_badge(match), trust_badge(opportunity)]),
                unsafe_allow_html=True)

        summary = opportunity.display_summary(lang)
        if summary:
            st.markdown(f'<p class="sa-section-lede" style="margin:.8rem 0 0">'
                        f'{summary}</p>', unsafe_allow_html=True)

        if match.matched_priority_groups:
            groups = join_list([priority_group_label(g, lang)
                                for g in match.matched_priority_groups], lang)
            callout(t("priority_body", lang, groups=groups),
                    title=t("priority_heading", lang))
        if match.listing_closed:
            callout(t("listing_closed_explainer", lang), tone="verify")

        with st.expander(t("view_eligibility", lang), expanded=highlight):
            render_checks(match)
            quota_note = opportunity.eligibility_conditions.special_quota_note
            if quota_note:
                callout(quota_note, title=t("quota_note_label", lang), tone="info")

            rule()
            doc_col, time_col = st.columns(2, gap="large")
            with doc_col:
                render_documents(opportunity)
            with time_col:
                render_timeline(opportunity)

            rule()
            render_source_card(opportunity)

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
    if animation:
        st.markdown("</div>", unsafe_allow_html=True)


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
    out = [f"{t('app_title', lang)} - {t('results_heading', lang)}",
           t("footer_disclaimer", lang), "=" * 68, ""]
    for index, match in enumerate(results, 1):
        opportunity = match.opportunity
        trust = (t("ai_extracted_badge", lang)
                 if opportunity.source_type == "user_uploaded"
                 else t("officially_verified_badge", lang) if opportunity.is_verified()
                 else t("unverified_badge", lang))
        out.append(f"{index:02d}  {opportunity.display_name(lang)}")
        out.append(f"    {status_label(match.overall_status, lang)}  |  {trust}")
        if match.listing_closed:
            out.append(f"    ** {t('listing_closed', lang)} **")
        out.append(f"    {t('provider_label', lang)}: {opportunity.provider}")
        for check in match.applicable_checks():
            title, detail = describe_check(check, lang)
            mark = {MET: "[x]", UNMET: "[ ]", UNKNOWN: "[?]"}.get(check.status, "[-]")
            out.append(f"      {mark} {title} - {detail}")
        if opportunity.required_documents:
            out.append(f"    {t('required_documents', lang)}:")
            out.extend(f"      - {d}" for d in opportunity.required_documents)
        if opportunity.application_steps:
            out.append(f"    {t('application_steps', lang)}:")
            out.extend(f"      {i}. {s}"
                       for i, s in enumerate(opportunity.application_steps, 1))
        if opportunity.official_url:
            out.append(f"    {t('official_source', lang)}: {opportunity.official_url}")
        out.append("")
    return "\n".join(out)


def render_followup() -> None:
    rule()
    section_title(t("ask_followup", lang), t("ask_followup_hint", lang))

    chips = ("chip_what_apply", "chip_why_qualify", "chip_documents")
    for column, chip_key in zip(st.columns(len(chips)), chips):
        with column:
            if st.button(t(chip_key, lang), key=f"chip_{chip_key}",
                         use_container_width=True):
                st.session_state["followup_question"] = t(chip_key, lang)
                st.rerun()

    question = st.text_input(t("ask_followup", lang),
                             placeholder=t("ask_placeholder", lang),
                             label_visibility="collapsed", key="followup_question")
    if st.button(t("ask_button", lang), key="ask_btn", type="primary") and question.strip():
        with st.spinner(""):
            evidence = get_rag_index().retrieve(question, top_k=3)
            answer = answer_followup(question, evidence, lang)
        if evidence:
            st.info(answer)
        else:
            callout(answer, tone="verify")


def render_results() -> None:
    profile = current_profile()
    selected = st.session_state.categories
    filtered = [o for o in opportunities if o.category in selected]

    if not filtered:
        section_title(t("empty_heading", lang), t("empty_body", lang))
        if st.button(t("nav_edit_answers", lang), key="back_from_empty", type="primary"):
            go_to(0)
        return

    results = evaluate_all(profile, filtered)
    totals = summarize_counts(results)
    token = results_token()

    if st.session_state.is_demo:
        st.markdown(badge(t("demo_badge", lang), "tone-info"), unsafe_allow_html=True)
        st.caption(t("demo_note", lang))

    # The count lands first, then the cards arrive - hierarchy, not decoration.
    heading_reveal = reveal(f"{token}:heading", 1)
    if heading_reveal:
        st.markdown(f'<div class="{heading_reveal}">', unsafe_allow_html=True)
    headline = (t("results_found_one", lang) if len(results) == 1
                else t("results_found", lang, n=len(results)))
    section_title(headline, t("results_breakdown", lang,
                              strong=totals[STATUS_ELIGIBLE],
                              verify=totals[STATUS_NEEDS_VERIFICATION],
                              no=totals[STATUS_NOT_ELIGIBLE]))
    if heading_reveal:
        st.markdown("</div>", unsafe_allow_html=True)

    render_answer_summary(profile)
    if completion_percent(profile) < 70:
        st.caption(t("more_detail_hint", lang))

    strong = [r for r in results if r.overall_status == STATUS_ELIGIBLE]
    if not strong:
        callout(t("empty_body", lang), title=t("empty_heading", lang), tone="verify")

    rank = 0
    for status, note_key in ((STATUS_ELIGIBLE, "group_eligible_help"),
                             (STATUS_NEEDS_VERIFICATION, "group_needs_verification_help"),
                             (STATUS_NOT_ELIGIBLE, "group_not_eligible_help")):
        group = [r for r in results if r.overall_status == status]
        if not group:
            continue
        section_label(f"{status_label(status, lang)} — {len(group)}")
        st.markdown(f'<p class="sa-section-lede">{t(note_key, lang)}</p>',
                    unsafe_allow_html=True)
        for match in group:
            rank += 1
            render_match_card(
                match, rank=rank,
                highlight=(rank == 1 and status == STATUS_ELIGIBLE),
                animation=reveal(f"{token}:card", rank))

    rule()
    render_pipeline()

    export_col, restart_col = st.columns(2)
    with export_col:
        st.download_button(t("export_button", lang),
                           data=build_export_text(results).encode("utf-8"),
                           file_name="sahulat-ai-results.txt", mime="text/plain",
                           use_container_width=True)
    with restart_col:
        if st.button(t("nav_start_over", lang), key="restart", use_container_width=True):
            start_over()

    render_followup()


def render_wizard() -> None:
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


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_discover, tab_read, tab_how = st.tabs(
    [t("nav_discover", lang), t("nav_read", lang), t("nav_how", lang)])


with tab_discover:
    if st.session_state.view == "home":
        render_home()
    else:
        render_wizard()


with tab_read:
    section_title(t("upload_ad_heading", lang), t("upload_ad_intro", lang))

    if not is_ai_available():
        callout(t("ai_mock_extraction_notice", lang), tone="info")

    uploaded_file = st.file_uploader(t("upload_ad_heading", lang),
                                     type=["png", "jpg", "jpeg", "pdf"],
                                     label_visibility="collapsed")

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "application/octet-stream"
        preview_col, action_col = st.columns([1, 2], gap="large")
        with preview_col:
            if mime_type.startswith("image/"):
                st.image(file_bytes, use_container_width=True)
            else:
                st.markdown(f"`{uploaded_file.name}`")
        with action_col:
            st.caption(t("upload_privacy_note", lang))
            if st.button(t("upload_ad_button", lang), type="primary"):
                with st.spinner(""):
                    extracted, raw = read_ad(file_bytes, mime_type, language=lang)
                st.session_state.uploaded_opportunity = extracted
                st.session_state.uploaded_raw = raw
                st.session_state.screen_upload = False

    if st.session_state.uploaded_opportunity is not None:
        opportunity = st.session_state.uploaded_opportunity
        raw = st.session_state.uploaded_raw or {}
        rule()

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
            badge(t("ai_extracted_badge", lang), "tone-verify") + " "
            + badge(f"{t('extraction_confidence', lang)}: {confidence_text}", "tone-mute"),
            unsafe_allow_html=True)

        if raw.get("_error"):
            callout(t("error_busy", lang), tone="verify")
            with st.expander(t("technical_details", lang)):
                st.code(str(raw["_error"]))

        st.markdown(f"**{opportunity.name}**")
        if opportunity.summary_en:
            st.write(opportunity.summary_en)
        st.caption(f"{t('provider_label', lang)}: {opportunity.provider}")

        with st.expander(t("raw_extraction_toggle", lang)):
            st.json(raw)

        rule()
        if not current_profile().is_screenable():
            callout(t("upload_needs_profile", lang), tone="info")
        else:
            if st.button(t("screen_uploaded", lang), type="primary"):
                st.session_state.screen_upload = True
            if st.session_state.screen_upload:
                render_match_card(evaluate(current_profile(), opportunity))

    st.caption(t("upload_privacy_note", lang))


with tab_how:
    section_title(t("how_heading", lang), t("how_intro", lang))

    for index, column in enumerate(st.columns(3), start=1):
        with column:
            st.markdown(
                f'<div class="sa-journey-item"><span class="sa-num">0{index}</span>'
                f'<div class="sa-item-title">{t(f"principle_{index}_title", lang)}</div>'
                f'<div class="sa-item-body">{t(f"principle_{index}_body", lang)}</div></div>',
                unsafe_allow_html=True)

    rule()
    trust_col, privacy_col = st.columns(2, gap="large")
    with trust_col:
        st.markdown(f"**{t('how_trust_heading', lang)}**")
        st.caption(t("how_trust_body", lang))
        st.markdown(badge(t("officially_verified_badge", lang), "tone-good") + " "
                    + badge(t("unverified_badge", lang), "tone-verify") + " "
                    + badge(t("ai_extracted_badge", lang), "tone-verify"),
                    unsafe_allow_html=True)
    with privacy_col:
        st.markdown(f"**{t('privacy_heading', lang)}**")
        st.caption(t("privacy_body", lang))

    rule()
    status_col, catalogue_col = st.columns(2, gap="large")
    with status_col:
        st.markdown(f"**{t('sidebar_status', lang)}**")
        if is_ai_available():
            st.caption(t("ai_enabled", lang))
        else:
            st.caption(t("ai_mock_mode", lang) + " — " + t("ai_mock_explainer", lang))
    with catalogue_col:
        st.markdown(f"**{t('sidebar_catalog', lang)}**")
        st.caption(t("sidebar_records", lang, n=health["total"]))
        if health["unverified"]:
            st.caption(t("sidebar_unverified", lang, n=health["unverified"]))

    render_pipeline()
    render_footer()

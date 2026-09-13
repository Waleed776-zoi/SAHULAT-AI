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

from core.ad_reader import build_record, extract_raw, read_ad
from core.brand import lockup_html, page_icon, symbol_html
from core.data_loader import (
    KNOWN_CATEGORIES, catalogue_health, category_counts, load_all_opportunities,
)
from core.i18n import (
    computer_label, describe_check, describe_comparison, describe_freshness,
    describe_gap, describe_next_action, describe_profile,
    describe_ranking_reason, describe_requirements, describe_urgency,
    education_label,
    english_label, field_of_study_label, gender_label, join_list,
    LANGUAGE_NAMES, LANGUAGES, is_rtl, priority_group_label,
    profile_field_label, scorecard_row, status_label, t,
    validation_message,
)
from core.llm_client import (
    REASON_NO_EVIDENCE, REASON_OFFLINE, SIMPLIFY_SECTIONS, answer_followup,
    explain_match, is_ai_available, simplify_opportunity,
)
from core.models import (
    COMPUTER_LEVELS, EDUCATION_LEVELS, ENGLISH_LEVELS, FIELDS_OF_STUDY, GENDERS,
    CHECK_DEADLINE, LISTING_ALWAYS_OPEN, LISTING_CLOSED, LISTING_OPEN, MET,
    PROVINCES, STATUS_ELIGIBLE,
    STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE, UNKNOWN, UNMET, UserProfile,
    sample_profile,
)
from core.comparison import compare
from core.impact import estimate_basis, measure
from core.next_action import (
    ACTION_ANSWER_MISSING, is_actionable_now, next_action,
)
from core.readiness import readiness
from core.timeliness import (
    URGENCY_CONTINUOUS, URGENCY_PASSED, URGENCY_UNKNOWN, days_remaining,
    days_since_verified, deadline_urgency, match_urgency, record_freshness,
    should_prompt_verification,
)
from core.rules_engine import (
    evaluate, evaluate_all, ranking_factors, summarize_counts, top_matches,
)
from core.validation import (
    AGE_MAX, AGE_MIN, EXPERIENCE_MAX, INCOME_MAX, MARKS_MAX, MARKS_MIN,
    RESULTS_STEP_INDEX, STEPS, completion_percent, validate_step,
)

# The tab icon is cut from the same artwork as the header lockup, by
# scripts/prepare_logo.py, so the two cannot drift apart. page_icon() resolves
# from core/brand.py rather than the working directory, which Streamlit does
# not guarantee, and returns None if the build has not been run.


st.set_page_config(
    page_title="Sahulat AI — Pakistan's Opportunity Navigator",
    page_icon=page_icon(),
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
LISTING_CLASS = {LISTING_OPEN: "tone-good", LISTING_CLOSED: "tone-mute",
                 LISTING_ALWAYS_OPEN: "tone-good"}
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
    # Roman Urdu is Urdu *language* in Latin *script*: it takes the Latin font
    # stack, Latin leading and left-to-right layout. Treating it as "the Urdu
    # one" and mirroring the page would be the obvious, wrong, shortcut.
    urdu = is_rtl(lang)
    body_font = ("'Noto Naskh Arabic','Inter',system-ui,sans-serif" if urdu
                 else "'Inter',system-ui,-apple-system,sans-serif")
    display_font = ("'Noto Nastaliq Urdu','Noto Naskh Arabic',serif" if urdu
                    else "'Source Serif 4',Georgia,serif")
    display_lh = "2.0" if urdu else "1.12"
    body_lh = "1.95" if urdu else "1.6"

    rtl = """
      .stMain .block-container { direction: rtl; text-align: right; }
      .sa-checkrow, .sa-stepper, .sa-inline-trust,
      .sa-brandbar, .sa-footer-brand { flex-direction: row-reverse; }
      a[href^="http"], .sa-ltr { direction: ltr; unicode-bidi: embed;
                                 display: inline-block; }
    """ if urdu else ""

    st.markdown(
        f"<style>{FONT_IMPORT}\n"
        f":root {{ --sa-font-body: {body_font};"
        f" --sa-font-display: {display_font};"
        f" --sa-display-lh: {display_lh};"
        f" --sa-body-lh: {body_lh}; }}\n"
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


# One card is shown for this long before the next slides in. Slow on purpose:
# the hero is read, not watched, and a faster cycle would pull attention away
# from the headline and the call to action beside it.
PREVIEW_SECONDS_PER_CARD = 4.0


def hero_preview_card(match, lang: str) -> str:
    """One real screening result, rendered at preview size."""
    opportunity = match.opportunity
    score = match.scorecard()

    category = (t(f"category_{opportunity.category}", lang)
                if opportunity.category in KNOWN_CATEGORIES else opportunity.category)
    deadline_label, _ = describe_urgency(match_urgency(match),
                                         days_remaining(match.deadline), lang)

    # Real condition rows, drawn from the checks the engine actually ran.
    # The deadline is excluded: it is a property of the listing rather than of
    # the person, it already has its own line above, and rendering it as
    # "your information: today's date" reads as nonsense at this size.
    rows = ""
    for check in [c for c in match.satisfied() + match.gaps() + match.blockers()
                  if c.key != CHECK_DEADLINE][:3]:
        title, _required, actual, outcome = scorecard_row(check, lang)
        tone = {MET: "is-met", UNMET: "is-unmet"}.get(check.status, "is-unknown")
        rows += (f'<div class="sa-preview-row">'
                 f'<span class="sa-preview-req">{title}</span>'
                 f'<span class="sa-preview-you">{actual}</span>'
                 f'<span class="sa-preview-mark {tone}">{outcome}</span></div>')

    action = describe_next_action(next_action(match, set()), lang)

    return (
        f'<div class="sa-preview-body">'
        f'<div class="sa-preview-eyebrow">{category}'
        f'<span class="sa-preview-pill">{status_label(match.overall_status, lang)}</span>'
        f'</div>'
        f'<div class="sa-preview-title">{opportunity.display_name(lang)}</div>'
        f'<div class="sa-preview-org">{opportunity.provider}</div>'
        f'<div class="sa-preview-score">'
        f'<span class="sa-preview-count">'
        f'{t("scorecard_summary", lang, met=score["met"], total=score["total"])}</span>'
        f'<span class="sa-preview-deadline">{deadline_label}</span></div>'
        f'{rows}'
        f'<div class="sa-preview-next">'
        f'<span class="sa-preview-next-label">{t("next_step_label", lang)}</span>'
        f'<span class="sa-preview-next-body">{action}</span></div>'
        f'</div>'
    )


def hero_preview_matches():
    """
    The best real match in each category, for the rotation.

    Not the overall top six - for the demo profile that is five NAVTTC courses,
    which is accurate and would imply the catalogue holds nothing else. One per
    category shows the whole product, and each card is still whatever the
    engine actually ranks first in its own category.
    """
    results = evaluate_all(sample_profile(), get_opportunities())
    picks = []
    for category in KNOWN_CATEGORIES:
        best = top_matches([r for r in results
                            if r.opportunity.category == category], limit=1)
        if best:
            picks.append(best[0])
    return picks or top_matches(results, limit=1)


def preview_cycle_css(count: int, seconds_each: float) -> str:
    """
    Keyframes for the rotation, generated because the percentages depend on
    how many categories actually have records.

    Each card holds still for most of its window and moves only at the
    handover, so what the reader sees is a settled card rather than a
    permanently animating one (V3 spec 40.5).
    """
    if count < 2:
        return ""
    total = count * seconds_each
    share = 100.0 / count           # this card's slice of the whole cycle
    enter = min(3.0, share / 6)     # slide in
    leave = share - enter           # start sliding out
    return (
        "<style>"
        "@keyframes sa-preview-cycle {"
        f"0%{{opacity:0;transform:translateY(14px) scale(.985)}}"
        f"{enter:.2f}%{{opacity:1;transform:none}}"
        f"{leave:.2f}%{{opacity:1;transform:none}}"
        f"{share:.2f}%{{opacity:0;transform:translateY(-14px) scale(.985)}}"
        f"100%{{opacity:0;transform:translateY(-14px) scale(.985)}}"
        "}"
        "@keyframes sa-preview-dot {"
        f"0%,{share:.2f}%,100%{{background:var(--border-hover);opacity:.45}}"
        f"{enter:.2f}%,{leave:.2f}%{{background:var(--primary);opacity:1}}"
        "}"
        f".sa-preview-slide{{animation:sa-preview-cycle {total:.1f}s"
        " var(--sa-ease-cycle, linear) infinite both}"
        f".sa-preview-dots i{{animation:sa-preview-dot {total:.1f}s linear infinite both}}"
        "</style>"
    )


@st.cache_data(show_spinner=False)
def hero_preview(lang: str) -> str:
    """
    A miniature of real results, for the hero (spec 13.2).

    NOT a mockup. Every card is a screening of the demo profile against the
    live catalogue - the same verdict, the same condition count, the same next
    step a user would get. A fabricated example card would be the one dishonest
    thing on the landing page of a product that exists to not fabricate things.

    The cards cycle in CSS rather than through reruns. A rerun every four
    seconds would re-screen the catalogue and reset every widget on the page,
    and Streamlit has no way to repaint one element on a timer without one.

    Cached per language: it costs one screening pass, and the landing page is
    the most re-rendered screen in the app.
    """
    matches = hero_preview_matches()
    if not matches:
        return ""

    slides = "".join(
        f'<div class="sa-preview-slide" style="animation-delay:'
        f'{index * PREVIEW_SECONDS_PER_CARD:.1f}s">{hero_preview_card(match, lang)}</div>'
        for index, match in enumerate(matches))

    dots = ""
    if len(matches) > 1:
        dots = ('<div class="sa-preview-dots" aria-hidden="true">' + "".join(
            f'<i style="animation-delay:{index * PREVIEW_SECONDS_PER_CARD:.1f}s"></i>'
            for index in range(len(matches))) + "</div>")

    return (
        preview_cycle_css(len(matches), PREVIEW_SECONDS_PER_CARD)
        + f'<div class="sa-preview" role="img" '
          f'aria-label="{t("hero_preview_alt", lang)}">'
          f'<div class="sa-preview-chrome"><span></span><span></span><span></span>'
          f'{dots}</div>'
          f'<div class="sa-preview-stack">{slides}</div>'
          f'</div>'
    )


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
        # Which product screen is on. "view" is a level below: home vs wizard
        # WITHIN Discover.
        "section": "discover",
        "view": "home",
        "answers": {},
        "categories": [c for c in KNOWN_CATEGORIES],
        "step": 0,
        "step_errors": {},
        "is_demo": False,
        "uploaded_opportunity": None,
        "uploaded_raw": None,
        "upload_match": None,
        "upload_corrected": False,
        "screen_upload": False,
        "explanations": {},
        "simplified": {},
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


# The three product screens. Not tabs: each is a destination with its own
# purpose, and the header treats them as such (spec 45.3).
SECTIONS = ("discover", "read", "how")
SECTION_LABEL_KEYS = {"discover": "nav_discover", "read": "nav_read",
                      "how": "nav_how"}


def go_to_section(name: str) -> None:
    st.session_state.section = name
    st.rerun()


def go_to(index: int) -> None:
    st.session_state.step = max(0, min(index, RESULTS_STEP_INDEX))
    st.session_state.step_errors = {}
    st.session_state.view = "wizard"
    # Every wizard step lives on Discover. Jumping to a step from elsewhere -
    # the Lens hand-off does this - has to bring the section with it.
    st.session_state.section = "discover"
    st.rerun()


def start_over() -> None:
    st.session_state.answers = {}
    st.session_state.categories = [c for c in KNOWN_CATEGORIES]
    st.session_state.explanations = {}
    st.session_state.is_demo = False
    st.session_state.step = 0
    st.session_state.step_errors = {}
    st.session_state.view = "home"
    st.session_state.section = "discover"
    st.session_state.documents_ready = {}
    st.session_state.simplified = {}
    # Per-opportunity Q&A answers are keyed dynamically (P1-3), so clear them
    # by prefix rather than by name.
    for key in [k for k in st.session_state if str(k).startswith("ctx_answer_")]:
        del st.session_state[key]
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

def logo_mark(animate: bool = False) -> str:
    """
    The supplied logo, from core.brand.

    Served there rather than built here so the header, the tab icon and the
    files in assets/brand/ cannot drift apart. The lockup already carries the
    name in both scripts, so the header no longer sets "Sahulat AI" as text
    beside it - that was the placeholder mark's arrangement, and repeating the
    name next to artwork that contains it reads as a mistake.

    `animate` settles it in once per session. The placeholder drew its own
    stroke; artwork cannot, so this is a fade rather than a pretend draw.
    """
    return lockup_html(
        height=46, alt=t("app_title", lang),
        css_class="sahulat-logo is-new" if animate else "sahulat-logo")


def render_language_picker() -> None:
    """
    One dropdown rather than three buttons.

    Each option is written in its own language, so a reader who cannot read
    the other two can still find theirs - that was the reason the buttons were
    always visible, and it survives the move into a menu because the labels
    themselves carry it.
    """
    codes = list(LANGUAGES)
    chosen = st.selectbox(
        t("footer_language", lang), codes,
        index=codes.index(lang) if lang in codes else 0,
        format_func=lambda code: LANGUAGE_NAMES[code],
        key="lang_picker", label_visibility="collapsed",
        help=t("language_help", lang),
    )
    if chosen != lang:
        st.session_state.language = chosen
        st.rerun()


def render_header() -> None:
    """
    The brand bar: identity on one side, language on the other.

    A real columns row rather than one HTML block, because a Streamlit widget
    cannot be nested inside a markdown string and the language picker has to
    live in here. `.sa-brandbar` is the hook the stylesheet matches on.
    """
    brand, picker = st.columns([3.4, 1], vertical_alignment="center")
    with brand:
        st.markdown(
            f'<div class="sa-brandbar">{logo_mark(animate=should_animate("logo"))}</div>',
            unsafe_allow_html=True)
    with picker:
        render_language_picker()


def render_nav_bar() -> None:
    """
    The three product screens and the primary action.

    Replaces `st.tabs`. A tab strip says "panels of one page"; these are
    different screens with different jobs, and the header is where a product
    puts them. The active item is the only `primary` button on the bar, which
    is what carries the current-location signal - never colour alone.

    Language used to sit here as three buttons. It is a setting, touched once,
    and it was taking three of the eight slots on the row that carries the
    navigation - so it moved into the brand bar as a picker.
    """
    st.markdown('<div class="sa-navbar">', unsafe_allow_html=True)
    columns = st.columns([1.2, 1.85, 1.6, 1.5, 1.85], vertical_alignment="center")

    for column, name in zip(columns[:3], SECTIONS):
        with column:
            active = st.session_state.section == name
            if st.button(t(SECTION_LABEL_KEYS[name], lang), key=f"section_{name}",
                         use_container_width=True,
                         type="primary" if active else "tertiary"):
                go_to_section(name)

    with columns[4]:
        if st.session_state.section == "discover" and st.session_state.view == "home":
            if st.button(t("cta_start", lang), key="header_cta",
                         type="primary", use_container_width=True):
                go_to(0)
        else:
            if st.button(t("nav_start_over", lang), key="header_restart",
                         use_container_width=True):
                start_over()
    st.markdown('</div>', unsafe_allow_html=True)


render_header()
render_nav_bar()


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

def render_footer() -> None:
    st.markdown('<div class="sa-footer">', unsafe_allow_html=True)
    brand, discover, trust, language = st.columns([2, 1, 1, 1])
    with brand:
        # The symbol, not the lockup: the footer sits on the deep green
        # surface, where the navy wordmark drops to almost no contrast. The
        # ribbon is green and reads there, so the name stays as text beside it.
        st.markdown(
            f'<div class="sa-footer-brand">{symbol_html(height=26)}'
            f'<span>{t("app_title", lang)} · {t("brand_urdu", lang)}</span></div>'
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
        # A real screening result, not an illustration of one (spec 13.2).
        preview = hero_preview(lang)
        st.markdown(preview or opportunity_map_svg(lang), unsafe_allow_html=True)
        if preview:
            st.caption(t("hero_preview_note", lang))

    # -- four clear paths, including the upload route (V2 P0-8) ------------
    # The fourth path is not a category: it is the Lens. Leaving it out of the
    # landing page hid the feature most likely to be the demo moment.
    section_label(t("home_paths_heading", lang))
    # One card per category, plus the Lens. The Lens is not a category - it was
    # promoted onto the landing page because leaving it in a tab hid the
    # feature most likely to be the demo moment. Public assistance joined the
    # row when DATA-07 filled it: a category with records and no way in from
    # the landing page is reachable only by someone who knows to go looking.
    path_cols = st.columns(5)
    paths = (("scholarship", "path_scholarship"), ("job", "path_job"),
             ("skills", "path_skills"), ("assistance", "path_assistance"))
    for column, (category, label_key) in zip(path_cols, paths):
        with column:
            with st.container(border=True):
                st.markdown(f"**{t(label_key, lang)}**")
                st.caption(t(f"find_{category}", lang))
                available = counts.get(category, 0)
                if st.button(t("path_start", lang), key=f"path_{category}",
                             use_container_width=True, disabled=not available):
                    st.session_state.categories = [category]
                    go_to(1)          # focus step is already answered for them
                if not available:
                    st.caption(t("coming_soon", lang))
    with path_cols[4]:
        with st.container(border=True):
            st.markdown(f"**{t('path_check_ad', lang)}**")
            st.caption(t("path_check_ad_body", lang))
            # The other four cards start a journey; this one used to just point
            # at a tab. Now that the tab is a screen, it can do the same thing
            # they do (spec 50: one dominant action per card).
            if st.button(t("path_start", lang), key="path_check_ad",
                         use_container_width=True):
                go_to_section("read")

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

    # -- why Sahulat (V2 P0-8) --
    section_label(t("benefits_heading", lang))
    benefits = ("personal", "evidence", "bilingual", "realworld")
    for column, name in zip(st.columns(4), benefits):
        with column:
            st.markdown(
                f'<div class="sa-benefit">'
                f'<div class="sa-benefit-title">{t(f"benefit_{name}_title", lang)}</div>'
                f'<div class="sa-benefit-body">{t(f"benefit_{name}_body", lang)}</div>'
                f'</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="sa-spacer"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sa-stat-num">{sourced}</div>'
                        f'<div class="sa-stat-label">{t("sourced_stat", lang)}</div>',
                        unsafe_allow_html=True)
        with stat_b:
            st.markdown(f'<div class="sa-stat-num">{providers}</div>'
                        f'<div class="sa-stat-label">{t("authorities_stat", lang)}</div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="sa-spacer"></div>', unsafe_allow_html=True)
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


RESULT_PILL = {MET: "pill-good", UNMET: "pill-no", UNKNOWN: "pill-verify"}


def render_ai_text(result, key_prefix: str = "") -> None:
    """
    Show a model answer, or say plainly why there isn't one (P2-5).

    An answer and a failure notice used to render identically - same blue box,
    same weight - so a user could not tell which they were reading. They are
    now visually different, and the notice names what is *not* affected, since
    the eligibility result never depended on the model in the first place.

    A raw API error is never shown. "Gemini API error 429" tells a scholarship
    applicant nothing they can act on.
    """
    if result is None:
        return
    if getattr(result, "ok", True):
        st.info(str(result))
        return

    reason = getattr(result, "reason", "")
    if reason == REASON_NO_EVIDENCE:
        callout(str(result), title=t("no_evidence_heading", lang), tone="verify")
    elif reason == REASON_OFFLINE:
        callout(t("ai_mock_explainer", lang), title=t("ai_offline_heading", lang),
                tone="info")
    else:
        callout(t("ai_unavailable_body", lang),
                title=t("ai_unavailable_heading", lang), tone="verify")


def render_scorecard(match) -> None:
    """
    The eligibility scorecard (V2 P0-1).

    Requirement / your information / result, one row per condition, so a user
    can see exactly what was checked rather than being asked to trust a
    verdict. The header counts conditions; it is deliberately NOT a
    percentage "fit" score. The spec permits "another clearly defined
    profile-match representation", and a count is one the reader can verify
    against the rows directly beneath it, whereas a percentage would imply a
    probability of success that no rule in this system computes.
    """
    score = match.scorecard()
    st.markdown(f"**{t('scorecard_heading', lang)}**")

    extra = ""
    if score["unmet"] or score["unknown"]:
        extra = (f'<span class="sa-score-extra">'
                 f'{t("scorecard_summary_extra", lang, unmet=score["unmet"], unknown=score["unknown"])}'
                 f'</span>')
    segments = "".join(
        f'<span class="sa-score-seg seg-{name}" style="flex:{score[name]}"></span>'
        for name in ("met", "unmet", "unknown") if score[name])
    st.markdown(
        f'<div class="sa-score-head">'
        f'<span class="sa-score-num">'
        f'{t("scorecard_summary", lang, met=score["met"], total=score["total"])}</span>'
        f'{extra}</div>'
        f'<div class="sa-score-bar">{segments}</div>',
        unsafe_allow_html=True)

    rows = []
    for check in match.applicable_checks():
        title, required, actual, result = scorecard_row(check, lang)
        rows.append(
            f'<tr><td><span class="sa-req">{title}</span>'
            f'<span class="sa-reqsub">{required}</span></td>'
            f'<td class="sa-reqval">{actual}</td>'
            f'<td><span class="sa-pill {RESULT_PILL.get(check.status, "pill-verify")}">'
            f'{result}</span></td></tr>')
    st.markdown(
        f'<div class="sa-scorecard"><table>'
        f'<thead><tr><th>{t("col_requirement", lang)}</th>'
        f'<th>{t("col_your_answer", lang)}</th>'
        f'<th>{t("col_result", lang)}</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True)
    st.caption(t("scorecard_no_score_note", lang))


def render_reasons(match) -> None:
    """
    Why this result came out the way it did (V2 P0-2).

    Three separate questions, kept separate because they call for different
    responses: what passed, what failed, and what could not be checked.
    """
    satisfied, blockers, gaps = match.satisfied(), match.blockers(), match.gaps()

    if blockers:
        st.markdown(f"**{t('why_you_dont', lang)}**")
        for check in blockers:
            st.markdown(f"- {describe_gap(check, lang)}")
        st.caption(t("decisive_note", lang))

        # "What would change this" - the requirement and the profile's own
        # value, and nothing about what would follow from changing it.
        st.markdown(f"**{t('what_would_change', lang)}**")
        st.caption(t("what_would_change_caveat", lang))

    if gaps:
        st.markdown(f"**{t('what_needs_verification', lang)}**")
        for check in gaps:
            st.markdown(f"- {describe_gap(check, lang)}")
        if match.missing_profile_fields:
            names = [profile_field_label(f, lang) for f in match.missing_profile_fields]
            st.caption(t("missing_fields_hint", lang, fields=join_list(names, lang)))

    if satisfied:
        st.markdown(f"**{t('why_you_match', lang)}**")
        for check in satisfied:
            title, detail = describe_check(check, lang)
            st.markdown(f"- {title}: {detail}")


def render_next_action(match, key_suffix: str = "") -> None:
    """
    One next step, prominently (V2 P0-6).

    Deliberately outside the detail expander: a user who never opens the
    details still needs to know what to do. The decision of which action this
    is belongs to core/next_action.py.
    """
    ticked = ticked_documents(match.opportunity)
    action = next_action(match, ticked)
    tone = "sa-next actionable" if is_actionable_now(match, ticked) else "sa-next"
    st.markdown(
        f'<div class="{tone}"><div class="sa-next-label">{t("next_step_label", lang)}</div>'
        f'<div class="sa-next-body">{describe_next_action(action, lang)}</div></div>',
        unsafe_allow_html=True)

    if action.key == ACTION_ANSWER_MISSING:
        if st.button(t("action_answer_now", lang),
                     key=f"answer_now_{match.opportunity.opportunity_id}{key_suffix}"):
            go_to(1)
    elif action.url:
        st.markdown(f'<a class="sa-source-link" href="{action.url}" target="_blank"'
                    f' rel="noopener">{t("open_official_site", lang)}'
                    f' <span class="sa-arrow">\u2197</span></a>', unsafe_allow_html=True)


def _num_or_none(value, as_int=False):
    """Streamlit gives back None for an empty number box; keep it None."""
    if value is None:
        return None
    return int(value) if as_int else float(value)


def render_correction(opportunity) -> None:
    """
    Let the user fix what the model read (V2 P0-4, step 4).

    Extraction from a photograph is not reliable, and the rules engine will
    treat whatever comes out of it as fact. Giving the user the edit is what
    keeps a misread number from silently becoming an eligibility verdict.

    Corrections are applied to the in-memory record only - nothing is written
    back to the catalogue, and the record keeps its user_uploaded trust level
    either way (Invariant 4).
    """
    conditions = opportunity.eligibility_conditions
    with st.expander(t("correct_heading", lang)):
        st.caption(t("correct_note", lang))

        col1, col2 = st.columns(2, gap="large")
        with col1:
            min_age = st.number_input(profile_field_label("age", lang) + " — min",
                                      min_value=AGE_MIN, max_value=AGE_MAX, step=1,
                                      value=_num_or_none(conditions.min_age, True),
                                      placeholder=t("correct_none", lang), key="fix_min_age")
            max_age = st.number_input(profile_field_label("age", lang) + " — max",
                                      min_value=AGE_MIN, max_value=AGE_MAX, step=1,
                                      value=_num_or_none(conditions.max_age, True),
                                      placeholder=t("correct_none", lang), key="fix_max_age")
            provinces = st.multiselect(profile_field_label("domicile_province", lang),
                                       options=list(PROVINCES),
                                       default=[p for p in (conditions.domicile_provinces or [])
                                                if p in PROVINCES],
                                       key="fix_provinces")
        with col2:
            levels = [None] + list(EDUCATION_LEVELS)
            current = conditions.min_education_level
            education = st.selectbox(
                profile_field_label("education_level", lang), options=levels,
                index=levels.index(current) if current in levels else 0,
                format_func=lambda v: t("correct_none", lang) if v is None
                else education_label(v, lang), key="fix_education")
            marks = st.number_input(profile_field_label("marks_percentage", lang),
                                    min_value=float(MARKS_MIN), max_value=float(MARKS_MAX),
                                    step=1.0, value=_num_or_none(conditions.min_marks_percentage),
                                    placeholder=t("correct_none", lang), key="fix_marks")
            income = st.number_input(profile_field_label("monthly_household_income", lang),
                                     min_value=0.0, max_value=float(INCOME_MAX), step=1000.0,
                                     value=_num_or_none(conditions.max_monthly_household_income),
                                     placeholder=t("correct_none", lang), key="fix_income")

        deadline = st.text_input(t("deadline_label", lang),
                                 value=conditions.application_deadline or "",
                                 help=t("correct_deadline_hint", lang), key="fix_deadline")

        if st.button(t("correct_apply", lang), key="apply_fixes", type="primary"):
            conditions.min_age = min_age
            conditions.max_age = max_age
            conditions.domicile_provinces = provinces or None
            conditions.min_education_level = education
            conditions.min_marks_percentage = marks
            conditions.max_monthly_household_income = income
            conditions.application_deadline = deadline.strip() or None
            st.session_state.upload_corrected = True
            st.session_state.upload_match = None      # force a fresh screening
            st.rerun()


def opportunity_facts(opportunity) -> str:
    """
    The record's own statements, for the plain-language rewrite (P1-7).

    Built ONLY from what the record says. No profile, no eligibility result:
    a model that is never told the verdict cannot leak it into the wording or
    tell the reader they qualify.
    """
    conditions = opportunity.eligibility_conditions
    stated, _ = describe_requirements(conditions, lang)
    lines = [f"Name: {opportunity.name}",
             f"Provider: {opportunity.provider}",
             f"Category: {opportunity.category}"]
    if opportunity.target_group:
        lines.append(f"Intended for: {opportunity.target_group}")
    if opportunity.summary_en:
        lines.append(f"Summary: {opportunity.summary_en}")
    if stated:
        lines.append("Conditions stated in the record:")
        lines.extend(f"  - {title}: {value}" for title, value in stated)
    if conditions.special_quota_note:
        lines.append(f"Preference noted: {conditions.special_quota_note}")
    if opportunity.required_documents:
        lines.append("Documents required: " + "; ".join(opportunity.required_documents))
    if opportunity.application_steps:
        lines.append("How to apply: " + " -> ".join(opportunity.application_steps))
    if conditions.application_deadline:
        lines.append(f"Deadline: {conditions.application_deadline}")
    lines.append(f"Official page: {opportunity.official_url or 'not stated in the record'}")
    return "\n".join(lines)


def render_plain_language(opportunity) -> None:
    """
    Explain Like I'm New (P1-7).

    Placed AFTER the scorecard, never instead of it. The rewrite is a reading
    aid; the conditions above remain the authority, and the caveat says so.
    """
    key = f"eli5_{opportunity.opportunity_id}"
    if st.button(t("eli5_button", lang), key=f"btn_{key}"):
        with ai_stages("stage_simplify_read", "stage_simplify_write") as stages:
            facts = opportunity_facts(opportunity)
            stages.advance()

            st.session_state.simplified[key] = simplify_opportunity(facts, lang)

    result = st.session_state.simplified.get(key)
    if not result:
        return

    st.markdown(f"**{t('eli5_heading', lang)}**")
    if result.get("_error"):
        callout(t("error_busy", lang), tone="verify")
        return

    for section in SIMPLIFY_SECTIONS:
        body = result.get(section)
        if body:
            st.markdown(f'<div class="sa-eli5"><div class="sa-eli5-q">'
                        f'{t("eli5_" + section, lang)}</div>'
                        f'<div class="sa-eli5-a">{body}</div></div>',
                        unsafe_allow_html=True)
    if result.get("_mock"):
        st.caption(t("ai_mock_explainer", lang))
    st.caption(t("eli5_caveat", lang))


def contextual_questions(match) -> list:
    """
    The questions worth offering for THIS result (P1-3).

    Driven by the match state, so a user who is eligible is never offered
    "why am I not eligible?" - a blank chatbot asks the user to guess what it
    knows, and a wrong suggestion is worse than none.
    """
    chips = []
    if match.blockers():
        chips.append("chip_why_not_eligible")
    else:
        chips.append("chip_why_eligible")
    if match.gaps():
        chips.append("chip_what_verify")
    if match.opportunity.required_documents:
        chips.append("chip_this_documents")
    if match.deadline:
        chips.append("chip_this_deadline")
    if match.opportunity.official_url:
        chips.append("chip_where_apply")
    return chips[:4]


def render_contextual_followup(match) -> None:
    """
    Grounded Q&A about one opportunity (P1-3).

    Evidence comes from this record alone. Retrieving across the catalogue
    would hand the model text about a different scheme labelled "evidence",
    which is how a confident answer about the wrong scholarship gets written.
    """
    opportunity = match.opportunity
    st.markdown(f"**{t('ask_about_this', lang)}**")
    st.caption(t("ask_scoped_note", lang))

    state_key = f"ctx_answer_{opportunity.opportunity_id}"
    chips = contextual_questions(match)
    for column, chip in zip(st.columns(len(chips)), chips):
        with column:
            if st.button(t(chip, lang), key=f"{chip}_{opportunity.opportunity_id}",
                         use_container_width=True):
                with ai_stages("stage_ask_search", "stage_ask_gather",
                               "stage_ask_write") as stages:
                    evidence = get_rag_index().retrieve_for(
                        opportunity.opportunity_id, t(chip, lang))
                    stages.advance()

                    evidence = list(evidence)
                    stages.advance()

                    st.session_state[state_key] = answer_followup(
                        t(chip, lang), evidence, lang)
                st.rerun()

    answer = st.session_state.get(state_key)
    if not answer:
        st.caption(t("answer_empty_hint", lang))
    else:
        render_ai_text(answer)
        if opportunity.official_url:
            st.markdown(f'<a class="sa-source-link" href="{opportunity.official_url}"'
                        f' target="_blank" rel="noopener">{t("open_official_site", lang)}'
                        f' <span class="sa-arrow">\u2197</span></a>', unsafe_allow_html=True)


def render_passport(profile) -> None:
    """
    The Opportunity Passport (P1-4).

    This is the existing session profile given a name and a visible home. The
    privacy line is not decoration: it states what is deliberately absent, and
    what is absent is the entire reason this can be reused freely.
    """
    percent = completion_percent(profile)
    with st.expander(f"{t('passport_heading', lang)} — "
                     f"{t('passport_complete', lang, percent=percent)}"):
        st.caption(t("passport_lede", lang))
        st.markdown(
            "".join(
                f'<div class="sa-answer">'
                f'<span class="sa-answer-label">{profile_field_label(f, lang)}</span>'
                f'<span class="sa-answer-value">{answer_value(profile, f)}</span></div>'
                for f in PROFILE_FIELDS),
            unsafe_allow_html=True)
        if percent < 70:
            st.caption(t("more_detail_hint", lang))
        st.caption(t("passport_privacy", lang))
        if st.button(t("nav_edit_answers", lang), key="edit_answers"):
            go_to(1)


def render_comparison(results) -> None:
    """
    Side-by-side comparison (P1-5).

    The summary line compares EFFORT, from countable things, and says so. It
    never recommends: a smaller award with a shorter form is "less work", which
    has nothing to do with which is worth having.
    """
    if len(results) < 2:
        return

    section_label(t("compare_heading", lang))
    st.caption(t("compare_hint", lang))

    by_id = {r.opportunity.opportunity_id: r for r in results}
    chosen = st.multiselect(
        t("compare_heading", lang), options=list(by_id),
        format_func=lambda i: by_id[i].opportunity.display_name(lang),
        default=[], key="compare_pick", label_visibility="collapsed")
    if len(chosen) < 2:
        return

    picked = [by_id[i] for i in chosen]
    comparison = compare(picked, st.session_state.documents_ready)
    rows = {row.opportunity_id: row for row in comparison.rows}

    factors = [
        (t("compare_eligibility", lang),
         lambda r: status_label(r.status, lang)),
        (t("compare_conditions", lang),
         lambda r: f"{r.met} / {r.total}"),
        (t("compare_deadline", lang),
         lambda r: r.deadline or t("urgency_unknown", lang)),
        (t("compare_documents", lang),
         lambda r: str(r.documents_missing) if r.documents_total else "\u2014"),
        (t("compare_verification", lang), lambda r: str(r.gaps)),
        (t("compare_apply", lang),
         lambda r: t("option_yes", lang) if r.has_official_url else t("option_no", lang)),
    ]

    header = "".join(f"<th>{rows[i].name}</th>" for i in chosen)
    body = "".join(
        f'<tr><td class="sa-compare-factor">{label}</td>'
        + "".join(f"<td>{value(rows[i])}</td>" for i in chosen)
        + "</tr>"
        for label, value in factors)
    st.markdown(
        f'<div class="sa-scorecard"><table>'
        f'<thead><tr><th>{t("compare_factor", lang)}</th>{header}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True)

    callout(describe_comparison(comparison, lang))
    st.caption(t("compare_effort_caveat", lang))


def render_impact(results) -> None:
    """
    What this session actually did (P2-2).

    Three of the four figures are counts of real work. The fourth is an
    estimate, and it is the only one carrying a badge, a stated basis and the
    arithmetic that produced it - because this panel exists to be shown to
    judges, and an unlabelled invented number would cost the counted ones
    their credibility.
    """
    impact = measure(results)
    if impact.is_empty():
        return

    basis = estimate_basis()
    section_label(t("impact_heading", lang))

    figures = [
        (impact.opportunities_screened, t("impact_screened", lang), ""),
        (impact.requirements_checked, t("impact_requirements", lang), ""),
        (impact.documents_identified, t("impact_documents", lang), ""),
        (f"~{impact.estimated_minutes_saved}", t("impact_minutes", lang),
         badge(t("impact_estimate_badge", lang), "tone-verify")),
    ]
    for column, (value, label, mark) in zip(st.columns(4), figures):
        with column:
            st.markdown(
                f'<div class="sa-impact">'
                f'<div class="sa-stat-num">{value}</div>'
                f'<div class="sa-stat-label">{label}</div>'
                f'<div class="sa-impact-mark">{mark}</div></div>',
                unsafe_allow_html=True)

    st.caption(t("impact_counted_note", lang))
    st.caption(t("impact_estimate_note", lang,
                 n=impact.opportunities_screened,
                 minutes=basis["minutes_per_lookup"]))


def render_empty_state(key_suffix: str = "") -> None:
    """
    An empty result with routes out of it (P2-4).

    A blank "no matches" is a dead end, and it also invites the wrong reading:
    that the user does not qualify for anything. The likelier explanation is
    that our catalogue is three records long, so say that too.
    """
    callout(t("empty_body", lang), title=t("empty_heading", lang), tone="verify")
    st.markdown(f"**{t('empty_try_heading', lang)}**")

    answers_col, categories_col, upload_col = st.columns(3)
    with answers_col:
        if st.button(t("empty_try_answers", lang), key=f"empty_answers{key_suffix}",
                     use_container_width=True):
            go_to(1)
    with categories_col:
        if st.button(t("empty_try_categories", lang), key=f"empty_categories{key_suffix}",
                     use_container_width=True):
            go_to(0)
    with upload_col:
        st.button(t("empty_try_upload", lang), key=f"empty_upload{key_suffix}",
                  use_container_width=True, disabled=True,
                  help=t("home_upload_hint", lang))
    st.caption(t("empty_catalogue_note", lang, n=health["total"]))


def render_top_matches(results) -> None:
    """
    The shortlist (V2 P0-3).

    Ranking is computed in core/rules_engine.evaluate_all from structured
    facts only; this just shows the head of that list together with the
    reason it is there. If nothing qualifies, nothing is shown - a shortlist
    padded with weak matches is worse than no shortlist.
    """
    shortlist = top_matches(results)
    if not shortlist:
        return

    section_label(t("top_matches_heading", lang))
    st.markdown(f'<p class="sa-section-lede">{t("top_matches_lede", lang)}</p>',
                unsafe_allow_html=True)

    for position, (column, match) in enumerate(
            zip(st.columns(len(shortlist)), shortlist), start=1):
        opportunity = match.opportunity
        reason = describe_ranking_reason(ranking_factors(match), lang)
        with column:
            st.markdown(
                f'<div class="sa-top {reveal(f"{results_token()}:top", position)}">'
                f'<div class="sa-top-rank">{position:02d}</div>'
                f'<div class="sa-top-name">{opportunity.display_name(lang)}</div>'
                f'<div class="sa-top-provider">{opportunity.provider}</div>'
                f'<div class="sa-top-status">'
                f'{badge(status_label(match.overall_status, lang), STATUS_CLASS.get(match.overall_status, "tone-mute"))}'
                f'</div>'
                f'<div class="sa-top-reason">{reason}</div></div>',
                unsafe_allow_html=True)


FRESHNESS_CLASS = {"recent": "tone-good", "aging": "tone-verify",
                   "stale": "tone-no", "never": "tone-verify"}


def render_source_card(opportunity) -> None:
    """
    Provenance as a visible block, not a footnote (spec 23/54, extended by
    P1-6 and P1-8).

    Every field the brief asks for is labelled and on screen: source document,
    organisation, official page, last verified - plus a freshness state, so
    "we have this on file" is never mistaken for "this is current".
    """
    verified = opportunity.is_verified()
    freshness = record_freshness(opportunity)
    age = days_since_verified(opportunity)
    fresh_label, fresh_detail = describe_freshness(freshness, age, lang)

    rows = [(t("source_org_label", lang), opportunity.provider)]
    if opportunity.source_title:
        rows.append((t("source_title_label", lang), opportunity.source_title))
    rows.append((t("source_last_checked", lang),
                 opportunity.last_verified if verified else t("source_not_checked", lang)))

    link = (f'<a class="sa-source-link" href="{opportunity.official_url}"'
            f' target="_blank" rel="noopener">{t("open_official_site", lang)}'
            f' <span class="sa-arrow">\u2197</span></a>'
            if opportunity.official_url
            else f'<div class="sa-source-meta">{t("source_none", lang)}</div>')

    st.markdown(
        f'<div class="sahulat-source{" verified" if verified else ""}">'
        f'<div class="sa-source-head">'
        f'<span class="sa-source-label">{t("source_heading", lang)}</span>'
        f'{badge(fresh_label, FRESHNESS_CLASS.get(freshness, "tone-verify"))}</div>'
        + "".join(f'<div class="sa-answer">'
                  f'<span class="sa-answer-label">{label}</span>'
                  f'<span class="sa-answer-value">{value}</span></div>'
                  for label, value in rows)
        + f'<div class="sa-source-meta">{fresh_detail}</div>{link}</div>',
        unsafe_allow_html=True)

    if should_prompt_verification(opportunity):
        st.caption(t("freshness_prompt", lang))


def ticked_documents(opportunity) -> set:
    """
    Which checklist boxes are ticked RIGHT NOW.

    Read from the widget keys rather than the derived set in session state.
    Same trap as UX-07: the derived set is only rebuilt when render_documents
    runs, so anything rendered before it - the readiness figure, the next step -
    would otherwise show the previous interaction's answer. Widget state, by
    contrast, already holds the new value at the top of the rerun.
    """
    stored = st.session_state.documents_ready.get(opportunity.opportunity_id, set())
    ticked = set()
    for index in range(len(opportunity.required_documents or [])):
        key = f"doc_{opportunity.opportunity_id}_{index}"
        if st.session_state.get(key, index in stored):
            ticked.add(index)
    return ticked


def render_documents(opportunity) -> None:
    """
    Application readiness (P1-1), built on the document checklist.

    ORDERING MATTERS (UX-07): the readiness figure must be written AFTER the
    checkboxes have been read, otherwise it renders the previous run's state
    and lags one interaction behind. A container reserved above the list lets
    us write into it once the true count is known.

    The percentage here is honest in a way a "profile match %" would not be:
    every term is something the user ticked or the record lists, and it is
    computed from the very rows shown beneath it.
    """
    st.markdown(f"**{t('readiness_heading', lang)}**")
    if not opportunity.required_documents:
        # "No documents listed" is a gap in our record, not permission to
        # turn up empty-handed. Saying nothing would imply the latter.
        st.caption(t("documents_none_listed", lang))
        return

    summary_slot = st.container()          # filled in below, once we know the count

    previously_ready = st.session_state.documents_ready.get(
        opportunity.opportunity_id, set())
    ready = set()
    for index, document in enumerate(opportunity.required_documents):
        if st.checkbox(document, value=index in previously_ready,
                       key=f"doc_{opportunity.opportunity_id}_{index}"):
            ready.add(index)
    st.session_state.documents_ready[opportunity.opportunity_id] = ready

    state = readiness(opportunity, ready)
    with summary_slot:
        st.markdown(
            f'<div class="sa-ready-head">'
            f'<span class="sa-ready-num">{t("readiness_percent", lang, percent=state.percent)}</span>'
            f'<span class="sa-ready-count">'
            f'{t("documents_ready", lang, have=len(state.have), total=state.total)}</span>'
            f'</div>', unsafe_allow_html=True)
        st.progress(state.percent / 100)

    if not state.have:
        st.caption(t("documents_none_marked", lang))
    if state.missing:
        st.markdown(f'<div class="sa-ready-label">{t("documents_still_needed", lang)}</div>'
                    '<div class="sa-unstated">'
                    + "".join(f"<span>{document}</span>" for document in state.missing)
                    + "</div>", unsafe_allow_html=True)
    st.caption(t("readiness_note", lang))


def render_deadline(match) -> None:
    """
    Deadline intelligence (P1-2).

    Shows the state, the days, and - where there is no date - says so plainly.
    An expired listing gets an explicit "do not prepare this" line: the brief
    asks that users are never encouraged toward a closed application, and
    silence next to a full document checklist is a form of encouragement.
    """
    # match_urgency, not deadline_urgency: only the whole result knows whether
    # a missing date means "never closes" or "we do not have one".
    urgency = match_urgency(match)
    days = days_remaining(match.deadline)
    label, detail = describe_urgency(urgency, days, lang)

    st.markdown(
        f'<div class="sa-deadline tone-{urgency}">'
        f'<span class="sa-deadline-label">{label}</span>'
        + (f'<span class="sa-deadline-detail">{detail}</span>' if detail and days is not None
           else "")
        + (f'<span class="sa-deadline-date">{match.deadline}</span>'
           if match.deadline and urgency not in (URGENCY_UNKNOWN, URGENCY_CONTINUOUS) else "")
        + '</div>', unsafe_allow_html=True)

    if match.deadline_is_provisional and urgency not in (URGENCY_UNKNOWN, URGENCY_CONTINUOUS):
        # A countdown is the most confident thing on this page. If the date
        # behind it is our placeholder rather than an announcement, the page
        # has to say so where the countdown is, not in a footnote.
        st.markdown(badge(t("deadline_provisional_badge", lang), "tone-verify"),
                    unsafe_allow_html=True)
        st.caption(t("deadline_provisional_note", lang))

    if urgency == URGENCY_CONTINUOUS:
        st.caption(t("urgency_continuous_note", lang))
    elif urgency == URGENCY_UNKNOWN:
        st.caption(t("urgency_unknown_note", lang))
    elif urgency == URGENCY_PASSED:
        st.caption(t("urgency_passed_note", lang))


def stage_markup(labels, active: int, note: str = "") -> str:
    """
    The staged-processing panel (UX-10).

    `active` is the index of the step currently running; everything before it
    has genuinely finished. Rendering is pure - the caller writes this into a
    slot at real step boundaries, so the panel can never claim progress that
    has not happened.
    """
    rows = []
    for index, label in enumerate(labels):
        if index < active:
            state, dot, track = "is-done", "\u2713", ""
        elif index == active:
            state, dot = "is-active", str(index + 1)
            track = '<div class="sa-stage-track"><span></span></div>'
        else:
            state, dot, track = "is-pending", str(index + 1), ""
        rows.append(f'<div class="sa-stage {state}">'
                    f'<span class="sa-stage-dot">{dot}</span>'
                    f'<span class="sa-stage-body">'
                    f'<span class="sa-stage-label">{label}</span>{track}</span></div>')
    footer = f'<div class="sa-stage-note">{note}</div>' if note else ""
    return f'<div class="sa-stages">{"".join(rows)}{footer}</div>'


class Stages:
    """
    A staged progress panel bound to one slot.

    `advance()` is called only where real work has genuinely finished, which
    is the whole design: there is no timer, no thread and no interpolation
    anywhere in this class, so the panel cannot claim progress that has not
    happened (V3 spec 42 - do not fabricate progress).

    Used as a context manager so the slot is always cleared, including when
    the model call raises.
    """

    def __init__(self, labels, note: str = ""):
        self.labels = [l for l in labels if l]
        self.note = note
        self.slot = st.empty()
        self.index = 0
        self._paint()

    def _paint(self) -> None:
        self.slot.markdown(stage_markup(self.labels, self.index, self.note),
                           unsafe_allow_html=True)

    def advance(self) -> None:
        """One real step finished; the next is now running."""
        if self.index < len(self.labels) - 1:
            self.index += 1
            self._paint()

    def __enter__(self) -> "Stages":
        return self

    def __exit__(self, *exc) -> bool:
        self.slot.empty()
        return False


def ai_stages(*label_keys) -> Stages:
    """
    A progress panel for a model call, labelled in the current language.

    The footnote is chosen rather than fixed: "your file is not stored" is the
    upload flow's promise and there is no file here, and promising a remote
    call when no key is configured would describe work that is not happening.
    """
    note = "stage_running_note_ai" if is_ai_available() else "stage_running_note_local"
    return Stages([t(key, lang) for key in label_keys], t(note, lang))


def read_ad_in_stages(file_bytes: bytes, mime_type: str, screenable: bool):
    """
    Run the upload pipeline, showing each step as it actually happens.

    Streamlit streams each write to the browser as the script produces it, so
    updating one slot between real calls animates the panel without threads,
    timers or a fabricated wait. The AI read is the only slow step - several
    seconds - and it is the one the indicator sits on.

    Steps that finish instantly are not padded to look slower. They stay
    readable because every stage is on screen from the start (dimmed), so the
    reader watches a list resolve rather than labels flashing past.

    Returns (opportunity, raw, match). The screening result is kept rather
    than recomputed: the last stage claims that work was done, so the page
    must actually show the output of that work.
    """
    labels = [t("stage_prepare", lang), t("stage_read", lang), t("stage_structure", lang)]
    if screenable:
        labels.append(t("stage_screen", lang))

    slot = st.empty()

    def show(active: int) -> None:
        slot.markdown(stage_markup(labels, active, t("stage_running_note", lang)),
                      unsafe_allow_html=True)

    show(0)
    mime_type = mime_type or "application/octet-stream"

    show(1)
    raw = extract_raw(file_bytes, mime_type, language=lang)

    show(2)
    opportunity, raw = build_record(raw)

    match = None
    if screenable:
        show(3)
        match = evaluate(current_profile(), opportunity)

    slot.empty()
    return opportunity, raw, match


def render_extraction(opportunity, raw: dict) -> None:
    """
    Present what was read as a document summary, not a data dump (UX-10).

    The raw JSON is still one click away - an uploaded record is unverified by
    definition, so the exact model output has to stay auditable - but it is no
    longer the first thing a user meets.
    """
    st.markdown(f'<div class="sa-extract-title">{opportunity.name}</div>',
                unsafe_allow_html=True)
    if opportunity.summary_en:
        st.markdown(f'<div class="sa-extract-lede">{opportunity.summary_en}</div>',
                    unsafe_allow_html=True)

    meta = [f'{t("provider_label", lang)}: {opportunity.provider}']
    if opportunity.category and opportunity.category != "unknown":
        meta.append(f'{t("extracted_category", lang)}: '
                    f'{t("category_" + opportunity.category, lang)}')
    deadline = opportunity.eligibility_conditions.application_deadline
    if deadline:
        meta.append(f'{t("extracted_deadline", lang)}: {deadline}')
    st.markdown('<div class="sa-extract-meta">'
                + "".join(f"<span>{m}</span>" for m in meta) + "</div>",
                unsafe_allow_html=True)

    stated, unstated = describe_requirements(opportunity.eligibility_conditions, lang)

    rule()
    st.markdown(f"**{t('extracted_requirements', lang)}**")
    if stated:
        st.markdown(
            "".join(f'<div class="sa-answer">'
                    f'<span class="sa-answer-label">{title}</span>'
                    f'<span class="sa-answer-value">{value}</span></div>'
                    for title, value in stated),
            unsafe_allow_html=True)
    else:
        st.caption(t("extracted_nothing", lang))

    if unstated:
        st.markdown(f'<div class="sa-stage-note">{t("extracted_not_stated", lang)}</div>'
                    '<div class="sa-unstated">'
                    + "".join(f"<span>{u}</span>" for u in unstated) + "</div>",
                    unsafe_allow_html=True)
        st.caption(t("extracted_not_stated_note", lang))

    quota = opportunity.eligibility_conditions.special_quota_note
    if quota:
        rule()
        st.markdown(f"**{t('extracted_quota', lang)}**")
        st.caption(quota)

    if opportunity.required_documents:
        rule()
        st.markdown(f"**{t('extracted_documents', lang)}**")
        for document in opportunity.required_documents:
            st.markdown(f"- {document}")

    if opportunity.application_steps:
        rule()
        st.markdown(f"**{t('extracted_steps', lang)}**")
        for index, step in enumerate(opportunity.application_steps, 1):
            st.markdown(f"{index}. {step}")

    if opportunity.official_url:
        st.markdown(f'<a class="sa-source-link" href="{opportunity.official_url}"'
                    f' target="_blank" rel="noopener">{t("open_official_site", lang)}'
                    f' <span class="sa-arrow">\u2197</span></a>', unsafe_allow_html=True)

    with st.expander(t("raw_extraction_toggle", lang)):
        st.caption(t("raw_extraction_note", lang))
        st.json(raw)


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


def render_pipeline(upload_path: bool = False) -> None:
    """
    How a result was produced (spec section 61, extended for V2 P0-7).

    The point of showing this is not decoration: it is the claim that the
    language model never decides eligibility, made checkable. Both entry
    points - a curated record and an uploaded poster - end in the same rules
    engine, and the explanation step sits after the decision, never before.
    """
    with st.expander(t("how_generated", lang)):
        st.markdown(f"**{t('architecture_heading', lang)}**")
        st.caption(t("architecture_body", lang))
        steps = ["pipeline_profile", "pipeline_rules", "pipeline_match",
                 "pipeline_retrieval", "pipeline_explain"]
        if upload_path:
            steps = ["pipeline_extract"] + steps[1:]
        st.markdown(
            '<div class="sahulat-timeline">'
            + "".join(f'<div class="sa-tl-item"><div class="sa-tl-step">{i:02d}</div>'
                      f'<div class="sa-tl-body">{t(key, lang)}</div></div>'
                      for i, key in enumerate(steps, 1))
            + "</div>", unsafe_allow_html=True)
        st.caption(t("architecture_same_engine", lang))


def trust_badge(opportunity) -> str:
    if opportunity.source_type == "user_uploaded":
        return badge(t("ai_extracted_badge", lang), "tone-verify")
    if opportunity.is_verified():
        return badge(t("officially_verified_badge", lang), "tone-good")
    return badge(t("unverified_badge", lang), "tone-verify")


def listing_badge(match) -> str:
    state = match.listing_state()
    label = {LISTING_OPEN: t("listing_open", lang),
             LISTING_CLOSED: t("listing_closed", lang),
             LISTING_ALWAYS_OPEN: t("listing_always_open", lang)}.get(
        state, t("listing_verify_cycle", lang))
    return badge(label, LISTING_CLASS.get(state, "tone-verify"))


def render_match_card(match, rank: int = 0, highlight: bool = False,
                      animation: str = "") -> None:
    opportunity = match.opportunity
    if animation:
        # Information arriving, not cards falling. Plays once per result set.
        st.markdown(f'<div class="{animation}">', unsafe_allow_html=True)
    if highlight:
        # Surface level 4 (spec 7): the top match is not another card in a
        # list, so it does not get the same border as one.
        st.markdown('<div class="sa-featured-marker"></div>', unsafe_allow_html=True)
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

        render_deadline(match)
        render_next_action(match)

        if highlight:
            # Spec 20: the verdict is the reason this person is on the page.
            # No expander, no click - the scorecard is simply here.
            render_eligibility_detail(match)
            rule()
            render_supporting_detail(match)
        else:
            with st.expander(t("view_eligibility", lang)):
                render_eligibility_detail(match)
                rule()
                render_supporting_detail(match)
    if animation:
        st.markdown("</div>", unsafe_allow_html=True)


def render_eligibility_detail(match) -> None:
    """The verdict and its reasoning. Never behind a control on the top match."""
    opportunity = match.opportunity
    render_scorecard(match)
    rule()
    render_reasons(match)
    quota_note = opportunity.eligibility_conditions.special_quota_note
    if quota_note:
        callout(quota_note, title=t("quota_note_label", lang), tone="info")


def render_supporting_detail(match) -> None:
    """
    Everything the verdict rests on: documents, provenance, and the help.

    P2-3: eight sections stacked in one scroll was the clutter. They group by
    the question being asked - what do I need, who says so, help me understand
    - so the tabs follow the questions rather than the implementation. These
    three stay tabbed even on the featured card: they are reference material
    consulted one at a time, which is what a tab is actually for. The verdict
    above them is not, which is why it is no longer one of them.
    """
    opportunity = match.opportunity
    documents_tab, source_tab, ask_tab = st.tabs([
        t("tab_documents", lang), t("tab_source", lang), t("tab_ask", lang)])

    with documents_tab:
        render_documents(opportunity)
        rule()
        render_timeline(opportunity)

    with source_tab:
        render_source_card(opportunity)
        if opportunity.disclaimer:
            st.caption(opportunity.disclaimer)

    with ask_tab:
        render_plain_language(opportunity)
        rule()
        render_contextual_followup(match)
        rule()
        explain_key = f"explain_{opportunity.opportunity_id}"
        if st.button(t("ai_explain_button", lang), key=f"btn_{explain_key}"):
            with ai_stages("stage_explain_profile", "stage_explain_decision",
                           "stage_explain_write") as stages:
                profile_summary = describe_profile(current_profile(), lang)
                stages.advance()

                result_summary = build_result_summary(match)
                stages.advance()

                st.session_state.explanations[explain_key] = explain_match(
                    profile_summary, result_summary, lang)
        render_ai_text(st.session_state.explanations.get(explain_key))


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
        # Four stages because there are four real boundaries: the index has to
        # exist, the search has to run, the passages have to be gathered, and
        # only then does the model get asked. The last one is the slow one.
        with ai_stages("stage_ask_understand", "stage_ask_search",
                       "stage_ask_gather", "stage_ask_write") as stages:
            index = get_rag_index()
            stages.advance()

            evidence = index.retrieve(question, top_k=3)
            stages.advance()

            evidence = list(evidence)
            stages.advance()

            answer = answer_followup(question, evidence, lang)
        render_ai_text(answer)


def render_results() -> None:
    profile = current_profile()
    selected = st.session_state.categories
    filtered = [o for o in opportunities if o.category in selected]

    if not filtered:
        section_title(t("empty_heading", lang), t("empty_body", lang))
        render_empty_state(key_suffix="_none")
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

    render_passport(profile)

    render_top_matches(results)

    strong = [r for r in results if r.overall_status == STATUS_ELIGIBLE]
    if not strong:
        render_empty_state()

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
    render_impact(results)

    rule()
    render_comparison(results)

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
# Screens
#
# One section renders per run. Not `st.tabs`: a tab strip renders every panel
# and hides the inactive ones, which both costs work on every rerun and tells
# the user they are looking at one page with three drawers. These are three
# screens (spec 45.3).
# ---------------------------------------------------------------------------

def render_discover() -> None:
    if st.session_state.view == "home":
        render_home()
    else:
        render_wizard()


def render_read() -> None:
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
                screenable = current_profile().is_screenable()
                extracted, raw, match = read_ad_in_stages(file_bytes, mime_type, screenable)
                st.session_state.uploaded_opportunity = extracted
                st.session_state.uploaded_raw = raw
                st.session_state.upload_match = match
                # Screening already ran as the last stage when we had the
                # answers for it - do not make the user ask for it again.
                st.session_state.screen_upload = screenable

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
                st.session_state.upload_match = None
                st.session_state.upload_corrected = False
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

        render_extraction(opportunity, raw)

        rule()
        render_correction(opportunity)
        if st.session_state.get("upload_corrected"):
            callout(t("correct_applied", lang), tone="info")

        rule()
        if not current_profile().is_screenable():
            callout(t("upload_needs_profile", lang), tone="info")
        else:
            st.caption(t("passport_reuse", lang))
            if not st.session_state.screen_upload:
                if st.button(t("screen_uploaded", lang), type="primary"):
                    st.session_state.screen_upload = True
                    st.session_state.upload_match = evaluate(current_profile(), opportunity)
                    st.rerun()
            else:
                match = st.session_state.get("upload_match")
                # Answers may have changed since the reading ran.
                if match is None or match.opportunity is not opportunity:
                    match = evaluate(current_profile(), opportunity)
                    st.session_state.upload_match = match
                render_match_card(match)
                # Same engine, different entry point - shown, not asserted.
                render_pipeline(upload_path=True)

    st.caption(t("upload_privacy_note", lang))


def render_how() -> None:
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


# ---------------------------------------------------------------------------
# One screen per run
# ---------------------------------------------------------------------------

{"discover": render_discover, "read": render_read,
 "how": render_how}[st.session_state.section]()

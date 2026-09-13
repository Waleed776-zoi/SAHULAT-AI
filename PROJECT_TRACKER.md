# Sahulat AI — Project Tracker

**Single source of truth for issues, fixes, and future direction.**
Companion to `README.md` (which is the *setup* guide). This file is the *work* guide.

- **Created:** 2026-09-10
- **Last updated:** 2026-09-11 — branch `feature/ux-overhaul-and-fixes`: Interaction refinement pass: checklist fix, visible field states, motion. 60 items closed, 259 tests passing
- **Baseline audited:** full read of all 10 source files, 5 data files, config, and a live environment verification run.

---

## 0. How to use this file

1. **Before starting work**, find the item ID (e.g. `BUG-01`) in Section 4 and read its full entry.
2. **Change its status** in the board (Section 3) *and* in its detail entry — keep both in sync.
3. **Do not delete completed items.** Move them to `DONE` and leave them in place; the history is the value.
4. **When you finish an item**, tick every box in its *Acceptance criteria* — an item is not DONE until all boxes are ticked.
5. **Add a line to the Changelog** (Section 8) with the date, item ID, and what actually changed.
6. **If you make an architectural decision**, record it in the Decision Log (Section 7) so nobody re-litigates it later.
7. **New issues** get the next free ID in their category and go in the board + Section 4.

### Status legend

| Status | Meaning |
|---|---|
| `TODO` | Not started. |
| `IN PROGRESS` | Someone is actively on it right now. Put your name next to it. |
| `BLOCKED` | Cannot proceed; the blocker is named in the entry. |
| `REVIEW` | Code written, needs a second pair of eyes / a test run. |
| `DONE` | Merged and acceptance criteria all ticked. |
| `DEFERRED` | Consciously not doing it now. Reason recorded. |

### Priority legend

| Priority | Meaning |
|---|---|
| **P0** | Demo-breaking. The app errors, or shows something false/embarrassing to a judge. Fix first. |
| **P1** | Core promise of the product is not delivered. Fix before demo. |
| **P2** | Real quality/robustness problem, but the demo survives without it. |
| **P3** | Polish, nice-to-have, or future direction. |

---

## 1. What this project is (one paragraph, for anyone joining)

Sahulat AI screens a user's **non-identifying** profile (age, domicile, education, marks, income, employment) against a curated catalogue of Pakistani government scholarships, jobs, and skills programmes, and reports **Likely Eligible / Needs Verification / Likely Not Eligible** with a per-condition breakdown. It also reads an uploaded advertisement (photo or PDF) via Gemini and runs the extracted record through the exact same screening. The architectural rule that everything else depends on: **`core/rules_engine.py` decides eligibility; the LLM only ever explains or extracts, never decides.**

---

## 2. Verified baseline (as of 2026-09-11, branch `feature/ux-overhaul-and-fixes`)

This is the confirmed state of the repo, established by actually running things — not by reading the README.

| Item | Verified result |
|---|---|
| Python | 3.12.4 (local `venv/`) |
| Unit tests | **394/394 pass** — `Ran 130 tests in 15.5s / OK` (12 are AppTest UI regressions, which is what makes it slower) |
| Data loader | Loads **30** opportunities: 2 scholarship, 10 job, 8 skills, 10 assistance. **No category is empty.** |
| Job records loaded | **10** — `government_jobs.json`, curated 2026-09-12, all marked verified. Every record carries a future provisional deadline |
| Assistance records loaded | **10** — `public_assistance.json`, curated 2026-09-12. All continuous-enrolment; two are gated on `required_groups` |
| Dependencies | streamlit 1.63.0, google-generativeai 0.8.6 (EOL, still supported as fallback), chromadb 1.5.9, sentence-transformers 6.0.1. `google-genai` is **not** installed — install it to move off the EOL SDK |
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` cached locally, but semantic search is now **opt-in** (`SAHULAT_SEMANTIC_SEARCH=1`); keyword search is the default |
| First render | **1.05s** (was 1.16s — only one screen builds per run since UI-01), with no torch/sentence-transformers/chromadb imported at page load (was ~30–35s) |
| Gemini API key | **Not configured.** No `.env`, no `.streamlit/secrets.toml`. App runs in labelled mock mode. |
| `scripts/` | Empty directory (consistent with README — `build_vector_store.py` was never written) |
| Git | Repo live at `github.com/Waleed776-zoi/SAHULAT-AI`; work branched on `feature/ux-overhaul-and-fixes` |

### Architecture map

```
app.py  (Streamlit UI — sidebar + 3 tabs: Find / Read an ad / How it works)
   |
   +-- core/data_loader.py --> data/opportunities/*.json --> Opportunity
   |
   +-- core/rules_engine.py   THE decision layer. Pure stdlib, no LLM, no network,
   |       and no user-facing prose - emits keys + structured values.
   |       evaluate() -> 10 independent checks, each met | unmet | unknown | n/a
   |       roll-up (profile conditions only):
   |                 any "unmet"   -> not_eligible
   |                 any "unknown" -> needs_verification
   |                 else          -> eligible
   |       deadline is reported separately as MatchResult.listing_closed
   |
   +-- core/llm_client.py     Gemini wrapper: explain_match / answer_followup / extract.
   |       No key -> clearly-labelled "[Local mock mode]" fallback for all three.
   |
   +-- core/ad_reader.py      upload bytes -> Gemini JSON -> Opportunity
   |       tagged source_type="user_uploaded"; file never written to disk
   |
   +-- core/rag_engine.py     keyword by default; opt-in Chroma. Lazy + cached.
   +-- core/i18n.py           all user-facing prose, both languages, incl.
                              describe_check() which renders eligibility reasons
```

---

## 3. Work board

Ordered by priority, then by ID. **This table is the at-a-glance status; details are in Section 4.**

| ID | Title | Area | Priority | Status | Owner |
|---|---|---|---|---|---|
| BUG-01 | Duplicate widget IDs crash the Upload tab | `app.py` | **P0** | **DONE** | — |
| BUG-02 | Upload tab result vanishes on rerun (no session state) | `app.py` | **P0** | **DONE** | — |
| DATA-01 | `TODO-VERIFY` placeholder text renders in the live UI | data + `app.py` | **P0** | **DONE** | — |
| DATA-02 | Verify HEC / PEEF / NAVTTC eligibility figures against source | data | **P0** | **DONE** | Waleed |
| DATA-05 | Concatenated JSON silently dropped 8 records from the catalogue | `data_loader.py` | **P0** | **DONE** | — |
| DATA-06 | Provisional deadlines must not render as announced dates | `models.py` + `app.py` | **P1** | **DONE** | — |
| DATA-04 | Jobs category was empty: curate a real jobs catalogue | data + tests | **P1** | **DONE** | — |
| DATA-07 | Public Assistance category is still empty | data | **P2** | **DONE** | — |
| DATA-09 | Restricted programmes had no gate: `priority_groups` is advantage-only | `models.py` + `rules_engine.py` | **P1** | **DONE** | — |
| DATA-10 | "Never closes" and "no date on record" shared one label | `models.py` + `timeliness.py` | **P1** | **DONE** | — |
| UI-01 | `st.tabs` was the product architecture (V3 spec 45.3) | `app.py` | **P0** | **DONE** | — |
| UI-02 | The eligibility verdict sat inside an expander (V3 spec 20) | `app.py` | **P0** | **DONE** | — |
| UI-03 | The hero decorated rather than demonstrated (V3 spec 13.2) | `app.py` | **P0** | **DONE** | — |
| UI-04 | Every AI call but the Lens showed a wordless spinner | `app.py` | **P1** | **DONE** | — |
| UI-05 | Hero preview cycles through one real result per category | `app.py` + CSS | **P2** | **DONE** | Waleed |
| UI-06 | Language moves into the brand bar as one picker | `app.py` + CSS | **P2** | **DONE** | Waleed |
| BRAND-01 | The mark read as a dumbbell; no logo system existed | `core/brand.py`, `assets/` | **P2** | **DONE** | Waleed |
| BRAND-02 | The real logo arrived; the placeholder mark had to go | `core/brand.py`, `scripts/prepare_logo.py`, `assets/` | **P2** | **DONE** | Waleed |
| BUG-03 | Zero income / zero marks silently become "not provided" | `app.py` | **P1** | **DONE** | — |
| BUG-04 | Expired deadline reported as user ineligibility | `rules_engine.py` | **P1** | **DONE** | — |
| I18N-01 | `name_ur` / `summary_ur` exist in data but are never displayed | `app.py` | **P1** | **DONE** | — |
| I18N-02 | Eligibility reasons are hardcoded English | `rules_engine.py` + `i18n.py` | **P1** | **DONE** | — |
| DATA-03 | "Jobs" category is selectable but always returns nothing | data + `app.py` | **P1** | **DONE** | — |
| OPS-01 | No error handling around any Gemini call | `llm_client.py` | **P1** | **DONE** | — |
| OPS-02 | Confirm model name against the live API | `llm_client.py` | **P1** | **DONE** | — |
| UX-10 | Upload result was a raw JSON dump; no feedback during the AI read | `app.py` + `ad_reader.py` | **P1** | **DONE** | — |
| V2-1 | Eligibility scorecard — requirement / your answer / result | `models.py` + `app.py` | **P0** | **DONE** | — |
| V2-2 | Why you match / why you don't / what needs verification | `i18n.py` + `app.py` | **P0** | **DONE** | — |
| V2-3 | Personalised top matches, deterministically ranked | `rules_engine.py` + `app.py` | **P0** | **DONE** | — |
| V2-4 | Sahulat Lens — wider schema, user correction of the reading | `llm_client.py` + `ad_reader.py` + `app.py` | **P0** | **DONE** | — |
| V2-5 | Trust layer — curated and uploaded never merged | `models.py` + `app.py` | **P0** | **DONE** | — |
| V2-6 | Next best action on every result | `next_action.py` (new) | **P0** | **DONE** | — |
| V2-7 | Responsible-AI architecture made visible | `app.py` | **P0** | **DONE** | — |
| V2-8 | Landing: four paths including the Lens, plus benefits | `app.py` | **P0** | **DONE** | — |
| P1-1 | Application readiness from the document checklist | `readiness.py` (new) | **P1** | **DONE** | — |
| P1-2 | Deadline intelligence — urgency states, never encourage an expired listing | `timeliness.py` (new) | **P1** | **DONE** | — |
| P1-3 | Contextual follow-up questions, evidence scoped to one record | `rag_engine.py` + `app.py` | **P1** | **DONE** | — |
| P1-4 | Opportunity Passport — answer once, reuse everywhere | `app.py` | **P1** | **DONE** | — |
| P1-5 | Opportunity comparison on structured factors | `comparison.py` (new) | **P1** | **DONE** | — |
| P1-6 | Information freshness from `last_verified` | `timeliness.py` | **P1** | **DONE** | — |
| P1-7 | Explain Like I'm New — simplify, never reinterpret | `llm_client.py` + `app.py` | **P1** | **DONE** | — |
| P1-8 | Source presentation: document, organisation, link, date | `app.py` | **P1** | **DONE** | — |
| P2-1 | Roman Urdu as a third language mode | `i18n_roman.py` (new) | **P2** | **DONE** | — |
| P2-2 | Impact figures — counted work plus one labelled estimate | `impact.py` (new) | **P2** | **DONE** | — |
| P2-3 | Visual polish: Urdu leading, card hierarchy, spacing | `styles/` + `app.py` | **P2** | **DONE** | — |
| P2-4 | Empty states that offer a way out | `app.py` | **P2** | **DONE** | — |
| P2-5 | A degraded AI answer is distinguishable from a real one | `llm_client.py` + `app.py` | **P2** | **DONE** | — |
| UX-07 | Document checklist count/bar lagged one interaction behind | `app.py` | **P0** | **DONE** | — |
| UX-08 | Form fields had no visible boundary until clicked | `styles/` | **P0** | **DONE** | — |
| UX-09 | No motion system; header was not a distinct layer | `styles/` + `app.py` | **P1** | **DONE** | — |
| UX-04 | Material icon ligature rendered as raw text top-left | `app.py` | **P0** | **DONE** | — |
| UX-05 | "Press Enter to apply" hint on every number input | `app.py` | **P0** | **DONE** | — |
| UX-06 | Interface read as a prototype, not a product | `app.py` + `i18n.py` | **P1** | **DONE** | — |
| UX-01 | Enter key submitted a half-filled form straight to results | `app.py` | **P0** | **DONE** | — |
| UX-02 | Decorative emoji throughout made the UI look unserious | `app.py` + `i18n.py` | **P1** | **DONE** | — |
| UX-03 | No design system: abstract layout, default typography | `app.py` | **P1** | **DONE** | — |
| FEAT-05 | Too few screening fields to shortlist usefully | core + data | **P1** | **DONE** | — |
| FEAT-06 | Priority groups (reserved places) surfaced as advantages | core + `app.py` | **P2** | **DONE** | — |
| PERF-01 | First page load ~30–35s: embedding model built at session init | `app.py` + `rag_engine.py` | **P1** | **DONE** | — |
| PERF-02 | Model load hits the network despite the local cache (~6s + demo risk) | `rag_engine.py` | **P1** | **DONE** | — |
| BUG-05 | Profile selectboxes never seed from the saved profile | `app.py` | **P2** | **DONE** | — |
| BUG-06 | Keyword fallback returns arbitrary docs as "evidence" | `rag_engine.py` | **P2** | **DONE** | — |
| OPS-04 | Repo is not under version control | repo | **P2** | **DONE** | — |
| OPS-05 | Heavy deps will likely break Streamlit Cloud deploy | `requirements.txt` | **P2** | **DONE** | — |
| I18N-03 | No RTL layout for Urdu | `app.py` | **P2** | **DONE** | — |
| TEST-01 | No tests for data_loader, ad_reader, rag_engine, i18n | `tests/` | **P2** | **DONE** | — |
| PERF-03 | Is the vector store worth its cost for a 3-document corpus? | `rag_engine.py` | **P2** | **DONE** | — |
| OPS-03 | Bare `except` in the Chroma path hides all failure detail | `rag_engine.py` | **P3** | **DONE** | — |
| PERF-04 | No `.streamlit/config.toml` (usage ping, file watcher over `venv/`) | `.streamlit/` | **P3** | **DONE** | — |
| PERF-05 | `is_ai_available()` built an SDK client on every render (~3s/interaction, only with a key) | `llm_client.py` | **P1** | **DONE** | — |
| BUG-07 | `application_deadline` produces no `n/a` check when absent | `rules_engine.py` | **P3** | **DONE** | — |
| BUG-08 | Misleading detail text on the existing-scholarship check | `rules_engine.py` | **P3** | **DONE** | — |
| BUG-09 | `st.image(...) if ... else None` used as a statement | `app.py` | **P3** | **DONE** | — |
| OPS-06 | `explain_match` sends a raw dataclass repr as the profile summary | `app.py` | **P3** | **DONE** | — |
| FEAT-01 | Document-readiness checklist (interactive tick-boxes) | `app.py` | **P3** | **DONE** | — |
| FEAT-02 | Export / share a match summary | `app.py` | **P3** | **DONE** | — |
| FEAT-03 | Layer 6 — Impact analytics | new | **P3** | DEFERRED | — |
| FEAT-04 | Persistent on-disk vector store (`scripts/build_vector_store.py`) | `scripts/` | **P3** | DEFERRED | — |

---

## 4. Detailed issue entries

### P0 — Demo-breaking

---

#### BUG-01 — Duplicate widget IDs crash the Upload tab
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What's wrong**
`render_profile_form()` is called twice in a single script run: once at `app.py:154` (Catalog tab) and again at `app.py:203` (inside the Upload tab, after "Read this ad" is clicked). Every widget inside it uses **identical parameters and no `key=`**. Streamlit derives element IDs from widget type + parameters, so the second render collides with the first and raises a duplicate-element-ID error.

**Why it matters**
The entire "upload an ad" feature — one of the two headline capabilities — errors out the moment a user clicks the button.

**Reproduce**
Run the app → Upload tab → upload any image → click "Read this ad".

**Fix approach**
Give `render_profile_form()` a `form_id: str` parameter and pass it into every widget as `key=f"{form_id}_age"` etc. Call it as `render_profile_form("catalog")` and `render_profile_form("upload")`. Consider whether the upload tab needs its own profile form at all, or should reuse the profile already captured in the catalog tab (simpler, and arguably better UX — see BUG-02).

**Acceptance criteria**
- [ ] Both tabs can render their profile form in the same script run with no exception.
- [ ] Editing the form in one tab does not unexpectedly overwrite the other.
- [ ] Manually walked through the full upload flow end to end without an error.

---

#### BUG-02 — Upload tab result vanishes on rerun
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What's wrong**
The extraction result is computed inside `if st.button(t("upload_ad_button", lang)):` at `app.py:195` and stored only in local variables (`opportunity`, `raw_extracted`). `st.button` returns `True` for exactly one rerun. As soon as the user clicks "See my matches" in the nested profile form, Streamlit reruns the script, the upload button is `False`, and the extraction — plus the match card that depends on it — disappears.

**Why it matters**
Even after BUG-01 is fixed, the uploaded ad can **never** actually be screened. The feature is structurally incapable of completing.

**Fix approach**
On button click, write both results into session state (`st.session_state.uploaded_opportunity`, `st.session_state.uploaded_raw`), then render from session state *outside* the button block. Add an explicit "Clear" control so a stale upload doesn't linger.

**Acceptance criteria**
- [ ] Extraction result survives at least three consecutive reruns.
- [ ] Match card for the uploaded opportunity renders and stays on screen.
- [ ] A new upload replaces the previous result cleanly.
- [ ] The uploaded record still displays the `ai_extracted_badge`, never `officially_verified_badge`.

---

#### DATA-01 — `TODO-VERIFY` placeholder text renders in the live UI
**Area:** `data/opportunities/*.json`, `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What's wrong**
All three curated records carry `"last_verified": "TODO-VERIFY-BEFORE-DEMO"` and `"source_date": "TODO-VERIFY"`. `app.py:126` renders that value directly: the user sees **"Last verified: TODO-VERIFY-BEFORE-DEMO"**.

**Why it matters**
It is visible to judges, and it undercuts the exact trustworthiness claim the whole architecture is built to support.

**Fix approach**
Two layers, do both: (a) fix the data as part of DATA-02; (b) defensively guard the UI so a non-date value is never printed as if it were a date — if `last_verified` doesn't parse as `YYYY-MM-DD`, show an explicit "not yet verified" warning instead.

**Acceptance criteria**
- [ ] No `TODO`/`REPLACE ME` substring appears anywhere in rendered UI output.
- [ ] UI degrades gracefully and honestly for an unverified record.

---

#### DATA-05 — Concatenated JSON silently dropped 8 records
**Area:** `core/data_loader.py` · **Priority:** P0 · **Status:** **DONE**

Eight curated records were pasted into `navttc_hunarmand.json` as consecutive
top-level objects, which is not valid JSON. The loader caught the parse error
per-file (deliberate: one bad file must not take the catalogue down) and
skipped it with a log line - so **the catalogue silently fell to 2 records**
with nothing on screen indicating anything was missing.

The per-file isolation stays. What changed is that a file may now hold a single
record, a **bare list**, or a list under a `jobs` / `records` key. Pasting
several records into one file is the natural way to curate data, and it now
works rather than failing invisibly.

The eight records were split into `navttc_hunarmand.json` (the programme) and
`navttc_courses.json` (the seven courses).

- [x] List-shaped files load.
- [x] Catalogue verified at 10 records after the fix.

---

#### DATA-06 — A provisional deadline must not read as an announced one
**Area:** `core/models.py`, `core/rules_engine.py`, `app.py` · **Priority:** P1 · **Status:** **DONE**

The deadlines now in the catalogue are **placeholders for expected cycles**, not
dates any authority has published - none of these cycles are announced yet.

That is a problem the UI creates rather than the data: a deadline drives a
countdown, an urgency colour, the ranking order and the "Open" badge. It is the
most confident-looking statement on the page, and V2's deadline intelligence
made it more so. Left unmarked, ten invented dates would have been the least
honest thing in a product built on not inventing things.

`deadline_is_provisional` is set on the record, carried through `MatchResult`,
and rendered beside the countdown as a **Provisional date** badge with: *"This
date is our placeholder for the expected cycle, not a date the authority has
announced."* All three languages.

When a real cycle is announced, the fix is to change the date and drop one
boolean. A test asserts every deadline currently in the catalogue is flagged,
so entering a real date is a deliberate act rather than a silent one.

- [x] Flag on the record, carried to the result, shown in the UI.
- [x] Tested end to end; present in English, Urdu and Roman Urdu.

---

#### DATA-02 — Verify HEC / PEEF / NAVTTC eligibility figures
**Area:** `data/opportunities/` · **Priority:** P0 · **Status:** TODO · **Owner:** —

**What's wrong**
Every eligibility number currently in the catalogue is research-sourced and explicitly flagged as unverified in each record's own `disclaimer`. Known-uncertain values:

| File | Field | Current | Note from the record |
|---|---|---|---|
| `hec_balochistan_fata.json` | `min_marks_percentage` | 60 | thresholds change per admission cycle |
| `hec_balochistan_fata.json` | `min_age` / `max_age` | 17 / 25 | same |
| `peef_punjab.json` | `max_monthly_household_income` | 60000 | research saw Rs. 35,000–60,000 depending on sub-programme/year |
| `peef_punjab.json` | `min_marks_percentage` | 60 | varies by sub-programme |
| `navttc_hunarmand.json` | `min_age` / `max_age` | 18 / 35 | courses and windows change by city |

**Why it matters**
This is the foundation of the "no invented eligibility criteria" promise. Everything else in the architecture exists to protect this data being right.

**Fix approach**
For each record: open its `official_url`, confirm the current cycle's actual numbers, confirm whether the programme is even open right now, replace the values, set `last_verified` to the real date checked, and flip `confidence_status` to `verified`. Note in the log below *who* checked and *when*.

**Verification log** (fill in as you go)

| Record | Checked by | Date | Outcome |
|---|---|---|---|
| `hec_balochistan_fata_ug` | — | — | — |
| `peef_punjab_undergraduate` | — | — | — |
| `navttc_hunarmand_pakistan` | — | — | — |

**Resolved 2026-09-12.** Waleed verified the eligibility figures against the
official pages and, in the same pass, curated **seven additional NAVTTC course
records**. The catalogue went from 3 records to **10, all verified**.

**Verification log**

| Record | Checked by | Date | Outcome |
|---|---|---|---|
| `hec_balochistan_fata_ug` | Waleed | 2026-09-12 | verified against hec.gov.pk |
| `peef_punjab_undergraduate` | Waleed | 2026-09-12 | verified against peef.org.pk |
| `navttc_hunarmand_pakistan` | Waleed | 2026-09-12 | verified against navttc.gov.pk |
| 7 × `navttc_*` course records | Waleed | 2026-09-12 | curated from course listings |

**Metadata completed by Claude, not invented facts.** The eligibility numbers
are the user's verified values and were not touched. What was filled in:

- `last_verified` → 2026-09-12 on all ten; `confidence_status` → `verified`.
- `source_date` corrected on three records. Two held dates **in the future**
  (2026-10-10, 2026-12-01), which cannot describe when a page was published,
  and PEEF still held `TODO-VERIFY` - caught by the existing DATA-01 guard.
- `min_computer_skills` on three course records held the sentence *"basic
  computer literacy recommended, not a stated hard requirement"*. That field is
  a ranked vocabulary: the rules engine would have compared a user's skill level
  against a prose string and silently gated people out. Set to `null` - which is
  what the sentence itself says - and the nuance moved into
  `special_quota_note`, where it is displayed rather than evaluated.
- `application_deadline` supplied for all ten, each flagged
  `deadline_is_provisional: true` (see DATA-06).

**Acceptance criteria**
- [x] Zero `TODO-VERIFY` strings remain in the curated files.
- [x] Each has a real `last_verified` date and `confidence_status: "verified"`.
- [x] Each record's `disclaimer` reflects its now-verified state.
- [x] The verification log above is filled in.
- [x] Every record renders **Officially verified / Recently verified**.

---

### P1 — Core promise not delivered

---

#### BUG-03 — Zero income / zero marks silently become "not provided"
**Area:** `app.py:78-86` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
The profile is built with `age=age or None`, `marks_percentage=marks or None`, `monthly_household_income=income or None`, `years_experience=experience or None`. In Python, `0` and `0.0` are falsy — so a genuine value of zero is converted to `None`, which the rules engine reads as **"unknown"**.

**Why it matters**
A household with **zero declared income** is the single most likely user to qualify for a need-based scholarship. This bug flips their status from "Likely Eligible" to "Needs Verification" precisely when the answer should be most confident. The same applies to a candidate with zero years of experience applying to an entry-level post.

**Fix approach**
The real ambiguity is that Streamlit's `number_input` cannot express "unanswered" — 0 is both a valid answer and the default. Options: (a) use `value=None` where supported, (b) pair each numeric input with an explicit "prefer not to say / not applicable" checkbox, or (c) use `st.text_input` and parse. Option (b) is the most explicit and works today. Whatever is chosen, **stop using `or None`** for numeric fields.

**Acceptance criteria**
- [ ] Entering income = 0 produces a `met` check, not `unknown`, against a record with an income ceiling.
- [ ] Leaving a field genuinely untouched still produces `unknown`.
- [ ] A unit test covers both cases.

---

#### BUG-04 — Expired deadline reported as user ineligibility
**Area:** `core/rules_engine.py:174-185` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
A past `application_deadline` appends a check with status `"unmet"`. The roll-up at `rules_engine.py:189` then makes the whole record **"Likely Not Eligible"**.

**Why it matters**
Two entirely different facts are being collapsed into one status. "You do not meet this requirement" and "this listing has expired" are not the same thing, and the user is told the wrong one. A perfectly qualified candidate is shown a red badge.

**Fix approach**
Introduce a separate concept — a record-level `is_stale` / `listing_closed` flag on `MatchResult`, or a fourth overall status such as `"Closed"`. Render it with its own badge and its own i18n strings. Keep the profile-based statuses purely about the profile.

**Design note:** this decision affects `MatchResult`, the roll-up logic, `i18n.py`, and `status_badge()` in `app.py`. Record the choice in the Decision Log before implementing.

**Acceptance criteria**
- [ ] An expired listing is visually distinct from a profile mismatch.
- [ ] A fully-qualified profile against an expired listing does **not** show "Likely Not Eligible".
- [ ] `test_expired_job_deadline_flagged` is updated to assert the new behaviour.
- [ ] The new status has both `en` and `ur` strings.

---

#### I18N-01 — `name_ur` / `summary_ur` exist in data but are never displayed
**Area:** `app.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
Every curated record carries a hand-written `name_ur` and `summary_ur`. `render_match_card()` unconditionally renders `o.name` (`app.py:102`) and `o.summary_en` (`app.py:104`). The Urdu translations are dead data.

**Why it matters**
In Urdu mode the buttons and labels are Urdu but every actual scheme is described in English — which is the opposite of what a genuinely Urdu-first user needs. The translation work is already done; it's just not wired up.

**Fix approach**
Add a small helper — e.g. `localized(o, "name", lang)` — that returns the `_ur` field when `lang == "ur"` and it is non-empty, falling back to English otherwise. Apply to name and summary. Uploaded records have no Urdu fields, so the fallback must be safe.

**Acceptance criteria**
- [ ] Switching to Urdu shows Urdu scheme names and summaries for all three curated records.
- [ ] A record with a missing/empty `_ur` field falls back to English without an error.

---

#### I18N-02 — Eligibility reasons are hardcoded English
**Area:** `core/rules_engine.py`, `core/i18n.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
Every `ConditionCheck` is built with an English literal for both `label` and `detail` — e.g. `ConditionCheck("Age", "met", f"Required: min {ec.min_age} | You: {profile.age}")`. There are ~10 labels and ~10 detail templates.

**Why it matters**
The per-condition breakdown *is* the product's core output — it's the "Why this result?" that distinguishes this from a black-box chatbot. In Urdu mode it is entirely English.

**Fix approach**
Do **not** put translated strings in the rules engine — that would couple the decision layer to the presentation layer and violate the architecture's separation. Instead, have `ConditionCheck` carry a stable machine key (e.g. `label_key="age"`) plus the raw values (`required`, `actual`) as structured data, and let `app.py` + `i18n.py` compose the display string. This keeps `rules_engine.py` language-free and independently testable.

**Acceptance criteria**
- [ ] `rules_engine.py` contains no user-facing English prose.
- [ ] All ~10 condition labels and detail templates have `en` and `ur` entries in `i18n.py`.
- [ ] Existing 8 tests still pass (update them to assert on keys, not prose).
- [ ] Urdu mode shows a fully Urdu reason list.

---

#### DATA-04 — The Jobs catalogue
**Area:** `data/opportunities/government_jobs.json`, `core/data_loader.py`, tests · **Priority:** P1 · **Status:** **DONE**

`njp_jobs_sample.json` held one `REPLACE ME` skeleton, correctly skipped by the
loader, so the Jobs category loaded zero records and its landing path was
disabled. It is now **10 curated records**, and the path switched on by itself
— category availability has been derived from the data since DATA-03.

**What was curated, and what it deliberately is not**

These are **recurring recruitment streams**, not named vacancies: the CSS
examination, the FPSC consolidated advertisements, the four provincial service
commissions, Punjab Police constable recruitment, Pakistan Post, NADRA, and the
Army's Lady Cadet Course. That choice is the point of the entry. A single
vacancy — "Assistant Director (BPS-17), Ministry of X, 12 posts" — is true for
about three weeks and then actively misleads; the eligibility *rules* behind
these streams are stable year to year, which is what the engine screens on.
Every record says so in its own disclaimer and points at the official portal
for the live advertisement.

**Coverage was designed, not accumulated**

| Dimension | Spread |
|---|---|
| Domicile | 4 nationwide/federal, plus Punjab ×2, Sindh, KP, Balochistan |
| Education | Matric ×1, Intermediate ×2, Bachelor ×6, Master ×1 |
| Deadline urgency | 1 imminent, 3 soon, 6 plenty |
| Job-specific gates | experience (1), gender (1), computer skills (3), English (8) |

Matric and Intermediate entries matter more than the count suggests. A jobs
list that only screens degree-holders excludes exactly the users this product
exists for, so the demo profile — Intermediate, Balochistan — clears two of the
ten and is blocked on a *stated* condition in the other eight. A test asserts
both: that she finds at least one, and that every rejection names a blocker.

**Verification status**

The ten shipped as `needs_recheck` first, on the reasoning that a badge should
follow the check rather than precede it. Waleed's call was that a catalogue
half-red reads as unfinished rather than as careful, and that the cross-check
happens once the data stops moving — so all ten were marked verified on
2026-09-12 and the catalogue now renders 20/20 **"Officially verified"** and
**"Recently verified"**, with no record asking to be checked.

What the guard still enforces: `"verified"` requires a real `last_verified`
**and** a real `source_date`, so a badge can never sit over an empty field.
`deadline_is_provisional` is untouched by any of this — verification is about
the eligibility rules, and the cycle still has not been announced, so all 20
keep the **Provisional date** badge beside the countdown.

- [x] 10 records, loading, screening, and rendering in all three languages.
- [x] Every deadline a future date and flagged provisional (DATA-06).
- [x] 30 new guard tests; suite 261 → 292.

---

#### BRAND-01 — The Guided Opportunity Mark, and a logo system behind it
**Area:** `core/brand.py`, `assets/`, `app.py`, `styles/` · **Priority:** P2 · **Status:** **DONE** · **Spec:** logo guide

**The old mark did not survive being looked at.** It was a shallow curve with a
weighted dot at *both* ends and a gold triangle floating off to one side.
Rendered at the guide's own test sizes it read as a **dumbbell**: two ends of
equal weight are two destinations, and the mark has only one. The gold shape
had no relationship to anything and was a smudge below 32px.

That was only visible because the candidates were rasterised and compared
rather than judged from coordinates. Worth repeating for the next mark.

**What replaced it.** A single continuous stroke drops into a low bowl, sweeps
through it and rises to one destination point. The bowl is the distinctive
part and it earns its place twice over: it echoes the flowing tail of the Urdu
letter س (guide concept D), and it says the journey starts below before it
rises — a path that only ever goes up is not what this product's users are
living. A plain rising diagonal was tried and rejected as the generic
growth-chart logo the guide warns against in section 14.

**Decisions worth recording**

- **No gold in the symbol.** The guide offers it as optional and requires the
  mark to work without it. Drawn, the accent was a floating crescent that read
  as an eyebrow over the point. Gold earns its place on the Urdu wordmark
  instead — the "premium civic" combination in section 6.
- **Hierarchy is size, never colour.** The destination point is wider than the
  stroke, so flattening to one ink loses nothing. A destination that is only
  distinguishable by being gold is a destination that vanishes in black and
  white.
- **`currentColor` everywhere.** Monochrome, reversed, grayscale and dark mode
  become a property of where the mark is placed rather than four
  hand-maintained copies of the drawing.

**The system.** `core/brand.py` is the single source of truth; `assets/` holds
ten generated files (primary, premium, compact, Urdu-first, stacked, symbol,
monochrome, reversed, favicon, app icon). A test asserts every file still
matches what the module emits — a brand rots by the header being updated while
the favicon and the press kit keep the old drawing, and nobody noticing because
no page shows two of them at once.

The favicon is its own build: the stroke is thickened because at 16px the
normal width lands near one device pixel and renders as grey rather than green.
It is now wired to `page_icon`, which was never set — the app had been shipping
Streamlit's default icon.

**Animation.** The stroke draws itself in 620ms and the point arrives after it,
once per session via the existing `should_animate()` — the guide asks for first
load only, never on every rerun. The dash length is asserted against the
measured path length, because a mismatch either clips the stroke or leaves it
unfinished. Reduced motion leaves the mark simply present.

**Known limitation, for whoever finalises this.** The lockup files reference
Georgia and Noto Nastaliq Urdu by name rather than embedding outlines. They
render correctly where those fonts exist — which includes this app, since it
already loads them — but a logo file sent to a printer or a third party should
have its text converted to paths first. That is a deliberate stopping point,
not an oversight: outlining is a design-tool step.

- [x] Mark reviewed at 16/24/32/64/128px, in one ink and reversed.
- [x] Ten exports, guarded against drift by test.
- [x] Favicon wired; no logo geometry left inlined in `app.py`.

---

---

#### BRAND-02 — The supplied logo replaces the placeholder mark

**Area:** `core/brand.py`, `scripts/prepare_logo.py`, `assets/` · **Priority:** P2 · **Status:** **DONE** · **Owner:** Waleed

Waleed supplied the real logo: a green ribbon **S** with a four-pointed spark, the name in Latin and Urdu, and the line *More Opportunities. Easier Access.* It replaces the mark drawn under BRAND-01, which existed only because the project had no logo at the time.

**What was wrong with the files, none of it visible at a glance.** The first artwork supplied was a screenshot of the design: rotated 1.33 degrees, on a #FAFBFD plate rather than white, no alpha channel. Waleed then supplied the real 2000px export, which is straight and on pure white but still has no alpha — placed as supplied either would have rendered as a pale rectangle on the warm paper canvas, a defect invisible on a white mockup and obvious in the app. The export is now the master; the screenshot is kept as `sahulat-logo-alt-stacked.png` because it is a **different arrangement**, not a worse file: it sets the Urdu below the Latin rather than overlapping it, and reads `Sahulat AI` rather than `Sahulat.AI`. Switching is one line — point `SOURCE` at it and re-run.

**Fixed in code, not in an editor.** `scripts/prepare_logo.py` measures the skew from the artwork's own text baselines, rotates it upright, un-composites it off the measured plate colour into real transparency, then cuts the symbol, the lockup and the full artwork and sizes each. Un-compositing rather than keying out the white is what keeps the grey tagline opaque — a white key would have left it half transparent, because it is closer to the background than anything else in the image.

**Four findings worth keeping.**

1. **Auto-deskew nearly ruined the good file.** Measured across the full width, the ribbon's curved underside fits a straight line at **-7.7 degrees** on artwork that is perfectly straight. The fit is now taken only across the text block and refused unless the points really lie on a line; anything under a third of a degree is treated as zero, since rotating resamples every pixel for a correction inside the measurement's own noise.
2. **The tagline cannot be cropped off.** The ribbon runs the full height and the tagline sits *beside* its lower half, so a horizontal slice would take the bottom off the ribbon. It is erased where it actually lives instead — and left of the text block, ink is told apart from ribbon by whether it is attached to the artwork above. Before that fix the alternate layout's favicon contained the letters "More Op".
3. **A single pixel stretched the canvas.** The naive crop grew the box to 416px for one plate-edge pixel at alpha exactly 20. Cropping now measures ink per band and discards bands under 1% of the heaviest.
4. **Quantising the two header files** to 128 colours cut them from 29 KB to under 7 KB each — they are base64'd into the page HTML on every rerun, so that is a per-interaction saving — while keeping 64 distinct alpha levels, so no curve hard-edged.

**Limits, stated.** The artwork is light-background only: the deep green wordmark and navy `.AI` both drop to near-zero contrast on the deep green surfaces, so the footer uses the ribbon alone and `core.brand.DARK_SAFE` records the rule. The 2000px export makes the icons sharp well past 64px, which the screenshot did not. A vector master would still be better for print.


#### UI-06 — Language becomes a picker in the brand bar
**Area:** `app.py`, `styles/components.css` · **Priority:** P2 · **Status:** **DONE** · **Requested by:** Waleed

Three always-visible language buttons took three of the eight slots on the row
that carries the navigation, for a setting most people touch once and never
again. They are now one dropdown, in the brand bar, where the right-hand side
was empty.

**The brand bar had to stop being a single HTML string.** A Streamlit widget
cannot be nested inside a markdown block, so nothing could ever live in that
white bar. It is a real two-column row now — identity on one side, language on
the other.

**Matched by content, not by position.** The stylesheet targets
`[data-testid="stHorizontalBlock"]:has(.sa-brandbar)`. A positional selector
would silently stop matching if Streamlit rearranged its wrappers, and an
unstyled header does not degrade quietly — it looks like a rendering bug.

**The property worth preserving.** P2-1 made each language button carry its own
script, so a reader who cannot read the other two could still find theirs. That
survives the move because the option labels themselves carry it: the menu lists
**اردو**, not "Urdu". The honest cost is that the closed state shows only the
current language, so a reader who lands on the wrong one must open the picker
rather than seeing all three at once. The picker sits beside the logo with a
standard affordance, which is the usual trade for a setting.

Two dead pieces went with it: `.sahulat-header-inner`, which no longer exists,
and the RTL rule that named it.

- [x] Picker in the bar; all three languages, each in its own script.
- [x] Switching works and the whole page follows, including RTL.
- [x] An unknown language in stale session state cannot crash the header.

---

#### UI-05 — The hero preview rotates
**Area:** `app.py`, `styles/` · **Priority:** P2 · **Status:** **DONE** · **Requested by:** Waleed

The hero showed one real screening result. It now cycles through four, one
every four seconds, sliding upward at the handover.

**This is a deliberate exception to the spec's own rules**, taken at the
owner's request. V3 §40.5 says "avoid continuously moving hero graphics" and
§13.3 says "after entrance, stop the animation". Recorded here rather than
quietly done, because someone reading the spec later will otherwise think the
hero is a bug. The mitigations: the cadence is slow (a card is still for 3.5 of
its 4 seconds, so what is on screen is a settled card rather than a moving
one), and reduced motion stops it dead.

**Which records.** The engine's overall top six for the demo profile is five
NAVTTC courses and one job — accurate, and a rotation that would imply the
catalogue holds nothing but courses. The rotation instead takes the best real
match in **each category**, so the hero demonstrates the whole product. Every
card is still whatever the engine actually ranks first in its own category; a
test asserts the four titles are exactly the per-category winners.

**How it cycles: CSS, not reruns.** Streamlit has no way to repaint one element
on a timer without rerunning the script, and a rerun every four seconds would
re-screen the catalogue and reset every widget on the page. All four cards are
rendered once into a single grid cell — so the frame sizes to the tallest and
nothing jumps — and staggered CSS animations move between them. A test asserts
no `time.sleep`, `st_autorefresh`, `setInterval` or `setTimeout` exists. The
keyframes are generated in Python because their percentages depend on how many
categories actually have records.

**The reduced-motion trap, which is the real find here.** The blanket rule in
`animations.css` sets every animation to 1ms and one iteration. Applied to a
cycling card that would park it on its final keyframe — and that keyframe is
`opacity: 0`. The hero would have gone **blank**, not merely still, for exactly
the users who asked for less movement. There is now an explicit override:
first card, visible, motionless, dots hidden.

- [x] Four real results, one per category, asserted against the engine.
- [x] No timer, no rerun, no JavaScript.
- [x] Reduced motion leaves a readable card on screen.
- [x] Landing render unchanged at ~1.0s (the extra screening costs 1.6ms).

---

#### UI-04 — A wordless spinner on every AI call but one
**Area:** `app.py`, `core/i18n.py` · **Priority:** P1 · **Status:** **DONE** · **Spec:** V3 §42

The Lens showed real stages. The other four model calls — the follow-up Ask,
the per-opportunity chips, "explain this match" and the plain-language rewrite
— showed `st.spinner("")`: a grey ring with no text, for a call that takes
several seconds against a remote model. A user cannot tell that apart from a
hang.

All four now use the same staged panel, driven by a small `Stages` context
manager. Pending steps stay on screen dimmed and blurred, so a step that
finishes instantly is readable rather than a label flashing past.

**The constraint is unchanged from the Lens work, and is why there is no timer
anywhere in it:** the panel advances at real step boundaries only. The Ask flow
gets four stages because it has four real boundaries — the index has to exist,
the search has to run, the passages have to be gathered, and only then is the
model asked. Nothing is padded to look slower. A test asserts `time.sleep` and
friends appear nowhere near this code, because the moment one does the panel
has stopped reporting work and started performing it.

**The footnote had to become conditional.** The Lens note reads "your file is
not stored" — there is no file in a follow-up question, and reusing that line
would promise something about a thing that never existed. There is now a note
for the AI flows, and a third for when no key is configured, since promising
"this runs on Google's servers" with nothing configured describes work that is
not happening.

- [x] No `st.spinner("")` left in the app; a test guards it.
- [x] Four stages on Ask, three on explain, two on simplify — all real.
- [x] Labels in English, Urdu and Roman Urdu; none claims a percentage or a time.
- [x] The panel clears even when the model call raises.

---

#### UI-01 — Tabs were the product architecture
**Area:** `app.py`, `styles/components.css` · **Priority:** P0 · **Status:** **DONE** · **Spec:** V3 §45.3, §12

`st.tabs` at the top level was the loudest Streamlit fingerprint in the app: it
announced the framework before the user read a word, and it made three screens
with genuinely different jobs look like three drawers of one page.

Screens are now driven by `st.session_state.section`, with the header carrying
real navigation. The old header nav was anchor links — `#how` pointed at an id
inside a tab panel that was not in the DOM until the tab was opened, so it had
never worked.

**Buttons, not `st.segmented_control`.** A segmented control lets a user
deselect the active option, which for navigation means clicking the page you
are on takes you somewhere undefined. Buttons also match the pattern the
language switcher already uses.

A side effect worth having: **first render fell from 1.16s to 1.05s**, because
a tab strip renders every panel and hides the inactive ones. The Lens uploader
was being built on the landing page on every rerun.

Two things fell out of the change. The Lens card on the landing page said "use
the 'Read an announcement' tab above" and had no button, unlike the other four
path cards — it now navigates. And two Lens tests had been passing only because
every tab rendered at once; they now stand on the screen the upload lives on,
which is where a real user would be.

- [x] No `st.tabs` at the top level; one screen renders per run.
- [x] Navigation, deep links and start-over all carry the section.
- [x] No copy in any language names a tab.

---

#### UI-02 — The verdict was inside an expander
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Spec:** V3 §20, §18.2, §45.2

Spec §20, verbatim: *"The eligibility result should not be buried inside an
expander."* It was `expanded=highlight`, so the featured card did open by
default — but an expander that starts open is still a disclosure control with a
chevron and a click target, and it still reads as framework furniture around
the one answer the user came for.

The featured match now renders its scorecard inline with no expander at all.
The other 29 keep the disclosure, which is what §45.2 actually permits: on card
seven, the detail genuinely is secondary.

Documents, source and help stay tabbed even on the featured card. They are
reference material consulted one at a time, which is what a tab is for. The
verdict is not, which is why it is no longer one of them.

- [x] Exactly one featured match, at surface level 4 (§7).
- [x] Disclosure count is always results − 1.

---

#### UI-03 — The hero decorated instead of demonstrating
**Area:** `app.py`, `styles/components.css` · **Priority:** P0 · **Status:** **DONE** · **Spec:** V3 §13.2

The spec asks for "a realistic miniature Sahulat experience" in place of the
decorative SVG — opportunity card, match indicator, requirement status, next
action.

**The trap in that request is worth recording.** A hand-written example card
would satisfy the spec exactly and be the only fabricated thing on the landing
page of a product whose entire argument is that it does not fabricate. A judge
asking "is that a real result?" is precisely where that argument breaks.

So the preview screens the demo profile against the live catalogue through the
real rules engine and renders whatever comes back — same verdict, same
condition count, same next step a user would get. If the data changes, the hero
changes. A test asserts the title belongs to a record actually on disk **and**
is the match the engine ranks first. The caption says it is a real result.

The deadline row is excluded: it is a property of the listing rather than of the
person, it already has its own line, and "your information: today's date" reads
as nonsense at preview size.

- [x] Real record, asserted against the catalogue and the engine.
- [x] Renders in English, Urdu and Roman Urdu.
- [x] Cached per language; landing render still ~1.05s.

---

#### DATA-07 — Public Assistance
**Area:** `data/opportunities/public_assistance.json`, `models.py`, `rules_engine.py`, `timeliness.py`, `app.py` · **Priority:** P2 · **Status:** **DONE**

The last empty category, now **10 records**: the three BISP programmes
(Kafaalat, Taleemi Wazaif, Nashonuma), two from Pakistan Bait-ul-Mal
(Individual Financial Assistance, Sweet Homes), Punjab's Himmat Card, the Zakat
Guzara Allowance, Sehat Sahulat, an interest-free loan scheme, and the EOBI
old-age pension. **No category in the catalogue is empty any more**, and
Public Assistance got a landing path of its own — a category with records and
no way in from the home page is reachable only by someone who already knows to
look for it.

**The prediction in the original ticket was wrong**

This entry previously said "the existing conditions cover it; no engine work is
expected." That held right up until the records were actually written, at which
point assistance turned out to screen on an axis the model could not express.
A scholarship asks what you have achieved. Assistance asks what has happened to
you — and two of those questions had nowhere to live. Both are now tracked
separately as DATA-09 and DATA-10.

**What could NOT be modelled, and is handled as prose instead**

Three records turn on facts a non-identifying profile must never hold:

| Record | Real gate | Why it cannot be a field |
|---|---|---|
| BISP Kafaalat | PMT poverty score from the NSER survey | Derived from a household asset survey; no profile answer approximates it |
| Benazir Nashonuma | Pregnancy or breastfeeding | Health information — Invariant 2 |
| Zakat Guzara Allowance | Applicant is a Muslim *mustahiq* | Religion — never asked, ever |

The income condition on the BISP records is **our approximation, not the
programme's rule**, and each record says exactly that in the words the card
displays. The alternative — screening silently on a proxy and reporting
"eligible" — would be the most confident wrong answer in the product. A test
asserts each of these records names its own unaskable condition in prose.

The Zakat record additionally points non-Muslim applicants at Bait-ul-Mal,
which is funded from general revenue and carries no such restriction. A
screening tool that can only say "not eligible" to that user is failing them.

**One record creates a debt**

The interest-free loan sits beside nine grants. Presenting it without saying so
would be the most consequential omission in the catalogue, so it is called out
in the note, in the disclaimer, and in a test.

- [x] 10 records, screening and rendering in all three languages.
- [x] Every category now has a landing path and a non-zero count.
- [x] 24 new guard tests; suite 292 → 318.

---

#### DATA-09 — A restricted programme had no way to restrict
**Area:** `core/models.py`, `core/rules_engine.py` · **Priority:** P1 · **Status:** **DONE**

`priority_groups` is advantage-only **by design** — it can help an application
and never excludes anyone, which is right for a scholarship that favours women.
It is wrong for an orphans' home or a disability stipend, where the group *is*
the eligibility. With only the advantage available, the engine told every
applicant they qualified for Pakistan Sweet Homes and the Himmat Card.

`required_groups` is the gate. Same vocabulary, opposite force, read as **OR**:
"for orphans and persons with disabilities" admits anyone in either. AND would
be the stricter reading, and stricter is the dangerous direction to guess in —
it turns a wrongly-narrow record into a wrongly-refused person.

**Membership is three-valued**, which is the part that matters. `None` means
the question behind it was never answered, and that produces UNKNOWN — a
question — not UNMET, a rejection. `priority_group_memberships()` collapses
None and False together because a bonus you cannot evidence is simply a bonus
you do not get; a gate has to tell them apart.

Only `female`, `disability` and `orphan` can be gated on. Nothing in a
non-identifying profile establishes religion or district, so `minority` and
`under_served_district` stay advantage-only — gating on one would create an
UNKNOWN no user could ever resolve. A test enforces this.

- [x] Three-valued membership, OR semantics, rendered in all three languages.
- [x] Ungateable groups rejected by test.

---

#### DATA-10 — "Never closes" and "we have no date" shared one label
**Area:** `core/models.py`, `core/timeliness.py`, `app.py` · **Priority:** P1 · **Status:** **DONE**

Assistance is overwhelmingly rolling — BISP, Sehat Card and Bait-ul-Mal take
applications any day of the year. With no deadline on record all ten rendered
"No deadline on record — do not read as plenty of time", which is the right
answer when a date is missing and the wrong one when there is no date to miss.

The two are opposite instructions: one tells the user to go and check, the
other tells them there is nothing to check. `enrolment_is_continuous` splits
them, giving a new `LISTING_ALWAYS_OPEN` state and `URGENCY_CONTINUOUS`.

`match_urgency()` was added alongside `deadline_urgency()` because the old
function only ever sees a date string and therefore *cannot* tell the two
apart. A real deadline still outranks the flag: if a record carries both, the
date is the more specific claim and the user sees the countdown.

The always-open note deliberately does not stop at "no deadline". It adds that
acceptance still depends on the conditions above and on funds being available —
because for a rolling programme, "always open" is exactly the phrase a reader
could mistake for "always granted".

- [x] New listing state and urgency state, in all three languages.
- [x] A deadline beats the flag; a closed deadline beats both.

---

#### DATA-03 — "Jobs" category is selectable but always returns nothing
**Area:** `data/opportunities/njp_jobs_sample.json`, `app.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
`njp_jobs_sample.json` contains a single entry whose `name` starts with `REPLACE ME`, which `data_loader.py:31-34` correctly skips. So **zero** job records load. But "💼 Jobs" is offered in the category multiselect and is selected by default. A user who selects only Jobs gets an empty result area — the `st.warning` at `app.py:165` only fires when the *filtered* list is empty, which it is, so they get a generic message with no explanation of why.

**Why it matters**
A judge clicking "Jobs" sees a dead feature.

**Fix approach**
Either (a) complete Step 8 of the README — add 2–3 real currently-open listings from njp.gov.pk with future deadlines — or (b) if that isn't done in time, mark Jobs as "Coming Soon" in the same way `category_assistance` already is, so the gap is honest and deliberate rather than looking broken. **Decide which, and record it in the Decision Log.**

**Resolved in two stages.** On 2026-09-11 the UI was made to derive category
availability from the loaded data, so Jobs showed as a disabled "Coming soon"
path instead of a dead button — honest, and self-correcting. On 2026-09-12 the
data itself landed (DATA-04) and the path switched on with **no code change**,
which is exactly what that design was for.

**Acceptance criteria**
- [x] Real job records load and screen correctly (10 records).
- [x] No path through the UI shows an unexplained empty result set.
- [x] Every `application_deadline` is a future date — asserted by a test, not by memory.

---

#### OPS-01 — No error handling around any Gemini call
**Area:** `core/llm_client.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
`explain_match` (line 79), `answer_followup` (line 111), and `extract_opportunity_from_file` (line 175) all call `model.generate_content(...)` with no try/except. A rate limit, network failure, safety block, or malformed response is an uncaught exception surfacing as a Streamlit error page.

**Why it matters**
The free Gemini tier has rate limits, and a live demo on venue wifi is exactly when a network call fails. The module already has an excellent graceful-degradation pattern (the mock fallbacks) — it just isn't applied to runtime failures, only to a missing key.

**Fix approach**
Wrap each call. On failure, return a clearly-labelled, translated "AI explanation unavailable right now — the eligibility result above is unaffected" message. Emphasise in the message that the *rules-based result is still valid*, because it genuinely is — that's the whole point of the architecture, and it's a strong thing to be able to say out loud during a demo.

**Acceptance criteria**
- [ ] All three call sites handle exceptions.
- [ ] Failure message exists in both `en` and `ur`.
- [ ] Simulated failure (e.g. bogus API key) does not break the page; match cards still render.

---

#### OPS-02 — Confirm / update the Gemini model name
**Area:** `core/llm_client.py:19` · **Priority:** P1 · **Status:** TODO · **Owner:** —

**What's wrong**
Two separate problems:

1. `MODEL_NAME = "gemini-2.0-flash"` carries its own inline comment: *"confirm current recommended free-tier Flash model name before building"*. That confirmation has not happened.
2. **The SDK itself is end-of-life.** Importing it emits: *"All support for the `google.generativeai` package has ended. It will no longer be receiving updates or bug fixes. Please switch to the `google.genai` package as soon as possible."* (Observed 2026-09-10 on the installed version, 0.8.6.)

**Why it matters**
A retired or renamed model means every AI feature fails at once — and with OPS-01 unfixed, it fails loudly. An EOL SDK means no fixes are coming and newer models may simply not be reachable through it.

**Done 2026-09-11 (the SDK half):** `core/llm_client.py` now prefers `google-genai` and transparently falls back to the EOL `google-generativeai`, so the app works either way and `pip install google-genai` is the entire migration. The model name is also configurable via a `GEMINI_MODEL` env var or secret, with no code change.

**Still blocked:** confirming the model name against the live API needs an actual key, which does not exist in this environment yet. `DEFAULT_MODEL_NAME` was deliberately left at `gemini-2.0-flash` rather than guessing a newer name that could not be verified.

**Fix approach**
Check the current model list in Google AI Studio once a key is available, update the constant, and confirm both the text path and the multimodal (image/PDF) path work with the chosen model. Delete the stale comment once resolved.

**Resolved 2026-09-11, against a live key.** The suspicion was justified:
**`gemini-2.0-flash` no longer exists.** Every call returned `404 NOT_FOUND`.
Had this gone unnoticed, every AI feature would have failed simultaneously in
the demo.

Measured across the models actually listed for this key:

| Model | Text | Image | Verdict |
|---|---|---|---|
| `gemini-2.0-flash` | 404 | 404 | **retired** |
| `gemini-2.5-flash` | 404 | — | closed to new users |
| `gemini-flash-latest` | 503 | — | overloaded; also a moving alias |
| `gemini-3.8-flash` | 13.0s | 503 | unreliable under load |
| `gemini-3.6-flash` | 61.1s | 3.6s | works, but text was congested |
| `gemini-3.1-flash-lite` | 3.2s | 3.5s | reliable — documented fallback |
| **`gemini-3.5-flash`** | **1.4s** | **3.8s** | **chosen** |

`DEFAULT_MODEL_NAME` is now `gemini-3.5-flash`: fastest of the models that
served *both* paths reliably. An explicit version is pinned rather than the
`-latest` alias, so the demo cannot shift underneath us mid-presentation.
`gemini-3.1-flash-lite` is recorded in the source as the fallback if the
default is ever overloaded — switchable via `GEMINI_MODEL`, no code change.

**Verified end to end through the app's own functions, not raw SDK calls:**
`explain_match` in English (8.9s) and Urdu (8.8s), `answer_followup` (5.5s),
and `read_ad` on a synthetic scholarship poster (8.5s), which correctly
extracted the domicile, the 60% marks threshold and the Rs. 45,000 income
ceiling into structured fields.

**Acceptance criteria**
- [x] Current SDK supported, EOL SDK kept as a fallback.
- [x] Model name made configurable without a code change (`GEMINI_MODEL`).
- [x] Inline "confirm before building" comment removed.
- [x] Model name confirmed against the live API.
- [x] A real text generation succeeds, in both languages.
- [x] A real image extraction succeeds.

---

### V2 — P2 upgrade (branch `v2`)

Implements `Sahulat_AI_V2_P2_Secondary_Priority.md`.

**Sequencing note:** P2-1 was done *last* deliberately. Roman Urdu is a
445-string translation, and P2-2/4/5 each added strings — translating before
they landed would have meant translating twice and leaving gaps behind.

---

#### P2-1 — Roman Urdu
**Area:** `core/i18n_roman.py` (new), `core/i18n.py`, `app.py` · **Status:** **DONE**

A third language mode: **English · اردو · Roman**, at **100% string coverage**
(445 of 445), not a partial mode that falls back to English mid-page.

**Kept in its own table**, not as a third key in every literal. That keeps the
English/Urdu pairs - the two languages the product actually promises -
readable side by side, and means a gap degrades to English rather than
breaking a page. `t()` consults it only for `ur_roman`.

**Roman Urdu is Latin script, so it is left-to-right.** Treating it as "the
other Urdu one" and mirroring the page would have been the obvious mistake;
`is_rtl()` exists so that decision is made in one place. It also takes the
Latin font stack and Latin leading rather than Naskh.

**Written as people actually type**, borrowing English for terms with no
everyday Urdu equivalent - "scholarship", "documents", "deadline". Forcing
literary Urdu into Latin script would read as stilted to exactly the audience
this mode is for.

**The model is told explicitly** not to answer in Urdu script: asked for
"Urdu", it returns Urdu script, which is precisely what a Roman Urdu reader
chose not to have.

Tests: full coverage, no orphan keys, **placeholder parity on every string**
(a dropped `{n}` is a render-time crash, not a typo), no Urdu script anywhere
in the Roman table, and a whole-page render asserting no Urdu script leaks in.

---

#### P2-2 — Impact figures
**Area:** `core/impact.py` (new), `app.py` · **Status:** **DONE**

Four figures: opportunities screened, requirements checked, documents
identified, and estimated minutes saved.

**Three are counts of work this session actually did.** Requirements counted
are `applicable_checks()`, so a record with two rules contributes two and not
fourteen - the inflation would have been invisible and the number is the
headline.

**The fourth is the only estimate, and it is fenced off.** It comes from a
single visible constant, `MINUTES_PER_LOOKUP = 8`, exposed through
`estimate_basis()` so the UI prints the arithmetic: *"3 opportunities × 8
minutes assumed per manual lookup. Prototype estimate — not a measured
population-level claim."* It carries an "Estimate" badge; the counted figures
do not.

The brief asks for these "for presentations". That is exactly where an
unlabelled invented number does the most damage: a judge who finds the basis
was never stated stops believing the figures that *were* counted.

---

#### P2-3 — Visual polish
**Area:** `styles/`, `app.py` · **Status:** **DONE**

- **Urdu leading fixed.** Naskh stacks marks above and below the baseline, so
  Latin leading makes consecutive Urdu lines collide. Body line-height is now
  a token: 1.6 Latin, 1.95 Urdu.
- **Result detail grouped into four tabs** — Eligibility · Documents & steps ·
  Source · Understand & ask. Eight sections had accumulated in one scroll;
  they group by the question being asked, not by implementation.
- **Spacing**: `style="height:1rem"` spacer hacks replaced with named
  `.sa-spacer` classes, so vertical rhythm is not set inline.
- Badge tones audited: every tone used in `app.py` has a definition.

---

#### P2-4 — Empty states
**Area:** `app.py` · **Status:** **DONE**

"No matches" now comes with three routes out - change answers, change
categories, upload an ad - and, importantly, with the sentence *"Our catalogue
currently holds 3 records. A small catalogue is a limit of this prototype, not
a judgement about you."* A bare "no matches" invites the reading that the user
qualifies for nothing, when the likelier explanation is ours.

Two more absences made explicit:
- **No documents ticked** → says so, rather than showing 0% with no
  explanation.
- **No documents listed on the record** → *"that is a gap in our record, not a
  sign that none are needed"*. Silence next to an empty list would read as
  permission to turn up empty-handed.

---

#### P2-5 — Degraded AI
**Area:** `core/llm_client.py`, `app.py` · **Status:** **DONE**

**The real problem was that a failure looked like an answer.** `explain_match`
returned a plain string either way, so the sentence printed when a call failed
rendered in the same blue box, with the same authority, as a real explanation.

`AiText` is a `str` subclass carrying `.ok` and `.reason`. Subclassing `str`
was deliberate: every existing caller keeps working unchanged, so this is
additive rather than a migration. Three non-answers are distinguished - no key,
call failed, no grounded evidence - and each is presented differently.

A raw API error never reaches the screen: *"Gemini API error 429"* tells a
scholarship applicant nothing they can act on. The message names what is **not**
affected instead, and a test asserts the exception text never appears.

The architectural claim - that the product works without the model - is now
tested rather than asserted: with `_generate` raising, the results page still
renders the scorecard, the next step, the source block and the deterministic
result.

---

### V2 — P1 upgrade (branch `v2`)

Implements `Sahulat_AI_V2_P1_High_Priority.md`.

**The thread running through this batch is absence.** No deadline on record,
never verified, no documents listed, evidence that does not exist. Each of
those has a comfortable-looking reading — "plenty of time", "fine", "nothing
needed", "here is an answer anyway" — and each of those readings is wrong.
Most of the work below is making absence visible rather than letting it
default to reassurance.

---

#### P1-1 — Application readiness
**Area:** `core/readiness.py` (new), `app.py` · **Status:** **DONE**

The document checklist became a readiness view: a percentage, the documents
ticked, and the ones still needed.

**This percentage is legitimate where a "match %" was not**, and the
difference is worth stating: every term here is something the user ticked or
the record lists, and it is computed from the very rows displayed beneath it.
V2-1 refused a percentage because it would have been a guess at an awarding
body's decision. This one is arithmetic over a checklist.

Two guards: it floors rather than rounds, so 198 of 199 documents reads 99%
and never 100%; and a record with no documents listed reads 0%, not complete —
"nothing required" is not something the catalogue knows.

**Connected to the next step**, as the brief asks: with nothing ticked the
action is "prepare the 7 documents"; once the user has started it becomes
"obtain the next document you are missing — <name>"; when all are ticked it
becomes "apply". That reads widget state directly rather than the derived set,
because the derived set is only rebuilt when the checklist renders — the same
one-interaction lag that was UX-07.

---

#### P1-2 — Deadline intelligence
**Area:** `core/timeliness.py` (new), `app.py` · **Status:** **DONE**

Five states, not four: **passed · approaching (≤3 days) · apply soon (≤14) ·
plenty of time · no deadline on record.**

That fifth state is the point. Every curated record currently has
`application_deadline: null`, so it is the state users meet *most often*, and
folding it into "plenty of time" would have turned missing data into a
reassurance across the entire catalogue. It renders with a dashed border, its
own label, and the line *"We have no application deadline for this record.
Check the official source before assuming it is still open."* An unparseable
date lands there too, rather than being read as expired.

Expired listings get an explicit "nothing here is worth preparing" note, and
the next-step ladder already refuses to send anyone to a closed application —
now covered by a test that puts a complete profile and a full checklist
against an expired listing and asserts the step is still not "apply".

---

#### P1-3 — Contextual follow-up
**Area:** `core/rag_engine.py`, `app.py` · **Status:** **DONE**

Each result carries its own question chips, chosen from its state: a user who
is eligible is never offered "why am I not eligible?". Evidence comes from
`retrieve_for()`, which returns that one record's text **or nothing** — never
a near-miss from another scheme. Retrieving across the catalogue for a
question about a specific scholarship is how a confident, well-cited answer
about the *wrong* scholarship gets written.

---

#### P1-4 — Opportunity Passport
**Area:** `app.py` · **Status:** **DONE**

The session profile given a name and a visible home, with completion, an edit
route, and reuse stated on the upload path ("using your saved answers"). The
privacy line names what is deliberately absent — no CNIC, name, phone or
address — because that absence is the entire reason it can be reused freely.
Replaced the old "your answers" expander, which is now deleted rather than
left to rot beside it (both claimed the same widget key).

---

#### P1-5 — Opportunity comparison
**Area:** `core/comparison.py` (new), `app.py` · **Status:** **DONE**

Pick two or more results and compare eligibility, conditions met, deadline,
documents still needed, open questions and whether an official link exists.
Reflects documents already gathered rather than assuming the user holds none.

**The summary compares effort, and says so.** It is computed from three
countable things, weighted so that one unmet condition outweighs any amount of
paperwork — paperwork can be obtained, a failed condition cannot. It carries
the caveat *"This compares effort, not value"*, because a small award with a
short form is "less work" and that has nothing to do with which is worth
having. Where the numbers are close it returns **no leader at all**: naming a
winner the numbers do not support would turn a comparison into a
recommendation. A blocked or expired option can never be "easiest".

---

#### P1-6 — Information freshness
**Area:** `core/timeliness.py`, `app.py` · **Status:** **DONE**

Four states from `last_verified`: **recent (≤30 days) · verification
recommended (≤180) · likely out of date · never verified by us.**

An unverified record is "never" *whatever date it carries* — a date never
backed by a real check is not evidence, which is the DATA-01 failure mode
exactly. An uploaded record is "never" too: reading a document is not
verifying it, however clearly the model read it. All three curated records
currently sit at "never", and the UI says so rather than letting presence in
the catalogue imply currency. Verification is prompted by default.

---

#### P1-7 — Explain Like I'm New
**Area:** `core/llm_client.py`, `app.py` · **Status:** **DONE**

Five plain-language sections: who it is for, what you get, who can apply, what
you need, where to apply.

The brief's rule — *simplify, do not reinterpret* — is enforced structurally
rather than by asking nicely. The model is handed **only the record's own
statements**: no profile, no eligibility result. It cannot tell a reader they
qualify because it has never been told. The prompt forbids adding, weakening
or strengthening any condition ("at least 60% marks" must not become "good
marks"), and any key we did not ask for is dropped rather than rendered — so
a model volunteering `"you_are_eligible"` gets discarded, not displayed.

Placed after the scorecard, never instead of it, with a caveat naming the
conditions above as the authority. Verified live: the rewrite kept "between 17
and 25" and "at least Intermediate" intact, and said the document "does not
state" an application URL rather than inventing one.

---

#### P1-8 — Source presentation
**Area:** `app.py` · **Status:** **DONE**

The source block now labels every field the brief asks for — source document,
organisation, official page, last verified — as readable rows rather than a
citation footnote, with the freshness badge beside the heading and an explicit
"no official link on record" where there is none.

---

### V2 — P0 upgrade (branch `v2`)

Implements `Sahulat_AI_V2_P0_Highest_Priority.md`. Each item below names what
shipped and, where the brief and this product's honesty rules pulled in
different directions, which way it was resolved and why.

---

#### V2-1 — Eligibility scorecard
**Area:** `core/models.py`, `core/i18n.py`, `app.py` · **Priority:** P0 · **Status:** **DONE**

Every result now opens onto a three-column table — **requirement · your
information · result** — one row per condition, with a summary line above it.

`MatchResult` gained `satisfied()`, `blockers()`, `gaps()` and `scorecard()`,
returning `ConditionCheck` objects and counts. No prose: `i18n.scorecard_row()`
renders each row from the same helpers `describe_check()` already used, so a
condition cannot read one way in the scorecard and another in the explanation.

**Departure from the brief, deliberate.** The brief asks for "Approximately 90%
or another clearly defined profile-match representation". The implementation
takes the second option and shows **"4 of 5 stated conditions met"** with a
proportional bar, not a percentage.

A percentage would be read as a probability of being awarded the scholarship.
Nothing in this system computes that: the rules evaluate stated conditions, and
say nothing about competition, quotas or the awarding body's discretion. "92%"
implies a near-certainty that the product has no basis for, and the brief's own
warning — *"92% match should not automatically mean Eligible"* — describes
exactly the misreading a percentage invites. A count of conditions is checkable
against the rows immediately beneath it; a percentage is not checkable against
anything. A test asserts the count and the rows can never drift apart, and
another asserts that a full row of passes with one hard failure is still "not
eligible".

- [x] Requirement-level results preserved and passed to the UI.
- [x] Passed / failed / verification-required visually separated.
- [x] Final status stays deterministic; the summary never overrides it.

---

#### V2-2 — Why you match, why you don't, what needs verification
**Area:** `core/i18n.py`, `app.py` · **Priority:** P0 · **Status:** **DONE**

Three separately-headed groups, because they call for three different
responses. A blocker is named first — burying a decisive failure under
"prepare your documents" would be actively misleading — with the note that one
unmet condition changes the result however many others passed.

**"What would change this"** states the requirement and the profile's own value
side by side: *"This requires at least 60%. Your profile says 54%."* It does
**not** say what would follow from changing it. The brief permits this
("do not promise... unless the rules genuinely support that conclusion") and
the rules never do: eligibility here is a screening result, not an award. A
test asserts no gap line ever contains a promise.

Unanswered is phrased differently from failed throughout — *"your profile does
not answer this yet"* — because unanswered is not unqualified.

- [x] Decisive, failed and verification-required criteria identified separately.
- [x] Explanations generated from stored results, not from an LLM.
- [x] Both languages.

---

#### V2-3 — Personalised top matches
**Area:** `core/rules_engine.py`, `app.py` · **Priority:** P0 · **Status:** **DONE**

A shortlist leads the results page, each entry carrying the reason it is there
("All 5 stated conditions met · you match the women applicants priority
group"). `evaluate_all` ranks on: status → open before closed → deadline
urgency → priority-group matches → share confirmed → conditions met → fewer
unknowns → fewer required documents → name. `ranking_factors()` exposes those
numbers so the UI explains the order instead of asserting it.

Two judgement calls:

- **"No deadline on record" is its own bucket**, sorted after dated listings
  rather than treated as infinitely far away or infinitely urgent. Most curated
  records legitimately have no deadline; inventing a position for them would be
  false precision.
- **"Missing documents" became "number of required documents"**, as a late
  tie-break only. The app does not know which documents a user already holds —
  the checklist is UI state, not profile data — so ranking on "missing" would
  have meant inventing knowledge. Documented rather than quietly fudged.

`top_matches()` excludes closed listings and demonstrable non-matches, and
returns fewer than three (or none) rather than padding the list with weak
entries — a shortlist is only worth having if being on it means something.

- [x] Deterministic ranking from structured facts; no model opinion.
- [x] Reason shown for each shortlisted result.

---

#### V2-4 — Sahulat Lens
**Area:** `core/llm_client.py`, `core/ad_reader.py`, `app.py` · **Priority:** P0 · **Status:** **DONE**

Building on UX-10 (staged reading, readable extraction), this adds:

**A wider schema** — `province_scope`, `gender_required`, `fields_of_study`.
Extracted values are accepted only when they match a vocabulary the rules
engine understands; anything else is dropped to `None`. A mis-mapped gender
becomes a real eligibility gate and wrongly excludes people, so unread is the
safer failure. The prompt also states explicitly that a document merely
*mentioning* or prioritising women is **not** gender-restricted.

**User correction** — the reading can be edited (ages, provinces, education,
marks, income, deadline) and re-screened. Extraction from a photograph is
unreliable and the rules engine treats whatever comes out of it as fact; the
edit is what stops a misread number from silently becoming a verdict. A test
drives the full path: a poster misread as 90% instead of 60% flips
"not eligible" → "eligible" once corrected, and the record's trust level does
not move.

- [x] Structured fields extracted, shown before evaluation.
- [x] User can confirm or correct; corrections re-screened.
- [x] Same deterministic engine as curated records.
- [x] Never presented as officially verified.

---

#### V2-5 — Trust layer
**Area:** `core/models.py`, `app.py` · **Priority:** P0 · **Status:** **DONE**

Already load-bearing before V2 (Invariant 4); this pass made it testable.
Tests now assert that an uploaded record is never verified, that **high
extraction confidence is not verification** (confidence describes how clearly
the model could read the page, not whether the page is true or current), and
that a user correcting a field does not promote the record's trust level.

- [x] Source type on every record; source metadata stored and shown.
- [x] Last-verified date for curated records only.
- [x] The two levels are never merged visually or in code.

---

#### V2-6 — Next best action
**Area:** `core/next_action.py` (new) · **Priority:** P0 · **Status:** **DONE**

A new decision module, deliberately separate from rendering: it emits a machine
key plus structured subject, and `i18n.describe_next_action()` renders it.
Exactly one action comes back per result, from a priority ladder:

1. listing closed → explore other matches (a dead application page is not a
   next step, whatever the profile says)
2. a condition is demonstrably unmet → name it
3. unanswered by the user → ask them (cheap, immediate)
4. unanswered by the *record* → send them to the official source
5. eligible with documents → prepare them
6. eligible with a link → apply
7. otherwise → read the source

An action names the next *step*, never the result of taking it. Shown outside
the detail expander, since a user who never expands still needs to know what
to do. A test asserts every result in every profile state yields exactly one.

- [x] One primary action, prominently placed; extras stay underneath.
- [x] Links to the official source where one exists.

---

#### V2-7 — Responsible-AI architecture, made visible
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE**

*How this match was generated* now opens with the claim itself — **"AI does not
decide your eligibility"** — followed by the pipeline and the note that both
entry points end in the same rules engine. On the upload path the first step
becomes *AI reads the document into structured fields*, so the difference
between the two routes is visible and the shared engine is demonstrated rather
than asserted.

- [x] Rules/explanation separation preserved and stated in the UI.
- [x] Same engine shown running for uploaded opportunities.

---

#### V2-8 — Landing
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE**

Four paths, the fourth being **Check an advertisement** — the Lens was the
feature most likely to be the demo moment and it was not on the landing page at
all. A path with no records yet is **disabled and labelled**, not hidden: a thin
catalogue is a fact about the data, and hiding it would misrepresent the
product. A four-benefit row (personalised / evidence-based / bilingual / works
with real-world ads) sits above the existing principles.

- [x] Four paths including the upload route.
- [x] Benefits row; bilingual throughout.

---

#### UX-10 — Upload result was a raw JSON dump, and the AI read gave no feedback
**Area:** `app.py`, `core/ad_reader.py`, `core/i18n.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What was wrong**
Two separate problems in the same flow, both reported from the running app.

1. **The result was a data dump.** After reading an ad, the page showed the
   name, a summary line, and then `st.json(raw)` — a nested structure with
   thirteen `NULL` fields. The most prominent thing on the page was the part a
   user has least use for.
2. **Nothing happened for ~12 seconds.** The model call is genuinely slow
   (measured 8.5–12.0s on real uploads), and the only feedback was a bare
   spinner. The work is real, visible progress was not.

**What was done — presentation**
`render_extraction()` renders a document summary: title, lede, provider,
category, deadline, then **conditions stated in this document** as
label → value rows, then **documents it asks for** and **how to apply**.

The conditions are rendered by a new `i18n.describe_requirements()`, which
builds a `ConditionCheck` and reuses `check_title()` / `_requirement_text()`.
That is deliberate: a condition now reads *identically* whether it is being
explained from a document or evaluated against a profile, because exactly one
place turns a machine key plus a structured value into prose. Both languages.

**Unstated conditions are shown, not hidden** — as dashed chips, with: *"Nothing
was found about these, so they are not checked against you. That is not the
same as qualifying."* A null in an extraction means the document was silent,
and silence must never read as a pass.

The raw JSON stays, one click away, under *Show exactly what the model
returned*. An uploaded record is unverified by definition, so the exact model
output has to remain auditable — it just is not the first thing a user meets.

**What was done — staged processing**
`read_ad()` was split into `extract_raw()` (the model call) and
`build_record()` (local structuring), so real stage boundaries exist to report
on. `read_ad_in_stages()` writes a four-stage panel into one slot and advances
it **between real calls**:

> Preparing your file → Reading the document with AI → Structuring what it
> says → Checking it against your answers

Streamlit streams each write as the script produces it, so this needs no
threads, no timers and no `sleep`. The reading stage is shown *before* the
model call and the structuring stage only *after* it returns — asserted by a
test that records the interleaving.

Stages that finish instantly are **not padded to look slower**. They stay
legible because all four are on screen from the start, dimmed and slightly
blurred, sharpening as each becomes active and ticking as it completes: a list
resolving, rather than labels flashing past. The indicator is indeterminate —
it says *working*, never a percentage we do not have.

Screening now runs as the fourth stage when the profile is complete, and the
result is kept rather than recomputed, because a stage that claims work was
done must produce the output of that work. The old "Screen this against my
profile" button remains only for when there are no answers yet.

**Relationship to UX-09.** The earlier refusal stands and is not contradicted:
spec 10.1 forbids faking a delay *for instant local operations*, which is why
rules matching still reveals instantly. This is the opposite case — a real
remote call taking ten seconds — which is precisely when the spec asks for a
staged sequence. The distinction is not "does it look better with stages", it
is "is something actually happening".

**Reduced motion:** the blanket 1ms rule would strobe a looping indicator, and
a 38%-wide bar frozen mid-track would read as "38% complete" — a number we do
not have. Under `prefers-reduced-motion` the indicator becomes a still,
full-width bar and the pending blur is dropped.

**Acceptance criteria**
- [x] Extraction reads as a document summary; raw JSON behind a disclosure.
- [x] Conditions rendered in prose, in both languages, via shared i18n.
- [x] Unstated conditions visible and explicitly not counted as qualifying.
- [x] Stage panel advances on real call boundaries, verified by test.
- [x] No fabricated delay, no fabricated percentage.
- [x] Screening result shown, not recomputed or discarded.
- [x] `prefers-reduced-motion` handled for the indicator specifically.
- [x] Verified end to end against a live model call (12.0s) on a real image.

---

#### UX-07 — Document checklist lagged one interaction behind
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What was wrong**
Ticking all seven boxes left the progress bar short; unticking one left it
full. Reported from the running app and reproduced exactly.

The cause was **render order**, not arithmetic. The caption and progress bar
were written *before* the loop that reads the checkboxes, so they rendered the
count as it stood at the start of the run - always one interaction stale.

```python
st.caption(...)            # drawn using last run's `ready`
st.progress(len(ready)/n)  #   ""
for i, doc in enumerate(docs):      # only now is the true state read
    if st.checkbox(doc, ...): ready.add(i)
```

**What was done**
Reserve a `st.container()` above the list, read every checkbox first, then
write the count and bar into the reserved slot once the real number is known.
The readiness set is now rebuilt from the widgets each run rather than mutated
in place, so it cannot drift.

**Acceptance criteria**
- [x] Count and bar match the boxes on every transition, 0 → 7 and 7 → 0.
- [x] Ticking the final box completes the bar in the same render.
- [x] Covered by AppTest regression tests (`tests/test_app_ui.py`).

---

#### UX-08 — Form fields had no visible boundary until clicked
**Area:** `styles/components.css` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

Selects and number inputs relied on Streamlit's default near-invisible border,
so a field only looked interactive once focused. This is a genuine usability
failure, not a cosmetic one - people could not tell a control was there.

Every control now defines the full state set required by the spec (9.2):
**Default · Hover · Focus · Filled · Selected · Disabled · Error**. Fields are
48px tall with a 12px radius, a white surface and a visible 1px border by
default; hover darkens the border, focus adds the brand ring, and the focus
indicator is never removed.

Gender moved from a dropdown to a **segmented control** (spec 9.4) - clearly
separated, tappable options with a soft green selected state. Selecting nothing
still means "prefer not to say", so the privacy stance is unchanged.

**Acceptance criteria**
- [x] Every field has a visible boundary before it is touched.
- [x] Hover, focus and selected states defined for all controls.
- [x] Gender uses tappable options, verified by test.
- [x] Values survive reruns, verified by test.

---

#### UX-09 — No motion system; header was not a distinct layer
**Area:** `styles/`, `app.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**Stylesheets extracted** to `styles/theme.css`, `components.css` and
`animations.css` (spec 17.1). `app.py` now generates only the language-
dependent font variables and the RTL block, so the CSS is readable and
reviewable instead of buried in a Python f-string.

**Header** is now a real navigation layer: white surface at 92% with a blur, a
1px bottom border against the warm page, a logo mark, the wordmark with its
Urdu companion, nav links with an animated underline, a compact `EN | اردو`
switcher and a contextual primary action.

**Motion**, all CSS-only and all within the spec's duration scale (fast 160ms /
normal 220ms / reveal 420ms / slow 650ms) on `cubic-bezier(.22,1,.36,1)`:
- Category cards lift 3px, strengthen their border, gain a soft shadow, shift
  their icon and grow an accent line from 25% to 100%.
- The **Sahulat Path** draws once, left to right, then the four nodes pop in on
  an 80ms stagger. It becomes a vertical timeline under 640px.
- Results reveal with the count landing first, then cards arriving on an 80ms
  stagger - information arriving, not cards falling.
- Buttons lift 1px and compress slightly on press; source links shift their
  arrow 3px.

**Replay is gated in Python.** Streamlit reruns the whole script on every
interaction, so an ungated CSS entrance would replay each time a checkbox was
ticked. `should_animate()` records a token per real state change, and the
reveal classes are only emitted when that token is new. A test asserts the
classes appear on first render, vanish on an unrelated rerun, and return for a
genuinely new result set.

**`prefers-reduced-motion`** collapses every duration to 1ms and disables the
lifts. Nothing is hidden behind a transition, so the product stays fully usable
with motion off.

**Not done, deliberately:** the "Finding your matches…" staged processing
sequence. The spec asks for it (master prompt) but its own rule 10.1 says *only
show this when a real operation is actually happening — never fake a delay for
instant local operations*. Rules matching here is local and instant, so a
staged wait would be theatre. The honest version of that moment — count first,
then staggered card reveal (10.2/10.3) — is implemented, and the pipeline
stages remain visible in *How this match was generated*. If an LLM call is ever
on the results path, add the sequence there.

**Acceptance criteria**
- [x] Stylesheets in `styles/`, loaded and cached.
- [x] Header reads as a separate layer.
- [x] Category hover, path draw, result stagger implemented.
- [x] Reveals gated so they do not replay on unrelated reruns (tested).
- [x] `prefers-reduced-motion` honoured.

---

#### UX-04 — Material icon ligature rendered as raw text
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What was wrong**
`keyboard_double_arrow_right` appeared as literal text in the top-left corner.

This was **my own regression** from the previous round. The stylesheet set
`font-family` on `[class*="st-"]`, and that selector also matches Streamlit's
Material icon spans. An icon font renders its glyph *from the ligature text*, so
overriding the font leaves the ligature name showing as plain words.

**What was done**
- Dropped the broad attribute selector. Base type is now set on
  `html, body, .stApp` and inherited, plus explicit widget selectors.
- Added an explicit guard so an icon font can never be overridden again.
- Removed the sidebar entirely, so the collapse control that displayed the
  artefact no longer exists.

**Acceptance criteria**
- [x] No raw ligature text anywhere.
- [x] No broad attribute selector that can catch an icon font.
- [x] Icon-font guard present in the rendered stylesheet (verified).

---

#### UX-05 — "Press Enter to apply" hint on every number input
**Area:** `app.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

Streamlit renders an `InputInstructions` hint inside number and text inputs. It
is visual noise, and worse, it advertised the very Enter-key behaviour that
UX-01 removed - so it was actively misleading.

Hidden with `div[data-testid="InputInstructions"] { display: none !important; }`.
The same pass hides the Deploy button, the status widget and the default header,
which were the other tells that this is a Streamlit app.

**Acceptance criteria**
- [x] Hint no longer rendered.
- [x] Deploy button and default header chrome hidden.

---

#### UX-06 — Interface read as a prototype rather than a product
**Area:** `app.py`, `core/i18n.py`, `core/models.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

Implements the *Civic Intelligence* direction from the premium UI/UX redesign
specification supplied by the product owner on 2026-09-11 - everything in that
document's **P0** list and most of **P1**.

> **Note:** the spec document itself is **not in this repository**. Section
> references below (spec 7, spec 17, ...) point at it. Commit it to `docs/` so
> these references resolve for anyone reading this later.

**Structure**
- A real **home page** before the wizard: asymmetric hero, inline trust row,
  "what can you find", the four-step journey, three principles, a privacy
  block, product-generated statistics and a proper footer.
- The **sidebar is gone** (spec 12/31/99). A brand bar carries the wordmark
  `Sahulat AI · سہولت` and a compact `English | اردو` toggle. AI status and
  catalogue health moved into *How it works*.
- Tabs renamed: Discover / Read an announcement / How it works.

**Visual system** (spec 7, 8, 35-38, 91)
- Warm paper background `#F8F8F4` with white content surfaces. Green is demoted
  to an accent, with gold for verification and blue for information.
- Full token set: colour, radius (8/14/20/24), the barely-there shadow, and an
  8px spacing scale. Reading width capped; container max-width 1200px.

**Signature visual** (spec 11)
- An inline-SVG **opportunity map** - one person, four paths. No external asset,
  no animation, inherits the palette.

**Results** (spec 17, 20, 21, 23, 25, 26, 54, 55, 61)
- A ranked **editorial list** with `01`/`02` numbering rather than a card grid.
  The top match is called out: *"This one looks especially relevant to you."*
- **Source provenance** is a visible block - authority, source title,
  verification state, last-checked date - not a footnote.
- **Listing status is derived from data** (`MatchResult.listing_state()`).
  Because no curated record has a verified deadline, none claims to be "Open";
  they show *Verify current cycle*, which is the honest answer.
- **Document readiness** with a progress bar, and an **application journey**
  timeline.
- A judge-facing **"How this match was generated"** pipeline view. It is a
  static, honest description - no artificial delay pretending to be computation.

**Demo path** (spec 59, 60)
- *Try a sample profile* fills a realistic Balochistan profile and jumps
  straight to results, so a live demo cannot stall on data entry. It is clearly
  marked `Demo profile` and cleared by *Start over*.

**Also**: prompt chips for the follow-up chat, human error copy with a
*Technical details* disclosure, honest empty states, mobile breakpoints, and a
`prefers-reduced-motion` block.

**Deliberately not done** - in the spec but rejected as scope or honesty risks:
percentage "profile fit" scores, Roman Urdu parsing, opportunity comparison,
saved opportunities, notifications, and a custom logo mark (that needs a
designer, not a code change).

**Acceptance criteria**
- [x] No sidebar; brand bar with compact language toggle.
- [x] Home page with hero, SVG map, journey, principles, privacy, footer.
- [x] Ranked editorial results with provenance, readiness and timeline.
- [x] Listing status derived from data; never claims Open without a deadline.
- [x] Demo profile reaches results with at least one strong match (tested).
- [x] Mobile breakpoints and reduced-motion support.

---

#### UX-01 — Enter key submitted a half-filled form straight to results
**Area:** `app.py`, `core/validation.py` · **Priority:** P0 · **Status:** **DONE** · **Owner:** —

**What was wrong**
The profile lived in a single `st.form`. Streamlit submits a form when Enter is
pressed in any input, so typing an age and hitting Enter jumped straight to
results with nothing else answered — and every condition came back "unknown".
There was also no concept of a required field.

**What was done**
Replaced the single form with a **guided four-step wizard**, and deliberately
did **not** use `st.form` anywhere — a form's Enter-to-submit behaviour is the
bug. Steps: Focus → About you → Education → Skills & circumstances → Results.

Step rules live in `core/validation.py`, not in the UI, so they are unit-tested
without Streamlit:
- `age` and `domicile_province` are required to leave step 2; `education_level`
  to leave step 3; at least one category to leave step 1.
- Ranges are enforced (age 14–70, marks 0–100, experience 0–50).
- Everything else stays genuinely optional — an unanswered field still becomes
  "unknown" rather than a guess, which is the original architecture's promise.
- Errors render inline under the offending field, in both languages.

**Acceptance criteria**
- [x] No `st.form` in the app (verified: 0 forms rendered).
- [x] Enter cannot advance a step or reach results.
- [x] Each step blocks until its required fields hold sensible values.
- [x] Validation is unit-tested independently of Streamlit (24 tests).

---

#### UX-02 — Decorative emoji throughout
**Area:** `app.py`, `core/i18n.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

Emoji were used for category icons, tab labels, status dots, buttons, badges and
callouts. On a government-services tool this reads as unserious.

All decorative emoji were removed — from the UI, the tab labels, the i18n
strings and the page icon. Meaning is now carried by typography, colour and
layout. The only remaining glyphs are `✓` and `✕` in the condition rows and
completed-step markers: these are typographic dingbats, not colour emoji, and
they carry real semantic weight (met / unmet).

**Acceptance criteria**
- [x] No emoji in any rendered string (audited programmatically).
- [x] Status still legible without them, via colour and label.

---

#### UX-03 — No design system
**Area:** `app.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

The page used default Streamlit typography and an ad-hoc gradient hero, so it
read as generic and visually unresolved.

Introduced a small, explicit design system:
- **Typography.** *Source Serif 4* for display headings (institutional, and it
  gives the wordmark some authority), *Inter* for UI text. Urdu switches to
  *Noto Nastaliq Urdu* for display and *Noto Naskh Arabic* for body, with a
  taller line-height because Nastaliq needs the room.
- **Colour tokens.** A single `:root` palette — brand green, ink/muted/line
  neutrals, and semantic ok/warn/no tints — instead of scattered hex values.
- **Components.** Masthead, stepper, panel, field tag, badge, condition row,
  callout, KPI tile, answer summary.
- **Restraint.** The loud gradient hero became a bordered masthead with a rule
  of assurances; cards use hairline borders rather than heavy shadows.

**Acceptance criteria**
- [x] Fonts load and apply in both languages.
- [x] One token palette; no ad-hoc colours in components.
- [x] Urdu keeps RTL layout with the new type stack.

---

#### FEAT-05 — Richer screening fields
**Area:** `core/models.py`, `core/rules_engine.py`, `core/i18n.py`, data · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

Six fields were added to `UserProfile`, each because a real Pakistani programme
screens or reserves places on it: `gender`, `field_of_study`, `english_level`,
`computer_skills`, `has_disability`, `is_orphan`.

Four became real eligibility **gates** in the rules engine, with their own
condition keys and bilingual rendering: `gender_required`, `min_english_level`,
`min_computer_skills`, `fields_of_study`. English and computer skills are
ranked vocabularies, so "at least intermediate" is a simple comparison.

**A note on `"none"`:** for English and computer skills, `"none"` is a real
answered value meaning *I have none of this*, and is distinct from Python `None`
meaning *not answered*. The first screens; the second stays "unknown".

Privacy is unchanged — every new field is an attribute, never an identifier
(Invariant 2). Gender carries an explicit note in the UI saying why it is asked.

**Important:** every new gate is `null` in all curated records. Inventing
thresholds would violate Invariant 6. They exist for the data work in DATA-02.

**Acceptance criteria**
- [x] Fields added to the model, wizard, engine, i18n and export.
- [x] All new gates null in curated data; schema.json documents them.
- [x] 13 new rules-engine tests.

---

#### FEAT-06 — Priority groups surfaced as advantages
**Area:** `core/models.py`, `core/rules_engine.py`, `app.py` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

Several records already described reserved places in prose — HEC notes female
and under-served-district priority, PEEF notes orphans, minorities and disabled
students. That was invisible to the engine.

Added `priority_groups` to `EligibilityConditions` and
`matched_priority_groups` to `MatchResult`. When a profile belongs to a group a
programme prioritises, the result card says so.

**These are advantages, never gates.** Not belonging to a priority group can
never exclude anyone, and priority groups add no conditions to the check list —
both are asserted by tests. They also rank matching records slightly higher.

The values populated are a faithful transcription of what each record's own
`special_quota_note` already stated. Nothing new was asserted about any
programme, and they are never inferred from prose at runtime.

**Acceptance criteria**
- [x] Advantage only — cannot reduce eligibility (tested).
- [x] Adds no conditions to the check list (tested).
- [x] Values transcribed from existing notes, not invented.

---

#### PERF-01 — First page load takes ~30–35s because the embedding model is built at session init
**Area:** `app.py:29-30`, `core/rag_engine.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**Measured 2026-09-10** (this machine, warm disk cache, cold process):

| Step | Cost | When it happens |
|---|---|---|
| `import streamlit` | 4.2s | process start |
| `import sentence_transformers` (pulls torch) | ~19s | **first page load**, lazily via `_try_build_chroma` |
| `import torch` | 4.8s | (included in the above) |
| `import chromadb` | 1.2s | first page load |
| Embedding model load (199 weight shards) + HF network calls | ~5–11s | first page load |
| **`RagIndex(opps)` total, cold process** | **24–31s** | **first page load** |
| `load_all_opportunities()` | 0.00s | negligible |
| `retrieve()` once built | 0.04s | negligible |
| `RagIndex` rebuild, model already in process | 0.15s | negligible |

**What's wrong**
`app.py:29-30` builds `RagIndex` unconditionally during session-state initialisation — before a single pixel renders. That drags a full PyTorch + sentence-transformers import and a 199-shard model load onto the critical path of the **first page view**.

The index is used in exactly **one** place: the follow-up chat box at `app.py:175`, which only runs after the user types a question and clicks. Most users — and most demos — never touch it. Everyone pays ~30s for a feature almost nobody reaches, and the profile form and match cards (which need none of it) are blocked behind it.

Note the last row: rebuilding is cheap *once the model is in the process*. The cost is per-process, not per-session — which is exactly what makes it fixable.

**Fix approach** (in order of payoff)
1. **Build the index lazily** — only when the user actually asks a follow-up question. Moves ~30s off first paint entirely.
2. **Wrap it in `@st.cache_resource`** so it is built at most once per process and shared across sessions, instead of living in per-session state.
3. **`@st.cache_data` on `load_all_opportunities()`** — cheap today (0.00s), but correct, and it stops re-reading JSON on every rerun.
4. Show a spinner with honest text ("preparing search, first time only") on the one interaction that does pay the cost.

**Acceptance criteria**
- [ ] First page paint no longer imports torch/sentence-transformers.
- [ ] Time from `streamlit run` to interactive form measured at **under ~5s**.
- [ ] Follow-up chat still works; its one-time cost is visible to the user via a spinner.
- [ ] Index built at most once per process (verify: two browser sessions, one build).

---

#### PERF-02 — Model load makes live network calls to Hugging Face despite the local cache
**Area:** `core/rag_engine.py:49-51` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What's wrong**
`SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")` contacts the HF Hub on every build to check the model revision, even though the weights are already cached locally. Confirmed by the emitted warning: *"You are sending unauthenticated requests to the HF Hub."*

**Measured:** cold `RagIndex` build **30.73s** online vs **24.14s** with `HF_HUB_OFFLINE=1` — roughly **6s of pure network round-trip** on the startup path.

**Why it matters**
Beyond the 6s, this is a **demo-day risk**: on venue wifi that is slow, captive-portalled, or absent, these calls don't fail fast — they hang or retry. A cached model that still needs the internet to load is a cached model that can strand the demo.

**Fix approach**
Force offline resolution — set `HF_HUB_OFFLINE=1` (and/or `TRANSFORMERS_OFFLINE=1`) before the model is constructed, or pass `local_files_only=True` through to the loader. Fail loudly and fall back to keyword search if the cache genuinely isn't there, rather than reaching for the network.

**Acceptance criteria**
- [ ] No HF Hub network request during startup (verify: run with wifi disabled).
- [ ] App still starts, and retrieval still works, with no network at all.
- [ ] Consistent with Invariant 5 (the app must run with no API key and no network).

---

#### PERF-03 — Reconsider whether the vector store is worth its cost at all
**Area:** `core/rag_engine.py`, `requirements.txt` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

**The case for dropping it**
The corpus is **3 documents** (verified in Section 2). Semantic retrieval over 3 short records is close to indistinguishable from keyword matching — `top_k=3` returns essentially the whole corpus either way. For that, the project currently pays: ~24–31s of startup, a PyTorch dependency, a network call (PERF-02), and the Streamlit Cloud deploy risk already tracked as OPS-05.

The keyword fallback is **already written, already tested, and already the documented deploy story** in the README's troubleshooting table.

**The case for keeping it**
The chosen model is *multilingual* — it is what would let an Urdu-language question retrieve an English-language record. That is a real capability, and it matters for the bilingual promise (I18N-01/02). It becomes genuinely valuable once the catalogue grows past a few dozen records.

**Decision needed.** Reasonable resolutions: drop it for the hackathon and keep the code path for later; keep it but make it lazy (PERF-01) and offline (PERF-02); or keep it and precompute embeddings offline (FEAT-04). **Record the choice in the Decision Log.**

**Acceptance criteria**
- [ ] An explicit, written decision exists — not an accident of what was easiest.
- [ ] If dropped: `requirements.txt` updated, keyword path confirmed as the only path, OPS-05 resolved as a side effect.
- [ ] If kept: PERF-01 and PERF-02 are both DONE first.

---

#### PERF-05 — `is_ai_available()` built an SDK client on every render
**Area:** `core/llm_client.py` · **Priority:** P1 · **Status:** **DONE** · **Owner:** —

**What was wrong**
Found while verifying OPS-02, not by looking for it: the moment a real key was
configured, the test suite went from **15.5s to 200s** and first render from
1.07s to ~4s.

`is_ai_available()` answered "could we make a real call?" by *constructing an
SDK client*, and the UI calls it on every render to draw the AI status chip.
That cost ~1.45s to import `google.genai` plus ~1.45s to build the client —
roughly **3s added to every single interaction**, including ticking a document
checkbox.

**Why it stayed hidden**
With no key, `_client()` returned `None` immediately. The entire cost existed
only in the configured state — which is to say, only in the demo. All the
startup work in PERF-01/02 would have been silently undone at the worst moment.

**What was done**
1. `is_ai_available()` and `active_sdk()` now answer from the key plus
   `importlib.util.find_spec`, which imports nothing and is free.
2. Client construction moved to `_build_client()`, `lru_cache`-d on the key, so
   it happens once per process and only when an AI button is actually pressed.

**Trade-off, accepted deliberately:** a present-but-malformed key now reads as
"available" on the status chip. That is safe — OPS-01 wraps every call path, so
a bad key surfaces as a labelled message at the moment of use, and the
rules-based result the product actually promises is unaffected.

**Measured after**

| | Before (with key) | After |
|---|---|---|
| First render | ~4s | **1.64s** |
| Subsequent rerun | ~3s | **0.17s** |
| Full test suite | 200.2s | **15.5s** |

Heavy modules imported at first render: **none**.

**Acceptance criteria**
- [x] The status chip costs no import and no client build.
- [x] The SDK is imported only when an AI feature is actually used.
- [x] Client built at most once per process per key.
- [x] Regression test asserts `is_ai_available()` never calls `_build_client()`.

---

#### PERF-04 — No `.streamlit/config.toml`
**Area:** `.streamlit/` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

The folder holds only `secrets.toml.example`. A `config.toml` would let the project turn off the usage-stats ping (`browser.gatherUsageStats = false` — one fewer network call at startup), pin `server.headless`, and tune `server.fileWatcherType` (the default watcher walks the project tree — and `venv/` sits inside this folder, so it may be scanning thousands of dependency files on every rerun).

**Worth testing specifically:** whether excluding `venv/` from the file watcher measurably improves *rerun* latency, which is a different problem from first-load latency and is felt on every single button click.

**Acceptance criteria**
- [ ] `config.toml` committed with usage stats off.
- [ ] File-watcher behaviour checked against the in-folder `venv/`.
- [ ] Rerun latency measured before and after, and the numbers written down.

---

### P2 — Robustness and quality

---

#### BUG-05 — Profile selectboxes never seed from the saved profile
**Area:** `app.py:60-73` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

`age` and `marks` seed from `p.age` / `p.marks_percentage`, but `domicile`, `education`, `enrolled`, `existing_scholarship`, and `employment` are all hardcoded `index=0`. Streamlit's own widget-state persistence masks this in normal use, but the inconsistency will bite the moment a profile is restored from anywhere other than the widgets themselves (a saved session, a URL param, a future "edit my profile" flow).

**Acceptance criteria**
- [ ] Every field seeds from `st.session_state.profile`.
- [ ] Setting a profile programmatically is reflected in the rendered form.

---

#### BUG-06 — Keyword fallback returns arbitrary docs as "evidence"
**Area:** `core/rag_engine.py:81` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

`_keyword_fallback` ends with `... or self._docs[:top_k]` — when no query term matches any document, it returns the first N documents anyway. Those are then passed to `answer_followup` as *evidence* and presented to the model as grounding.

The `CHAT_SYSTEM_PROMPT` does instruct the model to say it lacks verified information when the evidence doesn't answer the question, which mitigates this — but handing a model irrelevant text and labelling it "Evidence" invites exactly the grounding failure this architecture is built to avoid.

**Fix approach**
Return an empty list on no match and let the caller show an honest "no relevant information found — check the official source" message. Note that `answer_followup` already handles the empty case (`"(no evidence retrieved)"` at line 109).

**Acceptance criteria**
- [ ] A query with no term overlap returns `[]`.
- [ ] The UI shows an explicit "nothing relevant found" message rather than an answer built on unrelated documents.

---

#### OPS-03 — Bare `except` in the Chroma path hides all failure detail
**Area:** `core/rag_engine.py:43-64` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

> **Corrected 2026-09-10.** This entry originally claimed that re-adding duplicate IDs on a second session raises, gets swallowed, and silently degrades retrieval to keyword search. **That was tested and is false** — three consecutive `RagIndex` builds in one process all kept `chroma_collection` active with `count() == 3`. ChromaDB 1.5.9 tolerates the duplicate `add()`. Priority dropped P2 → P3 accordingly. The startup cost this entry mentioned in passing turned out to be the real problem and is now tracked separately as **PERF-01**.

What remains is a smaller, genuine issue: the bare `except Exception:` at line 60 swallows *every* failure — missing package, corrupt cache, no network, model-load error — into an identical silent fallback with no log line. If retrieval quality ever looks wrong, there is no way to find out whether Chroma is even running.

**Fix approach**
Keep the fallback (it is good design), but record why it triggered — log the exception and expose the active mode (`chroma` vs `keyword`) somewhere a developer can see it.

**Acceptance criteria**
- [ ] The reason for any fallback is recoverable (logged, or surfaced in a debug expander).
- [ ] Which retrieval mode is active is visible to a developer without a debugger.

---

#### OPS-04 — Repo is not under version control
**Area:** repo root · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

`git init` has never been run. There is a well-formed `.gitignore` (correctly excluding `.env`, `.streamlit/secrets.toml`, `venv/`, `chroma_db/`) waiting to be used, and README Step 9 assumes a GitHub repo exists for the Streamlit Cloud deploy.

**Why it matters**
No history, no rollback, no collaboration, and no deploy path. Every item in this tracker is riskier to attempt without it.

**Acceptance criteria**
- [ ] `git init`, initial commit made.
- [ ] Confirmed `venv/` and any real secrets file are **not** tracked.
- [ ] Pushed to a remote the whole team can access.

---

#### OPS-05 — Heavy deps will likely break the Streamlit Cloud deploy
**Area:** `requirements.txt` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

`chromadb>=0.5` and `sentence-transformers>=3.0` are active (not commented) in `requirements.txt`. `sentence-transformers` pulls in PyTorch. The README's own troubleshooting table already predicts this will exceed Streamlit Community Cloud's free-tier build resources.

**Fix approach**
Decide deliberately: either comment both out for the deployed build and accept keyword search in production (a defensible hackathon tradeoff — and the fallback is already implemented and tested), or attempt the deploy early enough that there's time to react if it fails. **Do not discover this at deploy time on demo day.** Record the choice in the Decision Log.

**Acceptance criteria**
- [ ] A successful deploy to a public URL exists.
- [ ] It is known and written down whether the deployed instance uses Chroma or keyword fallback.
- [ ] Deployment secrets are configured and the AI features verified working *on the deployed URL*, not just locally.

---

#### I18N-03 — No RTL layout for Urdu
**Area:** `app.py` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

Urdu strings render left-to-right in Streamlit's default layout. Mixed Urdu/English lines (which is most of the UI right now) will read awkwardly.

**Fix approach**
Inject scoped CSS setting `direction: rtl; text-align: right;` on the main container when `lang == "ur"`. Verify numbers, the match-card expanders, and the condition list still read correctly — RTL with embedded Latin-script numbers and URLs is where this usually goes wrong. Best tackled *after* I18N-01 and I18N-02, when there is actually full Urdu content to lay out.

**Acceptance criteria**
- [ ] Urdu mode renders right-to-left.
- [ ] Numbers, URLs, and status badges remain legible and correctly ordered.
- [ ] English mode is completely unaffected.

---

#### TEST-01 — No tests outside the rules engine
**Area:** `tests/` · **Priority:** P2 · **Status:** **DONE** · **Owner:** —

`tests/test_rules_engine.py` is genuinely good — 8 focused tests, zero external dependencies, covering eligible / hard-fail / unknown / income / education rank / exclusivity / no-conditions / expired-deadline. But it is the *only* test file. `data_loader`, `ad_reader`, `rag_engine`, `i18n`, and the mock paths in `llm_client` are untested.

**Suggested additions (in value order)**
1. `data_loader` — the `jobs` list unwrapping, the `REPLACE ME` skip, `schema.json` exclusion, underscore-prefixed file exclusion.
2. `ad_reader.read_ad` — with a stubbed extractor: correct `source_type`, disclaimer present, `None` values handled, missing keys defaulted.
3. `llm_client` mock paths — all three functions return labelled mock output with no key set.
4. `i18n.t` — missing key returns the key; missing language falls back to `en`.
5. `rag_engine._keyword_fallback` — after BUG-06 is fixed.

**Acceptance criteria**
- [ ] Each module above has at least one test file.
- [ ] Full suite still runs with no network and no API key.
- [ ] `python -m unittest discover tests` stays green.

---

### P3 — Polish and lower-priority correctness

---

#### BUG-07 — No `n/a` check when `application_deadline` is absent
**Area:** `core/rules_engine.py:174` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

Every other condition appends an explicit `"n/a"` `ConditionCheck` when the opportunity doesn't use it. The deadline branch appends nothing at all when `ec.application_deadline` is `None`. Harmless today (the UI skips `n/a` anyway) but it makes the checks list inconsistent in length and shape, which will surprise anyone writing analytics or tests over it later.

**Acceptance criteria**
- [ ] Deadline follows the same `n/a` convention as every other check.
- [ ] Existing tests still pass.

---

#### BUG-08 — Misleading detail text on the existing-scholarship check
**Area:** `core/rules_engine.py:141-145` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

The logic is correct (`ok = not (required and has_one)`), but the detail string is always `f"You already receive a scholarship: {profile.has_existing_scholarship}"` — so a user who does *not* have one sees "You already receive a scholarship: False", which reads as a contradiction. Fold this into I18N-02 when the detail strings are restructured.

**Acceptance criteria**
- [ ] Detail text reads correctly in both the True and False cases, in both languages.

---

#### BUG-09 — `st.image(...) if ... else None` used as a statement
**Area:** `app.py:193` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

A conditional expression evaluated purely for its side effect. It works, but it's the kind of line that makes a reviewer stop. Replace with a plain `if mime_type.startswith("image/"): st.image(...)`.

**Acceptance criteria**
- [ ] Replaced with a normal `if` statement; behaviour unchanged.

---

#### OPS-06 — `explain_match` sends a raw dataclass repr as the profile summary
**Area:** `app.py:131` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

`profile_summary = str(st.session_state.profile)` sends `UserProfile(age=20, domicile_province='Punjab', ...)` to the model. It works, and it is **privacy-safe** (the model has no PII fields by design — see Section 6), but a natural-language summary would produce noticeably better explanations, and it's a one-function change.

**Acceptance criteria**
- [ ] A readable prose summary is sent instead of the repr.
- [ ] `None` fields are described as "not provided", not omitted silently.
- [ ] Still contains no identifying information.

---

#### FEAT-01 — Document-readiness checklist
**Area:** `app.py` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

`i18n.py:50` already defines `document_checklist_heading` in both languages, but nothing uses it. `required_documents` renders as a static bullet list. Making it interactive tick-boxes (with state) turns a passive list into an actionable prep tool.

**Depends on:** nothing. Good candidate once P0/P1 are clear.

**Acceptance criteria**
- [ ] Tick state persists across reruns per opportunity.
- [ ] Progress is visible (e.g. "3 of 7 ready").
- [ ] The unused i18n key is now used.

---

#### FEAT-02 — Export / share a match summary
**Area:** `app.py` · **Priority:** P3 · **Status:** **DONE** · **Owner:** —

Let a user download or copy a summary of their matches, required documents, and application steps. Must carry the same disclaimers and the same curated-vs-uploaded trust distinction as the on-screen version — a stripped-down export that loses the "AI-read, verify against the original" badge would be a real regression.

---

#### FEAT-03 — Layer 6, Impact analytics · **DEFERRED**

Deliberately deferred per the original plan (README Section 5) as the first thing to cut under time pressure. Do not start this before every P0 and P1 is DONE.

---

#### FEAT-04 — Persistent on-disk vector store · **DEFERRED**

`scripts/build_vector_store.py` was never written; `scripts/` is empty. Only worth building if OPS-03 is fixed and startup cost is still a real problem. `.gitignore` already anticipates it with a `chroma_db/` entry.

---

## 5. Suggested sequencing

Phases, not deadlines. Each phase should leave the app in a demonstrable state.

**Phase 0 — Make it safe to work** ✅ DONE
`OPS-04` (git init) — everything below is safer with version control underneath it.

**Phase 1 — Stop the bleeding** ✅ DONE
`BUG-01` → `BUG-02` (upload tab works at all) → `DATA-01` (nothing embarrassing on screen).
*Exit criteria: every visible path through the app either works or is honestly labelled as unavailable.*

**Phase 1.5 — Make it fast** ✅ DONE — first render 1.07s
`PERF-01` (lazy + cached index) → `PERF-02` (offline model load).
*Exit criteria: `streamlit run` to an interactive form in under ~5s, with wifi disabled.*

**Phase 2 — Truth** ⚠️ PARTIAL — `DATA-02` (verify the real numbers) is the one blocker left; it needs a human with the official sources
`DATA-02` (verify the numbers) → `DATA-03` (jobs: fill or flag) → `DATA-04` (jobs: filled) → `OPS-02` (model name) → `OPS-01` (Gemini error handling). `DATA-07` (public assistance) closed the last empty category.
*Exit criteria: nothing shown to a user is unverified or capable of crashing the page.*

**Phase 3 — Deliver the bilingual promise** ✅ DONE
`I18N-01` → `I18N-02` → `I18N-03`.
*Exit criteria: an Urdu-first user gets a genuinely Urdu experience, including the reasons.*

**Phase 4 — Correctness of the core** ✅ DONE
`BUG-03` (zero values) → `BUG-04` (stale vs ineligible) → `TEST-01` (lock it all in).
*Exit criteria: the rules engine's output is trustworthy at the edges, and tests prevent regression.*

**Phase 5 — Ship it**
`OPS-05` (deploy, early enough to react) → README Step 10 (test ad reading with **real** photographs before demo day, not during it).

**Phase 6 — Only if there's time**
`OPS-03`, `BUG-05`–`BUG-09`, `OPS-06`, `FEAT-01`, `FEAT-02`.

---

## 6. Invariants — do not break these

These are load-bearing. If a change would violate one, stop and discuss it rather than working around it.

1. **The rules engine decides; the LLM explains.** `core/rules_engine.py` must never call an LLM, and no LLM output may alter an eligibility outcome. This is the entire reason the architecture is shaped this way.
2. **`UserProfile` holds no identifying data.** No name, CNIC, phone, or address — ever. If a new field seems necessary to "match better", first establish it is needed for *eligibility logic*, not identity.
3. **Uploaded files are never persisted.** `core/ad_reader.py` keeps bytes in memory for the request only.
4. **Curated and user-uploaded records never share a trust badge.** `officially_verified_badge` and `ai_extracted_badge` must stay visually and semantically distinct everywhere, including in any future export (FEAT-02).
5. **The app must run with no API key and no network** — the mock-mode fallbacks stay. This is what lets teammates work in parallel and what keeps a demo alive when the wifi dies.
6. **No eligibility criterion is invented.** If it isn't in the official source or the uploaded document, the value is `null` — not a plausible guess.

---

## 7. Decision log

Record any choice that a future reader might otherwise reverse by accident. Append; never edit a past entry.

| Date | Decision | Rationale | Made by |
|---|---|---|---|
| 2026-09-10 | Tracker created as `PROJECT_TRACKER.md` in the repo root | Work tracking lives beside the code and under version control, separate from `README.md`'s setup role | — |
| 2026-09-11 | **BUG-04** — a closed listing is a separate `MatchResult.listing_closed` flag, not a fourth status | Keeps the three profile statuses purely about the profile. A qualified person against an expired listing now reads "Likely Eligible" + "Applications closed", which is the truth | Claude |
| 2026-09-11 | **DATA-03** — empty categories are derived from the data and shown disabled as "Coming soon" | Automatic and self-correcting: the moment real job records land, Jobs switches on with no code change. Honest rather than a blank result set | Claude |
| 2026-09-11 | **OPS-05 / PERF-03** — semantic search is opt-in (`SAHULAT_SEMANTIC_SEARCH=1`); keyword is the default, and chromadb/sentence-transformers are commented out of `requirements.txt` | A 3-document corpus gains almost nothing from embeddings but pays ~25-30s of startup, a PyTorch dependency and the Cloud build risk. The multilingual path is preserved for when the catalogue grows | Claude |
| 2026-09-11 | **OPS-02** — support BOTH SDKs rather than migrating outright | `google-genai` is not installed here, so a hard migration would have broken a working app. `llm_client` now prefers the current SDK and falls back to the EOL one, so `pip install google-genai` is the whole migration | Claude |
| 2026-09-11 | **BUG-01** — one shared profile form, not two keyed copies | The upload tab reusing the Catalog profile removes the duplicate-widget collision by construction instead of papering over it, and is less to fill in | Claude |
| 2026-09-13 | **BRAND-02** — the placeholder mark was deleted, not kept alongside | Two logos in one repository is exactly how a brand rots: the header gets updated and the favicon and press kit keep the old drawing, because no page shows both at once. The BRAND-01 mark exists in git history if it is ever wanted | Claude |
| 2026-09-13 | **BRAND-02** — a measured skew is refused unless it fits a line | The ribbon's curve reads as -7.7 degrees across the full width. A correction that is confidently wrong is worse than none: it would rotate clean artwork into crookedness, and nobody would look for the cause in a deskew step | Claude |
| 2026-09-13 | **BRAND-02** — the logo is corrected by a script, not by hand | A hand-fixed PNG is unreproducible and unreviewable. A script makes the deskew and background removal deterministic, lets a better source file regenerate everything, and lets a test rebuild each asset and compare bytes | Claude |
| 2026-09-13 | **BRAND-02** — the logo is not on the home hero | The hero already leads with a headline and a live screening result, and the header sits directly above it. Placing it there would compete with both. "Everywhere it is necessary" is not everywhere | Claude |
| 2026-09-12 | **BRAND-01** — the symbol carries no gold | The guide makes gold optional and requires the mark to work without it. Rendered, the accent was a floating crescent that read as an eyebrow and turned to mush below 32px. Gold moved to the Urdu wordmark, where the guide also offers it | Claude |
| 2026-09-12 | **BRAND-01** — candidates were rasterised and compared before one was chosen | The original mark looked correct in coordinates and read as a dumbbell on screen. A logo cannot be reviewed from its geometry | Claude |
| 2026-09-12 | **UI-05** — the hero animates continuously, against the V3 spec's own 40.5 and 13.3 | Waleed asked for it directly. Mitigated rather than argued: a slow cadence so each card reads as settled, and a hard stop under reduced motion. Logged so a later reader of the spec does not file it as a bug | Waleed |
| 2026-09-12 | **UI-05** — the rotation shows one match per category, not the overall top four | The overall top four is three NAVTTC courses. Accurate, and it would advertise a catalogue of nothing but courses | Claude |
| 2026-09-12 | **UI-03** — the hero preview renders a real screening result, not a designed example card | The spec asked for a product demonstration in the hero. The obvious implementation is a mockup, which would be the one fabricated thing on the landing page of a product built on not fabricating. Running the real engine costs one cached screening pass and cannot drift from the truth | Claude |
| 2026-09-12 | **UI-02** — only the featured match loses its expander, not all 30 | Spec 45.2 permits expanders for secondary information, and on card seven the detail genuinely is secondary. Unfolding all thirty would be the dashboard overload spec 4.6 warns about | Claude |
| 2026-09-12 | **DATA-07** — unaskable gates (PMT score, pregnancy, religion) are stated as prose rather than approximated as fields | A proxy screened silently would report "eligible" against a rule the programme does not use. The honest version shows what can be checked and says on the card what cannot | Claude |
| 2026-09-12 | **DATA-09** — `required_groups` added rather than reusing `priority_groups` as a gate | Overloading the advantage would have made every existing scholarship's priority list start excluding people. Separate field, opposite force, unanswered reads as a question and not a rejection | Claude |
| 2026-09-12 | **DATA-04** — the Jobs catalogue records recruitment *streams*, not named vacancies | A named vacancy is true for about three weeks and then misleads. The eligibility rules behind a recurring stream are stable year to year, and the rules are what the engine screens on | Claude |
| 2026-09-12 | **DATA-04** — job records were marked verified after shipping as `needs_recheck` | Claude's position was that the badge should follow the check. Waleed's call, as owner of the data and of the demo: a half-red catalogue reads as unfinished, and the cross-check belongs after the data stops moving. Recorded here because it is a deliberate reversal, not an oversight - the guard requiring real dates behind a badge stays in force | Waleed |
| 2026-09-12 | **DATA-02** — deadlines were supplied, but flagged rather than asserted | The user asked for demo-suitable dates and that is reasonable for a prototype. A countdown is the most confident element on the page, so the honest version is to show it *and* say the date is ours. One boolean flips when a cycle is announced | Claude |
| 2026-09-12 | **DATA-02** — prose in `min_computer_skills` set to null, not mapped to a level | The field is a ranked vocabulary the engine compares against. Guessing "basic" would have invented a gate; the record's own wording says it is not a requirement | Claude |
| 2026-09-12 | **P2-1** — Roman Urdu ships at 100% coverage or not at all | A partially translated mode switches script mid-page, which is worse than not offering it. A coverage test is what makes the mode safe to ship and safe to extend | Claude |
| 2026-09-12 | **P2-1** — Roman Urdu is left-to-right | It is Urdu language in Latin script. Mirroring the page because it is "the Urdu one" would be a plausible and wrong shortcut; `is_rtl()` keeps that decision in one place | Claude |
| 2026-09-12 | **P2-2** — one constant behind the time estimate, printed in the UI | The figure cannot be counted, only assumed. Naming the assumption is what keeps the three counted figures credible in the room where it matters | Claude |
| 2026-09-12 | **P2-5** — `AiText` subclasses `str` rather than replacing it | The UI needs to know whether it got an answer or a notice; string-sniffing is not a way to know that. Subclassing keeps every existing call site working | Claude |
| 2026-09-12 | **P1-1** — a readiness percentage IS shown, unlike a match score | Every term is something the user ticked or the record lists, and it is computed from the rows displayed beneath it. A match score would be a guess at an awarding body's decision; this is arithmetic over a checklist | Claude |
| 2026-09-12 | **P1-2** — "no deadline on record" is a fifth state, not "plenty of time" | Every curated record currently has a null deadline, so this is the state users meet most often. Folding it into the benign band would turn missing data into reassurance across the whole catalogue | Claude |
| 2026-09-12 | **P1-5** — the comparison names no winner when the numbers are close | Below a set margin it returns no leader. Manufacturing one turns a comparison into a recommendation, and "less effort" is not "better" | Claude |
| 2026-09-12 | **P1-7** — the simplifier is given no profile and no verdict | The brief's "simplify, do not reinterpret" rule is enforced by what the model is handed, not by asking it nicely. It cannot leak an eligibility claim it was never told | Claude |
| 2026-09-11 | **V2-1** — count of conditions, not a percentage match score | A percentage reads as a probability of being awarded, which no rule here computes; the brief's own warning describes exactly that misreading. A count is checkable against the rows beneath it | Claude |
| 2026-09-11 | **V2-3** — rank on required-document count, not "missing documents" | The app never learns which documents a user holds; the checklist is UI state. Ranking on "missing" would have required inventing that knowledge. Late tie-break only, documented | Claude |
| 2026-09-11 | **V2-4** — drop extracted values outside the known vocabulary | A mis-mapped gender or field of study becomes a real eligibility gate and wrongly excludes people. Unread is recoverable; wrong is not | Claude |
| 2026-09-11 | **UX-10** — staged progress here, but still not on the results page | The test is whether real work is happening, not whether it looks better. The ad read is a remote call taking 8–12s; rules matching is local and instant. Same rule (spec 10.1), opposite answer | Claude |
| 2026-09-11 | **UX-10** — show what the document did *not* say | A null condition means the document was silent, and silence must never render as a pass. Unstated conditions are listed with an explicit caveat rather than omitted | Claude |
| 2026-09-11 | **OPS-02** — pin `gemini-3.5-flash`, not `gemini-flash-latest` | An alias can change model underneath a live demo, and `-latest` returned 503 when tested. An explicit version is reproducible; `GEMINI_MODEL` still overrides it without a code change | Claude |
| 2026-09-11 | **PERF-05** — the status chip may read "available" for a malformed key | The alternative costs ~3s on every interaction to pre-validate. Every call path is wrapped, so a bad key surfaces as a labelled message at the point of use instead | Claude |
| 2026-09-11 | **UX-09** — no fake "Finding your matches…" delay | The spec asks for the sequence but its own rule 10.1 forbids faking one for instant local work. Rules matching is local and instant; the honest version (count first, then staggered reveal) is implemented instead | Claude |
| 2026-09-11 | **UX-09** — reveal replay gated in Python, not CSS | Streamlit reruns the script on every interaction, so a CSS-only entrance would replay whenever a checkbox was ticked. A session-state token ties each reveal to a real state change | Claude |
| 2026-09-11 | **UX-06** — no percentage "profile fit" score | The spec shows one in a mock (17) but warns against implied precision (18). We have no defensible scoring model, and a number would read as an official probability. The per-condition list says more, honestly | Claude |
| 2026-09-11 | **UX-06** — listing status derived, never asserted | No curated record has a verified deadline, so none shows "Open"; they show "Verify current cycle". Claiming a cycle is open when we do not know would be the most damaging error this product could make | Claude |
| 2026-09-11 | **UX-06** — sidebar removed entirely | It held only language, status and catalogue counts, and its collapse control was the source of the icon artefact. A brand bar plus the How-it-works tab covers the same ground with less chrome | Claude |
| 2026-09-11 | **UX-01** — a step wizard with no `st.form` anywhere | A form submits on Enter, which was the reported bug. Explicit Back/Continue buttons make progression deliberate, and validation lives in a testable module rather than the UI | Claude |
| 2026-09-11 | **UX-01** — only age, domicile and education are required | These three change almost every result, so leaving them blank makes the whole screen read "needs verification". Income and the sensitive fields stay optional, preserving the "never guess, never pressure" stance | Claude |
| 2026-09-11 | **FEAT-06** — priority groups are advantages, never gates | A reserved place helps those inside the group; it must never exclude those outside it. Encoded as data transcribed from each record's own note, never inferred from prose | Claude |
| 2026-09-11 | Eligibility reasons moved to `i18n.describe_check()` | Translating inside the rules engine would have coupled the decision layer to presentation. The engine now emits keys + structured values and stays language-free and independently testable | Claude |

---

## 8. Changelog

Append one line per completed piece of work.

| Date | ID | What changed |
|---|---|---|
| 2026-09-10 | — | Baseline audit completed; tracker created. No code changed. |
| 2026-09-10 | PERF-01..04 | Startup performance profiled; four PERF items added. No code changed. |
| 2026-09-10 | OPS-03 | **Corrected** — the duplicate-ID/silent-degradation claim was tested and disproved. Rewritten and dropped P2 → P3. |
| 2026-09-10 | OPS-02 | Expanded — `google-generativeai` 0.8.6 found to be **end-of-life**, not just possibly-stale on model name. |
| 2026-09-11 | OPS-04 | Repo initialised and pushed to GitHub by the user; tracker committed. |
| 2026-09-11 | — | Branch `feature/ux-overhaul-and-fixes` opened off `main`. |
| 2026-09-11 | *landing page* | `app.py` rebuilt: sidebar (language, live AI status, catalogue health), hero with trust chips, and three tabs — Find / Read an ad / How it works. Numbered 3-step flow, grouped results with KPI row, styled status + trust badges, condition list, interactive document checklist. |
| 2026-09-11 | BUG-01, BUG-02 | Upload tab fixed: one shared profile form (no duplicate widget IDs), extraction persisted in session state with an explicit Clear control. |
| 2026-09-11 | BUG-03 | `number_input(value=None)` replaces `x or None`; zero income / zero experience now screen as real answers. |
| 2026-09-11 | BUG-04 | Closed listings separated from user ineligibility via `MatchResult.listing_closed`. |
| 2026-09-11 | BUG-05..09 | Form seeding, keyword-evidence honesty, deadline `n/a`, scholarship wording, `st.image` statement. |
| 2026-09-11 | DATA-01 | `Opportunity.is_verified()` guards the UI; a `TODO-VERIFY` string can no longer render as a date. |
| 2026-09-11 | DATA-03 | Category availability derived from loaded data; empty categories shown disabled as "Coming soon". |
| 2026-09-11 | I18N-01..03 | Urdu record fields now displayed; all eligibility reasons translated via `describe_check()`; RTL layout for Urdu. |
| 2026-09-11 | OPS-01, OPS-02 | Every Gemini call wrapped with graceful degradation; dual-SDK support (`google-genai` preferred, EOL SDK as fallback). |
| 2026-09-11 | OPS-03, OPS-06 | Fallback reason recorded and exposed via `RagIndex.mode`; prose profile summary replaces the dataclass repr. |
| 2026-09-11 | PERF-01..04 | Lazy + `@st.cache_resource` retrieval, offline model loading, opt-in semantic search, `.streamlit/config.toml`. **First render measured at 1.07s** (was ~30-35s), with no heavy modules imported at page load. |
| 2026-09-11 | TEST-01 | Test suite grown from 8 to **73 passing tests** covering data_loader, models, i18n, ad_reader, llm_client and rag_engine. |
| 2026-09-11 | FEAT-01, FEAT-02 | Document-readiness checklist with progress, and a plain-text results export that preserves every trust marker. |
| 2026-09-12 | **DATA-02** | **Closed.** Waleed verified the eligibility figures and curated 7 more NAVTTC course records: catalogue 3 → **10, all verified**. Metadata (dates, confidence, disclaimers) completed; three `source_date` values were invalid (two in the future, one still `TODO-VERIFY`). |
| 2026-09-13 | **BRAND-02** | **The supplied logo replaces the placeholder mark.** `scripts/prepare_logo.py` lifts it off its background into real transparency and cuts 10 assets into `assets/brand/`; `core/brand.py` now serves artwork rather than drawing a mark; the ten placeholder SVGs deleted. Wired to the tab icon, header and footer. Rebuilt on the 2000px export once it arrived, after the guards that stop auto-deskew rotating straight artwork by 7.7 degrees. Suite 394 → **404**. |
| 2026-09-13 | *(docs)* | README rewritten as a project README rather than the day-one handover checklist. |
| 2026-09-12 | **BRAND-01** | **New mark and a logo system.** `core/brand.py` as the single source of truth, ten generated exports in `assets/`, favicon wired to `page_icon` for the first time, one-per-session draw animation. Suite 368 → **394**. |
| 2026-09-12 | **UI-06** | Language moved into the brand bar as a single picker; the nav row is now three screens and one action. Brand bar became a real columns row, styled via `:has(.sa-brandbar)`. Suite 360 → **368**. |
| 2026-09-12 | **UI-05** | Hero preview cycles through four real results, one per category, on a 16s CSS loop. Reduced-motion override added — the blanket 1ms rule would have parked every card on an `opacity: 0` keyframe and blanked the hero. Suite 351 → **360**. |
| 2026-09-12 | **UI-04** | Staged progress on all four remaining AI calls, replacing wordless spinners. Four labelled steps on the follow-up Ask, with pending steps dimmed and blurred. Suite 335 → **351**. |
| 2026-09-12 | **UI-01/02/03** | **V3 visual spec, structural pass.** Top-level tabs replaced by stateful screens with real header navigation; featured match shows its verdict inline; hero renders a real screening result instead of a decorative SVG. First render 1.16s → **1.05s**. |
| 2026-09-12 | TEST-04 | `tests/test_v3_visual.py` (17 tests), including an assertion that the hero preview is a real catalogue record and the engine's actual top match. Suite 318 → **335**. |
| 2026-09-12 | **DATA-07** | **Public Assistance filled — no category is empty.** 10 records in `public_assistance.json` (BISP ×3, Bait-ul-Mal ×2, Himmat Card, Zakat Guzara, Sehat Sahulat, interest-free loan, EOBI). Catalogue 20 → **30**. Assistance got its own landing path. |
| 2026-09-12 | DATA-09 | `required_groups` gate added: three-valued membership, OR semantics, only the three groups a profile can answer. |
| 2026-09-12 | DATA-10 | `enrolment_is_continuous` splits "never closes" from "no date on record". New `LISTING_ALWAYS_OPEN` / `URGENCY_CONTINUOUS` and `match_urgency()`. |
| 2026-09-12 | TEST-03 | `tests/test_assistance_catalogue.py` (24 tests). Suite 292 → **318**. Also fixed two tests that passed `"roman"` as a language code - it is `"ur_roman"`, so they had been silently asserting English three times. |
| 2026-09-12 | DATA-08 | All 20 records marked verified with real `last_verified` and `source_date` values; catalogue renders 20/20 "Officially verified". "Checked 0 days ago" corrected to "Checked today" in all three languages. Suite → **292**. |
| 2026-09-12 | **DATA-04** | **Jobs category filled.** 10 curated federal and provincial recruitment streams in `government_jobs.json`; the `REPLACE ME` skeleton file removed. Catalogue 10 → **20**. The landing path switched on with no code change. |
| 2026-09-12 | TEST-02 | New `tests/test_jobs_catalogue.py` (26 tests). Guards every vocabulary field across the whole catalogue - the `min_computer_skills` prose bug and the province-string mismatch are now both impossible to reintroduce silently. Suite 261 → **288**. |
| 2026-09-12 | DATA-05 | Eight records were silently absent - concatenated JSON failed to parse and the file was skipped. Loader now accepts list-shaped files. |
| 2026-09-12 | DATA-06 | Provisional deadlines flagged and labelled in the UI, so a placeholder date cannot render as an announced one. |
| 2026-09-12 | TEST-01 | Suite grown 259 → **261 tests**. |
| 2026-09-12 | **V2 P2** | Branch `v2`: Roman Urdu (third language, 445/445 strings), impact figures, visual polish incl. result-detail tabs and Urdu leading, empty states with routes out, and degraded-AI handling via `AiText`. New modules `core/i18n_roman.py`, `core/impact.py`. |
| 2026-09-12 | TEST-01 | Suite grown 233 → **259 tests** (new `tests/test_p2_features.py`). |
| 2026-09-12 | **V2 P1** | Branch `v2`: application readiness, deadline intelligence, scoped contextual Q&A, opportunity passport, comparison, freshness, plain-language explainer, source presentation. New modules `core/readiness.py`, `core/timeliness.py`, `core/comparison.py`. |
| 2026-09-12 | TEST-01 | Suite grown 195 → **233 tests** (new `tests/test_p1_features.py`). |
| 2026-09-11 | **V2 P0** | Branch `v2`: eligibility scorecard, why/why-not explanations, deterministic top matches, Lens schema + correction, trust tests, next best action, architecture showcase, landing paths. New module `core/next_action.py`. |
| 2026-09-11 | TEST-01 | Suite grown 143 → **195 tests** (new `tests/test_v2_features.py`). |
| 2026-09-11 | UX-10 | Upload result rebuilt as a readable document summary (raw JSON moved behind a disclosure); conditions rendered in prose via a shared i18n path, with unstated ones shown and explicitly not counted as qualifying. |
| 2026-09-11 | UX-10 | `read_ad()` split into `extract_raw()` + `build_record()` so a four-stage progress panel can advance on real call boundaries during the ~12s model read. No timers, no padded delays. |
| 2026-09-11 | TEST-01 | Suite grown 132 → **143 tests**. |
| 2026-09-11 | OPS-02 | **Unblocked — key configured.** `gemini-2.0-flash` was found to be **retired (404)**; every AI feature would have failed at once. Six candidates measured; `gemini-3.5-flash` chosen and verified on the text, Urdu and image paths. |
| 2026-09-11 | PERF-05 | **Regression caught during that verification** — `is_ai_available()` built an SDK client on every render, adding ~3s per interaction, but only when a key existed. Made free; client now cached and lazily built. Suite 200s → 15.5s. |
| 2026-09-11 | *(fixed)* | `.streamlit/secrets.toml` had the key pasted unquoted, so the TOML failed to parse and Streamlit fell back to mock mode without saying why. Quotes added. |
| 2026-09-11 | TEST-01 | Suite grown 130 → **132 tests**. |
| 2026-09-11 | UX-07 | **Reported bug fixed** — the document checklist count and bar were written before the checkboxes were read, so they lagged one interaction. Deferred into a reserved container; readiness now rebuilt from the widgets each run. |
| 2026-09-11 | UX-08 | Every form control given a visible default boundary plus hover, focus and selected states; gender moved to a segmented control. |
| 2026-09-11 | UX-09 | Stylesheets extracted to `styles/`; header became a distinct navigation layer; category hover, Sahulat Path draw and staggered result reveal added, all gated so they do not replay on unrelated reruns; `prefers-reduced-motion` honoured. |
| 2026-09-11 | *(found & fixed)* | `start_over()` did not clear the animation tokens, so restarting the demo landed on a static page. Caught by a test. |
| 2026-09-11 | TEST-01 | Suite grown 118 → **130 tests**; new `tests/test_app_ui.py` drives the real widgets through AppTest. |
| 2026-09-11 | UX-04 | **Regression I introduced** - a broad `[class*="st-"]` font rule also matched Streamlit's Material icon spans, so `keyboard_double_arrow_right` rendered as literal text. Selector dropped and an icon-font guard added. |
| 2026-09-11 | UX-05 | Hid the "Press Enter to apply" input hint, the Deploy button and the default header chrome. |
| 2026-09-11 | UX-06 | Civic Intelligence redesign: home page with hero and inline-SVG opportunity map, sidebar removed in favour of a brand bar, warm paper palette with green demoted to an accent, ranked editorial results, visible source provenance, data-driven listing status, document readiness, application timeline, judge-facing pipeline view, sample demo profile, prompt chips, human error states, mobile breakpoints. |
| 2026-09-11 | TEST-01 | Suite grown 110 → **118 tests** (listing status, sample profile). |
| 2026-09-11 | UX-01 | Single `st.form` replaced by a validated four-step wizard; Enter can no longer submit a half-filled profile. Step rules extracted to `core/validation.py`. |
| 2026-09-11 | UX-02 | All decorative emoji removed; only the `✓` / `✕` condition dingbats remain. |
| 2026-09-11 | UX-03 | Design system added: Source Serif 4 + Inter (Nastaliq + Naskh for Urdu), one colour-token palette, and a component set (masthead, stepper, panel, badge, callout, KPI, answer summary). |
| 2026-09-11 | FEAT-05 | Six screening fields added (gender, field of study, English, computer skills, disability, orphan); four new rules-engine gates, all null in curated data. |
| 2026-09-11 | FEAT-06 | `priority_groups` surfaced as advantages, transcribed from each record's existing quota note. |
| 2026-09-11 | TEST-01 | Suite grown 73 → **110 tests** (validation: 24, new gates: 13). |
| 2026-09-11 | *(found & fixed)* | Streamlit rejects an `int` seed on a float `number_input` — a profile holding `75` rather than `75.0` crashed the form. Added `_as_float`/`_as_int` coercion. |

---

## 9. Open questions

Things that need a human answer before the work they block can proceed.

- [ ] **Who owns data verification (DATA-02)?** It is the largest single time investment and the highest-value item. It needs a named person.
- [ ] **Is a Gemini API key available yet?** `OPS-02` and the real-image testing of README Step 10 are blocked until one exists.
- [ ] **What is the actual demo date/time?** Every "before the demo" item needs a real deadline to be sequenced against.
- [ ] **Does the Upload tab need its own profile form** (BUG-01), or should it reuse the profile from the Catalog tab? The second is simpler and probably better UX.
- [ ] **Commit the UI/UX redesign spec to `docs/`** — UX-06 cites its section numbers, but the document lives outside the repo, so those citations currently resolve to nothing.
- [ ] **Is `assistance` (public assistance schemes) in scope at all?** It is a category in `schema.json` and a "Coming Soon" label in `i18n.py`, but has zero records and no plan attached.

# Sahulat AI — Project Tracker

**Single source of truth for issues, fixes, and future direction.**
Companion to `README.md` (which is the *setup* guide). This file is the *work* guide.

- **Created:** 2026-09-10
- **Last updated:** 2026-09-10 (startup performance profiled; PERF-01..04 added; OPS-03 corrected)
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

## 2. Verified baseline (as of 2026-09-10)

This is the confirmed state of the repo, established by actually running things — not by reading the README.

| Item | Verified result |
|---|---|
| Python | 3.12.4 (local `venv/`) |
| Unit tests | **8/8 pass** — `Ran 8 tests in 0.007s / OK` |
| Data loader | Loads **3** opportunities: `hec_balochistan_fata_ug` (scholarship), `navttc_hunarmand_pakistan` (skills), `peef_punjab_undergraduate` (scholarship) |
| Job records loaded | **0** — all `njp_jobs_sample.json` entries are `REPLACE ME` placeholders and are correctly skipped by the loader |
| Dependencies | streamlit 1.63.0, google-generativeai 0.8.6, chromadb 1.5.9, sentence-transformers 6.0.1 — **all installed**, including the heavy optional pair |
| Embedding model | `paraphrase-multilingual-MiniLM-L12-v2` **already cached** in the local HF hub → the real Chroma path will be attempted, not the keyword fallback |
| Gemini API key | **Not configured.** No `.env`, no `.streamlit/secrets.toml`. App runs in labelled mock mode. |
| `scripts/` | Empty directory (consistent with README — `build_vector_store.py` was never written) |
| Git | **Not a git repository yet.** See `OPS-04`. |

### Architecture map

```
app.py  (Streamlit UI — 2 tabs: Catalog / Upload ad)
   |
   +-- core/data_loader.py --> data/opportunities/*.json --> Opportunity
   |
   +-- core/rules_engine.py   THE decision layer. Pure stdlib, no LLM, no network.
   |       evaluate() -> 10 independent checks, each met | unmet | unknown | n/a
   |       roll-up:  any "unmet"   -> "Likely Not Eligible"
   |                 any "unknown" -> "Needs Verification"
   |                 else          -> "Likely Eligible"
   |
   +-- core/llm_client.py     Gemini wrapper: explain_match / answer_followup / extract.
   |       No key -> clearly-labelled "[Local mock mode]" fallback for all three.
   |
   +-- core/ad_reader.py      upload bytes -> Gemini JSON -> Opportunity
   |       tagged source_type="user_uploaded"; file never written to disk
   |
   +-- core/rag_engine.py     Chroma in-memory; falls back to keyword search on any exception
   +-- core/i18n.py           flat {key: {en, ur}} dict
```

---

## 3. Work board

Ordered by priority, then by ID. **This table is the at-a-glance status; details are in Section 4.**

| ID | Title | Area | Priority | Status | Owner |
|---|---|---|---|---|---|
| BUG-01 | Duplicate widget IDs crash the Upload tab | `app.py` | **P0** | TODO | — |
| BUG-02 | Upload tab result vanishes on rerun (no session state) | `app.py` | **P0** | TODO | — |
| DATA-01 | `TODO-VERIFY` placeholder text renders in the live UI | data + `app.py` | **P0** | TODO | — |
| DATA-02 | Verify HEC / PEEF / NAVTTC eligibility figures against source | data | **P0** | TODO | — |
| BUG-03 | Zero income / zero marks silently become "not provided" | `app.py` | **P1** | TODO | — |
| BUG-04 | Expired deadline reported as user ineligibility | `rules_engine.py` | **P1** | TODO | — |
| I18N-01 | `name_ur` / `summary_ur` exist in data but are never displayed | `app.py` | **P1** | TODO | — |
| I18N-02 | Eligibility reasons are hardcoded English | `rules_engine.py` + `i18n.py` | **P1** | TODO | — |
| DATA-03 | "Jobs" category is selectable but always returns nothing | data + `app.py` | **P1** | TODO | — |
| OPS-01 | No error handling around any Gemini call | `llm_client.py` | **P1** | TODO | — |
| OPS-02 | Confirm model name — `google-generativeai` is **EOL** | `llm_client.py` | **P1** | TODO | — |
| PERF-01 | First page load ~30–35s: embedding model built at session init | `app.py` + `rag_engine.py` | **P1** | TODO | — |
| PERF-02 | Model load hits the network despite the local cache (~6s + demo risk) | `rag_engine.py` | **P1** | TODO | — |
| BUG-05 | Profile selectboxes never seed from the saved profile | `app.py` | **P2** | TODO | — |
| BUG-06 | Keyword fallback returns arbitrary docs as "evidence" | `rag_engine.py` | **P2** | TODO | — |
| OPS-04 | Repo is not under version control | repo | **P2** | TODO | — |
| OPS-05 | Heavy deps will likely break Streamlit Cloud deploy | `requirements.txt` | **P2** | TODO | — |
| I18N-03 | No RTL layout for Urdu | `app.py` | **P2** | TODO | — |
| TEST-01 | No tests for data_loader, ad_reader, rag_engine, i18n | `tests/` | **P2** | TODO | — |
| PERF-03 | Is the vector store worth its cost for a 3-document corpus? | `rag_engine.py` | **P2** | TODO | — |
| OPS-03 | Bare `except` in the Chroma path hides all failure detail | `rag_engine.py` | **P3** | TODO | — |
| PERF-04 | No `.streamlit/config.toml` (usage ping, file watcher over `venv/`) | `.streamlit/` | **P3** | TODO | — |
| BUG-07 | `application_deadline` produces no `n/a` check when absent | `rules_engine.py` | **P3** | TODO | — |
| BUG-08 | Misleading detail text on the existing-scholarship check | `rules_engine.py` | **P3** | TODO | — |
| BUG-09 | `st.image(...) if ... else None` used as a statement | `app.py` | **P3** | TODO | — |
| OPS-06 | `explain_match` sends a raw dataclass repr as the profile summary | `app.py` | **P3** | TODO | — |
| FEAT-01 | Document-readiness checklist (interactive tick-boxes) | `app.py` | **P3** | TODO | — |
| FEAT-02 | Export / share a match summary | `app.py` | **P3** | TODO | — |
| FEAT-03 | Layer 6 — Impact analytics | new | **P3** | DEFERRED | — |
| FEAT-04 | Persistent on-disk vector store (`scripts/build_vector_store.py`) | `scripts/` | **P3** | DEFERRED | — |

---

## 4. Detailed issue entries

### P0 — Demo-breaking

---

#### BUG-01 — Duplicate widget IDs crash the Upload tab
**Area:** `app.py` · **Priority:** P0 · **Status:** TODO · **Owner:** —

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
**Area:** `app.py` · **Priority:** P0 · **Status:** TODO · **Owner:** —

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
**Area:** `data/opportunities/*.json`, `app.py` · **Priority:** P0 · **Status:** TODO · **Owner:** —

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

**Acceptance criteria**
- [ ] Zero `TODO-VERIFY` strings remain in the three curated files.
- [ ] Each has a real `last_verified` date and `confidence_status: "verified"`.
- [ ] Each record's `disclaimer` is updated or removed to reflect its now-verified state.
- [ ] The verification log above is filled in.

---

### P1 — Core promise not delivered

---

#### BUG-03 — Zero income / zero marks silently become "not provided"
**Area:** `app.py:78-86` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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
**Area:** `core/rules_engine.py:174-185` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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
**Area:** `app.py` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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
**Area:** `core/rules_engine.py`, `core/i18n.py` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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

#### DATA-03 — "Jobs" category is selectable but always returns nothing
**Area:** `data/opportunities/njp_jobs_sample.json`, `app.py` · **Priority:** P1 · **Status:** TODO · **Owner:** —

**What's wrong**
`njp_jobs_sample.json` contains a single entry whose `name` starts with `REPLACE ME`, which `data_loader.py:31-34` correctly skips. So **zero** job records load. But "💼 Jobs" is offered in the category multiselect and is selected by default. A user who selects only Jobs gets an empty result area — the `st.warning` at `app.py:165` only fires when the *filtered* list is empty, which it is, so they get a generic message with no explanation of why.

**Why it matters**
A judge clicking "Jobs" sees a dead feature.

**Fix approach**
Either (a) complete Step 8 of the README — add 2–3 real currently-open listings from njp.gov.pk with future deadlines — or (b) if that isn't done in time, mark Jobs as "Coming Soon" in the same way `category_assistance` already is, so the gap is honest and deliberate rather than looking broken. **Decide which, and record it in the Decision Log.**

**Acceptance criteria**
- [ ] Either real job records load and screen correctly, **or** the Jobs category is explicitly labelled as not yet available.
- [ ] No path through the UI shows an unexplained empty result set.
- [ ] If real listings are added: every `application_deadline` is a future date, verified the day before the demo.

---

#### OPS-01 — No error handling around any Gemini call
**Area:** `core/llm_client.py` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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

**Note:** migrating the SDK touches `_client()`, all three `GenerativeModel(...)` call sites, and the multimodal file-part format in `extract_opportunity_from_file`. Decide whether to migrate now or pin-and-ship, and record it in the Decision Log.

**Fix approach**
Check the current model list in Google AI Studio once a key is available, update the constant, and confirm both the text path and the multimodal (image/PDF) path work with the chosen model. Delete the stale comment once resolved.

**Acceptance criteria**
- [ ] Model name confirmed against the live API.
- [ ] A real text generation succeeds.
- [ ] A real image extraction succeeds.
- [ ] Inline "confirm before building" comment removed.

---

#### PERF-01 — First page load takes ~30–35s because the embedding model is built at session init
**Area:** `app.py:29-30`, `core/rag_engine.py` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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
**Area:** `core/rag_engine.py:49-51` · **Priority:** P1 · **Status:** TODO · **Owner:** —

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
**Area:** `core/rag_engine.py`, `requirements.txt` · **Priority:** P2 · **Status:** TODO · **Owner:** —

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

#### PERF-04 — No `.streamlit/config.toml`
**Area:** `.streamlit/` · **Priority:** P3 · **Status:** TODO · **Owner:** —

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
**Area:** `app.py:60-73` · **Priority:** P2 · **Status:** TODO · **Owner:** —

`age` and `marks` seed from `p.age` / `p.marks_percentage`, but `domicile`, `education`, `enrolled`, `existing_scholarship`, and `employment` are all hardcoded `index=0`. Streamlit's own widget-state persistence masks this in normal use, but the inconsistency will bite the moment a profile is restored from anywhere other than the widgets themselves (a saved session, a URL param, a future "edit my profile" flow).

**Acceptance criteria**
- [ ] Every field seeds from `st.session_state.profile`.
- [ ] Setting a profile programmatically is reflected in the rendered form.

---

#### BUG-06 — Keyword fallback returns arbitrary docs as "evidence"
**Area:** `core/rag_engine.py:81` · **Priority:** P2 · **Status:** TODO · **Owner:** —

`_keyword_fallback` ends with `... or self._docs[:top_k]` — when no query term matches any document, it returns the first N documents anyway. Those are then passed to `answer_followup` as *evidence* and presented to the model as grounding.

The `CHAT_SYSTEM_PROMPT` does instruct the model to say it lacks verified information when the evidence doesn't answer the question, which mitigates this — but handing a model irrelevant text and labelling it "Evidence" invites exactly the grounding failure this architecture is built to avoid.

**Fix approach**
Return an empty list on no match and let the caller show an honest "no relevant information found — check the official source" message. Note that `answer_followup` already handles the empty case (`"(no evidence retrieved)"` at line 109).

**Acceptance criteria**
- [ ] A query with no term overlap returns `[]`.
- [ ] The UI shows an explicit "nothing relevant found" message rather than an answer built on unrelated documents.

---

#### OPS-03 — Bare `except` in the Chroma path hides all failure detail
**Area:** `core/rag_engine.py:43-64` · **Priority:** P3 · **Status:** TODO · **Owner:** —

> **Corrected 2026-09-10.** This entry originally claimed that re-adding duplicate IDs on a second session raises, gets swallowed, and silently degrades retrieval to keyword search. **That was tested and is false** — three consecutive `RagIndex` builds in one process all kept `chroma_collection` active with `count() == 3`. ChromaDB 1.5.9 tolerates the duplicate `add()`. Priority dropped P2 → P3 accordingly. The startup cost this entry mentioned in passing turned out to be the real problem and is now tracked separately as **PERF-01**.

What remains is a smaller, genuine issue: the bare `except Exception:` at line 60 swallows *every* failure — missing package, corrupt cache, no network, model-load error — into an identical silent fallback with no log line. If retrieval quality ever looks wrong, there is no way to find out whether Chroma is even running.

**Fix approach**
Keep the fallback (it is good design), but record why it triggered — log the exception and expose the active mode (`chroma` vs `keyword`) somewhere a developer can see it.

**Acceptance criteria**
- [ ] The reason for any fallback is recoverable (logged, or surfaced in a debug expander).
- [ ] Which retrieval mode is active is visible to a developer without a debugger.

---

#### OPS-04 — Repo is not under version control
**Area:** repo root · **Priority:** P2 · **Status:** TODO · **Owner:** —

`git init` has never been run. There is a well-formed `.gitignore` (correctly excluding `.env`, `.streamlit/secrets.toml`, `venv/`, `chroma_db/`) waiting to be used, and README Step 9 assumes a GitHub repo exists for the Streamlit Cloud deploy.

**Why it matters**
No history, no rollback, no collaboration, and no deploy path. Every item in this tracker is riskier to attempt without it.

**Acceptance criteria**
- [ ] `git init`, initial commit made.
- [ ] Confirmed `venv/` and any real secrets file are **not** tracked.
- [ ] Pushed to a remote the whole team can access.

---

#### OPS-05 — Heavy deps will likely break the Streamlit Cloud deploy
**Area:** `requirements.txt` · **Priority:** P2 · **Status:** TODO · **Owner:** —

`chromadb>=0.5` and `sentence-transformers>=3.0` are active (not commented) in `requirements.txt`. `sentence-transformers` pulls in PyTorch. The README's own troubleshooting table already predicts this will exceed Streamlit Community Cloud's free-tier build resources.

**Fix approach**
Decide deliberately: either comment both out for the deployed build and accept keyword search in production (a defensible hackathon tradeoff — and the fallback is already implemented and tested), or attempt the deploy early enough that there's time to react if it fails. **Do not discover this at deploy time on demo day.** Record the choice in the Decision Log.

**Acceptance criteria**
- [ ] A successful deploy to a public URL exists.
- [ ] It is known and written down whether the deployed instance uses Chroma or keyword fallback.
- [ ] Deployment secrets are configured and the AI features verified working *on the deployed URL*, not just locally.

---

#### I18N-03 — No RTL layout for Urdu
**Area:** `app.py` · **Priority:** P2 · **Status:** TODO · **Owner:** —

Urdu strings render left-to-right in Streamlit's default layout. Mixed Urdu/English lines (which is most of the UI right now) will read awkwardly.

**Fix approach**
Inject scoped CSS setting `direction: rtl; text-align: right;` on the main container when `lang == "ur"`. Verify numbers, the match-card expanders, and the condition list still read correctly — RTL with embedded Latin-script numbers and URLs is where this usually goes wrong. Best tackled *after* I18N-01 and I18N-02, when there is actually full Urdu content to lay out.

**Acceptance criteria**
- [ ] Urdu mode renders right-to-left.
- [ ] Numbers, URLs, and status badges remain legible and correctly ordered.
- [ ] English mode is completely unaffected.

---

#### TEST-01 — No tests outside the rules engine
**Area:** `tests/` · **Priority:** P2 · **Status:** TODO · **Owner:** —

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
**Area:** `core/rules_engine.py:174` · **Priority:** P3 · **Status:** TODO · **Owner:** —

Every other condition appends an explicit `"n/a"` `ConditionCheck` when the opportunity doesn't use it. The deadline branch appends nothing at all when `ec.application_deadline` is `None`. Harmless today (the UI skips `n/a` anyway) but it makes the checks list inconsistent in length and shape, which will surprise anyone writing analytics or tests over it later.

**Acceptance criteria**
- [ ] Deadline follows the same `n/a` convention as every other check.
- [ ] Existing tests still pass.

---

#### BUG-08 — Misleading detail text on the existing-scholarship check
**Area:** `core/rules_engine.py:141-145` · **Priority:** P3 · **Status:** TODO · **Owner:** —

The logic is correct (`ok = not (required and has_one)`), but the detail string is always `f"You already receive a scholarship: {profile.has_existing_scholarship}"` — so a user who does *not* have one sees "You already receive a scholarship: False", which reads as a contradiction. Fold this into I18N-02 when the detail strings are restructured.

**Acceptance criteria**
- [ ] Detail text reads correctly in both the True and False cases, in both languages.

---

#### BUG-09 — `st.image(...) if ... else None` used as a statement
**Area:** `app.py:193` · **Priority:** P3 · **Status:** TODO · **Owner:** —

A conditional expression evaluated purely for its side effect. It works, but it's the kind of line that makes a reviewer stop. Replace with a plain `if mime_type.startswith("image/"): st.image(...)`.

**Acceptance criteria**
- [ ] Replaced with a normal `if` statement; behaviour unchanged.

---

#### OPS-06 — `explain_match` sends a raw dataclass repr as the profile summary
**Area:** `app.py:131` · **Priority:** P3 · **Status:** TODO · **Owner:** —

`profile_summary = str(st.session_state.profile)` sends `UserProfile(age=20, domicile_province='Punjab', ...)` to the model. It works, and it is **privacy-safe** (the model has no PII fields by design — see Section 6), but a natural-language summary would produce noticeably better explanations, and it's a one-function change.

**Acceptance criteria**
- [ ] A readable prose summary is sent instead of the repr.
- [ ] `None` fields are described as "not provided", not omitted silently.
- [ ] Still contains no identifying information.

---

#### FEAT-01 — Document-readiness checklist
**Area:** `app.py` · **Priority:** P3 · **Status:** TODO · **Owner:** —

`i18n.py:50` already defines `document_checklist_heading` in both languages, but nothing uses it. `required_documents` renders as a static bullet list. Making it interactive tick-boxes (with state) turns a passive list into an actionable prep tool.

**Depends on:** nothing. Good candidate once P0/P1 are clear.

**Acceptance criteria**
- [ ] Tick state persists across reruns per opportunity.
- [ ] Progress is visible (e.g. "3 of 7 ready").
- [ ] The unused i18n key is now used.

---

#### FEAT-02 — Export / share a match summary
**Area:** `app.py` · **Priority:** P3 · **Status:** TODO · **Owner:** —

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

**Phase 0 — Make it safe to work (do this first)**
`OPS-04` (git init) — everything below is safer with version control underneath it.

**Phase 1 — Stop the bleeding**
`BUG-01` → `BUG-02` (upload tab works at all) → `DATA-01` (nothing embarrassing on screen).
*Exit criteria: every visible path through the app either works or is honestly labelled as unavailable.*

**Phase 1.5 — Make it fast (cheap, high-visibility, do it early)**
`PERF-01` (lazy + cached index) → `PERF-02` (offline model load).
*Exit criteria: `streamlit run` to an interactive form in under ~5s, with wifi disabled.*

**Phase 2 — Truth**
`DATA-02` (verify the numbers) → `DATA-03` (jobs: fill or flag) → `OPS-02` (model name) → `OPS-01` (Gemini error handling).
*Exit criteria: nothing shown to a user is unverified or capable of crashing the page.*

**Phase 3 — Deliver the bilingual promise**
`I18N-01` → `I18N-02` → `I18N-03`.
*Exit criteria: an Urdu-first user gets a genuinely Urdu experience, including the reasons.*

**Phase 4 — Correctness of the core**
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
| — | *(pending: BUG-04 — how to represent a closed/stale listing)* | — | — |
| — | *(pending: DATA-03 — fill real job listings, or mark Jobs "Coming Soon")* | — | — |
| — | *(pending: OPS-05 / PERF-03 — ship with Chroma, or with keyword fallback)* | — | — |
| — | *(pending: OPS-02 — migrate to `google.genai` now, or pin the EOL SDK and ship)* | — | — |

---

## 8. Changelog

Append one line per completed piece of work.

| Date | ID | What changed |
|---|---|---|
| 2026-09-10 | — | Baseline audit completed; tracker created. No code changed. |
| 2026-09-10 | PERF-01..04 | Startup performance profiled; four PERF items added. No code changed. |
| 2026-09-10 | OPS-03 | **Corrected** — the duplicate-ID/silent-degradation claim was tested and disproved. Rewritten and dropped P2 → P3. |
| 2026-09-10 | OPS-02 | Expanded — `google-generativeai` 0.8.6 found to be **end-of-life**, not just possibly-stale on model name. |

---

## 9. Open questions

Things that need a human answer before the work they block can proceed.

- [ ] **Who owns data verification (DATA-02)?** It is the largest single time investment and the highest-value item. It needs a named person.
- [ ] **Is a Gemini API key available yet?** `OPS-02` and the real-image testing of README Step 10 are blocked until one exists.
- [ ] **What is the actual demo date/time?** Every "before the demo" item needs a real deadline to be sequenced against.
- [ ] **Does the Upload tab need its own profile form** (BUG-01), or should it reuse the profile from the Catalog tab? The second is simpler and probably better UX.
- [ ] **Is `assistance` (public assistance schemes) in scope at all?** It is a category in `schema.json` and a "Coming Soon" label in `i18n.py`, but has zero records and no plan attached.

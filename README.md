# Sahulat AI

<img src="assets/brand/logo-full.png" alt="Sahulat AI - More Opportunities. Easier Access." width="320">

**Pakistan Opportunity & Services Navigator** — tell it about your circumstances, and it tells you which government scholarships, jobs, skills courses and assistance programmes you are likely to qualify for, and exactly which condition decided it.

Built for the Pak Angels Cohort 11 Hackathon. Runs offline, asks for no identifying data, and never lets a language model decide whether you are eligible.

```
Status        30 curated records across 4 categories, all verified
Tests         404 passing  (python -m unittest discover tests)
Stack         Python 3.12 + Streamlit, stdlib rules engine, Gemini for explanation only
Languages     English, Urdu, Roman Urdu
```

---

## Why this exists

Pakistan runs a large number of genuinely useful public programmes — HEC and PEEF scholarships, NAVTTC skills courses, federal and provincial recruitment, BISP and Bait-ul-Mal support. Finding out whether *you* qualify means reading long PDFs written in bureaucratic English, for each programme, one at a time.

A chatbot is the obvious answer and the wrong one. A model asked "am I eligible?" will produce a confident, fluent, well-formatted answer that may be invented — and eligibility is exactly the kind of claim where a plausible guess does real harm. Someone skips an application they would have won, or spends a week assembling documents for one they never had a chance at.

So Sahulat AI splits the job in two.

---

## The one architectural rule

> **The rules engine decides. The LLM only ever explains.**

`core/rules_engine.py` is pure standard library. No network, no model, no imports beyond the data models. It reads a profile and a curated record and returns a verdict with a per-condition breakdown. Given the same inputs it returns the same answer every time, and the entire decision path is readable.

Gemini is used for four things only, none of which touch the verdict:

| Use | What it does | If it fails |
|---|---|---|
| `explain_match()` | Puts the engine's decision into plain sentences | Card still renders with the full condition list |
| `answer_followup()` | Answers questions grounded in retrieved record text | Says it has no evidence rather than guessing |
| `simplify_opportunity()` | Rewrites official wording as plain language | Original official text stays on the card |
| `extract_opportunity_from_file()` | Reads an uploaded ad into a structured record | Raw output shown, record marked user-uploaded |

Every one of them degrades to a clearly-labelled `[Local mock mode]` response with no API key at all. **The app is fully usable offline** — which is also what keeps a demo alive when the venue wifi dies.

```
app.py  (Streamlit — three screens: Discover / Read an announcement / How it works)
   |
   +-- core/data_loader.py ---> data/opportunities/*.json ---> Opportunity
   |
   +-- core/rules_engine.py    THE decision layer. stdlib only, no LLM, no network,
   |        |                  and no user-facing prose.
   |        |                  evaluate() -> 15 independent checks,
   |        |                                each met | unmet | unknown | n/a
   |        |                  roll-up (profile conditions only):
   |        |                      any unmet   -> Likely Not Eligible
   |        |                      any unknown -> Needs Verification
   |        |                      otherwise   -> Likely Eligible
   |        +---------------->  the deadline is reported SEPARATELY as listing state,
   |                            so a closed listing never reads as "you don't qualify"
   |
   +-- core/llm_client.py      Gemini: explain / answer / simplify / extract. Mock fallback on each.
   +-- core/ad_reader.py       upload bytes -> Gemini JSON -> Opportunity (never written to disk)
   +-- core/rag_engine.py      keyword retrieval by default; Chroma is opt-in
   +-- core/i18n.py            ALL user-facing prose, in all three languages
```

That last line is load-bearing too. The engine emits machine keys plus structured `required` / `actual` values, and `core/i18n.py` turns them into a sentence at render time — so adding a language never touches the decision logic.

---

## Quick start

```bash
git clone https://github.com/Waleed776-zoi/SAHULAT-AI.git
cd SAHULAT-AI

python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m unittest discover tests  # expect: Ran 404 tests ... OK
streamlit run app.py
```

That is the whole setup. No API key, no vector database, no model download. AI features will show `[Local mock mode]` text, which is correct rather than broken.

There is also a dev container (`.devcontainer/devcontainer.json`), so **Code → Codespaces → Create codespace** installs the dependencies and serves the app on port 8501 without any local Python at all.

### Turning the AI features on

1. Get a free key at <https://aistudio.google.com/apikey>.
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste it in — **quoted**:

   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```

   An unquoted value makes the TOML fail to parse, and Streamlit falls back to mock mode without saying why.
3. Restart. The header status flips from mock to live.

`.gitignore` already blocks the real `secrets.toml`. Never commit it.

### Configuration

| Setting | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | *(unset)* | Enables the four AI features. Absent means mock mode. |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Override the model without a code change. |
| `SAHULAT_SEMANTIC_SEARCH` | `0` | Set to `1` for multilingual embedding retrieval. Needs the optional dependencies. |

Read from environment variables or `.streamlit/secrets.toml`.

---

## What the app does

**Discover** — a validated four-step wizard (focus → about you → education → circumstances) leading to ranked results. Deliberately *not* built on `st.form`: a form submits on Enter, which sent half-filled profiles straight to results.

**Read an announcement** — upload a photo or PDF of a real advertisement. Gemini extracts it into the same record shape, and it is screened by the same engine, under a visibly different trust badge. Any extracted field can be corrected and re-screened.

**How it works** — the architecture, laid out for a judge or a sceptical user, including which layer made the decision.

On each result:

- **Eligibility scorecard** — every condition as met / unmet / unknown, with the required value beside your answer
- **Why, or why not**, in plain language, in your language
- **Readiness** — the documents you need, as a checklist with progress
- **Deadline intelligence** — days remaining, urgency, and a *Provisional date* badge when the date is an expected-cycle placeholder rather than an announced one
- **Freshness** — when the record was last checked against its official source
- **Next best action** — the single most useful thing to do now, including "answer this one missing question"
- **Comparison** across your top matches, and a plain-text export that preserves every trust marker

Language switches between **English**, **Urdu** (right-to-left, Nastaliq) and **Roman Urdu** from one picker in the header.

---

## The catalogue

30 records, hand-curated, each carrying its official source URL and verification date.

| Category | Records | What's in it |
|---|---|---|
| Scholarship | 2 | HEC Balochistan / ex-FATA, PEEF Punjab |
| Job | 10 | CSS, FPSC consolidated, four provincial commissions, Punjab Police, Pakistan Post, NADRA, Army LCC |
| Skills | 8 | NAVTTC Hunarmand plus 7 course streams |
| Assistance | 10 | BISP (×3), Bait-ul-Mal (×2), Himmat Card, Zakat Guzara, Sehat Sahulat, interest-free loans, EOBI |

Jobs are recorded as recruitment **streams** rather than named vacancies, on purpose: an advertised post is true for about three weeks, while the eligibility rules behind the stream are stable year to year — and the rules are what the engine screens on.

**On dates, honestly.** All 30 records are verified against their official sources and carry a real `last_verified` date. 20 carry a *provisional* deadline — a placeholder for the expected cycle, flagged in the data and badged in the UI so it can never render as an announced one. The other 10 are continuous-enrolment programmes that genuinely never close, which the model keeps distinct from "no date on record", because those are opposite instructions to a user. When a real closing date is announced, enter it and drop the flag.

Some conditions are deliberately **not** screened. BISP's PMT score, Nashonuma's pregnancy requirement and Zakat's religious criterion cannot be asked without either guessing or collecting something this app refuses to hold — so they appear as prose on the card, and are never approximated into a field that would silently screen someone out.

To add a record, copy the shape in `data/opportunities/schema.json`. A guard test rejects any record claiming `confidence_status: "verified"` without a `last_verified` and a `source_date`, so a badge can never appear with nothing behind it.

---

## Privacy, by construction

Enforced in code and guarded by tests — please don't undo these.

1. **`UserProfile` has no identifying fields.** No name, no CNIC, no phone, no address. If a new field seems to "match better", first establish that it is needed for *eligibility logic* rather than identity.
2. **Uploaded files are never written to disk.** `core/ad_reader.py` holds the bytes in memory for the request and drops them.
3. **Curated and AI-extracted records never share a trust badge.** `officially_verified_badge` and `ai_extracted_badge` stay visually and semantically distinct everywhere, the export included.
4. **No eligibility criterion is ever invented.** If it isn't in the official source or the uploaded document, the value is `null` — not a plausible guess. `null` produces *Needs Verification*, which is an honest answer.
5. **The app runs with no key and no network.** The mock fallbacks stay.

---

## The logo

A green ribbon **S** with a four-pointed spark, the name in Latin and Urdu, over the line *More Opportunities. Easier Access.*

`assets/source/sahulat-logo-source.png` is the master. Everything the app shows is cut from it by `scripts/prepare_logo.py` — lifted off its white background into real transparency, then separated and sized:

```bash
python scripts/prepare_logo.py     # assets/source/ -> assets/brand/
```

Everything in `assets/brand/` is generated. **Do not hand-edit it** — change the source or the script and re-run. A test rebuilds every variant in memory and compares it byte for byte against what is committed, so an edited file fails the suite rather than quietly becoming the odd one out.

| Placement | Variant | Reasoning |
|---|---|---|
| Browser tab | `icon-192.png` | Cut from the same artwork, so the tab and the header cannot drift apart |
| App header | `logo-lockup@2x.png` at 46px | The artwork carries the name in both scripts, so the header no longer repeats it as text |
| Footer | `logo-symbol@2x.png` at 26px | See the contrast note below |
| This README | `logo-full.png` | The only place with room for the tagline |

It is deliberately **not** on the home hero. The hero already leads with a headline and a live screening result; a logo there would compete with both, and the header sits directly above it.

### Two things the script exists to get right

**The tagline cannot be cropped off the bottom.** The obvious way to make a header lockup is to cut the tagline away with a horizontal slice — but the ribbon runs the full height of the artwork and the tagline sits *beside* its lower half, not below it. Slicing would take the bottom off the ribbon too. The script erases the tagline where it actually lives, inside the text block, leaving the symbol untouched.

**Deskew has to be able to refuse.** The earlier artwork was a screenshot, tilted about 1.4°, so the script measures rotation from the artwork's own text baseline and corrects it. Measured naively across the full width, though, the ribbon's curved underside fits a straight line at **−7.7°** — on artwork that is perfectly straight. Acting on that would have rotated a clean logo into a crooked one. So the fit is taken only across the text block, and rejected unless the points genuinely lie on a line; a quarter-degree reading is treated as zero, because rotating resamples every pixel and that correction is inside the measurement's own noise.

### The one real constraint

This is **light-background artwork**. Its wordmark is deep green and its `.AI` is navy, both of which fall to almost no contrast on the app's deep green surfaces — so the footer uses the ribbon alone, which is light enough to read there. `core.brand.DARK_SAFE` records which files may go on dark, and a test checks the footer honours it.

Smaller notes: the two files that appear in the header are base64'd into the page HTML on every rerun, so they are quantised to 128 colours — **under 7 KB each instead of 29 KB** — while keeping 64 distinct alpha levels, so no curve hard-edges; a test holds that budget. And `assets/source/` also keeps `sahulat-logo-alt-stacked.png`, an earlier arrangement that sets the Urdu *below* the Latin rather than overlapping it, and reads `Sahulat AI` rather than `Sahulat.AI`. It is kept because it is a different design decision, not a worse file — point `SOURCE` at it and re-run the script to switch.

---

## Project structure

```
sahulat_ai/
├── app.py                       # The Streamlit app — run this
├── requirements.txt             # streamlit + google-genai; heavy deps commented out
├── PROJECT_TRACKER.md           # work log, decision log, invariants, changelog
├── .devcontainer/
│   └── devcontainer.json        # Codespaces: installs deps and serves the app
├── .streamlit/
│   ├── config.toml              # theme and performance settings
│   └── secrets.toml.example     # template for the Gemini key
├── core/
│   ├── models.py                # UserProfile, Opportunity, MatchResult, condition keys
│   ├── rules_engine.py          # THE decision layer — deterministic, no LLM
│   ├── validation.py            # wizard step rules and field bounds
│   ├── data_loader.py           # data/opportunities/*.json -> Opportunity
│   ├── llm_client.py            # Gemini wrapper, with a mock fallback on every call
│   ├── ad_reader.py             # uploaded ad -> structured record
│   ├── rag_engine.py            # keyword retrieval; Chroma opt-in
│   ├── readiness.py             # document checklist state
│   ├── timeliness.py            # deadlines, urgency, record freshness
│   ├── comparison.py            # side-by-side of top matches
│   ├── next_action.py           # the single most useful next step
│   ├── impact.py                # aggregate figures for the results header
│   ├── i18n.py                  # English + Urdu prose, and describe_check()
│   ├── i18n_roman.py            # Roman Urdu
│   └── brand.py                 # the logo: where the files are, and how they reach a page
├── data/opportunities/
│   ├── schema.json              # the shared record shape (not a record itself)
│   ├── hec_balochistan_fata.json, peef_punjab.json   # 2 scholarships
│   ├── navttc_hunarmand.json, navttc_courses.json    # 8 skills records
│   ├── government_jobs.json                          # 10 job records
│   └── public_assistance.json                        # 10 assistance records
├── assets/
│   ├── source/                  # the logo as supplied — masters, never edited
│   └── brand/                   # generated by scripts/prepare_logo.py, never by hand
├── scripts/
│   └── prepare_logo.py          # deskew, un-composite, cut and size the logo
├── styles/
│   ├── theme.css                # design tokens
│   ├── components.css           # component styles
│   └── animations.css           # all motion, behind prefers-reduced-motion
└── tests/                       # 404 tests
    ├── test_rules_engine.py          (35)  the deterministic engine
    ├── test_core_modules.py          (63)  loading, verification state, i18n
    ├── test_validation.py            (24)  wizard step rules
    ├── test_v2_features.py           (38)  scorecard, ranking, corrections
    ├── test_p1_features.py           (34)  readiness, deadlines, comparison
    ├── test_p2_features.py           (26)  Roman Urdu, impact, degraded AI
    ├── test_jobs_catalogue.py        (30)  catalogue vocabulary + job guards
    ├── test_assistance_catalogue.py  (24)  group gates, always-open enrolment
    ├── test_app_ui.py                (44)  real widgets driven through AppTest
    ├── test_v3_visual.py             (34)  screens, hero preview, motion guards
    ├── test_ai_stages.py             (16)  staged progress on every AI call
    └── test_brand.py                 (36)  the artwork, its build, and where it is placed
```

---

## Tests

```bash
python -m unittest discover tests            # all 404
python -m unittest tests.test_rules_engine   # one module
```

Roughly a third of the suite tests *claims* rather than code. The catalogue tests assert that every vocabulary value in every record is one the engine actually recognises — a province spelled slightly differently, or a skill level written as prose, would otherwise silently match nobody and look like no bug at all. `test_app_ui.py` drives the real Streamlit widgets through `AppTest` rather than asserting on functions, because the interesting UI bugs here have all been ordering and state bugs that unit tests could not see.

The suite takes about a minute, nearly all of it the `AppTest` runs.

---

## Deploying

1. Push to GitHub.
2. <https://share.streamlit.io> → New app → your repo, branch `main`, main file `app.py`.
3. **Settings → Secrets**: paste the same content as your local `secrets.toml`.

Leave `chromadb` and `sentence-transformers` commented out in `requirements.txt`. They pull in PyTorch (~2GB), which is the usual cause of a failed Community Cloud build, and the app defaults to keyword retrieval without them.

---

## Known limits

- **Deadlines are provisional on 20 of the 30 records** — flagged in the data and badged in the UI, but they are expected-cycle dates, not announced ones.
- **Retrieval is keyword-based by default.** An Urdu question against English record text retrieves less well until `SAHULAT_SEMANTIC_SEARCH=1` and the optional dependencies are installed.
- **Ad reading is only as good as the photograph.** Test it on real ads before demoing it, not during.
- **The Chroma index is in-memory**, rebuilt per process. Fine at this scale; a persistent store would need a build script that does not exist yet.
- **This is a pre-screening tool, not an official government service.** Final eligibility is always decided by the programme itself. The app says so on every screen, and that disclaimer should stay.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'core'` | Running from the wrong directory | Run from the project root, not `core/` |
| AI still shows `[Local mock mode]` with a key set | The TOML failed to parse | Quote the key: `GEMINI_API_KEY = "..."` |
| Gemini returns 404 for the model | Model retired | Set `GEMINI_MODEL` to a current one; no code change needed |
| First AI call takes ~30s | Embedding model downloading | Only with `SAHULAT_SEMANTIC_SEARCH=1`, and only on first use |
| Cloud deploy fails building torch | Optional dependencies uncommented | Re-comment them; keyword retrieval is the default for a reason |

---

`PROJECT_TRACKER.md` holds the full work log — every issue, the decision log (including the choices a future reader might otherwise reverse by accident), the invariants above, and a changelog entry per piece of work.

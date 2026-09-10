# Sahulat AI — Pakistan Opportunity & Services Navigator
**Working codebase — Pak Angels Cohort 11 Hackathon**

This is a real, tested, running starting point — not a mockup. The rules engine, data loading, bilingual UI, Gemini integration (with graceful offline fallback), and ad-reading pipeline are all wired together and verified working end-to-end before you received this. What's left is genuine hackathon work: real API key, real verified scheme data, and polish.

---

## 0. What's already done for you (verified before delivery)

| Piece | Status | How it was verified |
|---|---|---|
| Deterministic rules engine (`core/rules_engine.py`) | ✅ Working | 8/8 unit tests pass (`tests/test_rules_engine.py`) |
| Data models (`core/models.py`) | ✅ Working | Used by all tests + data loader |
| Data loader (`core/data_loader.py`) | ✅ Working | Successfully loads all 3 curated JSON records |
| 3 curated opportunity records (HEC, PEEF, NAVTTC) | ⚠️ Structurally complete, **data needs real verification** | JSON validates and loads correctly; eligibility numbers are placeholders sourced from research and marked `TODO-VERIFY` |
| Gemini LLM wrapper (`core/llm_client.py`) | ✅ Working in mock mode | Runs without crashing with no API key — returns clearly labeled mock text |
| Ad/document reader (`core/ad_reader.py`) | ✅ Working in mock mode | Same as above — pipeline wired, needs a real key to do real extraction |
| RAG engine (`core/rag_engine.py`) | ✅ Working in keyword-fallback mode | Tested — correctly retrieves the Balochistan HEC record for a Balochistan-related query, with zero extra installs |
| Bilingual strings (`core/i18n.py`) | ✅ Working | English + Urdu strings for all current UI text |
| Streamlit app (`app.py`) | ✅ **Actually launched and confirmed serving (HTTP 200)** | Full smoke test run during build |

**What this means practically:** you can hand this to teammates right now and they can start building UI polish, writing tests, or curating data — without waiting on an API key, without installing chromadb/sentence-transformers, and without anything crashing. The app is "alive" in a safe, mock, offline state.

---

## 1. What YOU need to do — in order

This is the actual critical path. Follow it in this order; don't skip ahead to Step 5 before Step 2 is done, or you'll be demoing on fake data.

### Step 1 — Get VS Code ready (5 minutes)
1. Open the `sahulat_ai/` folder in VS Code (`File → Open Folder`).
2. Install the Python extension if you don't have it (VS Code will usually prompt you).
3. Open a terminal inside VS Code (`` Ctrl+` ``).

**Expected output:** a terminal prompt sitting in the `sahulat_ai` folder.

### Step 2 — Create a virtual environment and install dependencies (5–10 minutes)
```bash
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```
**Expected output:** pip installs Streamlit and `google-generativeai` without errors. This may take a few minutes.

> **Note on chromadb/sentence-transformers:** these are in `requirements.txt` but are the heaviest dependencies (they pull in PyTorch). If you want to move fast at first, you can comment them out and skip them — the app **already works without them** (falls back to keyword search, as tested). Install them later when you're ready to test real bilingual semantic retrieval.

### Step 3 — Confirm the tests still pass on your machine (2 minutes)
```bash
python3 -m unittest discover tests -v
```
**Expected output:** `Ran 8 tests in 0.00Xs` / `OK`. If this fails, something is wrong with your environment before you've even touched a line of code — fix this first.

### Step 4 — Run the app in mock mode, no API key needed yet (2 minutes)
```bash
streamlit run app.py
```
**Expected output:** a browser tab opens showing the Sahulat AI interface. You can fill in the profile form and see match results (from the 3 real curated schemes). AI explanation buttons and ad upload will show "[Local mock mode]" text — this is correct and expected at this stage, not a bug.

**What to do here:** click around. Confirm the category tabs, profile form, and match cards all render and behave sensibly before moving on.

### Step 5 — Get a free Gemini API key (5 minutes)
1. Go to **https://aistudio.google.com/apikey**
2. Sign in with a Google account, click "Create API key."
3. Copy the key.

**What to do with it (pick one):**
- **For local testing:** copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste your key in.
- **For deployment later:** you'll paste the same content into Streamlit Community Cloud's "Secrets" panel (Step 9).

**Never commit the real `secrets.toml` file** — `.gitignore` is already set up to block this.

### Step 6 — Re-run the app with your real key and confirm AI features work (5 minutes)
```bash
streamlit run app.py
```
Click an "AI explanation" button and try the "Ask a follow-up question" box.

**Expected output:** real Gemini-generated text instead of `[Local mock mode]` text. If you get an error instead, check: (a) the key is pasted correctly with no extra spaces, (b) you haven't exceeded the free-tier rate limit (unlikely during normal testing).

### Step 7 — THE REAL WORK: verify and finalize the scheme data (this is your biggest time investment — budget several hours, not minutes)
Open each file in `data/opportunities/`:
- `hec_balochistan_fata.json`
- `peef_punjab.json`
- `navttc_hunarmand.json`

Every field marked `"TODO-VERIFY"` or `"TODO-VERIFY-BEFORE-DEMO"` needs a real human to check it against the official source (`official_url` in each file) and replace it with the real, current value. This includes:
- Exact age/marks/income thresholds for the current admission cycle
- Whether the program is even currently accepting applications
- `last_verified`: set this to today's date once you've actually checked

**This is not optional polish — it's the actual foundation of your "no invented eligibility criteria" promise, and it's what the whole architecture is designed to protect.**

**Expected output:** three JSON files with no more `TODO` strings in them, each with a real `last_verified` date.

### Step 8 — Fill in real NJP job listings (30–60 minutes, only if time allows)
Open `data/opportunities/njp_jobs_sample.json`. Go to njp.gov.pk, find 2–3 real, currently-open listings, and replace every `"REPLACE ME"` field by hand. **Double-check the deadline is a future date** — the rules engine will flag a stale deadline automatically once you save it (it checks against today's date), so if you see `"Application deadline"` come back `unmet`, that's the engine correctly catching an expired listing.

### Step 9 — Deploy to Streamlit Community Cloud (15 minutes)
1. Push this folder to a GitHub repository (create one if you haven't).
2. Go to **share.streamlit.io**, sign in with GitHub, click "New app."
3. Point it at your repo, branch `main`, main file `app.py`.
4. In the app's **Settings → Secrets**, paste the same content as your local `.streamlit/secrets.toml`.
5. Click Deploy.

**Expected output:** a public URL for your live app, ready for the demo.

### Step 10 — Test the ad-reading feature with real images before the demo (do this, don't skip it)
Find or photograph 2–3 real scholarship/job/training ads. Upload each one in the "Upload an ad" tab and check the extracted fields are reasonable. **Do this now, not for the first time during your live demo** — this is exactly the caution flagged in the plan document.

---

## 2. Project structure

```
sahulat_ai/
├── app.py                          # Main Streamlit app - run this
├── requirements.txt                # Python dependencies
├── .env.example                    # Template for local script env vars
├── .streamlit/
│   └── secrets.toml.example        # Template for Streamlit secrets (Gemini key)
├── core/
│   ├── models.py                   # UserProfile, Opportunity, MatchResult data models
│   ├── rules_engine.py             # THE eligibility logic - deterministic, no LLM
│   ├── data_loader.py              # Loads data/opportunities/*.json into Opportunity objects
│   ├── llm_client.py               # Gemini wrapper: explain, chat, extract - with mock fallback
│   ├── ad_reader.py                # Turns an uploaded file into an Opportunity via Gemini
│   ├── rag_engine.py                # Retrieval for follow-up chat (Chroma or keyword fallback)
│   └── i18n.py                     # English/Urdu UI strings
├── data/opportunities/
│   ├── schema.json                 # Documents the shared record shape (not a real record)
│   ├── hec_balochistan_fata.json   # NEEDS DATA VERIFICATION (Step 7)
│   ├── peef_punjab.json            # NEEDS DATA VERIFICATION (Step 7)
│   ├── navttc_hunarmand.json       # NEEDS DATA VERIFICATION (Step 7)
│   └── njp_jobs_sample.json        # NEEDS REAL LISTINGS (Step 8)
└── tests/
    └── test_rules_engine.py        # 8 passing unit tests for the rules engine
```

---

## 3. How the architecture maps to the plan (for your own sanity-check, and for judges)

This directly implements the layered architecture from the final plan document:

| Plan layer | Code |
|---|---|
| 1 — Profile Intake | `render_profile_form()` in `app.py` |
| 2 — Eligibility Rules Engine | `core/rules_engine.py` (never touched by the LLM) |
| 3 — Curated Opportunity Database | `data/opportunities/*.json` + `core/data_loader.py` |
| 4 — Grounded Explanation | `core/llm_client.explain_match()` and `answer_followup()` |
| 5 — Action Generator | Document/steps rendering in `render_match_card()` |
| 6 — Impact Analytics | *(not yet built — see Section 5 below, deliberately deferred)* |
| 7 — Ad/Document Intelligence | `core/ad_reader.py` + `core/llm_client.extract_opportunity_from_file()` |

---

## 4. Privacy rules this codebase already enforces — don't undo these

- `UserProfile` (in `core/models.py`) has **no fields for CNIC, name, phone, or address** — don't add any. If you're tempted to add a field to "match better," ask whether it's really needed for eligibility logic, not identity.
- `core/ad_reader.py` never writes the uploaded file to disk — it stays in memory for the request only.
- Every AI-extracted (uploaded) result is tagged `source_type="user_uploaded"` and rendered with a distinct warning badge in the UI (`ai_extracted_badge` vs `officially_verified_badge` in `core/i18n.py`) — never merge these two trust levels in the UI.

---

## 5. What's intentionally NOT built yet (by design, not oversight)

- **Layer 6 (Impact Analytics)** — per the plan, this is the first thing to cut under time pressure. Add it last, only if Steps 1–10 above are done with time to spare.
- **Document-readiness checklist tick-boxes** — the required-documents list renders, but there's no interactive "tick what you have" state yet. Good next feature once core data is verified.
- **Export/share summary** — same, nice-to-have, not core.
- **A real, persistent on-disk Chroma store** — `rag_engine.py` currently builds an in-memory Chroma collection (or falls back to keyword search) on every app restart, which is fine for a hackathon demo's scale (a handful of documents) but would need `scripts/build_vector_store.py` if you want to precompute it. This script is not included yet — build it only if you actually install chromadb/sentence-transformers and notice startup is slow.

---

## 6. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'core'` | Running a script from the wrong directory | Always run commands from inside `sahulat_ai/`, not from `core/` or elsewhere |
| Tests fail immediately | Wrong Python version or venv not activated | Confirm `python3 --version` is 3.9+ and your terminal prompt shows `(venv)` |
| AI buttons still show `[Local mock mode]` after adding a key | Key not actually picked up | Confirm `.streamlit/secrets.toml` exists (not just the `.example` file) and has no typo in the key name `GEMINI_API_KEY` |
| Ad upload gives a JSON error / raw text dump | Gemini didn't return clean JSON for that particular image (rare but possible with poor image quality) | This is handled gracefully already — you'll see `_raw_model_output` in the debug JSON; try a clearer photo |
| Streamlit Cloud deploy fails on chromadb/torch | Free tier has limited build resources | Comment out `chromadb` and `sentence-transformers` in `requirements.txt` for deployment — the app still works via keyword fallback, which is a perfectly reasonable hackathon tradeoff |

---

## 7. Quick command reference

```bash
# Setup (once)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Every time you start working
source venv/bin/activate
python3 -m unittest discover tests      # confirm nothing's broken
streamlit run app.py                    # run the app locally
```

---

*Everything above was built, run, and tested before being handed to you — not just written. The remaining work (Steps 5, 7, 8, 9, 10) is real hackathon work that genuinely needs a human: getting your own API key, and verifying real government data against real official sources. That's exactly as it should be.*

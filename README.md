# Josh Talks AI — Product Task, July 2026

Submission by the candidate. Two questions, both delivered.

---

## Question 1 — *DukaanBench*: a text-to-image eval for Indian e-commerce creatives

| Deliverable | File |
|---|---|
| **1. Main document** | [`docs/MAIN_DOCUMENT.md`](docs/MAIN_DOCUMENT.md) |
| **2. One-page report** | [`docs/ONE_PAGE_REPORT.md`](docs/ONE_PAGE_REPORT.md) |
| **3. Supporting material** — prompts, 30 images, per-image metadata, proof of generation, notes | [`q1_eval/`](q1_eval/) |
| **4. UI / dashboard / leaderboard design** | [`docs/DESIGN_UI_DASHBOARD.md`](docs/DESIGN_UI_DASHBOARD.md) (+ built rating UI below) |
| **5. Video walkthrough (≤2 min)** — ▶ [**watch the walkthrough**](https://drive.google.com/file/d/1COEtU2dQ6jl9YrAIgCyAl0tZxNHgQ0d2/view?usp=drive_link) (script + shot list: [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md)) |
| **Results dashboard** — every model, rater, criterion, prompt and image view | [`q1_eval/rating_ui/dashboard.html`](q1_eval/rating_ui/dashboard.html) |
| Final reflection (5 questions) | [`docs/REFLECTION.md`](docs/REFLECTION.md) |

**Built artefacts**

```
q1_eval/
  prompts/prompts.json        10 prompts + 3 models + 5 criteria  (source of truth)
  images/                     30 generated images (10 prompts × 3 models), 1024×1024
  metadata/*.json             30 per-image records: company, model, prompt, where, settings, sha256
  metadata/api_attempt_logs/  preserved 429 payloads (proof the API path was blocked)
  metadata/screenshots/       proof-of-generation screenshots
  generate.py                 API generator (ready; fills the GPT Image 1 gap when a key exists)
  build_metadata.py           regenerates the 30 metadata records
  build_ui_data.py            rebuilds rating_ui/data.js from prompts + images
  manual_kit/index.html       manual generation checklist
  collect_images.sh           watcher that renames and files downloaded images
  rating_ui/index.html        ★ rating sheet: consent, shuffled/blinded trials, 5 criteria, export
  rating_ui/dashboard.html    ★ results dashboard: model/rater/criterion/prompt/image views (offline)
  rating_ui/dashboard_data.js built by rating_ui/build_dashboard_data.py from the 10 exports
  rating_ui/build_dashboard_data.py  regenerates the dashboard data from rate_results/
  rate_results/aggregate.py   ★ aggregates rater exports → leaderboard + CSVs
  docs/GENERATION_NOTES.md    how the images were really made, including what failed
  docs/PARTICIPANT_PROTOCOL.md how the 10 participants were run
```

**Model coverage — declared**

| Status | Company — model |
|---|---|
| Run (picker label only) | Google Gemini app: **3.5 Flash Lite** → set 1 |
| Run (picker label only) | Google Gemini app: **3.6 Flash** → set 2 |
| Run (picker label only) | Google Gemini app: **3.1 Pro** → set 3 |
| **Not confirmed** | Google — **Gemini 3.1 Flash Image Preview** (required) |
| **Not confirmed** | Google — **Gemini 2.5 Flash Image** (required) |
| **Not run** | OpenAI — **GPT Image 1** (required) — no API key; ready script is `q1_eval/generate.py` |

The Gemini consumer app does not report the image model it used, so all 30 metadata records
carry `model_identity_verified: false`. See `q1_eval/docs/GENERATION_NOTES.md` §3b.

---

## Question 2 — spotting low-quality transcribers from data

| Deliverable | File |
|---|---|
| **Part I + Part II writeup** | [`q2_quality/writeup/Q2_Transcriber_Quality_System.md`](q2_quality/writeup/Q2_Transcriber_Quality_System.md) |
| Dataset | `q2_quality/data/tasks.csv` (51,783 rows) |
| Analysis | `q2_quality/analysis/analyze.py`, `validate_rules.py` |
| Full numeric log | `q2_quality/analysis/out/run.log` |
| Validated task-level scores | `q2_quality/analysis/out/scored_tasks.csv` (5,410 tasks) |
| Per-user behavioural table | `q2_quality/analysis/out/user_risk.json` |
| Real examples for the writeup | `q2_quality/analysis/out/examples.json` |

**Reproduce:** `python3 q2_quality/analysis/analyze.py && python3 q2_quality/analysis/validate_rules.py`

---

## Quick start

```bash
# Question 1 — open the rating sheet
open q1_eval/rating_ui/index.html          # works offline, no server needed

# Question 1 — after rater exports arrive in q1_eval/rate_results/
python3 q1_eval/rate_results/aggregate.py

# Question 1 — rebuild derived files after editing prompts
python3 q1_eval/build_metadata.py && python3 q1_eval/build_ui_data.py

# Question 2 — rerun the analysis
python3 q2_quality/analysis/analyze.py
python3 q2_quality/analysis/validate_rules.py
```

## Secrets

`.env` (chmod 600, `.gitignore`d) may hold API keys. **Never screenshot or commit it.**

## Honest gaps, stated once

1. **OpenAI GPT Image 1 not run** — no key. Script ready.
2. **Gemini images produced through the Gemini web app**, not the API (API image quota = 0,
   evidence in `metadata/api_attempt_logs/`), under picker labels **3.5 Flash Lite / 3.6
   Flash / 3.1 Pro**. The app never names the image model, so **model identity is unverified
   for all 30 images** and the filenames are a labelling scheme, not provenance. Re-running
   through the API is the first scale-up step — it fixes attribution and the two required
   Google model gaps together.
3. ~~Proof-of-generation screenshots pending~~ **Done for what the brief needs** — three
   captures in `q1_eval/metadata/screenshots/`: the **Gemini model picker open** (provenance
   for the declared model-identity gap), a **prompt + generated image on screen**, and the
   **`"code": 429` payload** (proof of the API quota gap). Two internal workflow captures
   (download step, watcher log) are not taken and are not load-bearing — images are already
   verified by SHA-256 and dimensions.
4. ~~Human ratings pending~~ **Done** — 10 raters, 1,500 judgements, aggregated into
   `docs/MAIN_DOCUMENT.md` §6.3. Headline: the three models tied (3.78 / 3.79 / 3.78) and
   inter-rater consistency came back r = 0.007, so the leaderboard is labelled *not
   publishable* — the instrument finding is the result.

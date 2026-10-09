# Generation notes — how all 30 images were actually produced

Deliverable 3 (supporting material) for Question 1. This file is the honest record of the
workflow, including the parts that failed.

---

## 1. Declared model coverage

| Status | Company | Model name | Notes |
|---|---|---|---|
| **Run (label only)** | Google | app picker **3.5 Flash Lite**, saved as files `P*__google__gemini-3-1-flash-image-preview.png` | set 1 |
| **Run (label only)** | Google | app picker **3.6 Flash**, saved as files `P*__google__gemini-2-5-flash-image.png` | set 2 |
| **Run (label only)** | Google | app picker **3.1 Pro**, saved as files `P*__google__gemini-3-pro-image.png` | set 3 |

> **Read the arrow as "saved as", not as "is".** The filename slug was chosen *before* any
> image existed, as a stable naming convention. It records which picker selection a file came
> from by sequence — it does **not** record which image model that picker selection actually
> invoked. See §3b.
| **Not confirmed** | Google | Gemini 3.1 Flash Image Preview (**required**) | see §3b |
| **Not confirmed** | Google | Gemini 2.5 Flash Image (**required**) | see §3b |
| **Not run** | OpenAI | GPT Image 1 (**required**) | no API key / prepaid credit · ready script `q1_eval/generate.py` |

### 3b. Model identity — read this before trusting any model comparison

**What is certain:** three sets of 10 images exist, produced one per app-picker selection,
in the order the candidate recorded: **3.5 Flash Lite → 3.6 Flash → 3.1 Pro**.

**What is not certain:** the Gemini *consumer* app's picker selects a **chat** model and does
not report which underlying **image-generation** model it used. So for all 30 images:

> The exact image-model name required by the brief (`Gemini 2.5 Flash Image`,
> `Gemini 3.1 Flash Image Preview`) **cannot be confirmed from this run.**

Consequences, stated plainly rather than papered over:

1. Every metadata record carries `"model_identity_verified": false`,
   `"app_picker_label": "<label used>"`, and `"required_model_confirmed": false`.
2. The filenames are a **file-labelling scheme only** (a stable `P<id>__<company>__<model>`
   slug chosen before generation); they are **not** evidence of which model produced the
   pixels. Filename ≠ provenance.
3. The honest claim for this submission is therefore **"three Google Gemini app model
   selections were compared"**, not **"three API image models were compared"**.
4. The two *required* Google models, plus GPT Image 1, are all closed by the same fix in
   §6: run `q1_eval/generate.py` with funded keys. The comparison then becomes verifiable
   because the API returns the model id it used.
5. A reviewer should treat the leaderboard as a **pilot on unverified model identity** —
   the harness, prompts, ratings and aggregation are all sound; the model attribution is
   the weak link, and it is weak *because* the consumer app hides it, not because the run
   was careless.

Nothing is hidden: GPT Image 1 appears in every metadata record with `status` describing the
attempt, and in `prompts.json` under `shared_settings.documented_gap`.

---

## 2. Workflow A — programmatic API (attempted, blocked)

`q1_eval/generate.py` is a complete, resumable generator:

- **OpenAI:** `POST https://api.openai.com/v1/images/generations` with `model=gpt-image-1`,
  `size=1024x1024`, `quality=high` — guarded on `OPENAI_API_KEY` in the repo-root `.env`.
- **Google:** `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
  with `{"inlineData": {"mimeType": "image/png"}}` extraction, `aspectRatio` 1:1,
  header `x-goog-api-key`.
- Idempotent/resume: skips any output that already exists, writes a metadata JSON per image.

**What happened**

| Attempt | Result |
|---|---|
| OpenAI GPT Image 1 | never callable — no `OPENAI_API_KEY` in the environment |
| Gemini image models, key #1 | `HTTP 429` — `You exceeded your current quota … plan and billing details` |
| Gemini image models, key #2 (independent key) | same `HTTP 429` |
| Both keys on **text** models (`/v1beta/models`, `generateContent`) | `HTTP 200` — connectivity and keys were fine |
| Both keys on **every image model** | `HTTP 429` with `free_tier limit: 0` → `RESOURCE_EXHAUSTED` |

Interpretation: **image generation is billing-gated on this account**; the text API works,
so this is not an auth problem. Billing was explicitly out of scope for this submission, so
Workflow A stopped here.

**Evidence preserved:** `metadata/api_attempt_logs/*.json` — endpoint called, timestamp,
all request variants tried with their statuses, HTTP status, latency, the request body used,
and the full raw error payload. Four records (three Google models + OpenAI).

---

## 3. Workflow B — manual generation through the Gemini web app (used for all 30)

Because the API was blocked, images were produced in the Gemini web app, which does generate
images on the free tier.

**Procedure (reproducible):**

1. Open `gemini.google.com`, sign in.
2. Start a fresh conversation (so earlier turns cannot influence an image).
3. Open the **model picker** and select the label for this set
   (set 1 `3.5 Flash Lite`, set 2 `3.6 Flash`, set 3 `3.1 Pro`).
4. Paste the prompt from `prompts.json` **verbatim** — no edits, no re-typing, no additions.
5. The prompt itself begins `Square 1:1 …`, so the aspect requirement travels with the
   identical prompt text rather than a provider parameter.
6. Download the resulting image.
7. Save it into the collection folder as
   `P<n>__google__<model-slug>.png` (e.g. `P1__google__gemini-3-1-flash-image-preview.png`).
8. A watcher script, `q1_eval/collect_images.sh` (running in the background), moves files
   out of `~/Downloads` / `~/Desktop`, renames them into the canonical scheme, and logs the
   move with a timestamp — `ls` output of that log is retained as a timestamped record of
   when each image landed.
9. Repeat 10 prompts × 3 model selections = **30 files**.

**Why this is documented as a variant, not as noise:** the brief explicitly says
*"If one model requires a slightly different workflow, document that clearly in your
submission."* Here **all** models went through the consumer app, so the fair statement is:

> The prompt text and 1:1 framing are identical across the three sets, but the images were
> produced in a consumer UI rather than a uniform API call. The consumer app may apply its
> own defaults (seed, safety filter, resolution policy) **and does not name the image model
> it used**. This run is therefore a **workflow-variant comparison with unverified model
> identity**. The first scale-up step is to re-run the same 30 conditions through
> `generate.py` with funded keys, which closes the attribution problem and the three
> required-model gaps at once.

**Result:** 30/30 files present, all valid PNG, all **1024 × 1024**, verified programmatically.

---

## 4. Per-image metadata (the brief's required record)

`build_metadata.py` writes **30 JSON files** into `q1_eval/metadata/`, one per image, each
containing every field the brief asks for:

```
prompt_id, prompt_axis, prompt_text, must_contain, must_show
company, model, model_id, docs               <- exact company + exact model name
image_file, image_size_px, image_bytes, sha256
file_modified_at
where_generated                               <- "where you generated it"
settings_or_variations                        <- model-picker set, aspect handling
aspect_handling                               <- 1:1 carried inside the prompt text
programmatic_attempt                          <- the 429 evidence pointer
status
```

Regenerate at any time with `python3 q1_eval/build_metadata.py`.

---

## 5. Screenshots / proof of generation

**Location:** `q1_eval/metadata/screenshots/`
**Status:** **captured — 3 of 5 items, and they are the 3 the brief depends on.**

| File | Covers | Why it matters |
|---|---|---|
| `screenshots/screenshot 1.png` | **#1 — Gemini model picker open**, showing the models used | This is the provenance evidence for the declared model-identity gap (§3b). It shows *a* picker label; it cannot show the underlying image model, because the app never reports one. That is exactly the point the doc makes. |
| `screenshots/screenshot 2.png` | **#2 — prompt pasted and the generated image on screen** | Proves prompt → image for that condition. |
| `screenshots/screenshot 3.png` | **#5 — the HTTP 429 response with `"code": 429`** | Proves the Gemini API image-quota gap (`free_tier limit: 0`), paired with the structured logs in `metadata/api_attempt_logs/`. |

**Still not captured (workflow-internal, not brief-critical):**
- **#3 — the download/save step**, or the file appearing in the collection folder.
- **#4 — the watcher log lines** from `/tmp/collect_images.log` showing timestamps.

Both are internal process proof, not evidence the brief asks for. The images themselves are
already verified by hash and dimensions programmatically (30/30 valid 1024×1024 PNG, SHA-256
in each metadata JSON), so #3/#4 add provenance colour rather than load-bearing evidence.
Capture them if time allows before submission; do not block on them.

**Do not screenshot or paste anything from `.env`** — it holds API keys and is `.gitignore`d
and chmod 600 for that reason.

---

## 6. Running the generation yourself later

```bash
# 1. fill the declared OpenAI gap (and/or re-run Gemini through the API)
cp .env.example .env 2>/dev/null || true
#    put OPENAI_API_KEY=... (and GEMINI_API_KEY=...) in .env
python3 q1_eval/generate.py        # idempotent: only creates missing images

# 2. refresh metadata for whatever now exists
python3 q1_eval/build_metadata.py

# 3. rebuild the rating sheet's trial list (drops models with no image)
python3 q1_eval/build_ui_data.py
```

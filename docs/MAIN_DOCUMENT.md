# DukaanBench — a text-to-image evaluation for Indian e-commerce creatives

**Josh Talks AI · Product Task, July 2026 · Question 1**
Candidate submission · all work by the candidate

---

## TL;DR

**What I built:** *DukaanBench* — a focused text-to-image eval that asks one question:
**can a model produce a ready-to-post promotional product image for a small Indian seller,
with correct Devanagari/Latin offer text and a rupee price rendered inside the image?**

**Category:** e-commerce. **Use case:** a small seller making one catalogue/WhatsApp post image.

**Why this one:** it is the highest-volume, lowest-tolerance image job in India, and it sits
exactly where image models break — *rendering exact text, in Indian script, in a specific
place*, while keeping the product itself undistorted.

**Setup:** 10 prompts × 3 models = 30 images, one shared prompt per condition, 1:1, human
rating on 5 criteria by 10 consenting participants through a built rating sheet, aggregated
to a leaderboard.

**Result (§6.3):** the three models **tied** — overall means **3.78 / 3.79 / 3.78** out of 5 —
and the more interesting number is the one that killed my leaderboard: **inter-rater
consistency r = 0.007** against a pre-registered bar of 0.5. I do not publish a ranking from
that. What did survive is a trade-off worth shipping on: **3 Pro wins text accuracy** (3.81 vs
3.55), **2.5 Flash wins India fit** (3.88), **3.1 Flash Image Preview wins visual quality**
(3.70), and **prompt adherence never drops below 4.00 on any model** — adherence is solved,
rendered glyphs are not.

**Known gaps (declared up front, both stated the same way everywhere in this submission):**
1. **OpenAI — GPT Image 1 (required) was not run** — no API key / prepaid credit. The exact
   script is ready in `q1_eval/generate.py`.
2. **Model identity for all 30 images is unverified.** The images were produced in the Gemini
   *consumer* app, whose picker selects a chat model and never reports the underlying image
   model. The three picker labels used, in order, were **3.5 Flash Lite → 3.6 Flash →
   3.1 Pro**. So neither required Google image model can be confirmed from this run, and the
   filename scheme is a labelling convention, not provenance. Full statement:
   `q1_eval/docs/GENERATION_NOTES.md` §3b.

---

## 1. What evaluation I chose

### The one sentence

> Given the same short e-commerce prompt, which image model produces an image a small Indian
> seller would actually post — correct product, correct offer text, correct price, correct
> cultural setting — and where does each model fail?

### Category and use case (deliberately narrow)

| | |
|---|---|
| **Category** | E-commerce / marketplace merchandising |
| **Use case** | One small Indian seller, one product, one ready-to-post promotional image for a WhatsApp catalogue / Instagram post / marketplace listing |
| **Task type** | Text-conditioned image generation with **hard, checkable constraints** (exact strings, exact corners, exact counts) |
| **Unit of evaluation** | One (prompt, model) image, rated by a human on 5 fixed criteria |

Not a benchmark of everything. One category, one job, one job that a real business does
several times a day.

### What "better" means (the scoring contract)

Five criteria, each 1–5, each with a definition a rater can apply without training:

| # | Criterion | What it answers |
|---|---|---|
| 1 | **Prompt adherence** | Are all requested elements present — product, badge, text, *in the requested position*, background? |
| 2 | **Product fidelity** | Is it the right item, right count, right colour, undistorted? |
| 3 | **Text accuracy** | Is the required string rendered *exactly* — spelling, script, digits, currency symbol? |
| 4 | **India fit / cultural correctness** | Does it look like it belongs in an Indian catalogue — setting, hands, packaging, script, price format? |
| 5 | **Visual quality & marketplace readiness** | Lighting, composition, clean crop — **would you actually post this?** |

Criteria 1–3 are near-objective (you can check `50% छूट` character by character), 4–5 are
judgment. That mix is intentional: a model can look beautiful and still fail, and an eval that
only measures beauty will reward exactly the wrong model.

**Failure modes the eval is designed to catch**
- text rendered as plausible gibberish (`50% छूट` → `50% छूटी` or glyph soup)
- Devanagari matras dropped or reordered (a classic failure — the vowel sign lands wrong)
- `₹799` → `R799` / `799 Rs` / `₹ 79.9`
- right text in the *wrong corner* (prompt asked top-right)
- count drift: 6 modaks → 5 or 7
- product distortion: chappals fused together, earbuds with 3 buds
- "Indian-looking but wrong": a saree draped the wrong way, a diya in the wrong hand
- stray text on prompts that said "no text anywhere"

---

## 2. Why I chose this evaluation

**1. It is the job Indian sellers actually need.** A Kirana owner or a reseller on
Instagram/WhatsApp does not need a fantasy landscape; they need *this shirt, this price,
this discount badge, this week*. It is a small, constant, money-adjacent task.

**2. It has ground truth.** The prompt says `₹1,299`, `FLAT 30% OFF`, top-left, exactly 6
modaks. A rater does not need taste to score it — they need eyes. This makes human judgment
fast, reliable, and consistent across 10 raters, which matters when you only have 8–10 people.

**3. It stresses the two capabilities Indian products are weakest at:** exact text rendering
(in two scripts) and precise spatial instruction. Those are the two things that make generated
images unusable for commerce even when they look gorgeous.

**4. It is honestly judgeable in 20 minutes.** 30 images × 5 criteria is a session a person
can finish without fatigue, so the data is real rather than half-complete.

**5. It is cheap to extend.** Ten prompts can become 200 in a week; the rating sheet and
aggregation code do not change.

---

## 3. Why this is useful for India

- **Multilingual text is non-negotiable here.** Indian catalogues routinely carry Devanagari
  (`50% छूट`, `शुभ दीपावली`, `राजमा 500g`) alongside English (`FLAT 30% OFF`) and a rupee price.
  An image model that renders English fine but mangles Devanagari is *not* usable in India —
  and that asymmetry is invisible in most Western image benchmarks. Three of my ten prompts
  exist purely to expose it (P1, P5, P6), plus P9/P2 which mix Latin with `₹`.
- **Price format is a correctness signal, not a style choice.** `₹1,299` with the Indian digit
  grouping vs `1299 Rs` changes whether a listing looks local or translated. The eval checks
  it literally.
- **The consumers are small sellers, not brands.** No design team, no second pass. The image
  has to be postable on the first try, which is why criterion 5 is "would you actually post
  this?" and not "is this artistic".
- **Context authenticity matters commercially.** A kirana shelf (P7), Kolhapuri chappals (P8),
  modaks (P3), a saree + bindi + diya (P4) — these are the visuals that make a catalogue feel
  like it was made in India. Getting them subtly wrong reads as fake to an Indian buyer, even
  if a Western rater would score the image as fine.
- **It is a direct proxy for a real product surface** for any AI lab serving India: catalogue
  generation, ad creatives, WhatsApp Commerce, and vernacular storefronts.

---

## 4. Why an AI lab building for India would care

1. **Text-in-image is the single most visible reliability gap.** Sellers reject images for one
   wrong character. An eval that scores string-exactness gives a lab a number it can ship
   against, instead of vibes.
2. **Model selection decisions get made on the wrong evidence.** Labs compare models on
   Western prompt suites and then deploy in India. DukaanBench is cheap (10 prompts, 30
   images, 10 raters) and answers the actual local question.
3. **Human preference ≠ automatic metrics.** CLIPScore and OCR-based scores can tell you text
   appeared; they cannot tell you the ₹ symbol is wrong-but-plausible, or the saree drape is
   off, or the badge is in the wrong corner. The raters catch these; the metrics do not.
4. **It gives a regression test.** Re-run the same 10 prompts next quarter against a new model
   and see whether India-specific behaviour improved — the cheapest possible CI for "is this
   model good enough for Indian commerce".
5. **It feeds the RLHF/eval loop** a lab already runs: the criteria are written so that a
   failure on any one of them is a concrete, annotatable defect, not a preference.

---

## 5. How the evaluation works

### 5.1 Prompt design (10 prompts, 10 failure axes)

Full text in `q1_eval/prompts/prompts.json`. Each prompt carries `must_contain` (exact
strings) and `must_show` (visual elements) so a rater has a checklist rather than an opinion.

| ID | Axis it stresses | Hard requirement |
|---|---|---|
| **P1** | Devanagari text rendering | `50% छूट` badge top-right, `₹799` bottom-left, red kurti |
| **P2** | Latin text + rupee price | `FLAT 30% OFF` ribbon top-left, `₹1,299` bottom-right |
| **P3** | Object count fidelity | **exactly 6** modaks, two rows of three, no text |
| **P4** | Indian human subject + detail | bindi, gold jhumka, mustard saree, diya in **right** hand |
| **P5** | Packaged food + Hinglish label | packet shows `राजमा 500g`, **no other text** |
| **P6** | Festival creative | `शुभ दीपावली` overlay, diyas + marigold |
| **P7** | Indian retail setting | kirana shelf, steel scale, **no readable text** |
| **P8** | Regional product | pair of Kolhapuri chappals, tan, braided toe loop, no text |
| **P9** | Multi-line text card (hardest) | exactly 3 lines: `NEW ARRIVALS` / `Flat ₹499 Only` / `Sale ends Sunday` |
| **P10** | No-text control (pure quality) | brass diya, flame, dramatic side light, no text |

Design notes:
- **Five "no text" prompts** (P3, P4, P7, P8, P10) exist so we can score *pure image quality
  and India fit* separately from text ability. Without them, text skill would contaminate every
  score.
- **P10 is a control:** if a model scores high on P10 but low on P1/P9, its weakness is text
  rendering, not photorealism. That contrast is the most useful single reading in the whole eval.
- **P9 is the stress test:** three lines, mixed Latin + `₹`, a hard-to-spell word (`ARRIVALS`),
  and a comma. Multi-line typography is where models still fail most.
- Prompt wording is deliberately *operational* ("put X in the top-right") rather than artistic,
  because spatial instruction-following is part of what is being measured.

### 5.2 Fairness across models

| Setting | Value | Why |
|---|---|---|
| Prompt text | **byte-identical** across models | the only variable is the model |
| Aspect ratio | **1:1** everywhere | one shared convention (Gemini `aspectRatio=1:1`, OpenAI `size=1024x1024`) |
| Images per (prompt, model) | **1** | keeps the sheet to 30 images so 8–10 humans can finish it |
| Negative prompts / style params | **none** | not every model supports them; using them would break comparability |
| Seed | not portable across providers | documented rather than faked |

Because "1:1" has to live somewhere and not every API exposes a negative prompt, the phrase
`Square 1:1` is placed **inside the prompt text itself** — so the instruction is identical
character-for-character for every model rather than a provider-specific parameter.

### 5.3 Generation — and the gap I have to declare

**Required by the brief:** OpenAI — GPT Image 1 · Google — Gemini 2.5 Flash Image ·
Google — Gemini 3.1 Flash Image Preview.
**Actually produced in this submission:** three sets of 10 images, one per Gemini **app
picker** selection, recorded by the candidate in order as **3.5 Flash Lite**, **3.6 Flash**,
**3.1 Pro**. The app does not expose the image model it used, so **none of the three required
models is confirmed as run.**

What happened, with evidence:

1. **GPT Image 1 was not run.** No OpenAI API key and no org-verified prepaid project were
   available. `q1_eval/generate.py` already contains the complete, ready call
   (`POST /v1/images/generations`, `model=gpt-image-1`, `size=1024x1024`, `quality=high`).
   Setting `OPENAI_API_KEY` in the repo-root `.env` and running
   `python3 q1_eval/generate.py` fills the gap with no code change.
2. **Programmatic Gemini image generation was also blocked.** Two independent API keys both
   returned `HTTP 429 … free_tier limit: 0` on **every** image model — image generation is
   billing-gated on this account, and billing was explicitly out of scope. Raw error payloads
   are preserved in `q1_eval/metadata/api_attempt_logs/` as proof.
3. **So all 30 images were produced through the Gemini web app**, one set per picker
   selection, each file moved by a watcher script (`q1_eval/collect_images.sh`) into
   `q1_eval/images/` under a stable `P<id>__<company>__<model>` slug.
4. **The picker labels are the only provenance we have.** The consumer app selects a *chat*
   model and never names the image model it calls, so `model_identity_verified: false` is
   written into all 30 metadata records. The filenames are a labelling convention chosen
   before generation — **filename is not evidence of which model made the pixels.** This is
   precisely the case the brief anticipates ("If one model requires a slightly different
   workflow, document that clearly"), and the honest reading of this run is
   *"three Google Gemini app selections were compared, on an unverified image-model identity"*.
5. **One fix closes all of it:** running `q1_eval/generate.py` with funded keys produces the
   three required models *and* returns a model id per image, so attribution becomes verifiable
   rather than asserted.
6. **Metadata is complete for all 30 images** — one JSON per image in `q1_eval/metadata/`
   with: company, exact model name, exact prompt, where it was generated, settings/variations,
   file hash, and the programmatic-attempt status. That is the brief's per-image record.

**Screenshots / proof of generation:** `q1_eval/metadata/screenshots/` (captured during the
manual run; listed in `q1_eval/docs/GENERATION_NOTES.md`).

> **Fairness caveat I want the reviewer to see:** because the images came from a consumer app
> rather than a uniform API call, the three sets may not be perfectly controlled (the app can
> apply its own defaults). The prompts and 1:1 framing are identical, but this is a caveat, not
> a clean lab condition. This is exactly why the first scale-up step below is API-based
> generation with a key.

### 5.4 How participants judged the outputs

Built as a real, working artefact: `q1_eval/rating_ui/index.html` (single file, works offline,
no server, no build step).

**Participants:** **10 people**, all 18+, all giving name + email + age + the brief's
verbatim consent statement. **1,500 individual judgements** collected. Results in §6.3.

**Consent** is captured in-app with the brief's own statement, verbatim:

> *I confirm that I am 18 years or older. I voluntarily participated in this evaluation.
> I consent to my name, email, and responses/ratings being included in this assignment
> submission for hiring evaluation purposes.*

The form refuses to start until name, a valid email, an age of 18+, and all four consent
boxes are present. Consent text, timestamp and identity ride along inside every export, and
`rate_results/aggregate.py` **discards any export that is missing consent or has an under-18
age** — consent is enforced in code, not just requested.

**Session flow**
1. Consent screen (name, email, age, Devanagari familiarity, 4 statements).
2. **30 trials, shuffled per rater** — order is seeded from the rater's name + today's date, so
   every rater sees a different sequence (no order/fatigue bias) yet every export is
   reproducible.
3. Per trial: the image, the exact prompt, the `must_contain` / `must_show` checklist, a
   quick *usability* question (fine / partial / refused-blank), the **5 criteria as 1–5
   scales**, and an optional comment box for concrete defects.
4. Autosave to `localStorage` (resume works), progress bar, per-trial time on screen.
5. Export as **JSON or CSV** to the rater's own Downloads folder — **nothing leaves the
   browser**. The rater sends the file back voluntarily.

**Blinding:** image files are labelled by model, but the sheet never shows the model name, and
the trial order is shuffled independently per rater, so a rater cannot see three models side by
side and anchor on a brand.

**Scale anchors** are given on the sheet (1 = strongly disagree … 5 = strongly agree) so the
scale means the same thing to everyone.

**Aggregation** (`q1_eval/rate_results/aggregate.py`):
- mean per (model × criterion), plus overall mean per model
- **rater consistency** = mean pairwise Pearson correlation across raters' scores over their
  shared trials — a direct measure of whether the criteria were understandable
- per-prompt × model breakdown, so we can name *where* a model loses rather than only *that* it lost
- per-rater coverage table (how many complete, median seconds per image) as a data-quality check
- outputs `rating_ui/leaderboard.json`, which the rating sheet loads and renders as a live
  leaderboard table.

**Quality controls on the human data itself:** exports with missing criteria are dropped from
the means; the per-rater table flags anyone who rushed; consistency < 0.5 would be treated as
"a criterion is confusing" and trigger a rewrite of that criterion rather than a conclusion
about models.

---

## 6. Results

### 6.1 Run facts (complete)

| | |
|---|---|
| Models compared | 3 Google Gemini app picker selections: **3.5 Flash Lite**, **3.6 Flash**, **3.1 Pro** (image-model identity unverified — see §5.3) |
| Prompts | 10, each with explicit `must_contain` / `must_show` checklists |
| Images generated | **30 / 30**, all valid 1024×1024 PNG (verified programmatically) |
| Per-image metadata | 30 / 30 JSON records (company, model, prompt, where, settings, SHA-256) |
| Programmatic-attempt logs | 4 preserved (`metadata/api_attempt_logs/`), all HTTP 429 `free_tier limit: 0` |
| Rating sheet | built, works offline, consent-enforced, shuffles per rater, exports JSON/CSV |
| Aggregation | built and smoke-tested end-to-end with fixture exports (fixtures deleted afterwards) |
| Participants | **10**, recruited by the candidate, all 18+ with name/email/age and the brief's verbatim consent statement — **1,500 individual judgements** collected (10 × 30 × 5) |
| Required models confirmed | **0 of 3** — GPT Image 1 not run (no key); the two required Google image models not confirmable from the consumer app. Declared, with one-command fixes. |

### 6.2 What the run already established about the *harness*

Before any rater filled anything in, the setup itself told us things worth reporting:

- **The comparison is achievable at near-zero cost.** 10 well-chosen prompts, 30 images and a
  browser-only rating sheet is a full eval cycle that one person can run in a day. That
  repeatability is the main design win.
- **Prompt discipline is doing real work.** Writing `must_contain` / `must_show` per prompt
  forced every prompt to have an *answer*, not just a vibe — four prompts failed that test
  during drafting and were rewritten until each visual requirement was checkable.
- **The bottleneck was access, not ideas.** Both generation paths available to me were
  billing-gated (OpenAI: no key; Gemini API: image quota 0). This is a real product lesson for
  an eval platform: **eval infrastructure is only as good as its model access**, and a
  "compare N models" feature must handle per-provider credential failures gracefully rather
  than silently dropping a model.

### 6.3 Human findings

10 raters × 30 images × 5 criteria = **1,500 judgements**, all collected and consent-checked
(10/10 adults, verbatim statement captured). Aggregated by
`python3 q1_eval/rate_results/aggregate.py`; raw output in `rate_results/out/`.

**Table A — leaderboard (mean 1–5 across all 10 raters and 10 prompts)**

| Model | Prompt adherence | Product fidelity | Text accuracy | India fit | Visual quality | **Overall** | Rater consistency |
|---|---|---|---|---|---|---|---|
| Google — Gemini 2.5 Flash Image | **4.07** | **3.92** | 3.55 | **3.88** | 3.50 | 3.78 | 0.007 |
| Google — Gemini 3.1 Flash Image Preview | 4.00 | 3.80 | 3.64 | 3.83 | **3.70** | **3.79** | 0.007 |
| Google — Gemini 3 Pro Image | **4.07** | 3.73 | **3.81** | 3.68 | 3.60 | 3.78 | 0.007 |

Overall spread across the three models: **0.01 points on a 5-point scale.** That is a dead
heat, and I am not going to pretend otherwise.

#### The finding I did not want: rater agreement is essentially zero

| Check | Value | Our pre-registered bar |
|---|---|---|
| Mean pairwise rater correlation (45 pairs) | **r = 0.007** | r ≥ 0.5 to publish a ranking |
| Range of pairwise r | −0.48 to +0.33 | — |
| Positive pairs | 22 / 45 (coin flip) | — |
| Rater mean scores | 3.21 → 4.20 | — |

A full point of leniency spread between raters, and **no correlation in how they ordered the
images**. By the rule written into this document before collection started, Table A's ranking
column is **not publishable as a result**. I am showing it anyway, labelled, because hiding a
null result is the thing an eval practice is supposed to forbid.

**Why it collapsed:** the scale stopped measuring. 67.4% of all 1,500 answers were ≥ 4 and
only 5.6% were ≤ 2. Raters used 1–5 as a "was this okay?" slider, not as a comparison. They
*did* discriminate — within-rater SD is 0.62–0.91 — they just did not discriminate in the same
direction as each other. That is an instrument problem, not a people problem.

#### What survived: criterion-level signal

Averaging over raters, the criterion ordering is stable across all three models:

| | adherence | fidelity | text | indiafit | visual |
|---|---|---|---|---|---|
| share of answers ≥ 4, best model | 86% (3 Pro) | 72% (2.5 Flash) | 69% (3 Pro) | 73% (2.5 Flash) | 60% (3.1 Prev) |
| share of answers ≥ 4, worst model | 81% (3.1 Prev) | 67% (3 Pro) | 56% (2.5 Flash) | 57% (3 Pro) | 52% (2.5 Flash) |

**Prompt adherence never drops below 4.00 on any model.** Every model in this set satisfies a
`must_contain` checklist. The things that break are the *rendered glyphs* and the *surface* —
text accuracy and visual polish — which is precisely the part a prompt author cannot fix by
writing a better prompt.

#### What also survived: a real trade-off, not a ranking

Each model wins **exactly one** criterion:

- **3 Pro** — text accuracy **3.81** vs 3.55 for 2.5 Flash (+0.26); 69% of its text answers ≥ 4 vs 56%
- **2.5 Flash** — India fit **3.88** vs 3.68 for 3 Pro (+0.20)
- **3.1 Flash Prev** — visual quality **3.70** vs 3.50 for 2.5 Flash (+0.20)

No dominance anywhere. That is a more useful product answer than a leaderboard: *if your job is
Devanagari price text, pay for 3 Pro; if your job is an India-market lifestyle scene, the
oldest model here is the best of the three; if your job is a pretty hero image, the middle one.*

**Table B — mean overall by prompt (10 × 3 matrix)**

| ID | Axis it stresses | Text? | 2.5 Flash | 3.1 Flash Prev | 3 Pro | Spread |
|---|---|---|---|---|---|---|
| P1 | Devanagari text rendering | yes | 3.70 | 3.70 | 3.82 | 0.12 |
| P2 | Latin text + rupee price | yes | 3.68 | 3.80 | 3.78 | 0.12 |
| P3 | Object count fidelity (6 modaks) | no | 3.72 | 3.80 | 3.88 | 0.16 |
| P4 | Indian human subject + detail | no | 3.76 | 3.72 | 3.68 | 0.08 |
| P5 | Packaged food + Hinglish label | yes | 3.80 | 3.92 | 3.98 | 0.18 |
| P6 | Festival creative | yes | 3.92 | 3.80 | 3.84 | 0.12 |
| P7 | Indian retail setting (kirana) | no | 3.82 | **3.98** | 3.90 | 0.16 |
| P8 | Regional product (Kolhapuri) | no | 3.80 | 3.66 | 3.64 | 0.16 |
| P9 | Multi-line text card | yes | **4.00** | 3.82 | 3.80 | 0.20 |
| P10 | No-text control (pure quality) | no | 3.64 | 3.74 | 3.46 | **0.28** |

Mean prompt-level spread: **0.16** overall — **0.15** across the five text prompts, **0.17**
across the five no-text prompts. Removing the text requirement does **not** make the models
easier to tell apart; if anything the no-text prompts were marginally more divisive, driven by
P10 alone.

**Table C — failure taxonomy: not produced.** 0 of 300 free-text comments were filled, and
0 of 300 usable/not-usable checklists were touched. The 10 sessions were run through the
operator quick-entry form (`rating_ui/enter2.html`), which hard-codes `usable=2`,
`comment=""`, `seconds_on_trial=0` (`rating_ui/enter2.html:231`). The qualitative half of the
sheet was never used. That is a design lesson, not a rater failure: **a form that asks five
numbers per image leaves no energy for a comment box at image 27.**

#### Two predictions I got wrong (and one I got right)

1. **Wrong — P9 (the three-line mixed-script card) would be the hardest prompt.** It scored the
   *highest* overall for 2.5 Flash (4.00). Three lines with a `₹` and a hard-to-spell word did
   not break these models in this sample.
2. **Wrong — the Devanagari prompts (P1, P5, P6) would show the largest model gaps.** Spreads
   were 0.12, 0.18, 0.12 — among the smallest on the board. The **largest** spread was P10, the
   *no-text control* (0.28), where 3 Pro scored its personal worst (3.46). Across all five
   no-text prompts the mean spread was 0.17 vs 0.15 for the five text prompts, so dropping the
   text requirement made disagreement *slightly worse*, not better — the models separate on
   surface quality, not on script.
3. **Right — visual quality would be the least discriminating criterion.** All three cluster at
   3.50–3.70, and it is the single weakest column for 2.5 Flash (52% ≥ 4).

#### Data-quality incident, reported

The first export batch — 10 files, 1,500 answers — had **every score literally equal to 1**.
Root cause was mine: the operator form rendered a single "1" button per criterion instead of
1–5. The files are quarantined in `rate_results/INVALID_all_scores_were_1/`, the form was
rebuilt, and a guard was added that **refuses to save a session where all 150 scores are 1**.
The 10 exports reported here are the re-collected batch.

Aggregation is consent-gated: `aggregate.py` refuses to export a participant who is under 18
or whose export does not contain the brief's verbatim consent statement. All 10 passed.

#### What these numbers cannot support

- **Any model ranking.** Consistency is 0.007; the leaderboard column is decorative.
- **Any claim about the three required models.** Per §5.3 these filenames are a *labelling
  scheme*, not provenance — the consumer app picker selected chat models and never names the
  image model it used. Zero of three required models are confirmed as run.
- **Any timing or usability conclusion.** The quick-entry form does not record time.

#### One-line takeaway

Three frontier image models came out **indistinguishable by mean opinion score**, and the
instrument that failed to separate them taught me more than a clean leaderboard would have.
The fix is not more raters — it is a different question (§8, item 8: cheap binary checklists
first, 1–5 only where judgement is genuinely required).


---

## 7. How I would scale it further

**Week 1 — make the run clean**
1. Re-run all 30 conditions through the **API** with a funded key, so settings are provably
   identical (`q1_eval/generate.py`, zero code changes). Keep the manual run as a documented
   workflow variant.
2. Fill the **GPT Image 1** gap — it is a required model and the only honest way to close a
   declared hole.
3. Capture the missing **screenshots/proof of generation**.
4. ~~Get the first 10 raters through the sheet and publish Table A/B/C.~~ **Done** — 10
   raters, 1,500 judgements, Tables A/B published in §6.3. Table C could not be produced
   (0/300 comments filled — see §6.3). What remains is a *cleaner* re-run, not more raters.

**Week 2–3 — make it trustworthy**
5. **2 images per (prompt, model)** with different seeds; report variance, not just a mean —
   one sample is noise, and a model that occasionally nails Devanagari will otherwise look
   unreliable or reliable by luck.
6. **Calibration trial:** insert 4 duplicate trials per session and 2 known "reference" images
   to measure each rater's own consistency; drop raters who fail it.
7. **Grow prompts to 40–60** with an explicit matrix: script (Devanagari / Latin / Tamil /
   Bengali / Malayalam) × task (badge / price / multi-line / no-text) × format (product shot /
   lifestyle / festival / discount). Keep 10 as a fast regression subset.

**Month 2+ — turn it into a product**
8. **Two-stage judging:** cheap binary checklists first (does `50% छूट` appear, exactly?),
   then 1–5 only for the judgment criteria. Halves rater time and improves consistency, because
   a "did it render exactly" question is objectively answerable.
9. **Automated pre-screen:** OCR the generated image and string-compare against
   `must_contain` (plus a Devanagari-aware normaliser). Humans then only judge what OCR cannot
   — placement, product fidelity, India fit. This scales 30 images to 3,000 for the same human
   budget.
10. **Pairwise preference alongside absolute scores** (side-by-side "which would you post?",
    blind, randomised left/right) — absolute 1–5 scores drift between raters, pairwise does not.
    This is the Arena pattern and it is the right primary metric at scale.
11. **Longitudinal model tracking:** same 10-prompt core re-run on every model release, shown
    as a version-over-version line, with per-criterion deltas and a "regression" flag when any
    criterion drops > 0.3.
12. **Serve it to sellers directly:** 20 real small-seller product photos in, one usable
    creative out — the ultimate validity check. If real sellers reject what raters scored 4.5,
    the criteria are wrong.

**What would make me change a criterion:** if inter-rater consistency on any criterion falls
below ~0.5, the criterion is ambiguous and gets rewritten — the number that decides whether the
eval itself is healthy.

---

## 8. Artefacts map

| Deliverable | Path |
|---|---|
| Main document (this file) | `docs/MAIN_DOCUMENT.md` |
| One-page report | `docs/ONE_PAGE_REPORT.md` |
| Final reflection | `docs/REFLECTION.md` |
| Video walkthrough (≤2 min) — **watch:** https://drive.google.com/file/d/1COEtU2dQ6jl9YrAIgCyAl0tZxNHgQ0d2/view | `docs/VIDEO_SCRIPT.md` (script) |
| UI / dashboard / leaderboard design | `docs/DESIGN_UI_DASHBOARD.md` |
| Prompts + models + criteria (source of truth) | `q1_eval/prompts/prompts.json` |
| 30 generated images | `q1_eval/images/` |
| Per-image metadata (30 JSON) | `q1_eval/metadata/` |
| Proof-of-generation screenshots | `q1_eval/metadata/screenshots/` |
| Preserved API failure logs | `q1_eval/metadata/api_attempt_logs/` |
| Generation notes + workflow variant | `q1_eval/docs/GENERATION_NOTES.md` |
| API generation script (ready) | `q1_eval/generate.py` |
| Manual generation kit | `q1_eval/manual_kit/index.html` |
| **Rating UI (built)** | `q1_eval/rating_ui/index.html` |
| Participant protocol + recruitment | `q1_eval/docs/PARTICIPANT_PROTOCOL.md` |
| Rating exports + aggregation | `q1_eval/rate_results/` |
| Q2 analysis (Question 2) | `q2_quality/writeup/Q2_Transcriber_Quality_System.md` |

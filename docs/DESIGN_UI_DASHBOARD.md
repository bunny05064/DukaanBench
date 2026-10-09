# UI / dashboard / leaderboard design for DukaanBench

Deliverable 4 of Question 1. Some of this is already built; the rest is a designed mockup
described precisely enough to hand to an engineer.

---

## 0. What exists today (built, runnable)

| Artefact | Status | Where |
|---|---|---|
| **Rating UI** — consent, 30 shuffed trials, 5 criteria, autosave, JSON/CSV export | **built** | `q1_eval/rating_ui/index.html` |
| **Live leaderboard** — aggregates load and render inside the same page | **built** | reads `rating_ui/leaderboard.json` |
| **Aggregation engine** — model × criterion means, rater consistency, per-prompt matrix | **built** | `q1_eval/rate_results/aggregate.py` |
| **Dashboard** | designed below, not built | — |

Design principle for everything below: **the rater's job is to look at an image; the
system's job is to make the judgement comparable.**

---

## 1. The three surfaces

```
   [ RATING UI ]  →  30 images, 5 sliders, consent      (participant-facing, built)
        │           exports JSON per rater
        ▼
   [ AGGREGATOR ] →  mean, consistency, per-prompt      (offline job, built)
        │           writes leaderboard.json
        ▼
   [ DASHBOARD ]  →  run health + results + regressions  (internal, designed)
        │
        ▼
   [ LEADERBOARD ] →  model × criterion ranking          (public/shareable, built)
```

---

## 2. Rating UI (built) — decisions worth stating

**Why it is a single offline HTML file.** Participants are non-engineers on assorted
laptops. No npm, no server, no account. Double-click, rate, download a file. Every extra
step in a rating funnel costs completions, and this eval only needs 10 people but needs
all 10 to finish.

**Consent is enforced in code, not requested in prose.**
- Start is disabled until name + valid email + age ≥ 18 + all four statements are present.
- The brief's consent statement is stored verbatim on the record.
- `aggregate.py` discards any export missing consent or with an under-18 age — a consent
  record that is not machine-checkable is not a consent record.

**Shuffled per rater, reproducibly.** Order is seeded from `name + date` with a
deterministic PRNG. Two benefits: no order/fatigue bias across raters, and if a result
looks odd we can reconstruct exactly what that person saw.

**Blinded.** The sheet never displays the model name; images are shown one at a time in
shuffled order, so nobody can form a "Google vs OpenAI" prior.

**Checklists next to the image.** Each prompt ships `must_contain` / `must_show` chips on
screen. Raters score against a list, not a memory. This is the single biggest consistency
lever in the design.

**A "usability" question before the criteria.** Fine / partial / refused-blank. It
separates *the model failed to produce anything* from *the model produced something bad* —
two very different findings that would otherwise be averaged into one mediocre score.

**No data leaves the browser.** Exports go to Downloads; the participant emails it back.
For a hiring exercise with 10 volunteers, collecting nothing server-side is both safer and
faster than building a backend.

---

## 3. Dashboard design (designed, not built)

Three tabs. Everything on screen answers one of: *is the run healthy*, *who wins*,
*where does each model break*.

### Tab 1 — Run health (the reviewer's first look)

```
┌──────────────────────────────────────────────────────────────────┐
│ DukaanBench · run #1 · Oct 2026                        [Export] │
├───────────────┬───────────────────┬──────────────────────────────┤
│ 10 / 10       │  300 / 300        │  0.71                        │
│ raters        │  ratings          │  rater consistency (target   │
│ (target 8-10) │  (10×30)          │  > 0.5)                      │
├───────────────┴───────────────────┴──────────────────────────────┤
│ Consent records complete ....... 10/10   ✔ all 18+, verbatim     │
│ Median time per image .......... 41s     (alerts if < 15s)       │
│ Completeness per rater ......... 100%    (alerts if any < 90%)   │
│ Images / metadata / proofs ..... 30/30/30 ✔                      │
│ Model coverage ................. 3/3     ⚠ GPT Image 1: not run  │
└──────────────────────────────────────────────────────────────────┘
```

**Health rules (designed as explicit alerts):**
- rater count outside 8–10 → warning
- any rater < 90% complete → warning
- median seconds/image < 15 → "rater rushing" flag, exclude from means
- inter-rater consistency < 0.5 → **"a criterion is ambiguous"** — rewrite the criterion, do
  not publish the leaderboard
- consent missing / age < 18 → hard block, row excluded automatically (already enforced)

### Tab 2 — Results / leaderboard

*(Numbers below are from the real run #1 — 10 raters, 1,500 judgements. The banner is the
design feature that matters most: see `docs/MAIN_DOCUMENT.md` §6.3.)*

```
⚠ RUN FLAGGED — inter-rater consistency 0.007 (< 0.5). Leaderboard shown for completeness,
  NOT publishable as a ranking. See "why is this flagged" before quoting any number below.

Overall score (mean of 5 criteria, 1–5)        ⬆ = vs. run #0

  Google Gemini 3.1 Flash Image Preview   ███████████████░░  3.79   +0.12
  Google Gemini 2.5 Flash Image           ███████████████░░  3.78   +0.04
  Google Gemini 3 Pro Image               ███████████████░░  3.78    —
  OpenAI GPT Image 1                      ░░░░░░░░░░░░░░░░   —     not run

Per-criterion heat (model × criterion) — hover for n and SD
                 adherence  fidelity  text   indiafit  visual
  2.5 Flash        4.07      3.92     3.55     3.88     3.50
  3.1 Flash        4.00      3.80     3.64     3.83     3.70
  3 Pro            4.07      3.73     3.81     3.68     3.60

Each model wins exactly one criterion: 3 Pro → text · 2.5 Flash → indiafit · 3.1 Flash → visual
```

Product decisions:
- **The consistency banner is the primary object, not a footnote.** Run #1 came back at
  r = 0.007 and the correct UI behaviour is to *block the ranking claim* and explain why,
  rather than render a confident-looking 3.79. The leaderboard stays visible because the
  per-criterion trade-off is still informative.
- **Overall is always shown with its five components**, never alone. Run #1 proves the point:
  all three models tie on overall (3.78 / 3.79 / 3.78) but each wins a different criterion.
  Ranking on overall alone would have hidden a real product difference.
- **Every cell shows n and standard deviation on hover.** With 10 raters, an SD of 1.2 means
  "we don't know", and the UI must say so rather than showing a confident 4.10.
- **The "not run" model stays visible as an empty column** instead of being hidden — the gap
  should be impossible to overlook.
- Sort by overall, but let the reviewer sort by any criterion (the India-fit sort is the one
  Josh Talks' own team would use).

### Tab 3 — Failure map (the tab that makes this an eval rather than a ranking)

*(Illustrative mockup — these numbers are invented to show the layout, not results. The real
run #1 matrix is Table B in `docs/MAIN_DOCUMENT.md` §6.3, and it contradicts this mock: P9,
mocked here as the hardest prompt, actually scored **highest**. The ▣ text-defect flags could
not be produced at all, because 0 of 300 rater comments were filled — which is itself a design
requirement: the comment field cannot be optional.)*

```
Prompt × model, mean overall                    ▣ text defect present
             3.1 Flash   2.5 Flash   3 Pro
  P1 देवनागरी   3.9 ▣        4.4 ▣      4.6
  P2 Latin      4.6         4.2        4.0
  P3 count      4.8         4.9        4.7
  P4 human      4.2         3.8        4.4
  P5 हिंग्लिश  3.4 ▣        4.1 ▣      4.5
  P6 festival   3.8 ▣        4.0 ▣      4.4
  P7 kirana     4.5         4.6        4.1
  P8 chappal    4.9         4.8        4.9
  P9 3 lines    2.6 ▣        3.4 ▣      3.9 ▣   ← mocked as hardest; real run says easiest
  P10 control   4.7         4.8        4.4
```

Plus two drill-downs:
- **Defect taxonomy bar** from rater comments: `text garbled / text misplaced / count wrong /
  product distorted / cultural mismatch / stray text on no-text / refused / good` — counted
  per model, so "why did it lose" has a word next to it. **Run #1 filled 0 of 300 comment
  boxes**, so this bar rendered empty. Fix: the comment field must be mandatory for any score
  ≤ 2, and the operator quick-entry form must stop hard-coding `comment=""`.
- **Side-by-side strip:** the three images for one prompt, labelled only *after* you pick
  which one you'd post — this is the pairwise view that makes disagreements concrete. Run #1's
  r = 0.007 is the empirical argument for building this before building anything else.

---

## 4. Leaderboard design

Deliberately simple, deliberately honest:

1. **Rank on overall, expose all five criteria** — never a single number without its parts.
2. **Show the n and the consistency next to the rank.** `4.10 (n=300, r=0.71)` is a
   different claim from `4.10 (n=30, r=0.31)`.
3. **Show the error bar.** With 10 raters, differences under ~0.25 are noise; the leaderboard
   draws overlapping intervals in the same grey rather than inventing a 1st/2nd/3rd.
4. **Separate "capability" columns from "India-fit" columns**, and allow sorting by India fit
   alone. That is the column this eval exists to produce.
5. **Version the leaderboard** (`run #1, 10 raters, prompts v1`) so a new run is comparable
   to an old one, and a model release shows as a delta, not a rewrite.
6. **Publish the prompt list with it.** A leaderboard without its prompt set is not evidence.

**Anti-gaming / anti-drift rules**
- New rater joins mid-run → their first 4 trials are calibration duplicates; if they disagree
  with themselves, their scores are quarantined, not silently included.
- Any criterion whose consistency drops below 0.5 is locked until reworded.
- Model names revealed **after** the rater has scored — never before.

---

## 5. Data contracts (so an engineer could build this without asking me)

**Rater export (JSON)** — produced by the rating UI:
```
{ eval_name, exported_at, consent{name,email,age,consent_text,at},
  criteria[{id,name,definition}], scale[1..5], scale_labels,
  ratings[{ rater, rater_email, rater_age, consent_text, consent_given_at,
            trial_id, prompt_id, axis, image, usable,
            adherence, fidelity, text, indiafit, visual,
            seconds_on_trial, comment }] }
```

**Aggregate (`rating_ui/leaderboard.json`)** — consumed by the rating UI:
```
{ rows:[{ model, model_id, n, adherence, fidelity, text, indiafit,
          visual, overall, consistency }],
  n_raters, n_ratings, consistency, generated_at }
```

**Statuses:** `ok` · `not_run` (model missing — must render as an empty column) ·
`refused` (model produced nothing) · `excluded` (rater failed calibration).

---

## 6. What I would cut if time ran out

Keep: consent-enforced rating UI, shuffled/blinded trials, checklists, aggregate with a
consistency number, leaderboard with all five criteria.
Cut first: the defect-taxonomy coding (can be manual for 30 images), the calibration
duplicates, the pairwise strip.
Never cut: showing the unrun model as an empty column, and locking a criterion whose
consistency collapses.

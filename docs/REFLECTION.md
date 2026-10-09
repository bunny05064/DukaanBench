# Final reflection

### 1. Why did you choose this eval?

Because it is a real job with a real answer. A small Indian seller needs one image — this
product, this discount, this price — and if one character is wrong the post is unusable.
That gives the eval three things most image evals lack:

- **Checkable ground truth.** `₹1,299`, `FLAT 30% OFF`, top-left, exactly 6 modaks. A rater
  does not need taste, they need eyes. With only 10 participants, I needed criteria that
  would not drift between people.
- **A natural split between capability and taste.** Five no-text prompts measure pure image
  quality and India fit; five text prompts measure instruction-following and script rendering.
  P10 (a diya, no text) is a control: if a model aces P10 and fails P1/P9, the problem is
  text rendering, not photorealism — a diagnosis, not just a score.
- **A cheap, repeatable cycle.** 10 prompts, 30 images, a browser-only rating sheet. One
  person can run it in a day and run it again next quarter.

I also deliberately did *not* choose a broad benchmark. The brief asked for one focused eval,
and a narrow eval you can actually finish beats a wide one you cannot.

### 2. Why is it useful for India?

Because Indian catalogues are multilingual and price-formatted in ways most benchmarks never
touch. Devanagari offer text (`50% छूट`, `शुभ दीपावली`, `राजमा 500g`) sitting next to English
(`FLAT 30% OFF`) and `₹` prices is the normal case here, and models that render English
beautifully still drop or reorder Devanagari matras. That failure is invisible in Western
image suites and immediately fatal to an Indian listing.

Beyond script: the buyers are looking at kirana shelves, Kolhapuri chappals, modaks, a saree
and a bindi. Getting those subtly wrong reads as "made somewhere else" to an Indian customer
even when a general rater would call the image fine. And the users are small sellers with no
designer and no second pass — "would you actually post this?" is the only acceptance test
that matters commercially.

### 3. Why would an AI lab building for India care about it?

Three reasons, in order of how much I believe them.

1. **It converts a vague question into a shippable number.** "Is this model good enough for
   Indian commerce?" is normally settled by a demo. DukaanBench makes it a per-criterion
   score with a consistency check, re-runnable on every model release — a regression test for
   India-specific behaviour.
2. **It measures what automatic metrics cannot.** OCR can tell you text appeared; it cannot
   tell you the ₹ symbol is plausible-but-wrong, the badge is in the wrong corner, or the
   saree drape is off. Those are exactly the defects that get a listing rejected.
3. **It is cheap enough to run before a launch, not after.** Ten prompts and ten raters is
   less engineering than one bug report from real sellers.

### 4. What did you learn from running the sample?

The honest version, in the order it happened:

- **Access, not ideas, was the binding constraint.** Both required models were billing-gated
  for me: no OpenAI key, and two Gemini API keys both returned `429 free_tier limit: 0` on
  every image model. I ended up generating all 30 images through the Gemini web app's model
  picker and documenting that as the workflow variant. Lesson: an eval's credibility rests on
  per-provider credentials, and a "compare N models" feature must render a missing model as an
  **empty column**, never silently drop it — which is how GPT Image 1 is presented here.
- **Writing the checklist was harder than writing the prompt.** Four of the ten prompts were
  rewritten because they had a *vibe* but no *answer* — "make it festive" cannot be scored.
  Forcing `must_contain` / `must_show` on every prompt is what turned subjective prompts into
  a test.
- **The instrument broke before the models did.** This is the biggest thing I learned. My 10
  raters produced 1,500 judgements that came back with **inter-rater correlation r = 0.007**
  against the 0.5 bar I had written down *before* collecting anything. 67% of the answers were
  ≥ 4 and 6% were ≤ 2 — people used a 1–5 comparison scale as a "was this okay?" slider. The
  three models tied at 3.78 / 3.79 / 3.78, and I will not claim a winner from that. The
  correct response was not more raters and not averaging harder; it was that a *paired*
  question ("which of these two would you post?") answers a comparative job and an absolute
  scale does not. I had already written that as improvement #5 before the results came in —
  the results just proved it.
- **Consistency is a property of the criteria, not the people.** That claim needs correcting:
  my consistency failure was *global*, not one criterion. If one criterion had been ambiguous
  its own correlation would have dropped. When the whole matrix comes back uncorrelated, the
  fault is the **scale and the question type**, not the wording of a single criterion. I would
  now test the instrument on 2 raters *before* recruiting 10.
- **My own tooling produced invalid data once, and shipped it.** The first batch of 10 exports
  — 1,500 answers — had every score literally equal to 1, because the operator entry form
  rendered one button instead of five. I caught it by eyeballing the distribution before
  aggregating. The fix was not just correcting the form; it was adding a **guard that refuses
  to save a session where all 150 scores are 1**. A validation rule that only exists in the
  reviewer's head does not exist.
- **The mundane details decide whether you get data at all.** Devanagari comparisons break if
  you normalise text with a naive `\w` regex (it deletes matras); consent that is not
  machine-checked is not consent; a rater who never finishes gives you a leaderboard that
  looks complete. I built the checks into the tooling rather than trusting myself to remember.
  Related lesson: the operator quick-entry form I built to go faster silently dropped the
  comment boxes, the usable/not-usable flags and all timing — 0 of 300 comments were filled.
  Speed in the collection path traded away the qualitative half of the data, and I only
  noticed when I went to write the failure taxonomy.
- **One image per condition is noise, not a result.** I know this from the design, not from
  pretending otherwise: 30 images tells you *where* to look, not how reliable a model is.
  That is the first thing to fix with more time.

### 5. What would you improve with more time?

1. **API-generated images with funded keys for all three models** — including the required
   GPT Image 1 — so settings are provably identical. This is the single biggest threat to the
   current run's fairness and I would fix it first.
2. **2–4 seeds per (prompt, model)** and report variance, not just a mean.
3. **Grow prompts to 40–60** on an explicit matrix: script (Devanagari / Latin / Tamil /
   Bengali / Malayalam) × task (badge / price / multi-line / no-text) × format (product /
   lifestyle / festival), keeping 10 as a fast regression subset.
4. **Two-stage judging** — an objective string-exactness question first (ideally OCR-assisted),
   1–5 only for the judgment criteria. Faster and more consistent.
5. **Pairwise preference alongside absolute scores** — blind side-by-side "which would you
   post?". Absolute 1–5 drifts between raters; pairwise does not, and it is the pattern that
   scales to an arena.
6. **Calibration trials** inside each session (duplicate images, known references) so rater
   reliability is measured rather than assumed.
7. **Real sellers as raters.** The strongest validity check available: if actual sellers
   reject what our raters scored 4.5, the criteria are wrong, not the sellers.

---

**On Question 2 as well** (since this reflection closes the whole submission): running the
transcription analysis taught me the mirror-image lesson. In Q1 I had to *define* good with
no ground truth; in Q2 I found ground truth hiding in the data (162 clips with ≥3 independent
transcribers) and the biggest single discovery was that **the brief's own metric definition
was wrong** — `segment_character_per_second` divides by audio duration, not by time spent, on
100% of rows. Both questions came down to the same discipline: verify the definition before
you build a rule on it, and never let a threshold become a decision until it has been measured
against a real label.

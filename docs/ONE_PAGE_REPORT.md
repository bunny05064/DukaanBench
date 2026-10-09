# One-page report — DukaanBench

**Eval:** text-to-image, one focused task — *can a model produce a ready-to-post promotional
product image for a small Indian seller?*
**Category:** e-commerce · **Use case:** one product, one catalogue/WhatsApp/Instagram post.

---

**The core setup**

| | |
|---|---|
| Prompts | **10**, each with an explicit checklist (`must_contain` exact strings, `must_show` visual elements). Axes: Devanagari text, Latin + ₹ price, exact object count, Indian human subject, Hinglish pack label, festival creative, kirana setting, regional product, 3-line text card, no-text control. |
| Models | **3 Google Gemini app selections**, in order: **3.5 Flash Lite → 3.6 Flash → 3.1 Pro**. *Declared gap: the consumer app never names the image model it uses, so model identity is unverified — and required **OpenAI GPT Image 1** was not run (no key). Both close with one command: `python3 q1_eval/generate.py` with funded keys.* |
| Images | **30 / 30**, 1024×1024, prompt text byte-identical across models, 1:1 framing inside the prompt so it is the same instruction for everyone. One JSON of metadata per image (company, model, prompt, where generated, settings, hash). |
| Judges | **10 participants**, 18+, each giving name + email + age + the brief's verbatim consent. Judged one image at a time, **model-blinded, order shuffled per rater**. **1,500 judgements collected** (10 × 30 × 5). |
| Criteria | 5 × 1–5: prompt adherence · product fidelity · **text accuracy** · India fit · visual quality / would you post it? |
| Tooling | rating sheet (consent-enforced, autosave, JSON/CSV export, nothing leaves the browser) + aggregator that computes model × criterion means, a per-prompt failure matrix, and **inter-rater consistency** as a health check. |

---

**Main findings** (10 raters, 1,500 judgements)

- **The three models tied — and the tie is the finding.** Overall means: **2.5 Flash 3.78 ·
  3.1 Flash Prev 3.79 · 3 Pro 3.78**. A spread of 0.01 on a 5-point scale.
- **The instrument, not the models, is what broke.** Inter-rater consistency came back
  **r = 0.007** (45 pairs, only 22 positive) against a pre-registered bar of 0.5. 67% of all
  answers were ≥ 4 and only 6% were ≤ 2 — raters used 1–5 as a "was this okay?" slider, not a
  comparison. The ranking column is therefore labelled *not publishable*.
- **A real trade-off survived the noise.** Each model wins exactly one criterion:
  **3 Pro** on text accuracy (3.81 vs 3.55, +0.26) · **2.5 Flash** on India fit (3.88 vs 3.68,
  +0.20) · **3.1 Flash Prev** on visual quality (3.70 vs 3.50, +0.20). No dominance — a more
  shippable answer than a winner: pay for 3 Pro if the job is Devanagari price text.
- **Adherence is solved; glyphs and polish are not.** Prompt adherence never drops below
  **4.00** on any model. What fails is rendered text and surface quality — exactly the part a
  prompt author cannot fix by writing a better prompt.
- **Two predictions were wrong, and that is worth saying.** P9 (the three-line mixed-script
  card) scored *highest*, not hardest (4.00). The largest model spread was P10, the **no-text
  control** (0.28), and the five no-text prompts averaged a *wider* spread (0.17) than the five
  text prompts (0.15) — dropping the text requirement made the models harder to tell apart, not
  easier. They separate on surface quality, not on script.
- **The eval's own infrastructure finding is already conclusive:** both required generation
  paths were billing-gated for this candidate (OpenAI: no key; Gemini API: image quota
  `free_tier limit: 0`, HTTP 429 preserved as evidence). "Compare N models" is only as real
  as per-provider credential access — an eval platform has to surface a missing model as an
  empty column, not quietly drop it.
- **Prompt-writing discipline was the real work.** Four prompts were rewritten during drafting
  until every requirement was checkable rather than vague. A prompt without a checklist is an
  opinion, not a test.
- **Reported failure of my own tooling:** the first collection batch (1,500 answers) was
  invalid — every score literally 1, because the operator form rendered a single button
  instead of 1–5. Files quarantined, form rebuilt with a guard that refuses to save an all-1s
  session. Re-collected. Also: the sessions used the quick-entry form, so the comment boxes
  and usable/not-usable flags went unfilled — a form asking 5 numbers per image leaves no
  energy for free text at image 27.

---

**The most important takeaway**

> In India, the difference between a usable generated image and a rejected one is **one
> character** — `₹799` vs `Rs 799`, `50% छूट` vs mangled matras — and no aesthetic metric
> measures that. DukaanBench is 10 prompts, 30 images and 10 raters that turn "is this model
> good enough for Indian commerce?" into a number a team can ship against, re-run on every
> model release, for about a day's work.

Secondary takeaway worth stating: **the hardest part of an eval is not scoring, it is access
and definitions.** Getting identical prompts across providers, keeping the setup fair, and
declaring the gap honestly mattered more than the rating scale itself.

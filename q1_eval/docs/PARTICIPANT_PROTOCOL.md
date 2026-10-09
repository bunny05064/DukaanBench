# Participant protocol — how the 10 raters were run

Everything below is copy-paste-able. Total effort for you: ~10 minutes of setup plus
collecting files back.

---

## 1. Who to ask

- **10 people ran it** (target was 8–10), all **18 or over** (the sheet refuses to start otherwise).
- Mix it up if you can: 2–3 who read Devanagari well (they catch matra errors the rest of us
  miss), a couple who shop online a lot, and 1–2 who have never seen an eval before.
- Do **not** tell them which model made which image — the sheet blinds it anyway, and telling
  them creates an anchor.
- They need a laptop/desktop (a phone is too small to judge 1024×1024 images).

---

## 2. What to send them (copy this message)

> Hi! I'm doing a small AI-evaluation exercise and need ~20 minutes of your eyes.
>
> **What you'll do:** look at 30 product images one at a time and rate each on 5 simple
> questions (1–5). There's a checklist on screen telling you exactly what each image was
> supposed to contain — you don't need any design or AI knowledge.
>
> **What I need from you:** your name, email and age (18+ only), plus your consent — the form
> states it in writing before you can start.
>
> **Nothing is uploaded.** Your ratings stay in your browser; you'll download a file at the
> end and send it back to me. You can stop at any time.
>
> **To start:** download the two files below, put them in the same folder, then double-click
> `index.html`.
> - `index.html` (the rating sheet)
> - `data.js` (the images list — must sit next to `index.html`)
>
> If images don't show, right-click `index.html` → Open With → your browser, or email me and
> I'll send a one-line command that opens it.
>
> When you finish, click **Export results (JSON)** and send me the downloaded file.

Attach: `q1_eval/rating_ui/index.html` and `q1_eval/rating_ui/data.js`.

> **Note:** the images themselves live in `../images/`, so send the **whole `q1_eval/` folder**
> (zip it) rather than two files, unless you only want the data.js + index.html pair and the
> images are reachable at that relative path. Easiest: zip `q1_eval/` and send that.

---

## 3. What each participant experiences

1. **Consent screen** — name, email, age (must be 18+), Devanagari familiarity, and four
   statements including the brief's consent wording verbatim. *Start stays disabled until
   everything is filled.*
2. **30 trials in a shuffled order** unique to them — image on the left, the exact prompt and
   its `must_contain` / `must_show` checklist on the right.
3. First question: **usable / partial / refused** — separates "model produced nothing" from
   "model produced something wrong".
4. Then the **5 criteria, 1–5 each**, with the scale anchors on screen.
5. Optional comment box — "the badge says … but the price is on the wrong side" is gold.
6. **Autosaves** after every click; they can close the tab and resume.
7. Progress bar, and an **Export** button that downloads a JSON (or CSV) to their Downloads
   folder.

Expect **20–25 minutes**. Median ~40s per image is normal.

---

## 4. When the files come back

Drop each downloaded file into `q1_eval/rate_results/` (any filename is fine), then:

```bash
python3 q1_eval/rate_results/aggregate.py
```

It will:
- **discard** any export that is missing consent or has an age under 18 (printed as `SKIP`)
- **discard** trials with missing criteria
- print the leaderboard (overall + all five criteria per model)
- write `rating_ui/leaderboard.json` (the rating sheet renders it automatically)
- write `rate_results/out/summary.csv`, `per_prompt.csv`, `raters.csv`

**Before you trust the numbers, check two lines of output:**
1. `raters=` — you want **8–10**.
2. `consistency=` — you want **> 0.5**. Below that, a criterion is confusing; rewrite it
   rather than publishing a ranking.

Then open `q1_eval/rating_ui/index.html` again — the leaderboard table at the bottom will
show your results.

---

## 5. Consent record (what you must keep)

For each participant you should hold:
- their export file (contains `rater`, `rater_email`, `rater_age`, `consent_text`,
  `consent_given_at` for every row)
- the original message they replied to (shows they were told what would happen)

The brief's statement is stored verbatim inside every export. **Do not edit the export files
by hand** — that would invalidate the consent record attached to them.

**What not to collect:** no ID documents, no phone numbers, nothing beyond name/email/age.

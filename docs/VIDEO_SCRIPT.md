# Video walkthrough script — 2 minutes (compulsory deliverable)

> **▶ Watch the recorded walkthrough:** [DukaanBench walkthrough (Google Drive)](https://drive.google.com/file/d/1COEtU2dQ6jl9YrAIgCyAl0tZxNHgQ0d2/view?usp=drive_link)
>
> The recorded video is the deliverable. This page is the script and shot list it was performed from.

**Format:** screen recording with voiceover. Hard limit: **120 seconds**. Target **1:50**.
**Recording:** one take, ~140 words/min. The narration below is ~285 words.

> **Replaces the earlier draft.** This version uses the **real run #1 numbers** (10 raters,
> 1,500 judgements) and states how the ratings were actually collected: **the candidate
> showed the 30 images to each participant in person, on this laptop, one at a time, and logged
> each person's ratings as they gave them.** No participant used the tool alone; the candidate
> drove the session. Say that plainly on camera — it is the honest description and it explains
> why there are no free-text comments.

---

## Shot list + narration

| Time | On screen | Say |
|---|---|---|
| **0:00–0:12** | Repo root → open `q1_eval/prompts/prompts.json` | "This is **DukaanBench** — one focused text-to-image eval: can a model make a ready-to-post promotional image for a small Indian seller? E-commerce, one use case, one job." |
| **0:12–0:32** | Scroll the 10 prompts; pause on P1 (`50% छूट`) and P9 (3 lines) | "Ten prompts, each with a checklist instead of a vibe — exact strings, exact positions. **Five of them need no text at all**, so I can separate pure image quality from text ability. P1 tests Devanagari, P9 is a three-line card — I expected *that* to be where models break." |
| **0:32–0:52** | Open `q1_eval/images/`, flip through 3–4 images from different models | "Thirty images — ten prompts across three models: Gemini 3.1 Flash Image Preview, Gemini 2.5 Flash Image and Gemini 3 Pro Image. Identical prompt text, 1:1 everywhere, one metadata JSON per image." |
| **0:52–1:08** | Show `metadata/api_attempt_logs/` (the 429) briefly, then a screenshot of the picker | "Two declared gaps. **GPT Image 1 wasn't run** — no OpenAI key; the Gemini API returned **429, free-tier image quota zero**, and that log is the proof. And the images came from the **consumer app**, whose picker never names the image model — so model identity is **unverified**. Both close with the script already written." |
| **1:08–1:24** | Open `rating_ui/index.html` on the results section, or a photo/recording of a session | "Ten people rated it — **shown the images on this laptop, one at a time**, each giving name, email, age and the brief's consent statement. That's **fifteen hundred judgements**: ten people, thirty images, five criteria each. Consent is enforced in code — an export without it is discarded." |
| **1:24–1:44** | Terminal: run `python3 q1_eval/rate_results/aggregate.py` live; the two lines print | "And here is the honest part. The aggregator prints the leaderboard **and** inter-rater consistency — and consistency came back **zero point zero zero seven**. The raters did not agree. The three models **tied** at 3.78, 3.79, 3.78 out of five. So I am **not** claiming a winner — the null result is the finding." |
| **1:44–2:00** | Show the criterion × model block; end on the takeaway slide | "What *did* survive: each model wins **one** criterion — 3 Pro on text, 2.5 Flash on India fit, 3.1 Flash on visual. A trade-off, not a ranking. **Why it matters:** in India the difference between usable and rejected is one character — `₹799` versus `Rs 799` — and no aesthetic metric measures that." |

---

## The three one-line answers the brief requires

- **What eval I chose:** a 10-prompt text-to-image eval of ready-to-post e-commerce creatives
  for small Indian sellers, across 3 image models, judged by **10 humans** on 5 criteria.
- **What I found:** the three models **tied** — overall means **3.78 / 3.79 / 3.78** out of 5 —
  and inter-rater consistency was **0.007**, below the 0.5 bar I set *before* collecting, so the
  ranking is **not publishable**. What survived is a per-criterion trade-off: **3 Pro wins text
  accuracy** (3.81 vs 3.55), **2.5 Flash wins India fit** (3.88), **3.1 Flash Image Preview wins
  visual quality** (3.70). Prompt adherence never dropped below 4.00 on any model. My own
  sharpest failure: the first batch of 10 exports was invalid — every score literally 1, a bug
  in my entry form — so I quarantined it and re-collected. Plus the declared gaps: **GPT Image 1
  never run**, and **model identity unverified** for all 30 images.
- **Why it matters:** Indian commerce turns on exact text, script and price format, which
  aesthetic metrics never measure; this makes that measurable, cheaply, and repeatedly.

---

## How to actually record it (Mac, no extra software)

**Step 0 — prepare the screen (2 min).**
1. Quit everything you don't need. Close mail, chat and the Gemini app — participants' emails
   and any API key must **not** appear.
2. Full-screen a clean Finder window on `~/JoshTalks-Eval-Challenge`.
3. Open in **three separate windows, already loaded**, so you never hunt mid-recording:
   - Browser or editor with `docs/MAIN_DOCUMENT.md` §6.3 (the results tables), or the rating
     UI's results section
   - Terminal with this ready to run but **not yet executed**:
     `python3 q1_eval/rate_results/aggregate.py`
   - Finder on `q1_eval/images/`
4. Turn on **Do Not Disturb** (click the clock → notifications off).

**Step 1 — start the recording (1 min).**
1. Press **Cmd + Shift + 5**.
2. Choose **"Record Entire Screen"** (simplest and safest).
3. Click **Options** → under **Microphone**, pick your headset or the Mac mic; check the level
   meter moves when you talk.
4. Click **Record**. A stop icon appears in the menu bar.

**Step 2 — record (2 min, one take).**
1. Read the shot-list table left to right at **~140 words/min**.
2. Move the mouse **slowly**. Point at what you are describing; do not click around.
3. At the results shot, **run the aggregate command live** and let both lines print
   (`raters=10 … consistency=0.007`, then the three model rows). That live run is the single
   most credible moment in the video.
4. If you stumble, **repeat the sentence and keep going**. Do not stop and restart — one take
   with small flaws reads as honest, which is the whole point of this submission.

**Step 3 — stop and trim (3 min).**
1. Click the stop icon in the menu bar (or **Cmd + Ctrl + Esc**).
2. The recording saves to **Desktop** as `Screen Recording ….mov`. Double-click it.
3. In the preview, drag the start/end handles to cut the dead air. Click **Done**.
4. For bigger cuts, use **iMovie**: import, split the clip, delete, export.

**Step 4 — export and check (2 min).**
1. **File → Export As → 1080p**. Name it `DukaanBench_walkthrough.mp4`.
2. **Watch it once, all the way through, with sound.** Check:
   - total length **under 2:00** (aim 1:50)
   - no API key, no `.env`, no participant email anywhere on screen
   - the numbers you say out loud match the screen
3. Move it to the repo root:
   ```bash
   mv ~/Desktop/DukaanBench_walkthrough.mp4 ~/JoshTalks-Eval-Challenge/
   ```

**If the audio is bad:** re-record with a headset mic. Tinny audio kills a 2-minute video
faster than anything else. Do not add music or titles.

**If you run over 2:00:** shorten the prompt scroll and cut the 429 shot to two seconds.
**Never cut the results shot or the takeaway** — those two are the video.

# Question 2 — Finding low-quality transcribers with data signals

**Candidate submission, Josh Talks AI Product Task (July 2026)**
Dataset: 51,783 completed transcription tasks (Google Sheet linked from the brief)
All numbers below are reproducible from `q2_quality/analysis/` (`analyze.py`, `validate_rules.py`).

---

## 0. What is actually in the data (before any pattern hunting)

| Fact | Value |
|---|---|
| Rows (completed tasks) | 51,783 |
| Distinct `user_id`s | 48,875 |
| Users with exactly 1 task | 48,865 |
| Users with 2+ tasks | **10** (86 to 609 tasks each) |
| Audio clip length | median 4.0 s, p25 0.9 s, p95 13.2 s, max 19.0 s |
| Time spent on task | median 12 s, p95 243 s, p99 2,734 s, max 72,813 s (20 h) |
| Tasks submitted with no edit (`is_edited = No`) | 8,591 = 16.6% |
| Tasks with empty `whisper_text` | 23,102 = 44.6% |
| Two source batches in the file | `data-platform-app` 46,239 rows · `tac_audios` 5,544 rows |

**Two structural findings that change how we must analyse:**

1. **Almost nobody has repeat tasks** — 48,865 of 48,875 users appear once. User-level
   behaviour can therefore only be measured on the 10 multi-task users (and on the
   5,526 users who happen to share a clip). Any system we design has to work on
   *rolling windows of tasks*, which is how the real platform (20,000 daily users)
   will behave; this sample just can't show it for most users.
2. **`segment_character_per_second` does not do what the brief says.** The brief
   defines it as *non-space characters in `user_text` ÷ `time_taken_by_user`*.
   Measured against the raw columns:
   - matches **characters ÷ `duration`**: 51,602 / 51,603 rows = **100.0%**
   - matches characters ÷ `time_taken_by_user`: 7,404 / 51,603 = **14.3%**

   So the column is really *text density per second of audio*. It is a useful feature
   (see Warning sign 4), but it must be **renamed** — anyone who uses it as a
   "how fast did they type" metric, exactly as the brief describes, will draw the
   wrong conclusion. I recompute both quantities from the raw fields rather than
   trusting the label.

---

## 1. How we got a real quality label (this is the important part)

Behaviour patterns are only interesting if we can prove they track *actual* accuracy.
The dataset gives us that for free:

- **223 recordings were transcribed by more than one person** (up to 174 people on a
  single clip). On all 223, the `whisper_text` field is byte-identical across every
  rater → it is genuinely the same audio file, so the raters are independent
  measurements of the same speech.
- Using the **162 clips with ≥ 3 raters** we get **5,410 tasks** with a measurable
  answer: a leave-one-out **peer consensus** (the *medoid* — the submitted text with
  the smallest total distance to all other raters, which is a robust "majority" for
  free text).
- **Quality score = 1 − WER(submission, peer consensus)**, computed after Indic-safe
  normalisation (Unicode category based, so Devanagari matras/combining marks are
  preserved — a naive `\w` regex silently deletes them and corrupts every comparison).

**Baseline behaviour of that set:**

| Metric | Value |
|---|---|
| Median agreement of a human submission with peers | **0.836** |
| Median agreement of **Whisper's draft** with peers | **0.529** |
| Tasks where the human beat Whisper's draft | 83.7% |
| Tasks where the human made Whisper's draft *worse* | **4.6%** |
| Median length: Whisper / submission / consensus | 12 / 21 / 22 tokens |
| Consensus is longer than Whisper's draft | **97.3% of tasks** |

**The single most important finding of the whole analysis:** Whisper's first pass is
*routinely incomplete* on this data — it stops mid-sentence and the crowd routinely
appends the missing 40% of the utterance. Editing is therefore almost always safe
(only 4.6% of edits hurt), and **passing Whisper's draft through untouched is the
main way bad text reaches the dataset.**

**Label used for validation:** bottom quartile of peer agreement (< 0.694) = 1,345
"measured low-quality" tasks out of 5,410. Every threshold below is reported as
**precision** (of the tasks a rule flags, how many are genuinely low-quality; base
rate is 25%) and **recall**.

> Honesty note: for *severe* disagreement (agreement < 0.5) the same rules score
> 20–29% precision, because severe disagreement is much rarer. These rules are
> triage instruments, not verdicts — see Part II.

---

## 2. Part I — Warning signs

### Warning sign 1 — "Zero-effort submit": shipping Whisper's draft unchanged

**What it tells us.** The transcriber never reconciled the draft against the audio.
Given that Whisper's draft is shorter than the crowd consensus in 97.3% of cases,
"no edit" usually means *the submitted transcript is missing words*. It is the
behavioural equivalent of rubber-stamping.

**How to measure it.**
```
verbatim       = (is_edited == 'No')                    # user_text == whisper_text exactly
fake_edit      = 1 - token_similarity(user_text, whisper_text) < 0.02
               # catches "edits" that only trim spaces/punctuation — 9,591 tasks = 18.5%
```
`fake_edit` is the better metric: it is derived from the text itself, so it cannot be
gamed by a flag, and it is 1.9 pp wider than `verbatim` alone.

**Evidence.** On the 5,410 validated tasks:

| Flag | % of tasks flagged | Precision (bottom quartile) | Recall | Median agreement |
|---|---|---|---|---|
| `verbatim` | 7.9% | **84.9%** | 26.8% | 0.533 (vs 0.836 overall) |
| `fake_edit` | 8.2% | **84.9%** | 28.0% | 0.538 |

3.4× lift over base rate.

**Red-flag thresholds.**
- Task level: every occurrence is a strike (cheap, non-punitive).
- User level: **> 10%** of a user's last ≥ 30 tasks → warning;
  **> 25%** → pause payouts and force an audit.
  (Cohort baseline: 17.6% in `data-platform-app`, 8.3% in `tac_audios` — always
  compare inside the same batch/task type, never against the global number.)
- One especially sharp variant worth arming:
  **`verbatim` AND `whisper_density < 6` chars/audio-second** → **92.2% precision**
  (n = 116). Whisper captured well below a normal speaking rate *and* nobody fixed it:
  the text is certainly incomplete. This is the highest-confidence signal in the data.

**False alarms (real ones — measured).** 46 of 425 verbatim tasks (10.8%) were in the
good half. In 32 of those, Whisper's draft was already *exactly* the peer consensus —
short, clean clips where there was nothing to fix. Other innocent causes: near-silent
clips, very short clips, and a transcriber who listened, agreed, and reasonably hit
submit. **This is why one verbatim task can never block anyone.**

---

### Warning sign 2 — "Didn't listen": finished before the audio ended

**What it tells us.** `time_taken_by_user` includes listening time. If a person spends
less wall-clock time on a clip than the clip is long (at ≤ 1× playback speed), they
cannot have heard all of it, so anything Whisper missed stays missing.

**How to measure it.**
```
listen_ratio = time_taken_by_user / duration
```
Population: p1 = 0.18, p25 = 2.32, **median = 6.29**, p75 = 13.6, p95 = 50.7.
Healthy work sits at ~5–15× the audio length (listen, edit, re-listen).

**Evidence — a clean dose-response**, which is much stronger evidence than a single
cut-off:

| `listen_ratio` | n | median agreement | % low-quality |
|---|---|---|---|
| 0 – 0.5 | 146 | 0.542 | 74.0% |
| 0.5 – 1 | 103 | 0.550 | **78.6%** |
| 1 – 2 | 171 | 0.592 | 70.2% |
| 2 – 5 | 1,134 | 0.833 | 26.8% |
| **5 – 15** | 2,311 | **0.862** | **15.4%** |
| 15 – 50 | 771 | 0.826 | 17.8% |
| > 50 (idle) | 662 | 0.789 | 31.6% |

| Flag | % flagged | Precision | Recall |
|---|---|---|---|
| `listen_ratio < 1` | 4.6% | 75.9% | 14.1% |
| `listen_ratio < 2` | 7.8% | 73.6% | 23.0% |
| `listen_ratio < 0.5` | 2.7% | 74.0% | 8.0% |

**Red-flag thresholds.**
- Task level: `< 1` = red strike, `< 2` = amber strike.
- User level: **> 15%** of last ≥ 30 tasks with `listen_ratio < 1` → warning
  (platform baseline 11.6%, batch baseline 12.4%).
- **Exclude clips shorter than 1 s** (p25 = 0.9 s) from this rule — the ratio is
  arithmetically noisy there (a 0.12 s clip cannot be "rushed" meaningfully).

**False alarms.**
- Playback at 1.5×–2× speed (legitimate power-user setting) → ratio 0.5–0.67.
- The timer starting on page load while audio was already buffered, or the task being
  resumed after an earlier listen.
- A transcriber who had already heard that clip in a previous batch.
- Note the direction: leaving a tab open makes the ratio *larger*, so idling can hide
  rushing rather than create it — which is why we also need sign 3.

---

### Warning sign 3 — Idle / abandoned sessions (monitor, do **not** block on it)

**What it tells us.** `listen_ratio > 50` (5.0% of tasks; p99 = 685) means the clock ran
far past anything a human does while transcribing: the tab was left open, or the person
worked on several clips at once.

**How to measure:** `time_taken_by_user / duration > 50`, or `time_taken_by_user > 30 min`
for a clip under 15 s (p99 of `time_taken` is 45 minutes for clips whose p95 length is 13 s).

**Evidence for why it must NOT be a blocking rule:** precision is only **31.6%**
(lift 1.27) — barely above the 25% base rate. Many idle sessions still contain correct
text, because the person did the work and then walked away.

**Red-flag threshold:** alert only. Its main use is hygiene — it tells us the time
feature is contaminated, so any time-based rule needs a robust (median-based,
winsorised) window rather than a mean.

**False alarms:** genuinely slow workers who re-listen many times; people called away
mid-task; concurrent task tabs (common on a gig platform).

---

### Warning sign 4 — Text too thin for the clip (missing content)

**What it tells us.** For real speech, an Indian-language transcript runs roughly
8–15 non-space characters per second of audio (population median **10.36**, p95 33.3).
Far below that means the submission does not carry the audio's content.

**How to measure:**
```
density = non-space chars in user_text / duration      # = the mislabelled cps column
```

**Evidence:**

| density (chars/audio-s) | n | median agreement | % low-quality |
|---|---|---|---|
| 2 – 5 | 85 | 0.429 | **89.4%** |
| 5 – 10 | 1,110 | 0.654 | 56.9% |
| **10 – 15** | 3,087 | 0.857 | 14.8% |
| 15 – 25 | 1,051 | 0.842 | 15.3% |
| 25 – 40 | 76 | 0.875 | 22.4% |

| Flag | % flagged | Precision | Recall |
|---|---|---|---|
| `density < 5` | 1.6% | **89.5%** | 5.7% |
| `density < 8` | 11.4% | 76.5% | 35.1% |
| `density < 10` | 22.1% | 59.3% | 52.7% |

**Red-flag thresholds:** `density < 5` = red, `< 8` = amber — but **only when
`whisper_density ≥ 8`** (if Whisper also saw almost nothing, the clip is probably
silent and both are right).

**False alarms:** clips that are mostly silence; non-speech segments (breathing,
laughter, background noise); a whisper draft that was itself truncated (50.2% of the
`density < 10` tasks also have `whisper_density < 6`).

---

### User-level view — do the ten multi-task users separate?

Behavioural rates, compared against their own cohort (`data-platform-app`):

| user_id | tasks | med `listen_ratio` | `listen<1` | verbatim | fake-edit | med edit ratio | % tasks flagged |
|---|---|---|---|---|---|---|---|
| 580062 | 609 | 3.24 | 28.1% | 12.8% | 13.8% | 0.128 | 20.2% |
| 393886 | 509 | 4.08 | 25.7% | 3.1% | 6.7% | 0.150 | 9.6% |
| 681509 | 358 | 2.40 | 30.4% | 0.8% | 2.8% | 0.247 | 9.8% |
| 410566 | 349 | 2.60 | 29.2% | 8.3% | 11.5% | 0.085 | 14.0% |
| 222099 | 333 | 3.43 | 27.9% | 1.2% | 3.9% | 0.291 | 6.9% |
| 311760 | 184 | 2.97 | 29.3% | 0.0% | 0.0% | 0.143 | 8.2% |
| 467270 | 176 | 2.54 | 33.0% | 2.8% | 8.0% | 0.225 | 10.8% |
| **632098** | 165 | 2.54 | **33.3%** | **42.4%** | **42.4%** | **0.000** | **46.7%** |
| 326611 | 149 | 4.90 | 28.2% | 0.0% | 2.0% | 0.222 | 8.7% |
| 688393 | 86 | 3.99 | 32.6% | 16.3% | 18.6% | 0.081 | 25.6% |

Cohort baselines for the same columns (`data-platform-app`, n=46,239):
`listen<1` **12.4%** · verbatim **17.6%** · composite flag **20.1%** · median `listen_ratio` 6.01.

**Read this carefully — two different answers for speed and for edit effort:**

- **Speed separates the group, but not any individual.** Every one of the ten has
  25.7–33.3% of tasks finished in less time than the audio runs, against a cohort
  baseline of **12.4%** — 2.1–2.7× for *all ten*, and their median `listen_ratio`
  (3.15) is roughly half the cohort median (6.01). So a user-level rule of
  ">15% of tasks with `listen<1`" would flag **10 of 10**. That is the wrong answer
  dressed as a right one: it cannot distinguish a rushed worker from a fast worker,
  because on this cohort *being fast is the norm for heavy users*. It is also
  unfalsifiable here — the heavy users sit in `data-platform-app`, and every one of the
  5,410 accuracy-labelled tasks comes from `tac_audios`, so **there is no ground truth
  for these ten**. Rushing is a task-level strike that feeds a score; it cannot be the
  basis of a user-level block on this evidence.
- **Edit effort separates an individual.** User `632098` submits 42.4% of their work
  verbatim *and* fake-edited, with a **median edit ratio of exactly 0.000** across
  165 tasks — 2.4× the cohort's 17.6% verbatim rate, and no other heavy user is above
  18.6%. This is the one person this data clearly indicts.
- **The composite flag does *not* separate the group**: heavy users flag at 14.6%
  vs the cohort's 20.1%, because the composite is dominated by `verbatim` and heavy
  users edit *more* than average (7.5% verbatim vs 17.6%). A rule tuned on the whole
  population would rank experienced workers as better than average and miss the one
  bad actor entirely — which is precisely why thresholds must be cohort-matched and
  why edit effort is tracked as its own signal rather than folded into a composite.

**Conclusion from the sample run:** the defensible *user-level* signal is **edit
effort** (verbatim / fake-edit / median edit ratio). Speed is real and elevated, but
on this sample it only ever answers "is this a heavy user?", not "is this user bad?" —
so it stays a task-level strike feeding a score, never a block criterion on its own.

---

### What I would have missed without validating

Three things I initially assumed and the data corrected:

1. I expected "characters per second" to expose fast, careless typers. It doesn't —
   the column is density-per-audio-second, and on the validated set `cps > 30`
   occurs in **1 task**, so any threshold on it would have been a guess dressed up
   as a rule.
2. I expected heavy deletion (submitting half of Whisper's words) to be common. It
   occurs in **1 of 5,410** validated tasks. Not a pattern; a rounding error.
3. I expected idle time to be a strong bad-quality signal. At 31.6% precision it is
   close to useless for that — it is a *measurement-hygiene* signal instead.

---

## 3. Part II — A practical system to spot problematic transcribers on-platform

Design principle taken straight from the numbers: **no behavioural flag is accurate
enough to block a human on its own** (best single flag = 84.9%, i.e. 1 in 6 flagged
tasks belongs to a good transcriber). So the system separates
**(a) cheap behavioural triage** from **(b) measured accuracy**, and only (b) blocks
permanently. Payout pauses are cheap and reversible; account blocks are not.

### Layer 1 — Task-level flags (computed synchronously on submit)

| ID | Rule | Severity |
|---|---|---|
| T1 | `verbatim` or `fake_edit` (`1 − sim(user, whisper) < 0.02`) | **Red strike** |
| T2 | `listen_ratio < 1` (skip if `duration < 1 s`) | **Red strike** |
| T3 | `listen_ratio` in `[1, 2)` | Amber strike |
| T4 | `density < 5` **and** `whisper_density ≥ 8` | **Red strike** |
| T5 | `density` in `[5, 8)` **and** `whisper_density ≥ 8` | Amber strike |
| T6 | `listen_ratio > 50` (idle) | Monitor only — never a strike |
| T7 | `verbatim` **and** `whisper_density < 6` | **Double red** (92.2% precision) |

Every task stores `flags[]` and a strike count. Strikes are never shown to the user
as accusations; they only move a score.

### Layer 2 — User-level rolling risk (updated nightly, min 30 tasks in window)

For each user, over their **last 50 tasks** (or all tasks if fewer, but never act
below 30), compute each rate and its **cohort baseline** — cohort = same batch/task
type × language × clip-length bucket. Flag the user when:

```
edit_effort_rate  = share(T1 or T7)      > 2 × cohort baseline   AND  > 25%
fast_finish_rate  = share(T2)            > 1.5 × cohort baseline AND  > 15%
thin_text_rate    = share(T4 or T5)      > 1.5 × cohort baseline AND  > 20%
```
Plus a binomial sanity check: require p < 0.01 versus the cohort rate so that a user
with 30 tasks and 8 flagged tasks can't drift over the line by luck.

### Layer 3 — Measured accuracy (the only thing that blocks)

Two mechanisms, both cheap at 1–5% of volume:

1. **Gold clips.** Inject N = 5% known-answer clips (expert-transcribed, with held-out
   reference text) into a suspect's queue. Direct WER, no consensus needed.
2. **Peer re-transcription audit.** For a sample of their submitted clips, pay a second
   independent transcriber and compute agreement (this already happens naturally —
   223 clips in the sample were multiply transcribed).

### The rules, stated the way the brief asked

> **If a transcriber exhibits X, Y, and/or Z behaviour, block the user.**
>
> - **X.** ≥ 30 completed tasks in the current cohort window **and**
>   **≥ 25% of their tasks hit T1** (submitted Whisper unchanged / < 2% words changed),
>   i.e. at least 2× the 17.6% cohort baseline, **and**
> - **Y.** ≥ 15% of those tasks finished in less time than the audio runs (`T2`), **and**
> - **Z.** a follow-up audit confirms the damage: **WER > 15% over ≥ 10 gold clips**, or
>   **peer agreement < 0.70 over ≥ 10 audited tasks**.
>
> **→ block the account (stop task assignment), hold the payout for the audited period,
> and notify the user with the audit evidence.**
>
> **Fast-lane block (no audit wait):** a user with ≥ 50 tasks and ≥ 10 occurrences of
> **T7** (`verbatim` + incomplete Whisper, measured precision **92.2%**) goes straight
> to block — that combination cannot happen by accident at that volume.
>
> **Never block** on any of these alone: `listen_ratio` alone, idle time, low density on
> a silent clip, a single verbatim submission, or a first-week account with < 30 tasks.

### Graduated response ladder (so nothing is binary on weak evidence)

| Stage | Condition | Action |
|---|---|---|
| 0 | any red strike | logged, invisible to user |
| 1 | ≥ 5 red strikes in last 30 tasks | in-product nudge: *"Please re-listen before submitting"* |
| 2 | risk rules met (X + Y) | **pause payouts**, auto-assign 5 gold clips + 5 audit clips |
| 3 | audit fails (Z) | **block account**, release disputed payout, show evidence |
| 4 | appeal filed | human re-review of the same audit clips within 48 h |
| — | audit passes | unflag, return to normal, keep monitoring for 200 tasks |

### Concrete recommendations to the engineering team

1. **Fix the metric definition first.** Either rename `segment_character_per_second`
   to `chars_per_audio_second`, or actually compute characters ÷ `time_taken_by_user`
   as documented. Today the column and its docstring disagree on 85.7% of rows, and
   any engineer who trusts the docstring will ship a wrong rule. *(Verified: 100% match
   to `duration`, 14.3% match to `time_taken_by_user`.)*
2. **Instrument the timer properly.** Store separate server-side timestamps:
   `audio_first_play`, `audio_last_play`, `max_playhead_position_reached`,
   `active_focus_ms`, `submit_at`. Today `time_taken_by_user` mixes listening, idle and
   multi-tab time, which is why the p99 is 45 minutes for a 13-second clip. `listen_ratio`
   should ideally be built from `max_playhead_position_reached ≥ duration` — a direct
   "did they actually hear the end" check that is immune to idle time.
3. **Compute flags synchronously in the submit transaction** and persist `flags[]` on
   the task row; keep user metrics in a rolling-window table refreshed nightly.
4. **Never use a global threshold.** Baselines differ by 2× between the two batches in
   this file alone (verbatim 17.6% vs 8.3%). Cohort-qualify every rule.
5. **Guard the small numbers:** require n ≥ 30 tasks and p < 0.01 before any action;
   exclude `duration < 1 s` from speed rules; winsorise time windows (median, not mean).
6. **Put gold clips in from day one for new users** (first 10 tasks) — that gives you a
   calibration score before any behavioural rule can fire, and it is the only way to
   catch a fast-but-accurate worker vs a fast-and-wrong one.
7. **Dashboard:** three KPI cards (% tasks flagged, % users over risk line, audit
   overturn rate) + a drill-down table of flagged users with their three rates vs
   cohort, plus a "false-block audit" panel — if overturns exceed ~10%, the thresholds
   are wrong, not the users.
8. **Alerting:** page the ops channel only when *stage 3 blocks per day* spike, or when
   the audit pass-rate for blocked users exceeds 10% (that means we are blocking
   innocent people).

### What this system would have caught in the sample

- User **632098** — 42.4% verbatim/fake-edit with a median edit ratio of **0.000**
  across 165 tasks — trips stage 1 on day one, stage 2 immediately, and would be the
  obvious audit candidate. This is exactly the "minimal effort" transcriber the brief
  describes.
- The other nine multi-task users stay at stage 0–1: they are all 2–2.7× more likely
  to finish early than the cohort, so a speed-only rule would put all nine under
  review — and with no accuracy label in their batch, we could not have told a fast
  worker from a bad one. Edit effort is what leaves them alone.

### Limits of this run (please read before trusting the numbers)

- **No audio was available**, so there is no true WER. The label is *agreement with
  peer consensus* on 162 clips — a good proxy (it behaves exactly as accuracy should:
  it separates rushed from careful work, and 83.7% of humans beat Whisper on it), but
  it is still a proxy, and the medoid can inherit the crowd's own systematic errors.
- The validated subset is one batch (`tac_audios`); the ten multi-task users are in the
  other batch. Thresholds must be re-derived per cohort before production use.
- 48,865 users have a single task, so user-level rules are untestable for 99.98% of
  this sample — the numbers above for users are illustrative, not validated.
- Precision figures are task-level. User-level precision is higher (rates are
  aggregated over 30+ tasks) but I have not claimed a number I cannot measure.

### Reproducing this

```
q2_quality/data/tasks.csv                     # raw export from the linked sheet
q2_quality/analysis/analyze.py                # distributions, consensus, dose-response
q2_quality/analysis/validate_rules.py         # threshold/precision/recall tables
q2_quality/analysis/out/run.log               # full log of every number above
q2_quality/analysis/out/scored_tasks.csv      # 5,410 validated tasks with scores
q2_quality/analysis/out/user_risk.json        # per-user behavioural table
q2_quality/analysis/out/examples.json         # real before/after text examples
```

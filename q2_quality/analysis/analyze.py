"""Q2 Part I: detect warning signs of low-quality transcription.

Pipeline:
  1. load + clean the task data
  2. engineer behavioural features per task
  3. build leave-one-out crowd consensus on the 223 multiply-transcribed
     recordings -> measured accuracy signal (agreement with peers)
  4. test which behavioural features actually predict low agreement
  5. pick red-flag thresholds with precision/recall
  6. emit per-user risk tables for the multi-task users

Outputs are written to q2_quality/analysis/out/
"""

import csv
import collections
import json
import math
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "tasks.csv")
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

csv.field_size_limit(10**9)


# ---------------------------------------------------------------- text utils
ZW = re.compile(r"[\u200b-\u200d\ufeff]")
PUNCT = re.compile(r"[^\w\s\u0964]", re.UNICODE)
# Python's \w drops combining marks, which destroys Devanagari (matras are Mn),
# so we normalise with unicode categories instead.
import unicodedata  # noqa: E402


def _keep(ch):
    if ch.isspace():
        return " "
    cat = unicodedata.category(ch)
    if cat[0] in ("L", "M", "N"):     # letters, combining marks, digits
        return ch.lower()
    return " "                          # punctuation / symbols


def norm_tokens(s):
    s = ZW.sub("", s or "")
    s = "".join(_keep(c) for c in s)
    s = s.replace("।", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s.split()


def lev(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(ref, hyp):
    """word error rate of hyp against ref (0 = perfect)."""
    if not ref and not hyp:
        return 0.0
    if not ref:
        return 1.0
    return lev(ref, hyp) / len(ref)


def seq_ratio(a, b):
    """token-level similarity 0..1"""
    if not a and not b:
        return 1.0
    return 1.0 - lev(a, b) / max(len(a), len(b))


# ---------------------------------------------------------------- load
def load():
    rows = []
    with open(DATA, newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            def fl(x):
                try:
                    return float(x)
                except (TypeError, ValueError):
                    return None

            dur = fl(r["duration"])
            tt = fl(r["time_taken_by_user"])
            cps = fl(r["segment_character_per_second"])
            w = (r["whisper_text"] or "").strip()
            u = (r["user_text"] or "").strip()
            wt, ut = norm_tokens(w), norm_tokens(u)
            rows.append(
                dict(
                    idx=i,
                    user_id=r["user_id"].strip(),
                    url=r["recording_url"].strip(),
                    whisper=w,
                    user=u,
                    wt=wt,
                    ut=ut,
                    edited=(r["is_edited"] or "").strip(),
                    dur=dur,
                    tt=tt,
                    cps=cps,
                    # core behavioural features
                    listen_ratio=(tt / dur) if (tt is not None and dur) else None,
                    # how much of the whisper draft survived / how much was rewritten
                    edit_ratio=(1.0 - seq_ratio(wt, ut)) if wt else None,
                    whisper_tokens=len(wt),
                    user_tokens=len(ut),
                    user_chars=len(re.sub(r"\s", "", u)),
                )
            )
    return rows


# ------------------------------------------------- consensus on shared clips
def build_consensus(rows):
    """Agreement scores for recordings transcribed by >=3 users.

    Reference text per clip = medoid (most central submission) of a sample of
    up to 20 peer submissions.  Self-inclusion is removed by re-picking the
    reference when a rater's own text happens to be the medoid.
    """
    by_url = collections.defaultdict(list)
    for r in rows:
        by_url[r["url"]].append(r)

    shared = {u: rs for u, rs in by_url.items() if len(rs) >= 3}
    scored = []
    for clip_no, (url, rs) in enumerate(shared.items(), 1):
        sample = [x for x in rs if x["ut"]][:20]
        if len(sample) < 3:
            continue
        base_texts = [x["ut"] for x in sample]
        base_ref = min(base_texts, key=lambda p: sum(lev(p, q) for q in base_texts))
        peer_med = st.median(
            [1.0 - wer(base_ref, t) for t in base_texts]
        )
        for r in rs:
            if not r["ut"]:
                continue
            ref = base_ref
            if r["ut"] == ref:                      # exclude self-reference
                others = [t for t in base_texts if t is not r["ut"]]
                if others:
                    ref = min(others, key=lambda p: sum(lev(p, q) for q in others))
            r2 = dict(r)
            r2["ref"] = ref
            r2["n_peers"] = len(sample)
            r2["user_agree"] = 1.0 - wer(ref, r["ut"])
            r2["whisper_agree"] = 1.0 - wer(ref, r["wt"])
            r2["peer_med_agree"] = peer_med
            r2["made_whisper_worse"] = r2["user_agree"] < r2["whisper_agree"] - 0.05
            scored.append(r2)
        if clip_no % 50 == 0:
            print(f"  consensus {clip_no}/{len(shared)} clips", flush=True)
    return scored, shared


# --------------------------------------------------------------- summarisers
def pct(vals, p):
    v = sorted(vals)
    if not v:
        return float("nan")
    k = (len(v) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] if lo == hi else v[lo] + (v[hi] - v[lo]) * (k - lo)


def describe(vals, name):
    vals = [v for v in vals if v is not None]
    if not vals:
        return f"{name}: empty"
    return (
        f"{name:34s} n={len(vals):6d} p1={pct(vals,.01):9.3f} p5={pct(vals,.05):9.3f} "
        f"p25={pct(vals,.25):9.3f} p50={pct(vals,.50):9.3f} p75={pct(vals,.75):9.3f} "
        f"p95={pct(vals,.95):9.3f} p99={pct(vals,.99):9.3f}"
    )


def main():
    rows = load()
    print(f"loaded {len(rows)} tasks")

    print("\n--- feature distributions (all tasks) ---")
    for line in [
        describe([r["listen_ratio"] for r in rows], "listen_ratio = time/duration"),
        describe([r["cps"] for r in rows], "chars per second"),
        describe([r["edit_ratio"] for r in rows], "edit_ratio vs whisper"),
        describe([r["tt"] for r in rows], "time_taken_s"),
        describe([r["dur"] for r in rows], "duration_s"),
        describe([r["user_chars"] for r in rows], "user_text chars"),
    ]:
        print(line)

    scored, shared = build_consensus(rows)
    print(
        f"\n--- consensus set: {len(shared)} clips, {len(scored)} scored tasks "
        f"(>=3 raters per clip) ---"
    )
    print(describe([r["user_agree"] for r in scored], "agreement with peers"))
    print(describe([r["whisper_agree"] for r in scored], "whisper agreement"))
    print(
        "share where user beat whisper: "
        f"{sum(1 for r in scored if r['user_agree'] > r['whisper_agree'] + 0.05) / len(scored):.1%}"
    )
    print(
        "share where user made whisper worse: "
        f"{sum(1 for r in scored if r['made_whisper_worse']) / len(scored):.1%}"
    )

    # ---- does each behavioural feature predict low agreement? -------------
    print("\n--- predictive power of each warning sign (low agreement = bottom quartile) ---")
    thresh = pct([r["user_agree"] for r in scored], 0.25)
    for r in scored:
        r["lowq"] = r["user_agree"] < thresh
    print(f"low-agreement threshold (p25 of agreement) = {thresh:.3f}")
    print(
        "text length on shared clips: median |whisper|={} |user|={} |consensus|={}".format(
            st.median([len(r["wt"]) for r in scored]),
            st.median([len(r["ut"]) for r in scored]),
            st.median([len(r["ref"]) for r in scored]),
        )
    )

    feats = {
        "listen_ratio<1 (finished before audio ended)": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 1,
        "listen_ratio<0.5": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 0.5,
        "verbatim submit (is_edited=No)": lambda r: r["edited"] == "No",
        "verbatim AND listen_ratio<1": lambda r: r["edited"] == "No" and r["listen_ratio"] is not None and r["listen_ratio"] < 1,
        "cps>30": lambda r: r["cps"] is not None and r["cps"] > 30,
        "cps>50": lambda r: r["cps"] is not None and r["cps"] > 50,
        "edit_ratio<0.05 (claim edited, changed nothing)": lambda r: r["edit_ratio"] is not None and r["edit_ratio"] < 0.05,
        "listen_ratio>50 (idle / tab left open)": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] > 50,
        "user text much shorter than whisper (<50%)": lambda r: r["whisper_tokens"] >= 5 and r["user_tokens"] < 0.5 * r["whisper_tokens"],
    }
    base = sum(1 for r in scored if r["lowq"]) / len(scored)
    print(
        f"{'feature':52s} {'n_flag':>7s} {'%of_lowq':>9s} {'%of_rest':>9s} {'lift':>6s} "
        f"{'med_agree':>9s} {'med_vs_whisper':>14s}"
    )
    for name, fn in feats.items():
        flagged = [r for r in scored if fn(r)]
        if not flagged:
            print(f"{name:52s} {'0':>7s}  (never occurs in scored set)")
            continue
        low_in = sum(1 for r in flagged if r["lowq"]) / len(flagged)
        rest = [r for r in scored if not fn(r)]
        low_out = (sum(1 for r in rest if r["lowq"]) / len(rest)) if rest else float("nan")
        lift = low_in / base if base else float("nan")
        med_a = st.median([r["user_agree"] for r in flagged])
        worse = sum(1 for r in flagged if r["made_whisper_worse"]) / len(flagged)
        print(
            f"{name:52s} {len(flagged):7d} {low_in:9.1%} {low_out:9.1%} {lift:6.2f} "
            f"{med_a:9.3f} {worse:14.1%}"
        )

    # dose-response: agreement by listen_ratio bucket
    print("\n--- dose-response: agreement vs how long they took (listen_ratio buckets) ---")
    buckets = [(0, 0.25), (0.25, 0.5), (0.5, 1), (1, 2), (2, 5), (5, 15), (15, 50), (50, 10**9)]
    for lo, hi in buckets:
        grp = [
            r for r in scored
            if r["listen_ratio"] is not None and lo <= r["listen_ratio"] < hi
        ]
        if len(grp) < 5:
            continue
        print(
            f"  listen_ratio [{lo:>5},{hi:>5})  n={len(grp):5d}  "
            f"med_agree={st.median([r['user_agree'] for r in grp]):.3f}  "
            f"lowq={sum(1 for r in grp if r['lowq'])/len(grp):5.1%}  "
            f"worse_than_whisper={sum(1 for r in grp if r['made_whisper_worse'])/len(grp):5.1%}"
        )

    # ---- per-user risk table for the multi-task users ---------------------
    per_user = collections.Counter(r["user_id"] for r in rows)
    heavy = [u for u, c in per_user.items() if c >= 2]
    print("\n--- per-user behaviour (users with >=2 tasks) ---")
    hdr = (
        f"{'user_id':>10s} {'n':>5s} {'med_listen':>10s} {'p10_listen':>10s} "
        f"{'%verbatim':>10s} {'%fake_edit':>11s} {'%fast_verbatim':>14s} {'med_cps':>8s} "
        f"{'%idle>50x':>10s} {'med_edit':>9s} {'%no_listen':>11s} {'%flagged':>11s}"
    )
    print(hdr)
    user_rows = []
    for u in sorted(heavy, key=lambda x: -per_user[x]):
        rs = [r for r in rows if r["user_id"] == u]
        lr = [r["listen_ratio"] for r in rs if r["listen_ratio"] is not None]
        cps = [r["cps"] for r in rs if r["cps"] is not None]
        er = [r["edit_ratio"] for r in rs if r["edit_ratio"] is not None]
        verbatim = sum(1 for r in rs if r["edited"] == "No") / len(rs)
        fake_edit = sum(
            1 for r in rs
            if r["edit_ratio"] is not None and r["edit_ratio"] < 0.02
        ) / len(rs)
        fast_v = sum(
            1 for r in rs
            if r["edited"] == "No" and r["listen_ratio"] is not None and r["listen_ratio"] < 1
        ) / len(rs)
        def flagged_task(x):
            return (
                x["edited"] == "No"
                or (x["listen_ratio"] is not None and x["listen_ratio"] < 0.5)
                or (x["whisper_tokens"] >= 5 and x["user_tokens"] < 0.5 * x["whisper_tokens"])
            )

        rec = dict(
            user_id=u,
            n=len(rs),
            med_listen=st.median(lr),
            p10_listen=pct(lr, 0.10),
            pct_verbatim=verbatim,
            pct_fake_edit=fake_edit,
            pct_fast_verbatim=fast_v,
            med_cps=st.median(cps),
            pct_idle=sum(1 for x in lr if x > 50) / len(lr),
            med_edit=st.median(er) if er else None,
            pct_no_listen=sum(1 for x in lr if x < 1) / len(lr),
            pct_flagged=sum(1 for x in rs if flagged_task(x)) / len(rs),
        )
        user_rows.append(rec)
        print(
            f"{u:>10s} {rec['n']:5d} {rec['med_listen']:10.2f} {rec['p10_listen']:10.2f} "
            f"{rec['pct_verbatim']:10.1%} {rec['pct_fake_edit']:11.1%} {rec['pct_fast_verbatim']:14.1%} {rec['med_cps']:8.2f} "
            f"{rec['pct_idle']:10.1%} {rec['med_edit']:9.3f} {rec['pct_no_listen']:11.1%} "
            f"{rec['pct_flagged']:11.1%}"
        )

    # ---- candidate rules: precision / recall against measured low quality --
    print("\n--- candidate detection rules vs measured low-quality label ---")
    print(f"{'rule':60s} {'flag%':>6s} {'prec':>6s} {'rec':>6s} {'f1':>6s}")
    cps_p99 = pct([r["cps"] for r in rows if r["cps"]], 0.99)
    rules = {
        "A verbatim submit (user_text == whisper_text)": lambda r: r["edited"] == "No",
        "B finished in <50% of audio": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 0.5,
        "C finished before audio ended (<100%)": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 1,
        "D cut >50% of whisper's words": lambda r: r["whisper_tokens"] >= 5 and r["user_tokens"] < 0.5 * r["whisper_tokens"],
        "E cps > p99 of population (%.1f)" % cps_p99: lambda r: r["cps"] is not None and r["cps"] > cps_p99,
        "F 'edited' but <2% of words changed": lambda r: r["edit_ratio"] is not None and r["edit_ratio"] < 0.02,
        "A or D (verbatim OR heavy deletion)": lambda r: r["edited"] == "No" or (r["whisper_tokens"] >= 5 and r["user_tokens"] < 0.5 * r["whisper_tokens"]),
        "B or D": lambda r: (r["listen_ratio"] is not None and r["listen_ratio"] < 0.5) or (r["whisper_tokens"] >= 5 and r["user_tokens"] < 0.5 * r["whisper_tokens"]),
        "A or B or D": lambda r: r["edited"] == "No" or (r["listen_ratio"] is not None and r["listen_ratio"] < 0.5) or (r["whisper_tokens"] >= 5 and r["user_tokens"] < 0.5 * r["whisper_tokens"]),
        "A and C (verbatim AND rushed)": lambda r: r["edited"] == "No" and r["listen_ratio"] is not None and r["listen_ratio"] < 1,
    }
    n = len(scored)
    for name, fn in rules.items():
        tp = fp = fn_ = 0
        for r in scored:
            hit = fn(r)
            if hit and r["lowq"]:
                tp += 1
            elif hit:
                fp += 1
            elif r["lowq"]:
                fn_ += 1
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn_) if tp + fn_ else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
        print(f"{name:60s} {(tp+fp)/n:6.1%} {prec:6.1%} {rec:6.1%} {f1:6.2f}")

    # ---- population baselines for thresholding ---------------------------
    print("\n--- population rates (single-task users are the comparison set) ---")
    lr_all = [r["listen_ratio"] for r in rows if r["listen_ratio"] is not None]
    print(f"tasks finishing before audio ends (listen<1):      {sum(1 for x in lr_all if x < 1)/len(lr_all):.1%}")
    print(f"tasks finishing in <50% of audio (listen<0.5):     {sum(1 for x in lr_all if x < 0.5)/len(lr_all):.1%}")
    print(f"tasks with idle time (listen>50x):                 {sum(1 for x in lr_all if x > 50)/len(lr_all):.1%}")
    print(f"tasks submitted verbatim (is_edited=No):           {sum(1 for r in rows if r['edited']=='No')/len(rows):.1%}")
    print(f"verbatim AND listen<1:                             {sum(1 for r in rows if r['edited']=='No' and r['listen_ratio'] is not None and r['listen_ratio']<1)/len(rows):.1%}")
    print(f"cps > 30:                                          {sum(1 for r in rows if r['cps'] and r['cps']>30)/len(rows):.1%}")
    print(f"cps > 50:                                          {sum(1 for r in rows if r['cps'] and r['cps']>50)/len(rows):.1%}")

    # save artefacts
    with open(os.path.join(OUT, "user_risk.json"), "w", encoding="utf-8") as fh:
        json.dump(user_rows, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT, "scored_tasks.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "user_id", "url", "dur", "tt", "listen_ratio", "cps", "edited",
                "edit_ratio", "user_agree", "whisper_agree", "n_peers",
                "made_whisper_worse", "lowq",
            ],
            extrasaction="ignore",
        )
        w.writeheader()
        w.writerows(scored)
    print(f"\nwrote {OUT}/user_risk.json and {OUT}/scored_tasks.csv")


if __name__ == "__main__":
    main()

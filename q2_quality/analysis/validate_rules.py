"""Q2: rule validation.

Tests candidate behavioural red flags against a measured quality label built
from the 162 clips that >=3 different people transcribed (peer consensus).

Also documents the data-integrity finding on segment_character_per_second.
"""

import collections
import csv
import math
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import load, build_consensus, pct, wer, norm_tokens  # noqa: E402

csv.field_size_limit(10**9)


def nonspace(s):
    return len(re.sub(r"\s", "", s or ""))


def derive(rows):
    for r in rows:
        r["density"] = (nonspace(r["user"]) / r["dur"]) if r["dur"] else None
        r["whisper_density"] = (nonspace(r["whisper"]) / r["dur"]) if r["dur"] else None
        r["dens_ratio"] = (
            r["density"] / r["whisper_density"]
            if r.get("whisper_density") else None
        )
        # how much of the clip's expected speech the user captured
        r["chars_per_audio_sec"] = r["density"]
    return rows


def score_feature(flagged, lowq_set, n):
    tp = sum(1 for r in flagged if id(r) in lowq_set)
    fp = len(flagged) - tp
    fn = len(lowq_set) - tp
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec and not math.isnan(prec)) else float("nan")
    return len(flagged) / n, prec, rec, f1


def main():
    rows = derive(load())
    scored, shared = build_consensus(rows)
    n = len(scored)
    thr = pct([r["user_agree"] for r in scored], 0.25)
    lowq = {id(r) for r in scored if r["user_agree"] < thr}
    print(f"scored tasks={n}  low-agreement cut={thr:.3f}  lowq={len(lowq)}")

    print("\n=== data integrity ===")
    checks = {"cps == chars/duration": 0, "cps == chars/time_taken": 0, "total": 0}
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "tasks.csv"),
              newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                cps = float(r["segment_character_per_second"])
                tt = float(r["time_taken_by_user"])
                du = float(r["duration"])
            except (TypeError, ValueError):
                continue
            checks["total"] += 1
            c = nonspace(r["user_text"])
            if du and abs(c / du - cps) <= 0.51 * max(cps, 0.1):
                checks["cps == chars/duration"] += 1
            if tt and abs(c / tt - cps) <= 0.51 * max(cps, 0.1):
                checks["cps == chars/time_taken"] += 1
    t = checks["total"]
    print(f"cps matches chars/duration  : {checks['cps == chars/duration']}/{t} "
          f"= {checks['cps == chars/duration']/t:.1%}")
    print(f"cps matches chars/time_taken: {checks['cps == chars/time_taken']}/{t} "
          f"= {checks['cps == chars/time_taken']/t:.1%}")

    print("\n=== feature distributions (derived) ===")
    for name, key in [
        ("listen_ratio (time/audio)", "listen_ratio"),
        ("text density chars/audio-sec", "density"),
        ("density vs whisper density", "dens_ratio"),
        ("edit_ratio vs whisper", "edit_ratio"),
    ]:
        vals = [r[key] for r in rows if r.get(key) is not None]
        if vals:
            print(f"  {name:30s} p1={pct(vals,.01):8.2f} p50={pct(vals,.5):8.2f} "
                  f"p95={pct(vals,.95):8.2f} p99={pct(vals,.99):8.2f}")

    print("\n=== candidate task-level flags ===")
    print(f"{'flag':46s} {'flag%':>7s} {'precision':>10s} {'recall':>7s} {'f1':>6s}")
    candidates = {
        "listen_ratio < 1": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 1,
        "listen_ratio < 2": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 2,
        "listen_ratio < 0.5": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 0.5,
        "listen_ratio > 50 (idle)": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] > 50,
        "verbatim submit (is_edited=No)": lambda r: r["edited"] == "No",
        "'edited' but <2% words changed": lambda r: r["edit_ratio"] is not None and r["edit_ratio"] < 0.02,
        "verbatim OR fake-edit": lambda r: r["edited"] == "No" or (r["edit_ratio"] is not None and r["edit_ratio"] < 0.02),
        "density > 25 chars/audio-s": lambda r: r["density"] is not None and r["density"] > 25,
        "density > 40 chars/audio-s": lambda r: r["density"] is not None and r["density"] > 40,
        "density < 3 chars/audio-s": lambda r: r["density"] is not None and r["density"] < 3,
        "listen<2 AND verbatim": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 2 and r["edited"] == "No",
        "listen<2 AND fake-edit": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 2 and r["edit_ratio"] is not None and r["edit_ratio"] < 0.02,
        "listen<1 OR verbatim": lambda r: (r["listen_ratio"] is not None and r["listen_ratio"] < 1) or r["edited"] == "No",
        "listen<2 OR verbatim": lambda r: (r["listen_ratio"] is not None and r["listen_ratio"] < 2) or r["edited"] == "No",
        "(listen<2 OR verbatim) OR density>40": lambda r: (
            (r["listen_ratio"] is not None and r["listen_ratio"] < 2)
            or r["edited"] == "No"
            or (r["density"] is not None and r["density"] > 40)
        ),
    }
    results = {}
    for name, fn in candidates.items():
        fl = [r for r in scored if fn(r)]
        res = score_feature(fl, lowq, n)
        results[name] = res
        flag, prec, rec, f1 = res
        print(f"{name:46s} {flag:7.1%} {prec:10.1%} {rec:7.1%} {f1:6.2f}")

    # dose-response for density (independent behavioural axis)
    print("\n=== dose-response: agreement by text density (chars per audio second) ===")
    buckets = [(0, 2), (2, 5), (5, 10), (10, 15), (15, 25), (25, 40), (40, 10**9)]
    for lo, hi in buckets:
        grp = [r for r in scored if r["density"] is not None and lo <= r["density"] < hi]
        if len(grp) < 5:
            continue
        print(f"  density [{lo:>4},{hi:>4}) n={len(grp):5d} "
              f"med_agree={st.median([r['user_agree'] for r in grp]):.3f} "
              f"lowq={sum(1 for r in grp if id(r) in lowq)/len(grp):5.1%}")

    print("\n=== dose-response: agreement by listen_ratio ===")
    for lo, hi in [(0, .5), (.5, 1), (1, 2), (2, 5), (5, 15), (15, 50), (50, 1e9)]:
        grp = [r for r in scored if r["listen_ratio"] is not None and lo <= r["listen_ratio"] < hi]
        if len(grp) < 5:
            continue
        print(f"  listen [{lo:>5},{hi:>6}) n={len(grp):5d} "
              f"med_agree={st.median([r['user_agree'] for r in grp]):.3f} "
              f"lowq={sum(1 for r in grp if id(r) in lowq)/len(grp):5.1%}")

    # how often is whisper incomplete (the reason verbatim fails)?
    ext = sum(1 for r in scored if r["wt"] and len(r["ut"]) > len(r["wt"]) + 1)
    print(f"\nwhisper draft shorter than the crowd consensus: "
          f"{sum(1 for r in scored if len(r['wt']) < len(r['ref']) )/n:.1%} of tasks")
    print(f"user text longer than whisper draft: {ext/n:.1%}")
    print(f"median len whisper={st.median([len(r['wt']) for r in scored])} "
          f"user={st.median([len(r['ut']) for r in scored])} "
          f"consensus={st.median([len(r['ref']) for r in scored])}")

    # population-wide impact of the final flags
    print("\n=== population blast radius ===")
    pop = {
        "listen<1": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 1,
        "listen<2": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] < 2,
        "verbatim": lambda r: r["edited"] == "No",
        "fake-edit": lambda r: r["edit_ratio"] is not None and r["edit_ratio"] < 0.02,
        "density>40": lambda r: r["density"] is not None and r["density"] > 40,
        "listen>50 idle": lambda r: r["listen_ratio"] is not None and r["listen_ratio"] > 50,
    }
    for name, fn in pop.items():
        hit = sum(1 for r in rows if fn(r))
        print(f"  {name:16s} {hit:6d}/{len(rows)} = {hit/len(rows):6.1%}")

    # users with >=2 tasks: how many would a combined rule flag
    per_user = collections.Counter(r["user_id"] for r in rows)
    heavy = [u for u, c in per_user.items() if c >= 2]
    print("\n=== users with >=2 tasks: share of their tasks flagged ===")
    print(f"{'user_id':>10s} {'n':>5s} {'listen<2%':>10s} {'verbatim%':>10s} "
          f"{'fakeedit%':>10s} {'any%':>7s}")
    for u in sorted(heavy, key=lambda x: -per_user[x]):
        rs = [r for r in rows if r["user_id"] == u]
        def anyflag(x):
            return (
                (x["listen_ratio"] is not None and x["listen_ratio"] < 2)
                or x["edited"] == "No"
                or (x["edit_ratio"] is not None and x["edit_ratio"] < 0.02)
            )
        a = sum(1 for r in rs if r["listen_ratio"] is not None and r["listen_ratio"] < 2) / len(rs)
        b = sum(1 for r in rs if r["edited"] == "No") / len(rs)
        c = sum(1 for r in rs if r["edit_ratio"] is not None and r["edit_ratio"] < 0.02) / len(rs)
        d = sum(1 for r in rs if anyflag(r)) / len(rs)
        print(f"{u:>10s} {len(rs):5d} {a:10.1%} {b:10.1%} {c:10.1%} {d:7.1%}")


if __name__ == "__main__":
    main()

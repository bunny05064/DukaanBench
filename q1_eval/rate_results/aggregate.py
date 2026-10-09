"""Aggregates human rating exports from rating_ui into leaderboard.json + CSV.

Drop every rater's downloaded file (dukaanbench_ratings_<name>.json) into this
folder, then run:  python3 q1_eval/rate_results/aggregate.py

Outputs:
  q1_eval/rating_ui/leaderboard.json   <- loaded live by rating_ui/index.html
  q1_eval/rate_results/out/summary.csv <- model x criterion means
  q1_eval/rate_results/out/raters.csv  <- one row per rater (coverage + speed)
"""

import csv
import datetime as dt
import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "..", "rating_ui")
SPEC = os.path.join(HERE, "..", "prompts", "prompts.json")
OUT = os.path.join(HERE, "out")

CRIT = ["adherence", "fidelity", "text", "indiafit", "visual"]


def model_of(trial_id):
    """P1__google__gemini-3-1-flash-image-preview -> (google, gemini-3-1-flash-image-preview)"""
    parts = trial_id.split("__")
    return parts[1], parts[2] if len(parts) > 2 else "?"


def load_files():
    files = sorted(f for f in os.listdir(HERE) if f.endswith(".json"))
    runs = []
    for f in files:
        try:
            with open(os.path.join(HERE, f), encoding="utf-8") as fh:
                runs.append((f, json.load(fh)))
        except Exception as e:
            print(f"SKIP {f}: {e}")
    return runs


def main():
    runs = load_files()
    if not runs:
        print("No rating JSON files found in", HERE)
        return

    spec = json.load(open(SPEC, encoding="utf-8"))
    name_of = {}
    for m in spec["models"]:
        def slug(s):
            out = "".join(c.lower() if c.isalnum() else "-" for c in s)
            while "--" in out:
                out = out.replace("--", "-")
            return out.strip("-")
        name_of[slug(m["company"]) + "__" + slug(m["model"])] = (
            f"{m['company']} {m['model']}"
        )

    valid, rows_all, raters = [], [], []
    for fname, run in runs:
        if not run.get("ratings"):
            print(f"SKIP {fname}: no ratings")
            continue
        if not run.get("consent"):
            print(f"SKIP {fname}: no consent record attached")
            continue
        age = run["consent"].get("age")
        if not isinstance(age, int) or age < 18:
            print(f"SKIP {fname}: invalid/under-18 consent record")
            continue
        n = len(run["ratings"])
        complete = sum(1 for r in run["ratings"]
                       if r.get("usable") is not None
                       and all(r.get(c) for c in CRIT))
        raters.append({
            "rater": run["consent"].get("name", "?"),
            "file": fname,
            "ratings": n,
            "complete": complete,
            "median_seconds": int(st.median([r.get("seconds_on_trial") or 0
                                             for r in run["ratings"]])),
            "age": run["consent"].get("age", ""),
            "email": run["consent"].get("email", ""),
            "consent_at": run["consent"].get("at", ""),
            "consent_text_present": bool(run["consent"].get("consent_text")),
            "exported_at": run.get("exported_at", ""),
        })
        for r in run["ratings"]:
            if not all(r.get(c) for c in CRIT):
                continue
            rows_all.append(r)
        valid.append(run)

    if not rows_all:
        print("No complete ratings found.")
        return

    # per model x criterion means
    cells = {}
    for r in rows_all:
        comp, model = model_of(r["trial_id"])
        cells.setdefault(model, []).append(r)

    # rater consistency: pairwise Pearson over shared trials, mean across pairs
    def pearson(a, b):
        if len(a) < 3:
            return None
        ma, mb = st.mean(a), st.mean(b)
        da = [x - ma for x in a]
        db = [x - mb for x in b]
        num = sum(x * y for x, y in zip(da, db))
        den = (sum(x * x for x in da) * sum(y * y for y in db)) ** 0.5
        return num / den if den else None

    by_rater = []
    for run in valid:
        m = {}
        for r in run["ratings"]:
            if all(r.get(c) for c in CRIT):
                m[r["trial_id"]] = st.mean([float(r[c]) for c in CRIT])
        by_rater.append(m)

    cors = []
    for i in range(len(by_rater)):
        for j in range(i + 1, len(by_rater)):
            shared = sorted(set(by_rater[i]) & set(by_rater[j]))
            if len(shared) >= 6:
                c = pearson([by_rater[i][k] for k in shared],
                            [by_rater[j][k] for k in shared])
                if c is not None:
                    cors.append(c)
    consistency = st.mean(cors) if cors else None

    rows = []
    for model, rs in sorted(cells.items()):
        row = {"model": name_of.get(model, model), "model_id": model, "n": len(rs)}
        for c in CRIT:
            row[c] = st.mean([float(r[c]) for r in rs])
        row["overall"] = st.mean([st.mean([float(r[c]) for c in CRIT]) for r in rs])
        row["consistency"] = consistency
        rows.append(row)
    rows.sort(key=lambda r: -r["overall"])

    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "n_ratings"] + CRIT + ["overall", "rater_consistency"])
        for r in rows:
            w.writerow([r["model"], r["n"]] + [f"{r[c]:.3f}" for c in CRIT]
                       + [f"{r['overall']:.3f}",
                          f"{consistency:.3f}" if consistency is not None else ""])

    with open(os.path.join(OUT, "raters.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(raters[0].keys()))
        w.writeheader()
        for r in raters:
            w.writerow(r)

    # per prompt x model, so the writeup can name concrete winners/losers
    with open(os.path.join(OUT, "per_prompt.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["prompt_id", "model"] + CRIT + ["overall"])
        agg = {}
        for r in rows_all:
            comp, model = model_of(r["trial_id"])
            agg.setdefault((r["prompt_id"], model), []).append(r)
        for (pid, model), rs in sorted(agg.items()):
            w.writerow([pid, name_of.get(model, model)]
                       + [f"{st.mean([float(r[c]) for r in rs]):.2f}" for c in CRIT]
                       + [f"{st.mean([st.mean([float(r[c]) for c in CRIT]) for r in rs]):.2f}"])

    lb = {
        "rows": [{k: (round(v, 3) if isinstance(v, float) else v)
                  for k, v in r.items()} for r in rows],
        "n_raters": len(valid),
        "n_ratings": len(rows_all),
        "consistency": round(consistency, 3) if consistency is not None else None,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    with open(os.path.join(UI, "leaderboard.json"), "w", encoding="utf-8") as fh:
        json.dump(lb, fh, ensure_ascii=False, indent=2)

    print(f"raters={len(valid)} ratings={len(rows_all)} consistency={consistency}")
    for r in rows:
        print(f"  {r['model']:<38} overall={r['overall']:.3f}  " +
              " ".join(f"{c}={r[c]:.2f}" for c in CRIT))
    print("wrote", os.path.join(OUT, "summary.csv"), "and rating_ui/leaderboard.json")


if __name__ == "__main__":
    main()

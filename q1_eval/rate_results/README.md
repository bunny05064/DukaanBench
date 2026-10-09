# Rating exports

Drop each raters downloaded `dukaanbench_ratings_<name>.json` here, then run:

```
python3 q1_eval/rate_results/aggregate.py
```

Outputs: `rating_ui/leaderboard.json` (shown live in the rating sheet) and `out/` CSVs.

No rater data is committed to this repository.

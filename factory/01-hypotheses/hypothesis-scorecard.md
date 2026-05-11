# Hypothesis scorecard — weights and formula

Used by `scripts/score-hypotheses.ts`.

## Weights (positives)

| Field | Weight |
|---|---|
| speed | 25% |
| pain_strength | 20% |
| distribution_score | 15% |
| margin | 15% |
| cheapness | 10% |
| wow_factor | 10% |
| payment_simplicity | 5% |

Sum = 100%.

## Risk subtractions

Each risk field is `0–10` (higher = worse). Subtract a fraction of each from the positive composite.

| Field | Penalty multiplier |
|---|---|
| legal_risk | 0.05 |
| inference_cost_risk | 0.05 |
| platform_dependency_risk | 0.05 |

So a hypothesis with all three risks at 10 loses up to 1.5 points (out of 10).

## Formula

```
positive = 0.25*speed + 0.20*pain_strength + 0.15*distribution_score
         + 0.15*margin + 0.10*cheapness + 0.10*wow_factor
         + 0.05*payment_simplicity

penalty  = 0.05*legal_risk + 0.05*inference_cost_risk + 0.05*platform_dependency_risk

score    = positive - penalty
```

`score` is on a 0–10 scale (positive composite is 0–10; penalty caps at 1.5).

## Bands

| Score | Action |
|---|---|
| ≥ 7.0 | strong candidate; bring to Gate 1 |
| 5.0 – 6.9 | viable; consider only if no ≥ 7.0 exists |
| < 5.0 | kill or rework |

A hypothesis that fails the kill filter (`passed_kill_filter: false`) is excluded regardless of score.

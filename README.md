# A/B Test Design + Experiment Analysis Framework

An end-to-end experimentation framework for a real product decision:
**one-page vs. multi-step checkout.** Covers the full lifecycle a PM owns —
hypothesis, power/sample-size, minimum detectable effect, a pre-registered
decision rule, and a statistically correct readout (significance test,
confidence interval, guardrail check) ending in **ship / iterate / don't ship**.

**Stack:** Python (scipy, statsmodels) · Flask

---

## Why this project

Experimentation is core PM craft, and the thing that separates a PM who can run
experiments from one who eyeballs dashboards is doing the **statistics
correctly** — power analysis before the test, significance testing after, and a
decision rule set in advance so results aren't p-hacked. This framework does all
three.

## How to run

```bash
pip install pandas numpy scipy statsmodels flask

python src/power_analysis.py       # sample size + MDE  -> data/power_summary.json
python src/simulate_experiment.py  # generate arm data  -> data/experiment_data.csv
python src/analyze_experiment.py   # significance + decision -> output/experiment_result.json
python src/dashboard.py            # readout dashboard -> http://127.0.0.1:5000
```

## The experiment

- **Decision:** replace multi-step checkout with a one-page flow?
- **Primary metric:** checkout conversion (baseline ~62%).
- **Guardrail:** payment-error rate must not significantly worsen.
- **Design:** 50/50 session-level split, α=0.05, power=0.80.

## What's statistically load-bearing

- **Power analysis** — ~4,041 sessions/arm to detect a +3 pt lift; MDE tightens
  with runtime (2.09 pts at 1 week → 1.48 at 2 weeks). Cross-checked against the
  closed-form two-proportion sample-size formula.
- **Analysis** — two-proportion z-test, 95% CI on the absolute lift, and a
  one-sided guardrail test on error rate.
- **Pre-registered decision rule** — SHIP / ITERATE / DON'T SHIP decided before
  seeing results.

## Result (simulated run)

| | Control | Treatment |
|---|---|---|
| Conversion | 63.0% | 65.3% |
| Payment errors | 2.2% | 2.3% |

Lift **+2.3 pts** (95% CI [+0.2, +4.4]), **p = 0.015** → significant; guardrail
held → **SHIP**.

## Honest notes

- Data is simulated from a fixed true effect so the analysis pipeline can be
  validated; in a real run the effect is unknown and the same code produces the
  readout.
- The design doc lists real threats to validity (novelty effect, peeking,
  sample-ratio mismatch, segment heterogeneity) and how each is handled.

"""
analyze_experiment.py
---------------------
Proper analysis of the checkout experiment:
  - Two-proportion z-test on the PRIMARY metric (conversion)
  - 95% confidence interval on the absolute lift
  - Guardrail check on payment-error rate (must not significantly worsen)
  - A pre-registered DECISION RULE -> ship / iterate / don't ship

This is the piece that separates "the number moved" from a defensible
experiment readout.
"""
import os
import json
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA = 0.05


def two_prop(successes, nobs, alternative="two-sided"):
    stat, p = proportions_ztest(count=successes, nobs=nobs, alternative=alternative)
    return stat, p


def analyze():
    df = pd.read_csv(os.path.join(BASE, "data", "experiment_data.csv"))
    g = df.groupby("arm")

    c = df[df.arm == "control"]
    t = df[df.arm == "treatment"]

    c_conv, t_conv = c.converted.mean(), t.converted.mean()
    c_n, t_n = len(c), len(t)
    abs_lift = t_conv - c_conv
    rel_lift = abs_lift / c_conv

    # primary: two-proportion z-test (is treatment > control?)
    succ = np.array([t.converted.sum(), c.converted.sum()])
    nobs = np.array([t_n, c_n])
    z, p_primary = two_prop(succ, nobs, alternative="larger")  # one-sided: treatment better

    # 95% CI on the difference (treatment - control)
    ci_low, ci_high = confint_proportions_2indep(
        t.converted.sum(), t_n, c.converted.sum(), c_n, method="wald"
    )

    # guardrail: payment-error rate must NOT significantly increase
    c_err, t_err = c.payment_error.mean(), t.payment_error.mean()
    succ_e = np.array([t.payment_error.sum(), c.payment_error.sum()])
    nobs_e = np.array([t_n, c_n])
    z_e, p_guard = two_prop(succ_e, nobs_e, alternative="larger")  # is treatment error > control?
    guardrail_breached = p_guard < ALPHA  # error rate significantly HIGHER

    # decision rule
    significant = p_primary < ALPHA
    if significant and not guardrail_breached:
        decision = "SHIP"
        reason = "Conversion lift is statistically significant and the guardrail held."
    elif significant and guardrail_breached:
        decision = "ITERATE"
        reason = "Conversion improved, but payment errors rose significantly — fix the form before shipping."
    else:
        decision = "DON'T SHIP"
        reason = "No statistically significant conversion lift at alpha=0.05."

    result = {
        "primary_metric": "checkout conversion",
        "control_rate": round(c_conv, 4),
        "treatment_rate": round(t_conv, 4),
        "abs_lift_pts": round(abs_lift * 100, 2),
        "rel_lift_pct": round(rel_lift * 100, 2),
        "z_stat": round(float(z), 3),
        "p_value": round(float(p_primary), 5),
        "ci95_low_pts": round(ci_low * 100, 2),
        "ci95_high_pts": round(ci_high * 100, 2),
        "significant": bool(significant),
        "guardrail_metric": "payment-error rate",
        "control_error": round(c_err, 4),
        "treatment_error": round(t_err, 4),
        "guardrail_p": round(float(p_guard), 4),
        "guardrail_breached": bool(guardrail_breached),
        "decision": decision,
        "reason": reason,
        "control_n": c_n,
        "treatment_n": t_n,
    }

    with open(os.path.join(BASE, "output", "experiment_result.json"), "w") as f:
        json.dump(result, f, indent=2)

    # readout
    print("=== EXPERIMENT READOUT: one-page vs multi-step checkout ===\n")
    print(f"Primary metric: conversion")
    print(f"  Control:   {c_conv:.2%}  (n={c_n:,})")
    print(f"  Treatment: {t_conv:.2%}  (n={t_n:,})")
    print(f"  Absolute lift: {abs_lift*100:+.2f} pts   Relative: {rel_lift*100:+.2f}%")
    print(f"  95% CI on lift: [{ci_low*100:+.2f}, {ci_high*100:+.2f}] pts")
    print(f"  z = {z:.3f},  p = {p_primary:.5f}  -> {'SIGNIFICANT' if significant else 'not significant'}\n")
    print(f"Guardrail: payment-error rate")
    print(f"  Control {c_err:.2%} vs Treatment {t_err:.2%}  (p={p_guard:.4f}) "
          f"-> {'BREACHED' if guardrail_breached else 'held'}\n")
    print(f"DECISION: {decision}")
    print(f"  {reason}")
    print(f"\nSaved -> output/experiment_result.json")
    return result


if __name__ == "__main__":
    analyze()

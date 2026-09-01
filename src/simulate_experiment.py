"""
simulate_experiment.py
----------------------
Generates realistic experiment data for the checkout test.

Control  = current multi-step checkout (baseline conversion ~62%)
Treatment = one-page checkout (a modest true lift baked in, plus a guardrail
            metric so we can check the change doesn't hurt something else)

Guardrail: payment-error rate. A one-page flow could plausibly raise input
errors, so we track it and require it NOT to significantly worsen.

The TRUE effect is set here so the analysis can be checked; in a real test
it's unknown. We use the sample size from power_analysis so the sim mirrors
a properly-powered run.
"""
import os
import json
import numpy as np
import pandas as pd

SEED = 20
rng = np.random.default_rng(SEED)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TRUE parameters (unknown in reality; fixed here for a checkable sim)
CONTROL_CONV = 0.62
TRUE_LIFT = 0.028          # one-page adds +2.8 pts conversion (real but modest)
CONTROL_ERR = 0.021        # baseline payment-error rate
TREAT_ERR = 0.024          # slightly higher errors on one-page (guardrail watch)


def load_n():
    with open(os.path.join(BASE, "data", "power_summary.json")) as f:
        return json.load(f)["required_n_per_arm"]


def simulate():
    n = load_n()
    rows = []
    for arm, conv, err in [
        ("control", CONTROL_CONV, CONTROL_ERR),
        ("treatment", CONTROL_CONV + TRUE_LIFT, TREAT_ERR),
    ]:
        converted = rng.random(n) < conv
        had_error = rng.random(n) < err
        for i in range(n):
            rows.append({
                "user_id": f"{arm[:1]}{i:06d}",
                "arm": arm,
                "converted": int(converted[i]),
                "payment_error": int(had_error[i]),
            })
    df = pd.DataFrame(rows)
    out = os.path.join(BASE, "data", "experiment_data.csv")
    df.to_csv(out, index=False)
    print(f"Simulated {len(df):,} users ({n:,}/arm)")
    print(df.groupby("arm")[["converted", "payment_error"]].mean().round(4).to_string())
    print(f"Saved -> {out}")
    return df


if __name__ == "__main__":
    simulate()

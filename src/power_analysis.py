"""
power_analysis.py
-----------------
Sample-size and minimum-detectable-effect (MDE) calculation for the
one-page vs. multi-step checkout experiment.

Answers two questions BEFORE running the test:
  1. How many users per arm do we need to detect a given lift with adequate
     power?
  2. Given the traffic we actually have, what is the smallest lift we can
     reliably detect (MDE)?

Uses a two-proportion test with alpha=0.05 (two-sided) and power=0.80,
the standard defaults. This is what makes the experiment credible rather
than "we ran it until the number moved."
"""
import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ALPHA = 0.05
POWER = 0.80

# Baseline: current multi-step checkout converts at ~62% (browse->order)
BASELINE_RATE = 0.62
# We care about detecting a +3 percentage-point absolute lift or more
TARGET_ABS_LIFT = 0.03

# Traffic reality: ~ how many sessions/day hit checkout, per arm
DAILY_SESSIONS_PER_ARM = 1200


def sample_size_for_lift(p1, abs_lift, alpha=ALPHA, power=POWER):
    """Users per arm to detect p1 -> p1+abs_lift."""
    p2 = p1 + abs_lift
    effect = proportion_effectsize(p2, p1)  # Cohen's h
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=effect, alpha=alpha, power=power,
                             ratio=1.0, alternative="two-sided")
    return int(np.ceil(n))


def mde_for_sample(p1, n_per_arm, alpha=ALPHA, power=POWER):
    """Smallest absolute lift detectable with n_per_arm users per arm."""
    analysis = NormalIndPower()
    # find the effect size (Cohen's h) achievable at this n
    h = analysis.solve_power(effect_size=None, nobs1=n_per_arm, alpha=alpha,
                             power=power, ratio=1.0, alternative="two-sided")
    # invert Cohen's h back to an absolute lift around p1
    # h = 2*asin(sqrt(p2)) - 2*asin(sqrt(p1))  ->  solve for p2
    phi1 = 2 * np.arcsin(np.sqrt(p1))
    p2 = np.sin((h + phi1) / 2) ** 2
    return p2 - p1


def main():
    print("=== CHECKOUT EXPERIMENT — POWER ANALYSIS ===\n")
    print(f"Baseline conversion (multi-step): {BASELINE_RATE:.0%}")
    print(f"alpha = {ALPHA}, power = {POWER}, two-sided\n")

    n = sample_size_for_lift(BASELINE_RATE, TARGET_ABS_LIFT)
    days = np.ceil(n / DAILY_SESSIONS_PER_ARM)
    print(f"To detect a +{TARGET_ABS_LIFT:.0%} absolute lift "
          f"({BASELINE_RATE:.0%} -> {BASELINE_RATE+TARGET_ABS_LIFT:.0%}):")
    print(f"  Required sample: {n:,} per arm ({2*n:,} total)")
    print(f"  At {DAILY_SESSIONS_PER_ARM:,} sessions/arm/day -> ~{int(days)} days of runtime\n")

    print("MDE at various weekly traffic levels (per arm):")
    for wk in [1, 2, 3]:
        n_avail = DAILY_SESSIONS_PER_ARM * 7 * wk
        mde = mde_for_sample(BASELINE_RATE, n_avail)
        print(f"  {wk} week(s) = {n_avail:,}/arm -> can detect >= {mde*100:.2f} pts lift")

    # persist a small summary for the design doc / dashboard
    import json, os
    out = {
        "baseline_rate": BASELINE_RATE,
        "target_abs_lift": TARGET_ABS_LIFT,
        "required_n_per_arm": n,
        "runtime_days": int(days),
        "alpha": ALPHA,
        "power": POWER,
        "mde_by_week": {
            str(wk): round(mde_for_sample(BASELINE_RATE, DAILY_SESSIONS_PER_ARM*7*wk)*100, 2)
            for wk in [1, 2, 3]
        },
    }
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(base, "data"), exist_ok=True)
    with open(os.path.join(base, "data", "power_summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved -> data/power_summary.json")


if __name__ == "__main__":
    main()

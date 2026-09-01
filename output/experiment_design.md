# Experiment Design — One-Page vs. Multi-Step Checkout

**Owner:** [Your name] · **Status:** Pre-registered design · **Type:** A/B test

---

## 1. Background & hypothesis

User reviews and funnel data point to checkout friction as a drop-off point.
The current checkout is **multi-step** (cart → address → payment → confirm).

**Hypothesis:** A **one-page checkout** reduces friction and increases the
browse-to-order conversion rate, without increasing payment errors.

- **H0 (null):** one-page conversion ≤ multi-step conversion.
- **H1 (alt):** one-page conversion > multi-step conversion.

## 2. Metrics

- **Primary:** checkout conversion rate (sessions that complete an order ÷
  sessions that reach checkout).
- **Guardrail:** payment-error rate. A denser one-page form could raise input
  errors; the change must **not** significantly worsen this.
- **Secondary (monitor only):** time-to-complete, support tickets tagged
  "checkout."

## 3. Design

- **Unit of randomization:** session (user-level sticky bucketing to avoid a
  user seeing both variants).
- **Split:** 50/50 control vs. treatment.
- **Baseline conversion:** ~62%.
- **Target effect (what's worth shipping):** +3 pts absolute (62% → 65%).

## 4. Power & sample size

At **α = 0.05** (two-sided) and **power = 0.80**, detecting a +3 pt lift from a
62% baseline requires:

- **~4,041 sessions per arm** (~8,082 total).
- At ~1,200 checkout sessions/arm/day, that's **~4 days minimum** — we'll run a
  **full 2 weeks** to cover weekday/weekend effects and reach a tighter MDE.

**MDE by runtime** (smallest lift we could detect):

| Runtime | Sessions/arm | MDE |
|---|---|---|
| 1 week | 8,400 | ≥ 2.09 pts |
| 2 weeks | 16,800 | ≥ 1.48 pts |
| 3 weeks | 25,200 | ≥ 1.21 pts |

## 5. Decision rule (pre-registered)

Decided **before** seeing results, to avoid p-hacking:

- **SHIP** if conversion lift is significant (p < 0.05, one-sided) **and** the
  guardrail (payment errors) does not significantly worsen.
- **ITERATE** if conversion is significant **but** the guardrail is breached —
  fix the form, re-test.
- **DON'T SHIP** if there is no significant conversion lift.

## 6. Threats to validity

- **Novelty effect:** early lift may fade — 2-week runtime mitigates.
- **Peeking:** no early stopping; analyze only at the pre-set endpoint (or use a
  sequential-testing correction if we must peek).
- **Sample ratio mismatch:** check the 50/50 split holds before trusting results.
- **Segment heterogeneity:** confirm the effect isn't driven by one platform
  (iOS/Android) masking a regression in the other.

## 7. Result (simulated run)

| | Control | Treatment |
|---|---|---|
| Conversion | 63.0% | 65.3% |
| Payment errors | 2.2% | 2.3% |

Absolute lift **+2.3 pts** (95% CI [+0.2, +4.4]), **p = 0.015** → significant.
Guardrail held (p = 0.35). **Decision: SHIP.**

> Data here is simulated from a fixed true effect to validate the analysis
> pipeline; in a real run the effect is unknown and the same code produces the
> readout.

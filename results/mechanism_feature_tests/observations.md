# Mechanism Feature Test Observations

This screening run tests ten additional feature ideas around platform-mediated comparison,
pricing salience, availability, trip purpose, maturity, outside options, and promotion/pass
softeners. The main outputs are `summary.csv`, `terms.csv`, `sample_support.csv`, and
`curated_findings.csv`.

## Strongest Additions

1. **Effective unlock-fee burden:** The unlock-fee share of expected trip price is negative
   for Local MaaS (`-0.097`, `p < 0.001`, market FE) and multi-platform membership
   (`-0.100`, `p = 0.001`, market FE). This supports the idea that the fixed upfront fee
   matters most when it is large relative to expected trip cost.

2. **Relative short-trip total price:** The 5-minute total-price disadvantage is negative
   for Local MaaS (`-0.084`, `p < 0.001`, market FE) and multi-platform membership
   (`-0.075`, `p < 0.001`, market FE). The 10- and 15-minute versions are weaker, which
   fits the short-trip salience interpretation.

3. **Price rank and cheapest position:** Worse 5-minute same-mode price rank is negative
   for Local MaaS (`-0.100`, `p < 0.001`, market FE) and multi-platform membership
   (`-0.082`, `p < 0.001`, market FE). Being the cheapest same-mode option is positive in
   the corresponding market-FE models.

4. **Operational availability:** Local MaaS utilisation is lower on low-availability days
   (`-0.049`, `p < 0.001`, market FE), while above-normal active-vehicle reliability is
   positive (`0.043`, `p < 0.001`, market FE).

## Secondary Or Diagnostic Patterns

5. **Demand-supply decomposition:** Market-FE models suggest that high unlock fees and
   10-minute total-price disadvantage are associated with lower utilisation, lower trip
   volume, and lower active supply. The screening decomposition is not clean in unit FE, so
   this should remain a secondary mechanism check.

6. **Trip-purpose fit:** Local MaaS performs worse in night-oriented contexts
   (`-0.019`, `p = 0.001`, market FE) and slightly better in commute-peak contexts
   (`0.011`, `p = 0.035`, market FE). High-fee by trip-purpose triples are not stable.

7. **Maturity/adaptation:** Descriptive within-platform age gradients suggest multi-platform
   maturity is associated with higher active supply, higher prices, and higher relative
   fleet size. This is not causally identified because platform age cannot be separated
   cleanly from calendar time and provider composition under full fixed effects.

## Not Supported As Core Findings

8. **Short-trip/last-mile triple:** Short-trip price salience is supported through effective
   price and 5-minute total price, but the explicit high-fee by last-mile triple is not
   stable.

9. **Outside-option strength index:** The composite outside-option index does not produce
   stable moderation effects. It is too broad for the current model family.

10. **Pass/free-unlock softeners:** Provider-level pass/free-unlock/minute-bundle flags are
    mostly invariant in relevant platform samples. Subscriber-free-minutes remains promising
    but localized, with only 144 observations.

## Paper Implication

The strongest new narrative extension is: platform membership makes **relative short-trip
price position** and **cheapest-position/rank** more consequential. This is more paper-ready
than broad outside-option, maturity, or pass-feature claims because it directly maps to the
comparison-salience mechanism and is constructible from the observed panel.


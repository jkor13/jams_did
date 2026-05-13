# Isolated Competition Pricing Mechanism

This folder isolates the competition mechanism around one focal term:

`unlock_fee x platform_any x competition`

Competition is tested with five separate measures:

- `city_competition_z`: standardized `no_shared_provider_total`.
- `active_city_operators_z`: active city-operator count per city-day.
- `active_operators_z`: active operator count per city-day.
- `market_fragmentation_z`: `1 - trip_hhi` based on city-day trip shares.
- `leave_one_out_competitor_trips_z`: city-day trips by all other providers.

Outputs:

- `terms.csv`: all focal coefficients.

The OLS tests use market-FE and unit-FE specifications. A fully saturated city-date FE dummy model is intentionally omitted here because it is computationally unstable for this exploratory mechanism scan; DML residualization provides the nonlinear robustness check.
- `triple_interaction_stability.csv`: stability summary by competition measure and estimator.
- `sample_summary.csv`: sample diagnostics.

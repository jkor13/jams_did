# Data

This folder contains the clean platform-membership data used by the analysis.

## Files

- `JAMS_df_platform_clean_typed.csv`: full city-operator-day panel with platform flags, marketing variables, controls, and outcomes.
- `JAMS_df_platform_extended_features.csv`: full panel plus extended competition and marketing-mix features.
- `extended_competition_marketing_features.csv`: compact city-operator-day feature table for merging into analyses.
- `marketing_mix_external_feature_coding.csv`: provider-level external product/process/pass feature coding with source IDs.
- `jams_platform_type_features.csv`: platform-type feature subset keyed at the city-operator-day level.
- `platform_event_typology.csv`: event-level platform coding used to construct the daily flags.

## Platform membership coding

A city-operator-day is coded as clean platform membership (`platform_membership_clean = 1`) when a platform event is active for that city-operator-date and the integration is substantive: the provider is bookable/payable through the platform, with sufficient source confidence. Pure visibility, routing information, or deeplink-only cases are not treated as full membership.

Weak exposure (`weak_platform_exposure_clean = 1`) captures platform visibility without full bookable/payable integration. Promotions are coded separately as `promo_active_clean` and are not counted as membership.

Platform-type variables split clean membership into:

- `platform_large_aggregator_clean`: large aggregator membership, empirically FreeNow in this dataset.
- `platform_local_maas_clean`: local MaaS/transit-app integration.
- `platform_both_large_and_local_clean`: simultaneous large aggregator and local MaaS membership.
- `platform_large_only_clean`: large aggregator only.
- `platform_local_only_clean`: local MaaS only.
- `platform_weak_exposure_type_clean`: weak exposure only.
- `platform_membership_type_clean`: mutually exclusive category used for interpretation.

## Extended features

The extended feature table adds:

- same-city and same-mode competitor counts,
- trip-share and active-vehicle-share concentration measures, including HHI,
- relative price position and cheapest-provider indicators,
- same-platform competitor counts,
- commute-peak and night-trip shares from the raw trip panel on `bigbo`,
- provider-level external marketing-mix affordances such as reservation, pass/free-unlock/minute-bundle, and parking/geofence rules.

External provider-level features are broad product/process coding and should not be interpreted as city-specific 2024 campaign timing unless the source is event-specific. Source details are recorded in `results/feature_engineering/external_sources.md`.

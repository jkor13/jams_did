# Data

This folder contains the clean platform-membership data used by the analysis.

## Files

- `JAMS_df_platform_clean_typed.csv`: full city-operator-day panel with platform flags, marketing variables, controls, and outcomes.
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

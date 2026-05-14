# Extended Feature Inventory

Generated files:

- `data/extended_competition_marketing_features.csv`
- `data/JAMS_df_platform_extended_features.csv`
- `data/marketing_mix_external_feature_coding.csv`
- `results/feature_engineering/external_sources.md`
- `results/feature_engineering/feature_summary.csv`

Input paths:

- Panel: `/home/julianteusch/dev/ewgt_multilevel_model/platform_membership_moderation/data/JAMS_df_platform_clean_typed.csv`
- Trips: `/home/julianteusch/dev/ewgt_multilevel_model/data/input/raw/jams_roh_data/analyse_df.csv`
- Active vehicles: `/home/julianteusch/dev/ewgt_multilevel_model/cache/jams_active_vehicle_daily_counts.csv`

Feature families:

- Same-city and same-mode operator competition counts.
- Trip-share and active-vehicle-share concentration, including HHI.
- Relative price position and cheapest-provider indicators.
- Same-platform competitor counts and platform-type operator counts.
- Trip-behavior process features: commute-peak share, night-trip share, observed vehicle-type count.
- Provider-level external product/process/pass coding with source IDs.
- Source audit trail for external coding.

Identification note:

Competition and price-position features are city-operator-day measures. Provider-level external
features are broad product/process affordances and should be treated as moderators or controls,
not as city-specific 2024 campaign timing unless supported by additional local sources.

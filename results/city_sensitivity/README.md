# City Sensitivity

Leave-one-platform-city sensitivity checks for high unlock-fee platform-type effects.

The test drops each city with at least 100 local MaaS or multi-platform rows and re-estimates:

`ur_boxcox ~ unlock_fee_threshold * (local_maas_only + multi_platform) + controls + FE`

Thresholds:
- `unlock_fee_ge_0_99`
- `unlock_fee_ge_1_00`
- `unlock_fee_ge_1_20`

Outputs:
- `terms.csv`: all focal coefficients.
- `leave_one_city_stability.csv`: term-level stability across city drops.
- `significant_terms.csv`: significant focal coefficients.
- `sample_summary.csv`: sample diagnostics.
- `platform_cities.csv`: cities used for leave-one-city checks.

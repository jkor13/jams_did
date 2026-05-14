# Extended Feature Effects

Tests whether platform membership effects on capacity utilisation depend on the new competition,
relative-price, product/process, and pass/friction features.

Main models:

- `ur_boxcox ~ extended_feature * platform_any + controls + FE`
- `ur_boxcox ~ extended_feature * platform_type + controls + FE`
- `ur_boxcox ~ high_unlock_fee * platform_type * selected_extended_feature + controls + FE`

Use `curated_findings.csv` as a screening summary and `summary.csv` for model-level stability.

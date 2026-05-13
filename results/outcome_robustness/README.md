# Outcome Robustness

Tests whether high-unlock-fee platform-type effects appear for both capacity utilisation (`ur_boxcox`) and demand volume (`log_trip_count_day`).

Model:

`outcome ~ unlock_fee_threshold * (local_maas_only + multi_platform) + controls + FE`

Thresholds:
- `unlock_fee_ge_1_00`
- `unlock_fee_ge_1_20`

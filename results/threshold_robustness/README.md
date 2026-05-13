# Threshold Robustness

Robustness checks for the high-unlock-fee finding.

Thresholds:
- `unlock_fee_positive`: any positive unlock fee.
- `unlock_fee_ge_0_49`: unlock fee >= EUR 0.49.
- `unlock_fee_ge_0_75`: unlock fee >= EUR 0.75.
- `unlock_fee_ge_0_99`: unlock fee >= EUR 0.99.
- `unlock_fee_ge_1_00`: unlock fee >= EUR 1.00.
- `unlock_fee_ge_1_20`: unlock fee >= EUR 1.20.

Families:
- `threshold_any`: threshold x any platform membership.
- `threshold_type`: threshold x platform membership type.
- `leave_one_operator`: threshold x platform membership after dropping one major operator.

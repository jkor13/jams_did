# Feature-Fee Moderation

Tests whether underused product/service features moderate the high-unlock-fee platform penalty.

Model:

`ur_boxcox ~ unlock_fee_threshold * (local_maas_only + multi_platform) * feature + controls + FE`

Features:
- `group_ride`
- `no_of_vehicle_types_z`
- `complementary_services`

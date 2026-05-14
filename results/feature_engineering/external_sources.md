# External Sources For Extended Marketing-Mix Coding

This file records the sources used to create provider-level external product/process/pass
features in `data/marketing_mix_external_feature_coding.csv`. These are current/provider-level
sources unless a date-specific city event is explicitly noted.

## Lime

- Group Ride and parking guidance: https://help.li.me/hc/en-us/articles/360035073193-Starting-a-Group-Ride
- Reservation: https://help.li.me/hc/en-gb/articles/360022886073-Reserving-a-Lime-vehicle
- LimePass help entry: https://help.li.me/hc/en-us

Coding supported:

- `group_ride_external = 1`
- `reservation_available_external = 1`
- `reservation_minutes_external = 10`
- `pass_available_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

## Bolt

- Scooter product/pricing/reservation page: https://bolt.eu/en/scooters/

Coding supported:

- `group_ride_external = 1` from existing panel coding; official Bolt page used for the other product/process fields below.
- `reservation_available_external = 1`
- `reservation_minutes_external = 30`
- `pass_available_external = 1`
- `free_unlock_pass_external = 1`
- `minute_bundle_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

Note: Current page documents reserve up to 30 minutes, unlimited unlocks, and passes. Group-ride
availability is retained from the existing panel-level provider coding rather than newly inferred
from this page. Use as current product/process coding rather than precise 2024 city-level timing.

## TIER / Dott

- TIER Germany general terms: https://www.tier.app/germany-tcs-german
- TIER subscription help: https://intercom-help.eu/tier-mobility/en/articles/25607-i-have-a-subscription-but-i-was-still-charged-for-my-rides
- Dott support entry point: https://support.ridedott.com/

Coding supported:

- `group_ride_external = 1` from existing panel coding.
- `pass_available_external = 1`
- `free_unlock_pass_external = 1`
- `minute_bundle_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

Note: Existing panel coding marks TIER group-ride availability. Exact TIER-to-Dott market timing
should remain separate from these provider-level affordance flags.

## Voi / NürnbergMOBIL

- VAG press release on NürnbergMOBIL Voi integration and 15 Voi free minutes: https://www.vag.de/presse/aktuelle/umfangreiche-weiterentwicklung-der-app-nuernbergmobil-mehr-mobilitaet-durch-integration-von-voi-e-scooter-15-freiminuten-pro-monat-fuer-abonenntinnen
- VAG_Rad free-minutes page: https://www.vagrad.de/de/freiminuten/
- NürnbergMOBIL app page: https://www.nuernbergmobil.de/?lang=en

Coding supported:

- `pass_available_external = 1`
- `free_unlock_pass_external = 1`
- `minute_bundle_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

Note: The clean panel already includes the city-specific Nürnberg Voi event as
`subscriber_free_minutes_15_per_month`; the external provider-level flag is broader and should
not replace event-specific campaign coding.

## nextbike

- General nextbike tariff page: https://www.nextbike.de/de/
- nextbike tariff FAQ: https://nextbikesupport.zendesk.com/hc/de/articles/4411537443217-Wie-viel-kostet-nextbike-und-welche-Tarife-gibt-es
- VAG_Rad/nextbike station and flex-zone page: https://www.vagrad.de/en/nextbike/

Coding supported:

- `reservation_available_external = 1`
- `pass_available_external = 1`
- `minute_bundle_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

## EDDY

- Provider website: https://www.eddy-sharing.de/

Coding supported:

- `reservation_available_external = 1`
- `mandatory_parking_or_geofence_rules_external = 1`

Note: EDDY has limited support in the JAMS panel and should not drive central claims.

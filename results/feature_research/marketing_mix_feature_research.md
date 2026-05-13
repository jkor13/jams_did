# Marketing-Mix Feature Research

This note lists additional marketing-mix features that are relevant for the platform membership moderation story and assesses whether they can be used with the current panel.

## Skills And Search

- Used the local `research` skill workflow as the framing guide.
- Checked the `academic-research-hub` skill. It is geared toward formal paper retrieval through OpenClaw/Semantic Scholar/arXiv; for this pass, direct web and provider documentation were sufficient.
- Used online search across academic/shared-mobility sources and provider/help pages.

## Current Data Coverage

Already used heavily:

- Price: `unlock_fee`, `price_per_minute`.
- Promotion: `promo_active_clean`, `promo_types_clean`.
- Place/availability: `relative_fleet_size`, `Coverage`, `Exclusive_Coverage`.
- Platform architecture: large aggregator, local MaaS, multi-platform, weak exposure.
- Context controls: weather, public transport, city demographics, parking costs.

Underused but already present:

- `group_ride`: good support; 8,413 of 14,514 rows.
- `subscription_options`: weak standalone variation; 13,749 of 14,514 rows are `1`.
- `complementary_services`: sparse but meaningful; 1,224 rows.
- `no_of_vehicle_types`: usable assortment proxy; values 1, 2, 3.
- Parking fee/context variables: usable as place-friction or outside-option moderators.

## Highest-Priority Feature Ideas

1. **Pass/free-unlock/minute-bundle intensity**

   Best theoretical fit. It directly speaks to the high-unlock-fee mechanism because passes can remove or soften unlock fees. Current `subscription_options` is too broad, so the better variable would be provider-city-date coding of pass type: free unlocks, prepaid minutes, daily/monthly pass, or subscriber free minutes.

2. **Group ride availability**

   Immediately testable from `group_ride`. This is a product/social-use feature. Lime’s help page describes group rides as unlocking multiple vehicles from one account, making it a real service affordance rather than just metadata.

3. **Reservation availability**

   External coding needed. Reservation reduces search/place friction. Lime documentation states that users can reserve a vehicle, and pass/prime users can receive longer reservation windows in some cases.

4. **Parking-return friction**

   Partly testable through coverage/exclusive coverage and city parking variables, but richer external coding would help: mandatory station return, flex-zone return, designated parking areas, out-of-zone fees. This is a “place” friction and should moderate utilisation after platform discovery.

5. **Vehicle-type breadth**

   Immediately testable from `no_of_vehicle_types`. This is product assortment. It may matter especially in platform contexts where users compare modes and providers.

6. **Complementary services / multimodal bundling**

   Immediately testable but sparse. It can proxy whether the provider’s offering includes broader service integration beyond the core ride.

7. **App-service quality**

   External coding needed. App rating/review volume or app-update shocks could matter because platform membership is mediated through digital comparison and booking.

8. **Referral/new-user credits**

   External coding needed. Current promo data are too localized for causal event-window interpretation; broader campaign coding could rescue promotion as a stronger mechanism.

## Recommended Next Tests With Existing Data

Run a small underused-feature test family:

- `group_ride × platform_any/type`.
- `subscription_options × platform_any/type`, interpreted cautiously because of low variation.
- `complementary_services × platform_any/type`.
- `no_of_vehicle_types_z × platform_any/type`.
- Optional: interactions with `unlock_fee_ge_1_00` to see whether product/service affordances soften or amplify high-fee penalties.

## Recommended External Coding

Create a provider-city-date feature table with:

- `pass_free_unlock_available`
- `pass_minutes_bundle_available`
- `monthly_subscription_available`
- `reservation_available`
- `reservation_minutes`
- `mandatory_parking_or_station_return`
- `out_of_zone_fee_or_penalty`
- `new_user_credit_campaign`
- `referral_credit_campaign`
- `app_rating_monthly`
- `app_review_count_monthly`

## Sources

- Lime group ride documentation: https://help.li.me/hc/en-us/articles/360035073193-Starting-a-Group-Ride
- LimePass documentation: https://help.li.me/hc/en-us/articles/21280766615963-What-is-LimePass
- Lime reservation documentation: https://help.li.me/hc/en-gb/articles/360022886073-Reserving-a-Lime-vehicle
- KVV nextbike prices and station/flex-zone information: https://www.kvv-nextbike.de/en/prices/
- Southampton/Voi public information on Voi Pass, free unlocks, minutes, no-ride and slow-speed zones: https://www.southampton.gov.uk/travel-transport/getting-around-southampton/getting-around/bike-share-southampton/
- Voi app listing as app-service-quality data source: https://apps.apple.com/gb/app/voi-scooter-get-magic-wheels/id1395921017
- Shared e-scooter demand determinants review/context: https://www.tandfonline.com/doi/abs/10.1080/01441647.2023.2171500
- Shared-bike demand factors review/context: https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2022.848169/full
- Built environment/shared mobility demand context: https://www.sciencedirect.com/science/article/pii/S2210670719312387


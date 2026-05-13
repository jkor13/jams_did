# Findings Log

This file tracks the current empirical findings for the platform membership moderation paper. Status labels are intentionally conservative:

- **Robust**: recurring across the main model family and at least one robustness/deep-dive family.
- **Moderate**: substantively meaningful and recurring in several specifications, but limited by sample size, fixed-effect sensitivity, or overlap with city/platform structure.
- **Exploratory**: useful for theory-building or follow-up tests, but not yet suitable as a central claim.
- **Not supported**: tested and currently not stable enough to claim.

## Core Finding

### F1. Platform membership does not create a uniform utilisation lift; it changes marketing effectiveness.

**Status:** Robust.

**Evidence:** In the outcome comparison test, `platform_any` is positive in market FE for capacity utilisation (`0.061`, `p = 0.008`) and log trips (`0.285`, `p = 0.003`), but the effect is not stable in unit FE. The more stable empirical pattern is in interactions rather than a main platform effect.

**Interpretation:** The platform membership story should be framed as a moderation story: platforms reshape how pricing, promotion, and supply-side instruments translate into capacity utilisation rather than simply raising utilisation mechanically.

**Reference:** `results/idea_tests/05_outcome_comparison/summary.csv`; `results/concept_aligned_moderation/moderation_synthesis.csv`.

## Pricing Friction Findings

### F2. Unlock fees become more detrimental in platform contexts.

**Status:** Robust.

**Evidence:** In the concept-aligned model family, `unlock_fee_z:platform_any` is negative in 9 significant models, with `market FE all = -0.0715` (`p < 0.001`) and median coefficient `-0.0751`. In the separate pricing architecture test, `unlock_fee_z:platform_any` is negative in 3/6 models, with `market FE all = -0.0650` (`p < 0.001`).

**Interpretation:** Platform membership appears to make salient access charges more punitive for capacity utilisation, consistent with a platform-mediated comparison mechanism in which users can more easily compare alternatives before starting a trip.

**Reference:** `results/concept_aligned_moderation/moderation_synthesis.csv`; `results/idea_tests/01_pricing_architecture/summary.csv`.

### F3. The unlock-fee penalty is strongest when the unlock fee crosses a salient high-fee threshold.

**Status:** Robust candidate.

**Evidence:** In the deep-dive threshold test, `high_unlock_fee:platform_any` is negative in 6/6 models; `all market FE = -0.104` (`p = 0.0009`) and `all unit FE = -0.040` (`p = 0.0003`). Additional threshold-robustness tests confirm that the result is not tied to one median split. For any platform membership, EUR 0.99, EUR 1.00, and EUR 1.20 thresholds are all negative in market FE (`-0.160`, `-0.158`, and `-0.155`, all `p < 0.001`). The effect is strongest for `local_maas_only`, where all tested cutoffs are negative in 5/6 models, and `multi_platform`, where EUR 1.00 and EUR 1.20 cutoffs are negative in 6/6 models.

**Interpretation:** The pricing-friction result looks less like a smooth marginal price effect and more like a salience/threshold effect: once the upfront access fee becomes high, platform membership is associated with lower capacity utilisation.

**Caveat:** The any-platform threshold result is strongest in market FE; the platform-type results for local MaaS and multi-platform are more stable across both market FE and unit FE.

**Reference:** `results/deep_dive_effects/curated_findings.csv`; `results/deep_dive_effects/summary.csv`; `results/threshold_robustness/curated_findings.csv`; `results/threshold_robustness/summary.csv`.

### F3a. The high-unlock-fee platform-type result is not driven by a single platform city.

**Status:** Robust.

**Evidence:** Leave-one-platform-city tests drop each of 13 relevant platform cities one at a time. For Local MaaS, EUR 0.99, EUR 1.00, and EUR 1.20 thresholds remain negative and significant in 13/13 city-drop models under both market FE and unit FE. Median market-FE coefficients are `-0.199`, `-0.209`, and `-0.218`; median unit-FE coefficients are `-0.044`, `-0.035`, and `-0.038`. For multi-platform membership, EUR 1.00 and EUR 1.20 thresholds are negative and significant in 13/13 city-drop models under both market FE and unit FE.

**Interpretation:** The strongest threshold result is not explained by one specific platform city such as Berlin, Hamburg, Düsseldorf, Karlsruhe, or Leipzig. This materially strengthens the claim that Local MaaS and multi-platform contexts amplify salient unlock-fee penalties.

**Caveat:** The EUR 0.99 multi-platform threshold is directionally stable but weaker in market FE: all 13 city-drop coefficients remain negative, but only 9/13 are significant.

**Reference:** `results/city_sensitivity/curated_findings.csv`; `results/city_sensitivity/leave_one_city_stability.csv`.

### F3b. Local MaaS high-fee penalties generalize from utilisation to trip volume; multi-platform is cleaner for utilisation than demand.

**Status:** Robust for Local MaaS; moderate for multi-platform.

**Evidence:** Outcome-robustness tests estimate the same EUR 1.00 and EUR 1.20 high-unlock-fee platform-type interactions for both `ur_boxcox` and `log_trip_count_day`. For `ur_boxcox`, Local MaaS and multi-platform interactions are negative in 6/6 models at both thresholds. For `log_trip_count_day`, Local MaaS is also negative in 6/6 models; full-sample estimates are `-1.014` in market FE (`p < 0.001`) and `-0.130` in unit FE (`p < 0.001`) at EUR 1.00, and `-1.054` in market FE (`p < 0.001`) and `-0.126` in unit FE (`p < 0.001`) at EUR 1.20. Multi-platform log-trip effects are negative in 4/6 models and strongly negative in market FE, but not significant in full-sample unit FE.

**Interpretation:** The Local MaaS pricing-friction result is not only a capacity-ratio artifact; it also appears as lower trip volume. Multi-platform evidence is strongest for capacity utilisation and should be framed more cautiously for demand volume.

**Reference:** `results/outcome_robustness/curated_findings.csv`; `results/outcome_robustness/summary.csv`.

### F4. Local MaaS membership is a stronger unlock-fee boundary condition than Free Now alone.

**Status:** Robust.

**Evidence:** In platform-type boundary tests, `unlock_fee_z:local_maas_only` is negative in 2/4 models and strongly negative in market FE (`-0.071`, `p = 0.001`). In concept-aligned models, `unlock_fee_z:local_maas_only` has median coefficient `-0.237` and `market FE all = -0.107` (`p < 0.001`). Threshold robustness and leave-one-city tests strengthen this finding: Local MaaS high-unlock-fee interactions remain negative and significant across all tested city drops for EUR 0.99, EUR 1.00, and EUR 1.20 thresholds.

**Interpretation:** The strongest version of the platform membership mechanism is not “large aggregator membership” in general; it appears more pronounced in local MaaS and integrated platform contexts where the service is embedded in a broader urban mobility interface.

**Reference:** `results/concept_aligned_moderation/moderation_synthesis.csv`; `results/idea_tests/03_platform_type_boundary/summary.csv`; `results/threshold_robustness/curated_findings.csv`; `results/city_sensitivity/curated_findings.csv`.

### F4a. Free Now-only does not show a stable high-unlock-fee threshold penalty.

**Status:** Negative evidence.

**Evidence:** In the threshold-robustness tests, large-aggregator-only interactions are not significant for any tested unlock-fee threshold. For example, `unlock_fee_ge_1_00:large_aggregator_only` has `market FE all = -0.045` (`p = 0.066`) and `unit FE all = -0.016` (`p = 0.325`), while local MaaS and multi-platform interactions at the same threshold are strongly negative.

**Interpretation:** The core pricing-friction result is not a Free Now-only large-aggregator result. This supports a more nuanced platform-architecture story: local MaaS and multi-platform comparison environments appear to amplify access-fee salience more than broad aggregator membership alone.

**Reference:** `results/threshold_robustness/curated_findings.csv`; `results/threshold_robustness/summary.csv`.

## Promotion Findings

### F5. Generic platform-promotion interaction is positive mainly within-unit, but not strong enough as a broad claim.

**Status:** Moderate.

**Evidence:** In the outcome comparison test, `promo_active:platform_any` is positive in unit FE for capacity utilisation (`0.0097`, `p < 0.001`) and log trips (`0.555`, `p < 0.001`), but not significant in market FE. In the promotion channel fit test, `promo_active:platform_any` is positive in 2/4 models with `unit FE all = 0.0115` (`p < 0.001`).

**Interpretation:** Promotions can improve utilisation in platform contexts, but the broad promotion indicator is too coarse for a central claim.

**Reference:** `results/idea_tests/05_outcome_comparison/summary.csv`; `results/idea_tests/06_promotion_channel_fit/summary.csv`.

### F6. Subscriber-free-minutes promotions fit multi-platform exposure especially well.

**Status:** Exploratory mechanism candidate.

**Evidence:** In the deep-dive promotion-type test, `promo_subscriber_minutes:platform_any` is positive in 4/4 models (`market FE = 0.051`, `p < 0.001`; `unit FE = 0.026`, `p < 0.001`). `promo_subscriber_minutes:multi_platform` is also positive in 4/4 models (`market FE = 0.122`, `p < 0.001`; `unit FE = 0.043`, `p < 0.001`). The same promotion type is negative for `local_maas_only` (`market FE = -0.081`, `p = 0.0035`; `unit FE = -0.011`, `p = 0.049`).

**Interpretation:** Promotion effectiveness appears to depend on fit between the promotion design and the platform architecture: usage-cost-reducing promotions work especially well in multi-platform discovery contexts, but not necessarily in local MaaS contexts.

**Caveat:** Promotion diagnostics show that this is not event-window identified. Subscriber-free-minutes occurs only for VOI in Nuremberg (`144` rows), parking credit only for VOI in Stuttgart (`144` rows), and the EUR 20 voucher only in Berlin across BOLT, NEXTBIKE, and VOI (`450` rows). In each treated city-operator cell, promo rows cover the observed period without within-unit switching.

**Reference:** `results/deep_dive_effects/curated_findings.csv`; `results/deep_dive_effects/summary.csv`; `results/promotion_diagnostics/curated_findings.csv`; `results/promotion_diagnostics/promotion_unit_support.csv`.

### F6a. Promotion-type coefficients are campaign-context diagnostics, not causal event-window estimates.

**Status:** Identification caveat.

**Evidence:** Promotion diagnostics show no useful within-unit switching for the three observed promotion types. Voucher observations are limited to Berlin (`450` rows across BOLT, NEXTBIKE, and VOI), subscriber-free-minutes to Nuremberg VOI (`144` rows), and parking credit to Stuttgart VOI (`144` rows). Treated city-operator cells have `0` non-promo rows in the observed panel.

**Interpretation:** Promotion findings can still support theory about promotion-channel fit, but they should be written as localized mechanism evidence rather than robust causal estimates.

**Reference:** `results/promotion_diagnostics/curated_findings.csv`; `results/promotion_diagnostics/promotion_type_support.csv`; `results/promotion_diagnostics/promotion_unit_support.csv`.

## Platform Heterogeneity Findings

### F7. Free Now is not the dominant source of the pricing-friction finding.

**Status:** Moderate.

**Evidence:** Free Now-only unlock-fee interactions are weaker than local MaaS/multi-platform results. Deep-dive platform-specific tests show stronger price sensitivity for some local platforms, e.g. `price_per_minute_z:platform_KVV_regiomove_clean` is negative in 4/4 models (`market FE = -0.091`, `p < 0.001`; `unit FE = -0.091`, `p < 0.001`) and `price_per_minute_z:platform_LeipzigMOVE_clean` is negative in 4/4 models (`market FE = -0.065`, `p < 0.001`; `unit FE = -0.088`, `p < 0.001`).

**Interpretation:** The empirical story is heterogeneous platform architecture, not a Free Now-only aggregator story. Some local integrations appear to make price comparison more consequential than large aggregator membership alone.

**Caveat:** Individual platform effects are partly city-specific and should be framed as heterogeneity diagnostics.

**Reference:** `results/deep_dive_effects/curated_findings.csv`; `results/deep_dive_effects/summary.csv`.

### F7a. The high-unlock-fee penalty is not fully driven by one major operator.

**Status:** Moderate candidate.

**Evidence:** Leave-one-operator threshold tests for `unlock_fee_ge_0_99:platform_any` remain negative and significant in market FE after dropping BOLT (`-0.119`, `p < 0.001`), NEXTBIKE (`-0.052`, `p = 0.021`), TIER (`-0.091`, `p = 0.010`), or VOI (`-0.199`, `p < 0.001`).

**Interpretation:** The high-fee platform penalty is not only a single-operator artifact in market-FE specifications.

**Caveat:** Leave-one-operator evidence is weaker in unit FE, and the highest threshold becomes sparse after dropping TIER.

**Reference:** `results/threshold_robustness/curated_findings.csv`; `results/threshold_robustness/significant_terms.csv`.

### F7b. High-fee Local MaaS and multi-platform effects are mature-platform effects, but maturity is not separately identified there.

**Status:** Identification caveat.

**Evidence:** Maturity diagnostics show that Local MaaS and multi-platform high-fee observations occur almost exclusively in mature platform phases. For Local MaaS, early and mid maturity segments have zero observations with `unlock_fee_ge_1_00` or `unlock_fee_ge_1_20`; high-fee observations occur only in `mature_366_plus` rows (`90` rows for EUR 1.00; `72` rows for EUR 1.20). For multi-platform, early and mid maturity segments also have zero high-fee observations; high-fee observations occur only in mature rows (`1308` rows for EUR 1.00; `1029` rows for EUR 1.20).

**Interpretation:** The high-unlock-fee Local MaaS/Multi-platform finding should be described as a mature-platform pricing-friction effect. The current panel cannot cleanly distinguish whether the mechanism is high-fee salience, platform maturity, or their combination for these platform types.

**Reference:** `results/maturity_diagnostics/curated_findings.csv`; `results/maturity_diagnostics/maturity_support.csv`.

### F7c. Large aggregator maturity does not create a stronger high-fee penalty over time.

**Status:** Negative evidence.

**Evidence:** For large aggregator membership, high-fee variation exists in both early and mature segments. The maturity triple is positive, not negative: `unlock_fee_ge_1_00:large_aggregator_only:mature_366_plus` has `market FE all = 0.197` (`p < 0.001`) and `unit FE all = 0.083` (`p < 0.001`); the EUR 1.20 triple is also positive (`market FE all = 0.228`, `p < 0.001`; `unit FE all = 0.074`, `p < 0.001`).

**Interpretation:** For Free Now-style large aggregator exposure, the data do not support a simple “platform maturity strengthens the high-fee penalty” mechanism. If anything, the high-fee penalty is stronger in early aggregator exposure and attenuates in mature exposure.

**Reference:** `results/maturity_diagnostics/curated_findings.csv`; `results/maturity_diagnostics/summary.csv`.

### F8. Weak exposure behaves differently and should not be pooled with true platform membership.

**Status:** Robust data-design decision.

**Evidence:** Weak exposure terms often generate large and unstable coefficients, especially around price per minute and coverage. Removing weak exposure produces cleaner pricing-friction estimates and avoids mixing bookable/payable integrations with route-info or unclear exposure.

**Interpretation:** The analysis should keep bookable/payable platform membership distinct from weak exposure; weak exposure is useful as a sensitivity category, not as treatment.

**Reference:** `results/idea_tests/03_platform_type_boundary/summary.csv`; `data/README.md`.

## Supply-Side Findings

### F9. Supply-side adaptation is suggestive but not a clean central mechanism.

**Status:** Exploratory.

**Evidence:** In supply-side tests, coverage interactions are negative for local MaaS and multi-platform in unit FE (`Coverage_z:local_maas_only = -0.464`, `p < 0.001`; `Coverage_z:multi_platform = -0.460`, `p < 0.001`), while exclusive coverage has large positive unit-FE coefficients for local MaaS/multi-platform but negative scooter-only coefficients. Relative fleet size has only a weak positive within-unit platform interaction.

**Interpretation:** Supply variables likely capture strategic adaptation and market structure rather than a clean user-side mechanism. They are useful controls and exploratory extensions, but not the clearest JAMS story.

**Reference:** `results/idea_tests/07_supply_side_adaptation/summary.csv`.

## Competition And Context Findings

### F10. Competition is not a stable primary moderator.

**Status:** Not supported as main claim.

**Evidence:** In isolated competition tests, `unlock_fee × platform_any × competition` is not stable across competition measures, unit FE, and DML. Active operator count and fragmentation are sometimes negative in market FE, especially in cleaned/no-weak or scooter samples, but effects disappear or reverse under unit FE and DML.

**Interpretation:** Competition may be a mechanism probe or boundary condition, but it should not be positioned as the primary explanatory moderator.

**Reference:** `results/isolated_competition_pricing/triple_interaction_stability.csv`; `results/competition_mechanism_dml/competition_mechanism_synthesis.csv`.

### F11. Transit-rich or dense cities may intensify platform price sensitivity, but evidence is not yet stable.

**Status:** Exploratory.

**Evidence:** `price_per_minute_z:platform_any:PT_availability_z` is negative in market FE for all (`-0.043`, `p < 0.001`) and no-weak exposure (`-0.047`, `p < 0.001`), but not in unit FE. `unlock_fee_z:platform_any:population_density_z` is negative in market FE for all (`-0.058`, `p = 0.020`) and no-weak exposure (`-0.057`, `p = 0.017`), but not in unit FE.

**Interpretation:** Platform pricing may matter more where users have stronger multimodal outside options, but the identification is mostly cross-city so far.

**Reference:** `results/deep_dive_effects/curated_findings.csv`; `results/deep_dive_effects/summary.csv`.

### F12. Wet weather and trip context are small supplementary boundary conditions.

**Status:** Exploratory.

**Evidence:** `price_per_minute_z:platform_any:share_weather_is_wet_z` is negative in 3/4 models, including `all unit FE = -0.005` (`p = 0.017`) and scooter unit FE `-0.012` (`p = 0.011`). Network-distance interactions appear in scooter-only models but are not broad enough for a core claim.

**Interpretation:** Context can shape price sensitivity, but the effect size is small and best used as supporting evidence.

**Reference:** `results/deep_dive_effects/curated_findings.csv`; `results/deep_dive_effects/summary.csv`.

## Current Storyline

The strongest storyline is: **platform membership transforms pricing and promotion effectiveness by increasing the salience of comparable mobility options.** The most robust negative effect is not platform membership itself, but the interaction between platform membership and salient upfront pricing frictions, especially high unlock fees. Capacity utilisation remains the cleanest primary outcome, while trip volume provides supporting evidence for the Local MaaS mechanism. The most promising positive counterpoint is that promotions reducing marginal usage cost, especially subscriber-free-minutes promotions, can perform well in multi-platform contexts, but promotion evidence is localized. Competition and city context help explain when the mechanism may be stronger, but current evidence supports them as boundary probes rather than central claims.

## Marketing-Mix Feature Expansion

Online and provider-documentation research suggests several additional marketing-mix features that could strengthen the analysis.

**Immediately testable with current data:**

- `group_ride`: product/social-use affordance with good variation (`8,413/14,514` rows).
- `no_of_vehicle_types`: product assortment proxy with values 1, 2, and 3.
- `complementary_services`: multimodal/service-bundling proxy, sparse but meaningful (`1,224` rows).
- `subscription_options`: broad pass/subscription indicator, but weak standalone variation (`13,749/14,514` rows are `1`).

**Best external-coding candidates:**

- Pass/free-unlock/minute-bundle intensity by provider-city-date.
- Reservation availability and reservation duration.
- Mandatory parking/station-return/out-of-zone fee rules.
- Referral or new-user credit campaigns.
- Monthly app ratings/review volume as digital service-quality proxy.

**Interpretation:** The highest-value extension is not another generic promotion flag, but richer coding of **pricing architecture** and **usage-friction reducers**: free unlock passes, minute bundles, reservation, and return/parking friction. These map directly onto the high-unlock-fee salience mechanism.

**Reference:** `results/feature_research/marketing_mix_feature_research.md`; `results/feature_research/marketing_mix_feature_opportunities.csv`.

## Underused Marketing-Mix Feature Findings

### F13. Group ride availability is a plausible product-affordance moderator, but the sign is negative.

**Status:** Moderate candidate.

**Evidence:** In the underused marketing-mix tests, `group_ride:local_maas_only` is negative in 3/6 models: `all unit FE = -0.052` (`p = 0.0018`), no-weak unit FE `-0.052` (`p = 0.0018`), and scooter unit FE `-0.051` (`p = 0.039`). `group_ride:multi_platform` is also negative in 3/6 models: `all unit FE = -0.087` (`p < 0.001`), no-weak unit FE `-0.087` (`p < 0.001`), and scooter unit FE `-0.086` (`p < 0.001`).

**Interpretation:** Group ride should not be framed as a straightforward utilisation booster. It may mark a social/product affordance that is poorly aligned with platform-mediated utilisation, or it may proxy product positioning in lower-utilisation city-operator settings.

**Caveat:** Evidence is mainly within-unit; market-FE estimates are unstable or not interpretable for this feature.

**Reference:** `results/underused_marketing_mix/curated_findings.csv`; `results/underused_marketing_mix/summary.csv`.

### F14. Vehicle-type breadth may be a positive product-assortment feature in scooter markets.

**Status:** Exploratory candidate.

**Evidence:** In scooter-only unit FE, `no_of_vehicle_types_z` interactions are positive for any platform (`0.013`, `p < 0.001`), Local MaaS (`0.023`, `p < 0.001`), multi-platform (`0.030`, `p < 0.001`), and large aggregator (`0.014`, `p < 0.001`).

**Interpretation:** Product assortment may help platform contexts by offering better modal fit within the same city-operator setting, especially in scooter-relevant markets.

**Caveat:** Evidence is strongest only in scooter-only unit FE; market-FE and full-sample evidence is mixed.

**Reference:** `results/underused_marketing_mix/curated_findings.csv`; `results/underused_marketing_mix/significant_terms.csv`.

### F15. The current subscription_options dummy is not usable as a central marketing-mix feature.

**Status:** Negative evidence.

**Evidence:** `subscription_options` equals `1` in 13,749 of 14,514 rows and 10,996 of 11,149 scooter rows. Some unit-FE models produce implausibly huge coefficients, indicating near-collinearity or weak support.

**Interpretation:** We should not use the broad current subscription dummy as a main effect. The theoretically relevant construct is richer pass intensity: free unlocks, minute bundles, monthly subscription, and public-transport subscriber benefits.

**Reference:** `results/underused_marketing_mix/curated_findings.csv`; `results/underused_marketing_mix/sample_summary.csv`.

### F16. Vehicle-type breadth appears to buffer Local MaaS high-unlock-fee penalties.

**Status:** Moderate candidate.

**Evidence:** In feature-fee moderation tests, `unlock_fee_ge_1_00:local_maas_only:no_of_vehicle_types_z` is positive in 6/6 models: `all market FE = 0.074` (`p < 0.001`), `all unit FE = 0.014` (`p < 0.001`), no-weak market FE `0.052` (`p < 0.001`), and scooter market FE `0.029` (`p = 0.0067`). The EUR 1.20 interaction is positive in 5/6 models, with `all market FE = 0.075` (`p < 0.001`) and `all unit FE = 0.014` (`p < 0.001`).

**Interpretation:** Product assortment may reduce the harm of high upfront fees in Local MaaS contexts. This gives the story a useful marketing-mix nuance: pricing frictions are harmful, but broader product assortment can partially buffer the penalty by improving modal fit.

**Caveat:** The buffering effect is Local MaaS-specific; multi-platform evidence is mixed and should not be generalized.

**Reference:** `results/feature_fee_moderation/curated_findings.csv`; `results/feature_fee_moderation/summary.csv`.

### F17. Group ride does not buffer high unlock fees; if anything, it amplifies Local MaaS penalties within units.

**Status:** Exploratory candidate.

**Evidence:** `group_ride` triple interactions are negative for Local MaaS in unit-FE models. At EUR 1.00: `all unit FE = -0.039` (`p < 0.001`), no-weak unit FE `-0.035` (`p < 0.001`), scooter unit FE `-0.026` (`p < 0.001`). At EUR 1.20: `all unit FE = -0.011` (`p = 0.003`), no-weak unit FE `-0.007` (`p = 0.048`), scooter unit FE `-0.021` (`p < 0.001`).

**Interpretation:** Group ride should not be positioned as a friction reducer. In Local MaaS settings, it may mark a product usage mode or provider positioning where high upfront fees are especially harmful.

**Caveat:** Support is narrow because high-fee Local MaaS rows often have `group_ride = 1`, especially at EUR 1.20.

**Reference:** `results/feature_fee_moderation/curated_findings.csv`; `results/feature_fee_moderation/significant_terms.csv`.

### F18. Complementary services cannot explain the high-fee platform penalty with current data.

**Status:** Negative evidence.

**Evidence:** In the high-fee Local MaaS and multi-platform support table, `complementary_services` has zero nonzero observations. The estimated complementary-services triple coefficients are effectively zero with tiny p-values, indicating collinearity rather than interpretable effects.

**Interpretation:** Complementary services require richer service coding before they can be used as a high-fee buffer or amplifier.

**Reference:** `results/feature_fee_moderation/curated_findings.csv`; `results/feature_fee_moderation/sample_summary.csv`.

## Next Tests

1. Convert the threshold result into a compact paper table with three cutoffs: EUR 0.99, EUR 1.00, and EUR 1.20.
2. Consider a parsimonious main model centered on EUR 1.00 and EUR 1.20 unlock-fee thresholds for Local MaaS and multi-platform membership.
3. Avoid claiming that platform maturity independently strengthens the Local MaaS/Multi-platform penalty unless additional data introduce high-fee variation in early maturity phases.
4. Treat promotion-type findings as qualitative/mechanism support unless additional campaign data add within-unit switching.
5. Use `log_trip_count_day` as a secondary mechanism outcome mainly for Local MaaS, not as the primary outcome.
6. If more external coding is feasible, prioritize pass/free-unlock/minute-bundle intensity over the current broad `subscription_options` dummy.
7. If adding a product-side moderator to the paper story, prioritize vehicle-type breadth as a Local MaaS buffer; keep group ride as exploratory and avoid complementary-services claims.

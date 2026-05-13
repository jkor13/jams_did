# jams_did

## Platform Membership as Marketing-Mix Moderator

This folder contains the clean, push-ready analysis code and curated result
tables for the platform membership paper. It intentionally excludes the earlier
exploratory FreeNow-only diagnostics and classic DiD scripts.

## Research Logic

The concept paper asks whether platform membership changes the effectiveness of
providers' marketing activities on provider performance. The primary outcome is
capacity utilisation (`ur_boxcox`), not platform adoption itself.

Core model:

```text
capacity utilisation =
  marketing mix
  + platform membership / platform type
  + marketing mix x platform membership / platform type
  + fixed effects
```

The main interpretation is therefore about moderation effects, especially how
platform membership changes the effect of access-pricing frictions such as
unlock fees.

## Folder Structure

```text
platform_membership_moderation/
  README.md
  requirements.txt
  scripts/
    run_concept_moderation.py
    run_competition_mechanism_dml.py
  src/platform_moderation/
    config.py
    data.py
    modeling.py
    reporting.py
  results/
    concept_aligned_moderation/
    competition_mechanism_dml/
    platform_typology/
  docs/
    findings_interpretation_table.tex
```

## Inputs

The scripts expect the clean platform-typed panel at:

```text
~/dev/ewgt_multilevel_model/outputs/reports/platform_feature_research/platform_types/JAMS_df_platform_clean_typed.csv
```

This input is not duplicated here.

## Reproduction

Run from the repository root on `bigbo`:

```bash
python3 platform_membership_moderation/scripts/run_concept_moderation.py
python3 platform_membership_moderation/scripts/run_competition_mechanism_dml.py
```

Outputs are written to:

```text
~/dev/ewgt_multilevel_model/platform_membership_moderation/results/
```

## Main Analysis

`scripts/run_concept_moderation.py` estimates the concept-aligned moderation
models:

- Outcome: `ur_boxcox` as transformed capacity utilisation.
- Robustness outcome: `log_trip_count_day`.
- Marketing-mix variables: price per minute, unlock fee, relative fleet size,
  coverage, exclusive coverage, and promotion active.
- Moderators: any platform membership, FreeNow-only, local MaaS-only,
  multi-platform membership, and weak exposure only.
- Fixed effects:
  - `market_fe`: city, date, and operator fixed effects.
  - `unit_fe`: city-operator and date fixed effects.
- Standard errors are clustered by `city_operator`.

Key output files:

- `results/concept_aligned_moderation/concept_moderation_terms.csv`
- `results/concept_aligned_moderation/moderation_synthesis.csv`
- `results/concept_aligned_moderation/primary_ur_moderation_terms.csv`

## Mechanism and DML Analysis

`scripts/run_competition_mechanism_dml.py` tests the exploratory comparison
mechanism:

```text
pricing friction x platform type x competitive intensity
```

Competitive intensity is measured with `no_shared_provider_total`, standardized
as `competition_z`.

The script estimates:

- OLS with `market_fe`.
- OLS with `unit_fe`.
- Double Machine Learning residualization using Histogram Gradient Boosting and
  Random Forest learners with GroupKFold by `city_operator`.

Key output files:

- `results/competition_mechanism_dml/competition_mechanism_terms.csv`
- `results/competition_mechanism_dml/competition_mechanism_synthesis.csv`

## Current Findings

1. There is no robust universal platform bonus. Platform membership should not
   be framed as an automatic demand or utilisation boost.
2. Platform type matters. Local MaaS, large aggregator, multi-platform, and weak
   exposure contexts behave differently.
3. The strongest paper-relevant result is moderation: platform membership
   changes marketing-mix effectiveness.
4. The most consistent mechanism is pricing friction. In the main market-FE
   model, `unlock_fee x any_platform` is negative (`coef = -0.0715`, `p < .001`).
5. The local MaaS pricing-friction result is stronger in the main market-FE
   model: `unlock_fee x local_maas_only` is negative (`coef = -0.1075`,
   `p < .001`).
6. FreeNow-only does not provide a robust direct performance effect. FreeNow
   promotion moderation appears in market-FE models but is not robust to
   city-operator fixed effects.
7. The competition mechanism is plausible but exploratory. Some models suggest
   that competition amplifies pricing-friction penalties, but the triple
   interactions are not stable enough to serve as the main claim.

## Recommended Paper Positioning

The strongest story is not "platform membership increases provider
performance." It is:

> Platform membership changes the rules of marketing effectiveness. In
> platform-mediated mobility markets, access-pricing frictions become more
> consequential for capacity utilisation, especially in locally integrated MaaS
> contexts.

## Findings Table

`docs/findings_interpretation_table.tex` contains a push-ready LaTeX table with
one sentence per interpretation-relevant finding, the coefficient or descriptive
value used to support it, and the exact result file/term used as reference.

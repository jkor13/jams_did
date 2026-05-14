# jams_did

Clean analysis code and curated results for the platform membership paper.
The analysis tests whether platform membership changes the effectiveness of
marketing-mix instruments on provider capacity utilisation (`ur_boxcox`).

## Structure

- `src/platform_moderation/`: shared data prep, model, and reporting code
- `scripts/build_extended_features.py`: builds extended competition and marketing-mix feature tables
- `scripts/run_concept_moderation.py`: main moderation models
- `scripts/run_competition_mechanism_dml.py`: competition-mechanism and DML checks
- `scripts/run_isolated_competition_pricing.py`: isolated competition-pricing mechanism tests
- `scripts/run_deep_dive_effects.py`: additional exploratory mechanism and boundary-condition probes
- `scripts/run_threshold_robustness.py`: alternative unlock-fee threshold checks
- `scripts/run_city_sensitivity.py`: leave-one-city checks for platform-type threshold effects
- `scripts/run_maturity_diagnostics.py`: maturity support and high-fee timing diagnostics
- `scripts/run_promotion_diagnostics.py`: support diagnostics for promotion-type findings
- `scripts/run_outcome_robustness.py`: capacity-utilisation versus trip-volume robustness
- `scripts/run_underused_marketing_mix.py`: tests underused marketing-mix features already in the panel
- `scripts/run_feature_fee_moderation.py`: tests whether product features moderate high unlock-fee platform penalties
- `scripts/run_idea_*.py`: seven separate JAMS story-extension tests
- `scripts/run_all_idea_tests.py`: runs all seven idea tests
- `results/`: curated CSV outputs used for interpretation
- `docs/findings_interpretation_table.tex`: findings table source
- `docs/findings_interpretation_table.pdf`: compiled findings table

## Data

The clean typed panel is included in `data/JAMS_df_platform_clean_typed.csv`. See `data/README.md` for the platform-membership coding.

## Run

From the repository root on `bigbo`:

```bash
python3 scripts/build_extended_features.py
python3 scripts/run_concept_moderation.py
python3 scripts/run_competition_mechanism_dml.py
python3 scripts/run_isolated_competition_pricing.py
python3 scripts/run_deep_dive_effects.py
python3 scripts/run_threshold_robustness.py
python3 scripts/run_city_sensitivity.py
python3 scripts/run_maturity_diagnostics.py
python3 scripts/run_promotion_diagnostics.py
python3 scripts/run_outcome_robustness.py
python3 scripts/run_underused_marketing_mix.py
python3 scripts/run_feature_fee_moderation.py
```

Run the separate idea tests:

```bash
python3 scripts/run_all_idea_tests.py
```

## Main Takeaway

The strongest result is not a universal platform-performance boost. Platform
membership appears to moderate marketing effectiveness: access-pricing frictions,
especially unlock fees, become more detrimental to capacity utilisation in
platform contexts, particularly for local MaaS integrations.

Key files:

- `results/concept_aligned_moderation/primary_ur_moderation_terms.csv`
- `results/concept_aligned_moderation/moderation_synthesis.csv`
- `results/competition_mechanism_dml/competition_mechanism_synthesis.csv`
- `results/isolated_competition_pricing/triple_interaction_stability.csv`
- `results/deep_dive_effects/curated_findings.csv`
- `results/threshold_robustness/curated_findings.csv`
- `results/city_sensitivity/curated_findings.csv`
- `results/maturity_diagnostics/curated_findings.csv`
- `results/promotion_diagnostics/curated_findings.csv`
- `results/outcome_robustness/curated_findings.csv`
- `results/feature_research/marketing_mix_feature_research.md`
- `results/feature_engineering/feature_inventory.md`
- `results/feature_engineering/external_sources.md`
- `data/extended_competition_marketing_features.csv`
- `results/underused_marketing_mix/curated_findings.csv`
- `results/feature_fee_moderation/curated_findings.csv`
- `results/idea_tests/all_idea_terms.csv`
- `findings.md`
- `results/idea_tests/significant_idea_terms.csv`
- `docs/findings_interpretation_table.pdf`

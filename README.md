# jams_did

Clean analysis code and curated results for the platform membership paper.
The analysis tests whether platform membership changes the effectiveness of
marketing-mix instruments on provider capacity utilisation (`ur_boxcox`).

## Structure

- `src/platform_moderation/`: shared data prep, model, and reporting code
- `scripts/run_concept_moderation.py`: main moderation models
- `scripts/run_competition_mechanism_dml.py`: competition-mechanism and DML checks
- `results/`: curated CSV outputs used for interpretation
- `docs/findings_interpretation_table.tex`: findings table source
- `docs/findings_interpretation_table.pdf`: compiled findings table

## Input

The scripts expect the clean typed panel on `bigbo`:

```text
~/dev/ewgt_multilevel_model/outputs/reports/platform_feature_research/platform_types/JAMS_df_platform_clean_typed.csv
```

## Run

From the repository root on `bigbo`:

```bash
python3 scripts/run_concept_moderation.py
python3 scripts/run_competition_mechanism_dml.py
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
- `docs/findings_interpretation_table.pdf`

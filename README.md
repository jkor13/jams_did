# jams_did

Clean analysis code and curated results for the platform membership paper.
The analysis tests whether platform membership changes the effectiveness of
marketing-mix instruments on provider capacity utilisation (`ur_boxcox`).

## Structure

- `src/platform_moderation/`: shared data prep, model, and reporting code
- `scripts/run_concept_moderation.py`: main moderation models
- `scripts/run_competition_mechanism_dml.py`: competition-mechanism and DML checks
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
python3 scripts/run_concept_moderation.py
python3 scripts/run_competition_mechanism_dml.py
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
- `results/idea_tests/all_idea_terms.csv`
- `results/idea_tests/significant_idea_terms.csv`
- `docs/findings_interpretation_table.pdf`

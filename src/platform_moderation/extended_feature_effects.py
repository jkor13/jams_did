"""Test platform effects with extended competition and marketing-mix features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, REPO_ROOT, WEATHER_CONTROLS
from .data import prepare_panel, zscore
from .modeling import fit_ols_cluster
from .reporting import add_report_columns, label_term


INPUT = REPO_ROOT / "data/JAMS_df_platform_extended_features.csv"
OUT = OUTPUT_BASE / "extended_feature_effects"
OUT.mkdir(parents=True, exist_ok=True)

PLATFORM_TYPES = ["large_aggregator_only", "local_maas_only", "multi_platform"]

MODERATORS = {
    "same_mode_competition": {
        "column": "same_mode_competitor_count_day_z",
        "raw": "same_mode_competitor_count_day",
        "category": "competition",
        "centrality": "high",
        "interpretation": "direct same-mode competitive intensity",
    },
    "same_platform_competition": {
        "column": "same_platform_competitor_count_day_z",
        "raw": "same_platform_competitor_count_day",
        "category": "platform_competition",
        "centrality": "high",
        "interpretation": "choice pressure inside the platform environment",
    },
    "active_vehicle_hhi_same_mode": {
        "column": "active_vehicle_hhi_same_mode_day_z",
        "raw": "active_vehicle_hhi_same_mode_day",
        "category": "competition_concentration",
        "centrality": "medium",
        "interpretation": "same-mode supply concentration",
    },
    "unlock_fee_gap_same_mode": {
        "column": "unlock_fee_gap_to_same_mode_min_z",
        "raw": "unlock_fee_gap_to_same_mode_min",
        "category": "relative_price_position",
        "centrality": "very_high",
        "interpretation": "own unlock-fee premium over the cheapest same-mode competitor",
    },
    "price_per_minute_gap_same_mode": {
        "column": "price_per_minute_gap_to_same_mode_min_z",
        "raw": "price_per_minute_gap_to_same_mode_min",
        "category": "relative_price_position",
        "centrality": "high",
        "interpretation": "own per-minute price premium over the cheapest same-mode competitor",
    },
    "active_vehicle_share_same_mode": {
        "column": "active_vehicle_share_same_mode_z",
        "raw": "active_vehicle_share_same_mode",
        "category": "availability_position",
        "centrality": "high",
        "interpretation": "own same-mode supply availability share",
    },
    "commute_peak_share": {
        "column": "commute_peak_trip_share_z",
        "raw": "commute_peak_trip_share",
        "category": "process_usage_context",
        "centrality": "medium",
        "interpretation": "commute-oriented usage process",
    },
    "night_trip_share": {
        "column": "night_trip_share_z",
        "raw": "night_trip_share",
        "category": "process_usage_context",
        "centrality": "medium",
        "interpretation": "night/leisure-oriented usage process",
    },
    "reservation_available": {
        "column": "reservation_available_external",
        "raw": "reservation_available_external",
        "category": "process_product",
        "centrality": "medium",
        "interpretation": "reservation affordance",
    },
    "free_unlock_pass": {
        "column": "free_unlock_pass_external",
        "raw": "free_unlock_pass_external",
        "category": "price_pass",
        "centrality": "high",
        "interpretation": "free-unlock/pass affordance",
    },
    "minute_bundle": {
        "column": "minute_bundle_external",
        "raw": "minute_bundle_external",
        "category": "price_pass",
        "centrality": "high",
        "interpretation": "minute-bundle/pass affordance",
    },
    "parking_geofence_rules": {
        "column": "mandatory_parking_or_geofence_rules_external",
        "raw": "mandatory_parking_or_geofence_rules_external",
        "category": "place_process_friction",
        "centrality": "medium",
        "interpretation": "parking/geofence process constraints",
    },
}


def plus(terms: list[str]) -> str:
    return " + ".join(terms)


def fe_terms(fe_strategy: str) -> str:
    if fe_strategy == "market_fe":
        return "C(city) + C(date_str) + C(operator)"
    if fe_strategy == "unit_fe":
        return "C(city_operator) + C(date_str)"
    raise ValueError(fe_strategy)


def load_extended_panel() -> pd.DataFrame:
    df = prepare_panel(pd.read_csv(INPUT, low_memory=False))
    df["date_str"] = pd.to_datetime(df["start_date"]).dt.strftime("%Y-%m-%d")
    for spec in MODERATORS.values():
        raw = spec["raw"]
        col = spec["column"]
        if col == raw:
            df[col] = pd.to_numeric(df[raw], errors="coerce").fillna(0)
        else:
            df[col] = zscore(df[raw]).fillna(0)
    df["no_of_vehicle_types_z"] = zscore(df["no_of_vehicle_types"]).fillna(0)
    df["unlock_fee_ge_1_00"] = pd.to_numeric(df["unlock_fee"], errors="coerce").fillna(0).ge(1.00).astype(int)
    return df


def samples(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "all": df,
        "no_weak_exposure": df.loc[df["weak_exposure_only"].eq(0)].copy(),
        "scooter_only": df.loc[df["scooter_operator"].eq(1)].copy(),
    }


def sample_support(sample_map: dict[str, pd.DataFrame]) -> None:
    rows = []
    for sample_name, data in sample_map.items():
        for name, spec in MODERATORS.items():
            col = spec["column"]
            row = {
                "sample": sample_name,
                "moderator": name,
                "category": spec["category"],
                "column": col,
                "non_missing": int(data[col].notna().sum()),
                "unique_values": int(data[col].nunique(dropna=True)),
                "mean": pd.to_numeric(data[col], errors="coerce").mean(),
                "sd": pd.to_numeric(data[col], errors="coerce").std(),
                "min": pd.to_numeric(data[col], errors="coerce").min(),
                "max": pd.to_numeric(data[col], errors="coerce").max(),
            }
            for platform in PLATFORM_TYPES:
                subset = data.loc[data[platform].eq(1)]
                row[f"{platform}_rows"] = len(subset)
                row[f"{platform}_unique"] = int(subset[col].nunique(dropna=True))
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "sample_support.csv", index=False)


def fit_platform_feature_models(sample_map: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = [
        "price_per_minute_z",
        "unlock_fee_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    for sample_name, data in sample_map.items():
        for moderator, spec in MODERATORS.items():
            col = spec["column"]
            for platform_family, platforms in {
                "any_platform": ["platform_any"],
                "platform_types": PLATFORM_TYPES,
            }.items():
                for fe in ["market_fe", "unit_fe"]:
                    focus = [f"{col}:{platform}" for platform in platforms]
                    fitted = fit_ols_cluster(
                        f"{moderator}_{platform_family}_{fe}_{sample_name}",
                        data,
                        "ur_boxcox",
                        f"ur_boxcox ~ {col} * ({plus(platforms)}) + {plus(controls)} + {fe_terms(fe)}",
                        focus,
                        OUT,
                        fe_strategy=fe,
                    )
                    for row in fitted:
                        row["sample"] = sample_name
                        row["family"] = "platform_feature_moderation"
                        row["moderator"] = moderator
                        row["moderator_category"] = spec["category"]
                        row["moderator_centrality"] = spec["centrality"]
                        row["platform_family"] = platform_family
                    rows.extend(fitted)
    return rows


def fit_high_fee_feature_models(sample_map: dict[str, pd.DataFrame]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    controls = [
        "price_per_minute_z",
        "relative_fleet_size_z",
        "Coverage_z",
        "Exclusive_Coverage_z",
        "promo_active",
        *WEATHER_CONTROLS,
    ]
    selected = [
        "same_mode_competition",
        "same_platform_competition",
        "unlock_fee_gap_same_mode",
        "active_vehicle_share_same_mode",
        "free_unlock_pass",
        "minute_bundle",
    ]
    for sample_name, data in sample_map.items():
        for moderator in selected:
            col = MODERATORS[moderator]["column"]
            for fe in ["market_fe", "unit_fe"]:
                focus = [f"unlock_fee_ge_1_00:{platform}:{col}" for platform in PLATFORM_TYPES]
                fitted = fit_ols_cluster(
                    f"high_fee_{moderator}_{fe}_{sample_name}",
                    data,
                    "ur_boxcox",
                    f"ur_boxcox ~ unlock_fee_ge_1_00 * ({plus(PLATFORM_TYPES)}) * {col} + {plus(controls)} + {fe_terms(fe)}",
                    focus,
                    OUT,
                    fe_strategy=fe,
                )
                for row in fitted:
                    row["sample"] = sample_name
                    row["family"] = "high_fee_feature_moderation"
                    row["moderator"] = moderator
                    row["moderator_category"] = MODERATORS[moderator]["category"]
                    row["moderator_centrality"] = MODERATORS[moderator]["centrality"]
                    row["platform_family"] = "platform_types"
                rows.extend(fitted)
    return rows


def summarize(results: pd.DataFrame) -> None:
    rows = []
    for (family, moderator, term), group in results.groupby(["family", "moderator", "term"]):
        all_market = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("market_fe")]
        all_unit = group.loc[group["sample"].eq("all") & group["fe_strategy"].eq("unit_fe")]
        rows.append(
            {
                "family": family,
                "moderator": moderator,
                "category": group["moderator_category"].iloc[0],
                "centrality": group["moderator_centrality"].iloc[0],
                "term": term,
                "label": label_term(term),
                "n_models": len(group),
                "n_negative_sig_05": int(((group["coef"] < 0) & group["significant_05"]).sum()),
                "n_positive_sig_05": int(((group["coef"] > 0) & group["significant_05"]).sum()),
                "median_coef": group["coef"].median(),
                "all_market_fe_coef": all_market["coef"].iloc[0] if len(all_market) else pd.NA,
                "all_market_fe_p": all_market["p_value"].iloc[0] if len(all_market) else pd.NA,
                "all_unit_fe_coef": all_unit["coef"].iloc[0] if len(all_unit) else pd.NA,
                "all_unit_fe_p": all_unit["p_value"].iloc[0] if len(all_unit) else pd.NA,
            }
        )
    pd.DataFrame(rows).sort_values(
        ["n_negative_sig_05", "n_positive_sig_05", "centrality"], ascending=[False, False, True]
    ).to_csv(OUT / "summary.csv", index=False)


def write_curated(results: pd.DataFrame) -> None:
    summary = pd.read_csv(OUT / "summary.csv")
    support = pd.read_csv(OUT / "sample_support.csv")
    findings = []

    def pick(family: str, moderator: str, contains: str | None = None) -> pd.DataFrame:
        out = summary.loc[(summary["family"].eq(family)) & (summary["moderator"].eq(moderator))]
        if contains:
            out = out.loc[out["term"].str.contains(contains, regex=False)]
        return out

    rel_price = pick("platform_feature_moderation", "unlock_fee_gap_same_mode")
    findings.append(
        {
            "finding_id": "EF1",
            "finding": "Relative same-mode unlock-fee disadvantage is a strong platform-relevant pricing feature.",
            "status": "candidate",
            "evidence": rel_price.sort_values(["n_negative_sig_05", "n_positive_sig_05"], ascending=False)
            .head(4)
            .to_json(orient="records"),
            "interpretation": "The best extension of the unlock-fee story is not only absolute fee level, but whether the provider is expensive relative to same-mode competitors in the same city-day.",
            "caveat": "Needs paper-table distillation; price-position features are constructed from observed provider prices and can be collinear with platform/operator structure.",
        }
    )

    same_mode = pick("platform_feature_moderation", "same_mode_competition")
    same_platform = pick("platform_feature_moderation", "same_platform_competition")
    findings.append(
        {
            "finding_id": "EF2",
            "finding": "Competition can now be tested more cleanly as same-mode and same-platform pressure.",
            "status": "diagnostic",
            "evidence": pd.concat([same_mode, same_platform]).sort_values(
                ["n_negative_sig_05", "n_positive_sig_05"], ascending=False
            )
            .head(6)
            .to_json(orient="records"),
            "interpretation": "The new feature layer separates generic city competition from direct substitute pressure and platform-internal choice pressure.",
            "caveat": "This is a measurement improvement; whether competition becomes a stable moderator depends on the signs across market FE, unit FE, and samples.",
        }
    )

    pass_rows = pd.concat(
        [
            pick("platform_feature_moderation", "free_unlock_pass"),
            pick("platform_feature_moderation", "minute_bundle"),
            pick("high_fee_feature_moderation", "free_unlock_pass"),
            pick("high_fee_feature_moderation", "minute_bundle"),
        ]
    )
    pass_support = support.loc[support["moderator"].isin(["free_unlock_pass", "minute_bundle"])]
    findings.append(
        {
            "finding_id": "EF3",
            "finding": "Pass/free-unlock and minute-bundle affordances are now codable, but mostly provider-level.",
            "status": "support_caveat",
            "evidence": pass_rows.sort_values(["n_negative_sig_05", "n_positive_sig_05"], ascending=False)
            .head(6)
            .to_json(orient="records"),
            "interpretation": "These features map tightly to the pricing-friction mechanism and should be used as moderators or mechanism probes.",
            "caveat": f"Support/variation is provider-level rather than city-date campaign timing. Support summary: {pass_support[['sample','moderator','unique_values']].drop_duplicates().to_json(orient='records')}",
        }
    )

    high_fee = summary.loc[summary["family"].eq("high_fee_feature_moderation")]
    findings.append(
        {
            "finding_id": "EF4",
            "finding": "High-fee platform penalties can now be decomposed by competition, relative price position, and pass affordances.",
            "status": "next_model_family",
            "evidence": high_fee.sort_values(["n_negative_sig_05", "n_positive_sig_05"], ascending=False)
            .head(8)
            .to_json(orient="records"),
            "interpretation": "The next paper-facing model should focus on a small set: same-mode unlock-fee gap, same-platform competitor count, same-mode competitor count, and pass/free-unlock affordances.",
            "caveat": "Avoid overloading the paper with all 12 moderators; use the full table as appendix/screening.",
        }
    )
    pd.DataFrame(findings).to_csv(OUT / "curated_findings.csv", index=False)


def run_extended_feature_effects() -> pd.DataFrame:
    df = load_extended_panel()
    sample_map = samples(df)
    sample_support(sample_map)
    rows = fit_platform_feature_models(sample_map)
    rows.extend(fit_high_fee_feature_models(sample_map))
    results = add_report_columns(pd.DataFrame(rows))
    results.to_csv(OUT / "terms.csv", index=False)
    results.loc[results["significant_05"]].to_csv(OUT / "significant_terms.csv", index=False)
    summarize(results)
    write_curated(results)
    (OUT / "README.md").write_text(
        """# Extended Feature Effects

Tests whether platform membership effects on capacity utilisation depend on the new competition,
relative-price, product/process, and pass/friction features.

Main models:

- `ur_boxcox ~ extended_feature * platform_any + controls + FE`
- `ur_boxcox ~ extended_feature * platform_type + controls + FE`
- `ur_boxcox ~ high_unlock_fee * platform_type * selected_extended_feature + controls + FE`

Use `curated_findings.csv` as a screening summary and `summary.csv` for model-level stability.
""",
        encoding="utf-8",
    )
    return results


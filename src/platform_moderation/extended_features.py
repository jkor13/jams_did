"""Build extended competition and marketing-mix features."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import INPUT_DATA, REPO_ROOT


OUT_FEATURES = REPO_ROOT / "data/extended_competition_marketing_features.csv"
OUT_PANEL = REPO_ROOT / "data/JAMS_df_platform_extended_features.csv"
OUT_EXTERNAL = REPO_ROOT / "data/marketing_mix_external_feature_coding.csv"
OUT_REPORT = REPO_ROOT / "results/feature_engineering/feature_inventory.md"
OUT_SUMMARY = REPO_ROOT / "results/feature_engineering/feature_summary.csv"

SCOOTER_OPERATORS = {"BOLT", "LIME", "TIER", "VOI"}
BIKE_OPERATORS = {"NEXTBIKE"}
MOPED_OPERATORS = {"EDDY"}


EXTERNAL_PROVIDER_FEATURES = [
    {
        "operator": "BOLT",
        "group_ride_external": 1,
        "reservation_available_external": 1,
        "reservation_minutes_external": 30,
        "pass_available_external": 1,
        "free_unlock_pass_external": 1,
        "minute_bundle_external": 1,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_BOLT_MICROMOBILITY_HELP_CURRENT",
        "source_url": "https://bolt.eu/en/scooters/",
        "coding_notes": "Current official scooter page documents reservation up to 30 minutes, unlimited-unlock plans, passes, parking guidance, and riding/parking rules. Group-ride coding follows the existing panel feature. Use as broad product/process coding, not 2024 city-specific timing.",
    },
    {
        "operator": "LIME",
        "group_ride_external": 1,
        "reservation_available_external": 1,
        "reservation_minutes_external": 10,
        "pass_available_external": 1,
        "free_unlock_pass_external": 1,
        "minute_bundle_external": 1,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_LIME_HELP_GROUP_RIDE_PASS_RESERVE_CURRENT",
        "source_url": "https://help.li.me/",
        "coding_notes": "Official help pages document Group Ride, LimePass, and vehicle reservation; availability can vary by market.",
    },
    {
        "operator": "TIER",
        "group_ride_external": 1,
        "reservation_available_external": 1,
        "reservation_minutes_external": np.nan,
        "pass_available_external": 1,
        "free_unlock_pass_external": 1,
        "minute_bundle_external": 1,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_DOTT_TIER_HELP_CURRENT",
        "source_url": "https://support.ridedott.com/",
        "coding_notes": "TIER/Dott support and TIER package terms support pass/process coding; group-ride coding follows the existing panel feature. 2024 TIER-specific city timing should be checked before causal use.",
    },
    {
        "operator": "VOI",
        "group_ride_external": 0,
        "reservation_available_external": 0,
        "reservation_minutes_external": np.nan,
        "pass_available_external": 1,
        "free_unlock_pass_external": 1,
        "minute_bundle_external": 1,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_VOI_PASS_ZONES_CURRENT",
        "source_url": "https://support.voi.com/",
        "coding_notes": "Official/current Voi help and city pages support passes, local subscriber benefits, and geofenced zones; market availability varies.",
    },
    {
        "operator": "NEXTBIKE",
        "group_ride_external": 0,
        "reservation_available_external": 1,
        "reservation_minutes_external": 15,
        "pass_available_external": 1,
        "free_unlock_pass_external": 0,
        "minute_bundle_external": 1,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_NEXTBIKE_PRICES_RESERVATION_CURRENT",
        "source_url": "https://www.nextbike.de/",
        "coding_notes": "nextbike tariff pages document monthly/yearly plans and station/flex-zone/reservation rules; exact local tariffs vary.",
    },
    {
        "operator": "EDDY",
        "group_ride_external": 0,
        "reservation_available_external": 1,
        "reservation_minutes_external": np.nan,
        "pass_available_external": 0,
        "free_unlock_pass_external": 0,
        "minute_bundle_external": 0,
        "mandatory_parking_or_geofence_rules_external": 1,
        "source_id": "SRC_EDDY_HELP_CURRENT",
        "source_url": "https://www.eddy-sharing.de/",
        "coding_notes": "Provider-level moped-sharing process coding; limited relevance because EDDY has small support in the panel.",
    },
]


def _norm_operator(series: pd.Series) -> pd.Series:
    return series.astype(str).str.upper().str.strip()


def _vehicle_mode(operator: str) -> str:
    if operator in SCOOTER_OPERATORS:
        return "scooter"
    if operator in BIKE_OPERATORS:
        return "bike"
    if operator in MOPED_OPERATORS:
        return "moped"
    return "unknown"


def _safe_divide(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.replace(0, np.nan)
    return num / den


def _rank_within(frame: pd.DataFrame, value: str, group: list[str]) -> pd.Series:
    return frame.groupby(group)[value].rank(method="dense", ascending=True)


def _candidate_paths() -> dict[str, list[Path]]:
    base = Path.home() / "dev/ewgt_multilevel_model"
    return {
        "trips": [
            base / "data/input/raw/jams_roh_data/analyse_df.csv",
            base / "data/input/raw/jams_roh_data/clean_df.csv",
            REPO_ROOT.parent / "data/input/raw/jams_roh_data/analyse_df.csv",
        ],
        "active_vehicles": [
            base / "cache/jams_active_vehicle_daily_counts.csv",
            REPO_ROOT.parent / "cache/jams_active_vehicle_daily_counts.csv",
        ],
    }


def _first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def load_panel(path: Path = INPUT_DATA) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df["operator"] = _norm_operator(df["operator"])
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["date"] = df["start_date"].dt.strftime("%Y-%m-%d")
    df["vehicle_mode"] = df["operator"].map(_vehicle_mode)
    return df


def add_price_competition(panel: pd.DataFrame) -> pd.DataFrame:
    keys = ["city", "date"]
    mode_keys = ["city", "date", "vehicle_mode"]
    out = panel.copy()
    out["city_operator_count_day"] = out.groupby(keys)["operator"].transform("nunique")
    out["same_mode_operator_count_day"] = out.groupby(mode_keys)["operator"].transform("nunique")
    out["competitor_count_day"] = out["city_operator_count_day"] - 1
    out["same_mode_competitor_count_day"] = out["same_mode_operator_count_day"] - 1

    for price_col in ["unlock_fee", "price_per_minute"]:
        values = pd.to_numeric(out[price_col], errors="coerce")
        out[price_col] = values
        city_mean = out.groupby(keys)[price_col].transform("mean")
        city_min = out.groupby(keys)[price_col].transform("min")
        city_max = out.groupby(keys)[price_col].transform("max")
        mode_mean = out.groupby(mode_keys)[price_col].transform("mean")
        mode_min = out.groupby(mode_keys)[price_col].transform("min")
        out[f"{price_col}_rank_city_day"] = _rank_within(out, price_col, keys)
        out[f"{price_col}_rank_same_mode_day"] = _rank_within(out, price_col, mode_keys)
        out[f"{price_col}_gap_to_city_min"] = values - city_min
        out[f"{price_col}_gap_to_same_mode_min"] = values - mode_min
        out[f"{price_col}_minus_city_mean"] = values - city_mean
        out[f"{price_col}_minus_same_mode_mean"] = values - mode_mean
        out[f"{price_col}_city_dispersion"] = city_max - city_min
        out[f"is_city_cheapest_{price_col}"] = values.eq(city_min).astype(int)
        out[f"is_same_mode_cheapest_{price_col}"] = values.eq(mode_min).astype(int)
    return out


def add_share_competition(panel: pd.DataFrame) -> pd.DataFrame:
    keys = ["city", "date"]
    mode_keys = ["city", "date", "vehicle_mode"]
    out = panel.copy()
    out["trip_count_day"] = pd.to_numeric(out["trip_count_day"], errors="coerce").fillna(0)
    out["daily_trip_share_city"] = _safe_divide(out["trip_count_day"], out.groupby(keys)["trip_count_day"].transform("sum"))
    out["daily_trip_share_same_mode"] = _safe_divide(
        out["trip_count_day"], out.groupby(mode_keys)["trip_count_day"].transform("sum")
    )
    out["trip_hhi_city_day"] = out.groupby(keys)["daily_trip_share_city"].transform(lambda s: float(np.square(s).sum()))
    out["trip_hhi_same_mode_day"] = out.groupby(mode_keys)["daily_trip_share_same_mode"].transform(
        lambda s: float(np.square(s).sum())
    )
    out["competitor_trips_city_day"] = out.groupby(keys)["trip_count_day"].transform("sum") - out["trip_count_day"]
    out["competitor_trips_same_mode_day"] = out.groupby(mode_keys)["trip_count_day"].transform("sum") - out["trip_count_day"]
    out["largest_competitor_trip_share_city_day"] = out.groupby(keys)["daily_trip_share_city"].transform(
        lambda s: s.where(s.ne(s.max()), np.nan).max() if len(s) > 1 else 0
    )
    return out


def add_active_vehicle_competition(panel: pd.DataFrame, active_path: Path | None) -> pd.DataFrame:
    out = panel.copy()
    if active_path is not None:
        active = pd.read_csv(active_path)
        active = active.rename(columns={"provider": "operator", "active_vehicles_day": "active_vehicles_day"})
        active["operator"] = _norm_operator(active["operator"])
        active["date"] = pd.to_datetime(active["date"]).dt.strftime("%Y-%m-%d")
        out = out.merge(active[["city", "operator", "date", "active_vehicles_day"]], on=["city", "operator", "date"], how="left")
    else:
        out["active_vehicles_day"] = np.nan
    out["active_vehicles_day"] = pd.to_numeric(out["active_vehicles_day"], errors="coerce")
    out["active_vehicles_day"] = out["active_vehicles_day"].fillna(pd.to_numeric(out["weekly_fleetsize"], errors="coerce"))
    keys = ["city", "date"]
    mode_keys = ["city", "date", "vehicle_mode"]
    out["active_vehicle_share_city"] = _safe_divide(
        out["active_vehicles_day"], out.groupby(keys)["active_vehicles_day"].transform("sum")
    )
    out["active_vehicle_share_same_mode"] = _safe_divide(
        out["active_vehicles_day"], out.groupby(mode_keys)["active_vehicles_day"].transform("sum")
    )
    out["active_vehicle_hhi_city_day"] = out.groupby(keys)["active_vehicle_share_city"].transform(
        lambda s: float(np.square(s).sum())
    )
    out["active_vehicle_hhi_same_mode_day"] = out.groupby(mode_keys)["active_vehicle_share_same_mode"].transform(
        lambda s: float(np.square(s).sum())
    )
    out["competitor_active_vehicles_city_day"] = (
        out.groupby(keys)["active_vehicles_day"].transform("sum") - out["active_vehicles_day"]
    )
    out["competitor_active_vehicles_same_mode_day"] = (
        out.groupby(mode_keys)["active_vehicles_day"].transform("sum") - out["active_vehicles_day"]
    )
    return out


def _split_platforms(value: object) -> set[str]:
    if pd.isna(value) or not str(value).strip():
        return set()
    return {part.strip() for part in str(value).split(";") if part.strip()}


def add_platform_competition(panel: pd.DataFrame) -> pd.DataFrame:
    keys = ["city", "date"]
    out = panel.copy()
    out["_platform_set"] = out["platforms_clean"].map(_split_platforms)
    platform_rows = out[["city", "date", "operator", "_platform_set"]].copy()
    same_platform_counts = []
    for _, row in platform_rows.iterrows():
        peers = platform_rows.loc[(platform_rows["city"].eq(row["city"])) & (platform_rows["date"].eq(row["date"]))]
        count = 0
        for _, peer in peers.iterrows():
            if peer["operator"] != row["operator"] and row["_platform_set"].intersection(peer["_platform_set"]):
                count += 1
        same_platform_counts.append(count)
    out["same_platform_competitor_count_day"] = same_platform_counts
    out["platform_member_operator_count_day"] = out.groupby(keys)["platform_membership_clean"].transform("sum")
    out["local_maas_operator_count_day"] = out.groupby(keys)["platform_local_maas_clean"].transform("sum")
    out["large_aggregator_operator_count_day"] = out.groupby(keys)["platform_large_aggregator_clean"].transform("sum")
    out["multi_platform_operator_count_day"] = out.groupby(keys)["platform_both_large_and_local_clean"].transform("sum")
    out = out.drop(columns=["_platform_set"])
    return out


def add_trip_behavior_features(panel: pd.DataFrame, trip_path: Path | None) -> pd.DataFrame:
    out = panel.copy()
    if trip_path is None:
        out["commute_peak_trip_share"] = np.nan
        out["night_trip_share"] = np.nan
        out["observed_vehicle_type_count"] = np.nan
        return out
    usecols = ["city", "operator", "start_date", "s_hour", "vehicle_type"]
    trips = pd.read_csv(trip_path, usecols=usecols, low_memory=False)
    trips["operator"] = _norm_operator(trips["operator"])
    trips["date"] = pd.to_datetime(trips["start_date"]).dt.strftime("%Y-%m-%d")
    trips["is_commute_peak_trip"] = trips["s_hour"].between(7, 9) | trips["s_hour"].between(16, 18)
    trips["is_night_trip"] = trips["s_hour"].ge(22) | trips["s_hour"].le(5)
    agg = (
        trips.groupby(["city", "operator", "date"], as_index=False)
        .agg(
            raw_trip_rows=("operator", "size"),
            commute_peak_trip_share=("is_commute_peak_trip", "mean"),
            night_trip_share=("is_night_trip", "mean"),
            observed_vehicle_type_count=("vehicle_type", "nunique"),
        )
    )
    return out.merge(agg, on=["city", "operator", "date"], how="left")


def add_external_marketing_features(panel: pd.DataFrame) -> pd.DataFrame:
    external = pd.DataFrame(EXTERNAL_PROVIDER_FEATURES)
    external.to_csv(OUT_EXTERNAL, index=False)
    out = panel.merge(external, on="operator", how="left")
    return out


def build_extended_features() -> pd.DataFrame:
    paths = _candidate_paths()
    trip_path = _first_existing(paths["trips"])
    active_path = _first_existing(paths["active_vehicles"])

    panel = load_panel()
    panel = add_price_competition(panel)
    panel = add_share_competition(panel)
    panel = add_active_vehicle_competition(panel, active_path)
    panel = add_platform_competition(panel)
    panel = add_trip_behavior_features(panel, trip_path)
    panel = add_external_marketing_features(panel)

    feature_columns = [
        "city",
        "operator",
        "city_operator",
        "start_date",
        "date",
        "vehicle_mode",
        "city_operator_count_day",
        "same_mode_operator_count_day",
        "competitor_count_day",
        "same_mode_competitor_count_day",
        "daily_trip_share_city",
        "daily_trip_share_same_mode",
        "trip_hhi_city_day",
        "trip_hhi_same_mode_day",
        "competitor_trips_city_day",
        "competitor_trips_same_mode_day",
        "largest_competitor_trip_share_city_day",
        "active_vehicles_day",
        "active_vehicle_share_city",
        "active_vehicle_share_same_mode",
        "active_vehicle_hhi_city_day",
        "active_vehicle_hhi_same_mode_day",
        "competitor_active_vehicles_city_day",
        "competitor_active_vehicles_same_mode_day",
        "same_platform_competitor_count_day",
        "platform_member_operator_count_day",
        "local_maas_operator_count_day",
        "large_aggregator_operator_count_day",
        "multi_platform_operator_count_day",
        "commute_peak_trip_share",
        "night_trip_share",
        "observed_vehicle_type_count",
    ]
    for stem in ["unlock_fee", "price_per_minute"]:
        feature_columns.extend(
            [
                f"{stem}_rank_city_day",
                f"{stem}_rank_same_mode_day",
                f"{stem}_gap_to_city_min",
                f"{stem}_gap_to_same_mode_min",
                f"{stem}_minus_city_mean",
                f"{stem}_minus_same_mode_mean",
                f"{stem}_city_dispersion",
                f"is_city_cheapest_{stem}",
                f"is_same_mode_cheapest_{stem}",
            ]
        )
    feature_columns.extend(
        [
            "group_ride_external",
            "reservation_available_external",
            "reservation_minutes_external",
            "pass_available_external",
            "free_unlock_pass_external",
            "minute_bundle_external",
            "mandatory_parking_or_geofence_rules_external",
            "source_id",
        ]
    )
    features = panel[feature_columns].copy()
    features.to_csv(OUT_FEATURES, index=False)
    panel.to_csv(OUT_PANEL, index=False)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for column in feature_columns:
        values = features[column]
        row = {
            "feature": column,
            "dtype": str(values.dtype),
            "non_missing": int(values.notna().sum()),
            "missing": int(values.isna().sum()),
            "unique_values": int(values.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(values):
            row["mean"] = values.mean()
            row["std"] = values.std()
            row["min"] = values.min()
            row["max"] = values.max()
        summary_rows.append(row)
    pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY, index=False)
    OUT_REPORT.write_text(
        f"""# Extended Feature Inventory

Generated files:

- `data/extended_competition_marketing_features.csv`
- `data/JAMS_df_platform_extended_features.csv`
- `data/marketing_mix_external_feature_coding.csv`
- `results/feature_engineering/external_sources.md`
- `results/feature_engineering/feature_summary.csv`

Input paths:

- Panel: `{INPUT_DATA}`
- Trips: `{trip_path if trip_path else 'not found'}`
- Active vehicles: `{active_path if active_path else 'not found; weekly_fleetsize fallback used'}`

Feature families:

- Same-city and same-mode operator competition counts.
- Trip-share and active-vehicle-share concentration, including HHI.
- Relative price position and cheapest-provider indicators.
- Same-platform competitor counts and platform-type operator counts.
- Trip-behavior process features: commute-peak share, night-trip share, observed vehicle-type count.
- Provider-level external product/process/pass coding with source IDs.
- Source audit trail for external coding.

Identification note:

Competition and price-position features are city-operator-day measures. Provider-level external
features are broad product/process affordances and should be treated as moderators or controls,
not as city-specific 2024 campaign timing unless supported by additional local sources.
""",
        encoding="utf-8",
    )
    return features

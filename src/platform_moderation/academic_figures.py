"""Create caption-ready figures for platform-membership findings."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, REPO_ROOT


OUT = REPO_ROOT / "docs/figures"
MECH = OUTPUT_BASE / "mechanism_feature_tests"


ACCESSIBLE_PRINT_COLORS = {
    "black": "#000000",
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "purple": "#CC79A7",
    "dark_gray": "#666666",
    "light_gray": "#D9D9D9",
    "grid": "#D9D9D9",
}

PLATFORM_STYLES = {
    "large_aggregator_only": {
        "label": "Large aggregator",
        "color": ACCESSIBLE_PRINT_COLORS["black"],
        "marker": "s",
        "linestyle": "--",
        "hatch": "///",
    },
    "local_maas_only": {
        "label": "Local MaaS",
        "color": ACCESSIBLE_PRINT_COLORS["blue"],
        "marker": "o",
        "linestyle": "-",
        "hatch": "",
    },
    "multi_platform": {
        "label": "Multi-platform",
        "color": ACCESSIBLE_PRINT_COLORS["orange"],
        "marker": "^",
        "linestyle": "-.",
        "hatch": "xx",
    },
}

FEATURE_STYLES = {
    "unlock_fee_ge_1_00": {
        "label": "High unlock fee",
        "color": ACCESSIBLE_PRINT_COLORS["blue"],
        "marker": "o",
        "hatch": "",
    },
    "total_price_10min_gap_to_same_mode_min_z": {
        "label": "10-min total-price gap",
        "color": ACCESSIBLE_PRINT_COLORS["orange"],
        "marker": "^",
        "hatch": "xx",
    },
}


@dataclass(frozen=True)
class FigureRow:
    label: str
    idea: str
    term: str
    platform: str
    family: str | None = None
    feature: str | None = None
    outcome: str = "ur_boxcox"
    sample: str = "all"
    fe_strategy: str = "market_fe"


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 320,
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.8,
            "ytick.labelsize": 8.8,
            "legend.fontsize": 8.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "grid.color": ACCESSIBLE_PRINT_COLORS["grid"],
            "grid.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def load_results() -> tuple[pd.DataFrame, pd.DataFrame]:
    terms = pd.read_csv(MECH / "terms.csv")
    summary = pd.read_csv(MECH / "summary.csv")
    return terms, summary


def p_label(p_value: float) -> str:
    if not np.isfinite(p_value):
        return "p n/a"
    if p_value < 0.001:
        return "p < .001"
    return f"p = {p_value:.3f}".replace("0.", ".")


def get_term(terms: pd.DataFrame, row: FigureRow) -> pd.Series:
    mask = (
        terms["idea"].eq(row.idea)
        & terms["term"].eq(row.term)
        & terms["outcome"].eq(row.outcome)
        & terms["sample"].eq(row.sample)
        & terms["fe_strategy"].eq(row.fe_strategy)
    )
    if row.family is not None:
        mask &= terms["family"].eq(row.family)
    if row.feature is not None:
        mask &= terms["feature"].eq(row.feature)
    matches = terms.loc[mask].copy()
    if matches.empty:
        raise KeyError(f"No term found for {row}")
    matches = matches.sort_values(["model", "term"])
    return matches.iloc[0]


def save_figure(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def platform_line_handles(platforms: list[str]) -> list[Line2D]:
    return [
        Line2D(
            [0],
            [0],
            color=PLATFORM_STYLES[platform]["color"],
            marker=PLATFORM_STYLES[platform]["marker"],
            linestyle=PLATFORM_STYLES[platform]["linestyle"],
            label=PLATFORM_STYLES[platform]["label"],
            markersize=5.5,
            linewidth=1.7,
        )
        for platform in platforms
    ]


def platform_bar_handles(platforms: list[str]) -> list[Patch]:
    return [
        Patch(
            facecolor=PLATFORM_STYLES[platform]["color"],
            edgecolor="#222222",
            hatch=PLATFORM_STYLES[platform]["hatch"],
            label=PLATFORM_STYLES[platform]["label"],
        )
        for platform in platforms
    ]


def coefficient_plot() -> None:
    terms, _ = load_results()
    rows = [
        FigureRow(
            "Unlock-fee share of expected trip price",
            "I1_effective_price",
            "unlock_fee_share_expected_z:local_maas_only",
            "local_maas_only",
            family="unlock_fee_burden",
        ),
        FigureRow(
            "Unlock-fee share of expected trip price",
            "I1_effective_price",
            "unlock_fee_share_expected_z:multi_platform",
            "multi_platform",
            family="unlock_fee_burden",
        ),
        FigureRow(
            "5-min total-price gap vs. same-mode minimum",
            "I2_relative_total_price",
            "total_price_5min_gap_to_same_mode_min_z:local_maas_only",
            "local_maas_only",
            family="relative_total_price_5min",
        ),
        FigureRow(
            "5-min total-price gap vs. same-mode minimum",
            "I2_relative_total_price",
            "total_price_5min_gap_to_same_mode_min_z:multi_platform",
            "multi_platform",
            family="relative_total_price_5min",
        ),
        FigureRow(
            "Worse 5-min same-mode price rank",
            "I6_cheapest_rank",
            "total_price_5min_rank_same_mode_z:local_maas_only",
            "local_maas_only",
            family="cheapest_rank_platform_fit",
        ),
        FigureRow(
            "Worse 5-min same-mode price rank",
            "I6_cheapest_rank",
            "total_price_5min_rank_same_mode_z:multi_platform",
            "multi_platform",
            family="cheapest_rank_platform_fit",
        ),
        FigureRow(
            "Worse same-mode unlock-fee rank",
            "I6_cheapest_rank",
            "unlock_fee_rank_same_mode_day_z:local_maas_only",
            "local_maas_only",
            family="cheapest_rank_platform_fit",
        ),
        FigureRow(
            "Worse same-mode unlock-fee rank",
            "I6_cheapest_rank",
            "unlock_fee_rank_same_mode_day_z:multi_platform",
            "multi_platform",
            family="cheapest_rank_platform_fit",
        ),
        FigureRow(
            "Low availability day",
            "I5_operational_reliability",
            "low_availability_day:local_maas_only",
            "local_maas_only",
            family="reliability_platform_fit",
        ),
        FigureRow(
            "Above-normal active-vehicle reliability",
            "I5_operational_reliability",
            "active_vehicle_reliability_z:local_maas_only",
            "local_maas_only",
            family="reliability_platform_fit",
        ),
    ]
    records = []
    for row in rows:
        value = get_term(terms, row)
        records.append(
            {
                "label": row.label,
                "platform": row.platform,
                "coef": value["coef"],
                "ci_low": value["ci_low"],
                "ci_high": value["ci_high"],
                "p_value": value["p_value"],
            }
        )
    data = pd.DataFrame(records)

    y = np.arange(len(data))[::-1]
    fig, ax = plt.subplots(figsize=(7.8, 5.0), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.85)
    for idx, row in data.iterrows():
        yy = y[idx]
        style = PLATFORM_STYLES[row["platform"]]
        xerr = None
        if np.isfinite(row["ci_low"]) and np.isfinite(row["ci_high"]):
            xerr = np.array([[row["coef"] - row["ci_low"]], [row["ci_high"] - row["coef"]]])
        ax.errorbar(
            row["coef"],
            yy,
            xerr=xerr,
            fmt=style["marker"],
            color=style["color"],
            ecolor=style["color"],
            elinewidth=1.5,
            capsize=3,
            markersize=6.5,
            zorder=3,
        )
        ax.text(
            0.205,
            yy,
            f"{row['coef']:.3f} ({p_label(row['p_value'])})",
            ha="left",
            va="center",
            fontsize=8.2,
            color="#333333",
        )

    labels = [f"{record['label']}\n{PLATFORM_STYLES[record['platform']]['label']}" for record in records]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(-0.18, 0.28)
    ax.set_xlabel("Interaction coefficient on transformed capacity utilisation")
    used_platforms = [p for p in PLATFORM_STYLES if p in set(data["platform"])]
    ax.legend(
        handles=platform_line_handles(used_platforms),
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
    )
    save_figure(fig, "fig01_key_mechanism_coefficients")


def trip_duration_salience_plot() -> None:
    terms, _ = load_results()
    records = []
    platforms = ["large_aggregator_only", "local_maas_only", "multi_platform"]
    for platform in platforms:
        for minutes in [5, 10, 15]:
            row = FigureRow(
                f"{minutes}-min total price",
                "I2_relative_total_price",
                f"total_price_{minutes}min_gap_to_same_mode_min_z:{platform}",
                platform,
                family=f"relative_total_price_{minutes}min",
            )
            value = get_term(terms, row)
            records.append(
                {
                    "minutes": minutes,
                    "platform": platform,
                    "coef": value["coef"],
                    "ci_low": value["ci_low"],
                    "ci_high": value["ci_high"],
                }
            )
    data = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(6.2, 3.9), layout="constrained")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.grid(axis="y", alpha=0.85)
    for platform, group in data.groupby("platform", sort=False):
        group = group.sort_values("minutes")
        style = PLATFORM_STYLES[platform]
        ax.plot(
            group["minutes"],
            group["coef"],
            marker=style["marker"],
            markersize=6.5,
            lw=2.0,
            linestyle=style["linestyle"],
            color=style["color"],
            label=style["label"],
        )
        ax.fill_between(
            group["minutes"].to_numpy(dtype=float),
            group["ci_low"].to_numpy(dtype=float),
            group["ci_high"].to_numpy(dtype=float),
            color=style["color"],
            alpha=0.10,
            linewidth=0,
        )
    ax.set_xticks([5, 10, 15])
    ax.set_xlabel("Assumed trip duration in total-price feature")
    ax.set_ylabel("Interaction coefficient")
    ax.legend(
        handles=platform_line_handles(platforms),
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
    )
    save_figure(fig, "fig02_trip_duration_price_salience")


def build_rank_data(terms: pd.DataFrame, specs: list[tuple[str, str]]) -> pd.DataFrame:
    platforms = ["large_aggregator_only", "local_maas_only", "multi_platform"]
    rows = []
    for metric, stem in specs:
        for platform in platforms:
            row = FigureRow(
                metric,
                "I6_cheapest_rank",
                f"{stem}:{platform}",
                platform,
                family="cheapest_rank_platform_fit",
            )
            value = get_term(terms, row)
            rows.append(
                {
                    "metric": metric,
                    "platform": platform,
                    "coef": value["coef"],
                    "ci_low": value["ci_low"],
                    "ci_high": value["ci_high"],
                }
            )
    return pd.DataFrame(rows)


def grouped_horizontal_bar_plot(
    data: pd.DataFrame,
    specs: list[tuple[str, str]],
    xlim: tuple[float, float],
    stem: str,
) -> None:
    platforms = ["large_aggregator_only", "local_maas_only", "multi_platform"]
    metric_order = [spec[0] for spec in specs]
    ybase = np.arange(len(metric_order))[::-1]
    bar_h = 0.22
    offsets = {"large_aggregator_only": -bar_h, "local_maas_only": 0.0, "multi_platform": bar_h}

    fig, ax = plt.subplots(figsize=(5.8, 2.9), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.8)
    for platform in platforms:
        group = data.loc[data["platform"].eq(platform)].copy()
        style = PLATFORM_STYLES[platform]
        ys = np.array([ybase[metric_order.index(m)] for m in group["metric"]]) + offsets[platform]
        ax.barh(
            ys,
            group["coef"],
            height=bar_h * 0.82,
            color=style["color"],
            alpha=0.92,
            label=style["label"],
            edgecolor="#222222",
            linewidth=0.45,
            hatch=style["hatch"],
        )
        for yy, (_, row) in zip(ys, group.iterrows(), strict=False):
            if np.isfinite(row["ci_low"]) and np.isfinite(row["ci_high"]):
                ax.plot([row["ci_low"], row["ci_high"]], [yy, yy], color="#222222", lw=0.9)
    ax.set_xlim(*xlim)
    ax.set_xlabel("Interaction coefficient")
    ax.set_yticks(ybase)
    ax.set_yticklabels(metric_order)
    ax.legend(
        handles=platform_bar_handles(platforms),
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
    )
    save_figure(fig, stem)


def price_rank_penalty_plot() -> None:
    terms, _ = load_results()
    specs = [
        ("Unlock-fee rank", "unlock_fee_rank_same_mode_day_z"),
        ("5-min total-price rank", "total_price_5min_rank_same_mode_z"),
    ]
    data = build_rank_data(terms, specs)
    grouped_horizontal_bar_plot(data, specs, (-0.16, 0.08), "fig03_price_rank_penalty")


def cheapest_position_benefit_plot() -> None:
    terms, _ = load_results()
    specs = [
        ("Cheapest unlock fee", "is_same_mode_cheapest_unlock_fee"),
        ("Cheapest 5-min total price", "is_same_mode_cheapest_total_price_5min"),
    ]
    data = build_rank_data(terms, specs)
    grouped_horizontal_bar_plot(data, specs, (-0.08, 0.24), "fig04_cheapest_position_benefit")


def demand_supply_outcome_plot(
    outcome: str,
    family: str,
    xlim: tuple[float, float],
    stem: str,
) -> None:
    terms, _ = load_results()
    features = [
        ("High unlock fee", "unlock_fee_ge_1_00", "unlock_fee_ge_1_00:local_maas_only"),
        (
            "10-min total-price gap",
            "total_price_10min_gap_to_same_mode_min_z",
            "total_price_10min_gap_to_same_mode_min_z:local_maas_only",
        ),
    ]

    y = np.array([1, 0])
    fig, ax = plt.subplots(figsize=(4.4, 2.8), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.8)
    for idx, (label, feature, term) in enumerate(features):
        value = get_term(
            terms,
            FigureRow(
                label,
                "I4_demand_supply_decomposition",
                term,
                "local_maas_only",
                family=family,
                feature=feature,
                outcome=outcome,
            ),
        )
        style = FEATURE_STYLES[feature]
        ax.errorbar(
            value["coef"],
            y[idx],
            xerr=np.array([[value["coef"] - value["ci_low"]], [value["ci_high"] - value["coef"]]]),
            fmt=style["marker"],
            color=style["color"],
            ecolor=style["color"],
            elinewidth=1.5,
            capsize=3,
            markersize=6.5,
        )
        ax.text(
            value["coef"],
            y[idx] + 0.16,
            p_label(value["p_value"]),
            ha="center",
            fontsize=7.5,
            color="#555555",
        )
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.5, 1.55)
    ax.set_yticks(y)
    ax.set_yticklabels([feature[0] for feature in features])
    ax.set_xlabel("Coefficient")
    save_figure(fig, stem)


def demand_supply_capacity_utilisation_plot() -> None:
    demand_supply_outcome_plot(
        "ur_boxcox",
        "decomposition_ur_boxcox",
        (-0.30, 0.08),
        "fig05_demand_supply_capacity_utilisation",
    )


def demand_supply_trip_volume_plot() -> None:
    demand_supply_outcome_plot(
        "log_trip_count_day",
        "decomposition_log_trip_count_day",
        (-1.35, 0.18),
        "fig06_demand_supply_trip_volume",
    )


def demand_supply_active_vehicles_plot() -> None:
    demand_supply_outcome_plot(
        "log_active_vehicles_day",
        "decomposition_log_active_vehicles_day",
        (-0.95, 0.18),
        "fig07_demand_supply_active_vehicles",
    )


def screening_map_plot() -> None:
    _, summary = load_results()
    counts = (
        summary.groupby(["idea", "idea_label"], as_index=False)
        .agg(
            negative_terms=("n_negative_sig_05", lambda s: int((s > 0).sum())),
            positive_terms=("n_positive_sig_05", lambda s: int((s > 0).sum())),
        )
        .sort_values(["negative_terms", "positive_terms"], ascending=[True, True])
    )
    label_map = {
        "I1_effective_price": "Effective price",
        "I2_relative_total_price": "Relative total price",
        "I3_short_last_mile": "Short/last-mile",
        "I4_demand_supply_decomposition": "Demand-supply",
        "I5_operational_reliability": "Availability",
        "I6_cheapest_rank": "Cheapest/rank",
        "I7_trip_purpose_fit": "Trip purpose",
        "I8_maturity_adaptation": "Maturity",
        "I9_outside_options": "Outside options",
        "I10_pass_promotion_softeners": "Pass/promo softeners",
    }
    counts["short_label"] = counts["idea"].map(label_map)
    y = np.arange(len(counts))

    fig, ax = plt.subplots(figsize=(7.0, 4.6), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.8)
    ax.barh(
        y,
        -counts["negative_terms"],
        color=ACCESSIBLE_PRINT_COLORS["blue"],
        alpha=0.92,
        label="Negative significant terms",
        edgecolor="#222222",
        linewidth=0.45,
        hatch="",
    )
    ax.barh(
        y,
        counts["positive_terms"],
        color=ACCESSIBLE_PRINT_COLORS["orange"],
        alpha=0.92,
        label="Positive significant terms",
        edgecolor="#222222",
        linewidth=0.45,
        hatch="xx",
    )
    for yy, (_, row) in zip(y, counts.iterrows(), strict=False):
        if row["negative_terms"]:
            ax.text(-row["negative_terms"] - 0.2, yy, str(row["negative_terms"]), ha="right", va="center", fontsize=8)
        if row["positive_terms"]:
            ax.text(row["positive_terms"] + 0.2, yy, str(row["positive_terms"]), ha="left", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(counts["short_label"])
    max_count = int(max(counts["negative_terms"].max(), counts["positive_terms"].max())) + 2
    ax.set_xlim(-max_count, max_count)
    ax.set_xlabel("Number of terms with at least one significant screening model")
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, "fig08_mechanism_screening_map")


def write_readme() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        """# Paper Figures

Generated by `python3 scripts/create_academic_figures.py`.

Figure files are caption-ready: no plot titles, subtitles, source notes, or
interpretive headlines are embedded in the image. Add titles in LaTeX captions
and combine panels later with LaTeX subfigures/subcaptions.

Figures:

- `fig01_key_mechanism_coefficients`: forest plot for the strongest mechanism coefficients.
- `fig02_trip_duration_price_salience`: line plot for trip-duration-specific relative price disadvantage.
- `fig03_price_rank_penalty`: standalone price-rank penalty panel.
- `fig04_cheapest_position_benefit`: standalone cheapest-position benefit panel.
- `fig05_demand_supply_capacity_utilisation`: standalone demand-supply panel for capacity utilisation.
- `fig06_demand_supply_trip_volume`: standalone demand-supply panel for trip volume.
- `fig07_demand_supply_active_vehicles`: standalone demand-supply panel for active vehicles.
- `fig08_mechanism_screening_map`: screening overview of which feature ideas generated signal.

Design choices:

- Matplotlib-only for reproducibility.
- One stable accessible print palette across figures.
- Color-vision-deficiency-friendly colors plus marker, line-style, and hatch redundancy for black-and-white printing.
- PDF and PNG exports for manuscript and preview use.
- Full-sample market-FE coefficients are used for the paper-facing mechanism plots because several unit-FE screening variants have rank-deficient covariance estimates.
""",
        encoding="utf-8",
    )


def create_academic_figures() -> None:
    configure_style()
    coefficient_plot()
    trip_duration_salience_plot()
    price_rank_penalty_plot()
    cheapest_position_benefit_plot()
    demand_supply_capacity_utilisation_plot()
    demand_supply_trip_volume_plot()
    demand_supply_active_vehicles_plot()
    screening_map_plot()
    write_readme()

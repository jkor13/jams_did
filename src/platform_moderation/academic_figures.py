"""Create paper-facing figures for platform-membership findings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from .config import OUTPUT_BASE, REPO_ROOT


OUT = REPO_ROOT / "docs/figures"
MECH = OUTPUT_BASE / "mechanism_feature_tests"


OKABE_ITO = {
    "orange": "#E69F00",
    "sky": "#56B4E9",
    "green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "black": "#000000",
}

PLATFORM_COLORS = {
    "large_aggregator_only": "#7A7A7A",
    "local_maas_only": OKABE_ITO["blue"],
    "multi_platform": OKABE_ITO["vermillion"],
}

PLATFORM_LABELS = {
    "large_aggregator_only": "Large aggregator",
    "local_maas_only": "Local MaaS",
    "multi_platform": "Multi-platform",
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
            "axes.titlesize": 12,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.8,
            "ytick.labelsize": 8.8,
            "legend.fontsize": 8.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "grid.color": "#D9D9D9",
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
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight")
    plt.close(fig)


def add_source_note(fig: plt.Figure, note: str) -> None:
    # Source details are kept in docs/figures/README.md and paper captions; placing
    # them inside compact panels made the exported figures harder to read.
    _ = (fig, note)


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
                "nobs": int(value["nobs"]),
            }
        )
    data = pd.DataFrame(records)

    y = np.arange(len(data))[::-1]
    fig, ax = plt.subplots(figsize=(8.4, 5.4), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.85)
    for idx, row in data.iterrows():
        yy = y[idx]
        color = PLATFORM_COLORS[row["platform"]]
        xerr = None
        if np.isfinite(row["ci_low"]) and np.isfinite(row["ci_high"]):
            xerr = np.array([[row["coef"] - row["ci_low"]], [row["ci_high"] - row["coef"]]])
        ax.errorbar(
            row["coef"],
            yy,
            xerr=xerr,
            fmt="o",
            color=color,
            ecolor=color,
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

    labels = [f"{r.label}\n{PLATFORM_LABELS[r.platform]}" for r in rows]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(-0.18, 0.28)
    ax.set_xlabel("Interaction coefficient on transformed capacity utilisation")
    ax.set_title("Platform contexts penalise visible short-trip price disadvantages", loc="left", pad=10)
    ax.text(
        -0.18,
        len(data) + 0.35,
        "Full sample, market fixed effects; points show focal interactions, whiskers show 95% CIs.",
        ha="left",
        va="bottom",
        fontsize=8.4,
        color="#555555",
    )
    handles = [
        Line2D([0], [0], marker="o", lw=0, color=color, label=PLATFORM_LABELS[key], markersize=6)
        for key, color in PLATFORM_COLORS.items()
        if key in set(data["platform"])
    ]
    ax.legend(handles=handles, frameon=False, loc="upper right", bbox_to_anchor=(1.0, 1.02), ncol=2)
    add_source_note(fig, "Source: results/mechanism_feature_tests/terms.csv")
    save_figure(fig, "fig01_key_mechanism_coefficients")


def trip_duration_salience_plot() -> None:
    terms, _ = load_results()
    records = []
    for platform in ["large_aggregator_only", "local_maas_only", "multi_platform"]:
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
                    "p_value": value["p_value"],
                }
            )
    data = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(7.2, 4.4), layout="constrained")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.grid(axis="y", alpha=0.85)
    for platform, group in data.groupby("platform"):
        group = group.sort_values("minutes")
        color = PLATFORM_COLORS[platform]
        ax.plot(
            group["minutes"],
            group["coef"],
            marker="o",
            markersize=6.5,
            lw=2.0,
            color=color,
            label=PLATFORM_LABELS[platform],
        )
        ax.fill_between(
            group["minutes"].to_numpy(dtype=float),
            group["ci_low"].to_numpy(dtype=float),
            group["ci_high"].to_numpy(dtype=float),
            color=color,
            alpha=0.14,
            linewidth=0,
        )
    ax.set_xticks([5, 10, 15])
    ax.set_xlabel("Assumed trip duration in total-price feature")
    ax.set_ylabel("Interaction coefficient")
    ax.set_title("Relative price disadvantage is strongest for short trips", loc="left", pad=10)
    ax.text(
        5,
        0.047,
        "Same-mode price gap to the cheapest visible alternative; full sample, market fixed effects.",
        ha="left",
        va="bottom",
        fontsize=8.4,
        color="#555555",
    )
    ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    add_source_note(fig, "Source: results/mechanism_feature_tests/terms.csv")
    save_figure(fig, "fig02_trip_duration_price_salience")


def price_rank_cheapest_plot() -> None:
    terms, _ = load_results()
    platforms = ["large_aggregator_only", "local_maas_only", "multi_platform"]
    rank_specs = [
        ("Unlock-fee rank", "unlock_fee_rank_same_mode_day_z"),
        ("5-min total-price rank", "total_price_5min_rank_same_mode_z"),
    ]
    cheapest_specs = [
        ("Cheapest unlock fee", "is_same_mode_cheapest_unlock_fee"),
        ("Cheapest 5-min total price", "is_same_mode_cheapest_total_price_5min"),
    ]

    def build(specs: list[tuple[str, str]]) -> pd.DataFrame:
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
                        "p_value": value["p_value"],
                    }
                )
        return pd.DataFrame(rows)

    rank_data = build(rank_specs)
    cheap_data = build(cheapest_specs)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.6), sharey=False, layout="constrained")
    bar_h = 0.22
    offsets = {"large_aggregator_only": -bar_h, "local_maas_only": 0.0, "multi_platform": bar_h}
    metric_order = [spec[0] for spec in rank_specs]
    ybase = np.arange(len(metric_order))[::-1]

    for ax, data, specs, title in [
        (axes[0], rank_data, rank_specs, "Penalty for worse same-mode price rank"),
        (axes[1], cheap_data, cheapest_specs, "Benefit of being the cheapest visible option"),
    ]:
        panel_metric_order = [spec[0] for spec in specs]
        panel_ybase = np.arange(len(panel_metric_order))[::-1]
        ax.axvline(0, color="#333333", lw=0.9)
        ax.grid(axis="x", alpha=0.8)
        for platform in platforms:
            group = data.loc[data["platform"].eq(platform)].copy()
            ys = np.array([panel_ybase[panel_metric_order.index(m)] for m in group["metric"]]) + offsets[platform]
            ax.barh(
                ys,
                group["coef"],
                height=bar_h * 0.82,
                color=PLATFORM_COLORS[platform],
                alpha=0.88,
                label=PLATFORM_LABELS[platform],
            )
            for y, (_, row) in zip(ys, group.iterrows(), strict=False):
                if np.isfinite(row["ci_low"]) and np.isfinite(row["ci_high"]):
                    ax.plot([row["ci_low"], row["ci_high"]], [y, y], color="#222222", lw=0.8)
        ax.set_title(title, loc="left")
        ax.set_xlabel("Interaction coefficient")
        ax.set_yticks(panel_ybase)
        ax.set_yticklabels(panel_metric_order)

    axes[0].set_xlim(-0.16, 0.08)
    axes[1].set_xlim(-0.08, 0.24)
    axes[1].legend(frameon=False, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.suptitle("Price rank, not only price level, carries the platform comparison mechanism", x=0.01, ha="left")
    add_source_note(fig, "Source: results/mechanism_feature_tests/terms.csv")
    save_figure(fig, "fig03_price_rank_and_cheapest_position")


def demand_supply_decomposition_plot() -> None:
    terms, _ = load_results()
    outcomes = [
        ("Capacity utilisation", "ur_boxcox", "decomposition_ur_boxcox", (-0.30, 0.08)),
        ("Trip volume", "log_trip_count_day", "decomposition_log_trip_count_day", (-1.35, 0.18)),
        ("Active vehicles", "log_active_vehicles_day", "decomposition_log_active_vehicles_day", (-0.95, 0.18)),
    ]
    features = [
        ("High unlock fee", "unlock_fee_ge_1_00", "unlock_fee_ge_1_00:local_maas_only"),
        (
            "10-min total-price gap",
            "total_price_10min_gap_to_same_mode_min_z",
            "total_price_10min_gap_to_same_mode_min_z:local_maas_only",
        ),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(10.0, 4.3), layout="constrained")
    y = np.array([1, 0])
    for ax, (title, outcome, family, xlim) in zip(axes, outcomes, strict=False):
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
            color = OKABE_ITO["blue"] if idx == 0 else OKABE_ITO["orange"]
            ax.errorbar(
                value["coef"],
                y[idx],
                xerr=np.array([[value["coef"] - value["ci_low"]], [value["ci_high"] - value["coef"]]]),
                fmt="o",
                color=color,
                ecolor=color,
                elinewidth=1.5,
                capsize=3,
                markersize=6.5,
            )
            ax.text(value["coef"], y[idx] + 0.16, p_label(value["p_value"]), ha="center", fontsize=7.5, color="#555555")
        ax.set_title(title)
        ax.set_xlim(*xlim)
        ax.set_ylim(-0.5, 1.55)
        ax.set_yticks(y)
        ax.set_yticklabels([f[0] for f in features] if ax is axes[0] else [])
        ax.set_xlabel("Coefficient")
    fig.suptitle("Local MaaS price frictions appear in utilisation, demand, and supply-side deployment", x=0.01, ha="left")
    add_source_note(fig, "Full sample, market fixed effects; outcome scales differ across panels. Source: results/mechanism_feature_tests/terms.csv")
    save_figure(fig, "fig04_demand_supply_decomposition")


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

    fig, ax = plt.subplots(figsize=(7.8, 4.8), layout="constrained")
    ax.axvline(0, color="#333333", lw=0.9)
    ax.grid(axis="x", alpha=0.8)
    ax.barh(y, -counts["negative_terms"], color=OKABE_ITO["blue"], alpha=0.85, label="Negative significant terms")
    ax.barh(y, counts["positive_terms"], color=OKABE_ITO["orange"], alpha=0.85, label="Positive significant terms")
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
    ax.set_title("Screening map: where the new feature ideas produced signal", loc="left", pad=10)
    ax.legend(frameon=False, loc="lower right")
    add_source_note(fig, "Counts summarise screening terms, not independent hypotheses. Source: results/mechanism_feature_tests/summary.csv")
    save_figure(fig, "fig05_mechanism_screening_map")


def write_readme() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text(
        """# Paper Figures

Generated by `python3 scripts/create_academic_figures.py`.

Figures:

- `fig01_key_mechanism_coefficients`: paper-facing forest plot for the strongest mechanism coefficients.
- `fig02_trip_duration_price_salience`: line plot showing that relative total-price disadvantage is strongest for short trips.
- `fig03_price_rank_and_cheapest_position`: price-rank penalty and cheapest-position benefit.
- `fig04_demand_supply_decomposition`: Local MaaS price-friction signals across utilisation, trip volume, and active-vehicle deployment.
- `fig05_mechanism_screening_map`: compact overview of which feature ideas generated signal.

Design choices:

- Matplotlib-only for reproducibility.
- Okabe-Ito-style colorblind-safe palette.
- PDF and PNG exports for manuscript and preview use.
- Full-sample market-FE coefficients are used for the paper-facing mechanism plots because several unit-FE screening variants have rank-deficient covariance estimates.
""",
        encoding="utf-8",
    )


def create_academic_figures() -> None:
    configure_style()
    coefficient_plot()
    trip_duration_salience_plot()
    price_rank_cheapest_plot()
    demand_supply_decomposition_plot()
    screening_map_plot()
    write_readme()

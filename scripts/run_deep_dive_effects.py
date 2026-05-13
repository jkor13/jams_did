#!/usr/bin/env python3
"""Run additional exploratory deep-dive effect probes."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.deep_dive_effects import run_deep_dive_effects


if __name__ == "__main__":
    run_deep_dive_effects()


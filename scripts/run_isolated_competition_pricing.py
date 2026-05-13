#!/usr/bin/env python3
"""Isolated competition tests for the pricing-friction mechanism."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.isolated_competition import run_isolated_competition


if __name__ == "__main__":
    run_isolated_competition()


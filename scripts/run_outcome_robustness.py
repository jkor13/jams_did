#!/usr/bin/env python3
"""Run outcome robustness for high-unlock-fee platform-type effects."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.outcome_robustness import run_outcome_robustness


if __name__ == "__main__":
    run_outcome_robustness()


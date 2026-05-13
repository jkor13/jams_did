#!/usr/bin/env python3
"""Run robustness checks for unlock-fee threshold effects."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.threshold_robustness import run_threshold_robustness


if __name__ == "__main__":
    run_threshold_robustness()


#!/usr/bin/env python3
"""Run feature-by-high-fee moderation tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.feature_fee_moderation import run_feature_fee_moderation


if __name__ == "__main__":
    run_feature_fee_moderation()


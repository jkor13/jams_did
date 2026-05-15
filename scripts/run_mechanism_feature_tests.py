#!/usr/bin/env python3
"""Run additional mechanism-feature screening tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.mechanism_feature_tests import run_mechanism_feature_tests


if __name__ == "__main__":
    run_mechanism_feature_tests()


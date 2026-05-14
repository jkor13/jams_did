#!/usr/bin/env python3
"""Run extended feature platform-effect tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.extended_feature_effects import run_extended_feature_effects


if __name__ == "__main__":
    run_extended_feature_effects()


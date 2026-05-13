#!/usr/bin/env python3
"""Run leave-one-city sensitivity checks for platform-type threshold effects."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.city_sensitivity import run_city_sensitivity


if __name__ == "__main__":
    run_city_sensitivity()


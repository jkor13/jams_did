#!/usr/bin/env python3
"""Run tests for underused marketing-mix features."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.underused_marketing_mix import run_underused_marketing_mix


if __name__ == "__main__":
    run_underused_marketing_mix()


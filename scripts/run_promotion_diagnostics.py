#!/usr/bin/env python3
"""Run support diagnostics for promotion-type findings."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.promotion_diagnostics import run_promotion_diagnostics


if __name__ == "__main__":
    run_promotion_diagnostics()


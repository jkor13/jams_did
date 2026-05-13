#!/usr/bin/env python3
"""Run maturity diagnostics for platform threshold effects."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.maturity_diagnostics import run_maturity_diagnostics


if __name__ == "__main__":
    run_maturity_diagnostics()


#!/usr/bin/env python3
"""Create paper-facing figures from the curated results."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.academic_figures import create_academic_figures


if __name__ == "__main__":
    create_academic_figures()


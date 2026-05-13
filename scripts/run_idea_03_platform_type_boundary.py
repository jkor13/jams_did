#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.idea_tests import run_idea


if __name__ == "__main__":
    run_idea("03_platform_type_boundary")


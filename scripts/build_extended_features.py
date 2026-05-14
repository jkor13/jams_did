#!/usr/bin/env python3
"""Build extended competition and marketing-mix feature tables."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from platform_moderation.extended_features import build_extended_features


if __name__ == "__main__":
    build_extended_features()


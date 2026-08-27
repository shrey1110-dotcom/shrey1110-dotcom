#!/usr/bin/env python3
"""Update README image cache-bust params so GitHub Camo refetches fresh SVGs."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

ASSETS = {
    "github-streak.svg": ROOT / "assets" / "github-streak.svg",
    "activity-graph.svg": ROOT / "assets" / "activity-graph.svg",
}

RAW = "https://raw.githubusercontent.com/shrey1110-dotcom/shrey1110-dotcom/main/assets"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main() -> None:
    text = README.read_text(encoding="utf-8")
    original = text

    streak_h = file_hash(ASSETS["github-streak.svg"])
    activity_h = file_hash(ASSETS["activity-graph.svg"])

    # Normalize streak image to absolute raw URL with content hash
    text = re.sub(
        r'<img src="[^"]*github-streak\.svg[^"]*"',
        f'<img src="{RAW}/github-streak.svg?v={streak_h}"',
        text,
        count=1,
    )
    text = re.sub(
        r'<img src="[^"]*activity-graph\.svg[^"]*"',
        f'<img src="{RAW}/activity-graph.svg?v={activity_h}"',
        text,
        count=1,
    )

    if text != original:
        README.write_text(text, encoding="utf-8")
        print(f"updated README cache bust streak={streak_h} activity={activity_h}")
    else:
        print("README cache bust already current")


if __name__ == "__main__":
    main()

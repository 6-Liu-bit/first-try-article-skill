#!/usr/bin/env python3
"""Fidelity check: verify every quoted span in a cards file exists verbatim in the source.

Usage:
    python tests/fidelity_check.py <source-article> <cards.md>

The check extracts every 「...」 span from the cards file and confirms it appears
(whitespace-insensitive) in the source article. A quote that cannot be found means
the card may have altered the original wording -- review it.

Exit code 0 = all quotes traceable; 1 = at least one quote not found.
"""

import re
import sys
from pathlib import Path

QUOTE = re.compile(r"「([^」]+)」")


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def extract_quotes(cards_text: str):
    return [q.strip() for q in QUOTE.findall(cards_text)]


def check(source_path: Path, cards_path: Path) -> int:
    source = normalize(source_path.read_text(encoding="utf-8"))
    cards_text = cards_path.read_text(encoding="utf-8")
    quotes = extract_quotes(cards_text)

    if not quotes:
        print(f"[WARN] {cards_path.name}: 未找到任何「」原文引用。")
        return 0

    missing = [q for q in quotes if normalize(q)[:40] not in source]
    print(f"原文引用检查：{cards_path.name} -> 共 {len(quotes)} 处引用")
    for q in quotes:
        ok = normalize(q)[:40] in source
        print(f"  [{'OK ' if ok else 'FAIL'}] {q[:50]}{'...' if len(q) > 50 else ''}")
    if missing:
        print(f"[FAIL] {len(missing)} 处引用无法在原文中定位，请核对是否改动了原文。")
        return 1
    print("[PASS] 所有引用均可在原文中逐字定位。")
    return 0


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    return check(Path(argv[1]), Path(argv[2]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))

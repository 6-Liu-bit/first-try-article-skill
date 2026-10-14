#!/usr/bin/env python3
"""Render a knowledge-card Markdown file into a standalone HTML card deck.

Usage:
    python render_deck.py <cards.md> [-o output.html] [-t "Deck Title"]

The input Markdown must follow the card format produced by first-try-article-skill:

    ## <title>
    **核心内容**
    ...
    **批注解释**
    ...

Only blocks that contain the `**核心内容**` marker are treated as cards, so an
optional overview section written with `##` is ignored.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = HERE.parent / "assets" / "card-deck.html"

CARD_HEADING = re.compile(r"^##\s+(.*\S)\s*$")
FIELD_CONTENT = re.compile(r"^\*\*核心内容\*\*\s*$")
FIELD_NOTE = re.compile(r"^\*\*批注解释\*\*\s*$")
RULE = re.compile(r"^-{3,}\s*$")


def parse_cards(md_text: str):
    """Split card Markdown into a list of {title, content, note} dicts."""
    cards = []
    cur = None
    mode = None  # "content" | "note" | None

    def flush():
        nonlocal cur
        if cur is not None and (cur["content"] or cur["note"]):
            cur["content"] = "\n".join(cur["content"]).strip()
            cur["note"] = "\n".join(cur["note"]).strip()
            cards.append(cur)
        cur = None

    for line in md_text.splitlines():
        m = CARD_HEADING.match(line)
        if m:
            flush()
            cur = {"title": m.group(1).strip(), "content": [], "note": []}
            mode = None
            continue
        if line.lstrip().startswith("#"):
            # heading of another level (e.g. '### section', '# doc title'): not a card, ignore
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if FIELD_CONTENT.match(stripped):
            mode = "content"
            continue
        if FIELD_NOTE.match(stripped):
            mode = "note"
            continue
        if RULE.match(stripped):
            continue
        if mode:
            cur[mode].append(line)

    flush()
    return cards


def render(cards_path: Path, out_path: Path, title: str, template_path: Path) -> Path:
    md_text = cards_path.read_text(encoding="utf-8")
    cards = parse_cards(md_text)
    if not cards:
        raise SystemExit(
            "No cards found. Make sure each card has a '## title' and a '**核心内容**' block."
        )

    template = template_path.read_text(encoding="utf-8")
    # Escape '</' so card text can never terminate the surrounding <script> block.
    payload = json.dumps(cards, ensure_ascii=False).replace("</", "<\\/")
    html_out = (
        template
        .replace("__DECK_TITLE__", html.escape(title))
        .replace("__CARDS_JSON__", payload)
    )
    out_path.write_text(html_out, encoding="utf-8")
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render knowledge cards to an HTML deck.")
    ap.add_argument("cards", help="path to the cards Markdown file")
    ap.add_argument("-o", "--output", help="output HTML path (default: alongside input)")
    ap.add_argument("-t", "--title", default="知识卡片", help="deck title")
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="HTML template path")
    args = ap.parse_args(argv)

    cards_path = Path(args.cards).resolve()
    if not cards_path.exists():
        raise SystemExit(f"Input not found: {cards_path}")
    title = args.title if args.title != "知识卡片" else cards_path.stem
    out_path = Path(args.output).resolve() if args.output else cards_path.with_suffix(".html")

    result = render(cards_path, out_path, title, Path(args.template))
    print(f"Rendered {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

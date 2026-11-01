#!/usr/bin/env python3
"""Unit sprite extractor.

Fetches the Conflict of Nations widgets stylesheet, downloads the sprite
sheets it references, and crops every selected sprite into output/units.
"""

import argparse
import io
import urllib.request
from pathlib import Path

from PIL import Image

from parse import BASE_CSS_URL, Filter, positions, spritesheets

# Very important! urllib is notorious for being blocked by servers.
# This header tells the server we're a real browser (lying)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/css,*/*;q=0.1",
}

OUTPUT_DIR = Path(__file__).parent / ".." / "output" / "units"


def fetch(url: str) -> bytes:
    """Single transport funnel for every upstream request."""
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch unit sprites from the Conflict of Nations client."
    )
    parser.add_argument(
        "families",
        nargs="*",
        metavar="FAMILY",
        help="unit families to fetch (e.g. infantry tank); wildcards allowed, "
        "all families fetched when omitted",
    )
    parser.add_argument(
        "-g", "--generations", nargs="+", metavar="GEN",
        help="only fetch these generations (e.g. a b c)",
    )
    parser.add_argument(
        "-d", "--doctrines", nargs="+", metavar="DOCTRINE",
        help="only fetch these doctrines (e.g. 0 1 2)",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list available unit families and exit without downloading images",
    )
    return parser.parse_args()


def list_families(sprites: dict[str, list[dict]]) -> None:
    for family in sorted(sprites):
        entries = sprites[family]
        generations = sorted({e["generation"] or "-" for e in entries})
        doctrines = sorted({e["doctrine"] or "-" for e in entries})
        print(
            f"{family}: {len(entries)} sprites "
            f"(generations: {', '.join(generations)}; doctrines: {', '.join(doctrines)})"
        )


def main() -> None:
    args = parse_args()

    print("Fetching CSS...")
    css = fetch(BASE_CSS_URL).decode("utf-8")

    sprites = positions(css, Filter(
        families=frozenset(f.lower() for f in args.families),
        generations=frozenset(args.generations or ()),
        doctrines=frozenset(args.doctrines or ()),
    ))

    list_families(sprites)
    if not sprites:
        print("No sprites matched the given filters.")

    # Dry run won't write anything.
    if args.list or not sprites:
        return

    needed = {e["doctrine"] for entries in sprites.values() for e in entries}
    sheets: dict[str, Image.Image] = {}
    for doctrine, url in spritesheets(css).items():
        if doctrine not in needed:
            continue
        print(f"  [{doctrine}] {url}")
        sheets[doctrine] = Image.open(io.BytesIO(fetch(url)))

    total = 0
    for family, entries in sprites.items():
        for e in entries:
            sheet = sheets.get(e["doctrine"])
            if sheet is None:
                continue
            sprite = sheet.crop(
                (e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"])
            )
            name = family + "".join(
                f"_{v}" for v in (e["generation"], e["doctrine"]) if v
            )
            path = OUTPUT_DIR / family / f"{name}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            sprite.save(path)
            print(path)
            total += 1

    print(f"Wrote {total} sprite images to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

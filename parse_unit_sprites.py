#!/usr/bin/env python3
"""Unit Sprite Extractor

Downloads and extracts unit sprite images from the Conflict of Nations client.

Author: cet
Date: 2026-09-27

This module is the entry point for the tool. It fetches the game's published
widgets stylesheet, parses the unit sprite rules that stylesheet declares,
downloads the sprite sheets those rules reference, and crops every selected
sprite into its own image under the repository's output/units directory.

No starter code was supplied for this project. The sprite rule pattern and the
sprite sheet discovery logic were written against the live widgets-built.css
published by the game client. Pillow handles image decoding and cropping; every
other operation relies on the Python standard library.

Usage:
    python3 parse_unit_sprites.py --help
"""

import argparse
import fnmatch
import re
import urllib.request
from pathlib import Path

from PIL import Image

BASE_URL = "https://www.conflictnations.com/clients/con-client/con-client_live/"
BASE_CSS_URL = BASE_URL + "css/widgets-built.css"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/css,*/*;q=0.1",
}

def parse_args() -> argparse.Namespace:
    """Parse the command line arguments that select which assets to fetch.

    Returns:
        The parsed arguments, including the requested family patterns and the
        optional generation and doctrine filters.
    """
    parser = argparse.ArgumentParser(
        description="Fetch unit sprites from the Conflict of Nations client."
    )
    parser.add_argument(
        "families",
        nargs="*",
        metavar="FAMILY",
        help=(
            "unit families to fetch (e.g. infantry tank); wildcards are allowed "
            "and all families are fetched when omitted"
        ),
    )
    parser.add_argument(
        "-g",
        "--generations",
        nargs="+",
        metavar="GEN",
        help="only fetch these generations (e.g. a b c)",
    )
    parser.add_argument(
        "-d",
        "--doctrines",
        nargs="+",
        metavar="DOCTRINE",
        help="only fetch these doctrines (e.g. 0 1 2)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available unit families and exit without downloading images",
    )
    return parser.parse_args()


def fetch_css(url: str) -> str:
    """Download the stylesheet that declares the sprite rules.

    Args:
        url: Address of the stylesheet to download.

    Returns:
        The decoded stylesheet text.
    """
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def get_spritesheets(css: str) -> dict[str, str]:
    """Find the sprite sheet image URLs declared in the stylesheet.

    Args:
        css: Stylesheet text to search.

    Returns:
        A mapping of doctrine digit to absolute sprite sheet URL.
    """
    pattern = re.compile(r"\.\./(images/sprites/units-(\d).+?\.png)'")
    sheets: dict[str, str] = {}
    for match in pattern.finditer(css):
        rel = match.group(1)
        doctrine = match.group(2)
        sheets[doctrine] = BASE_URL + rel
    return sheets


def fetch_image(url: str) -> Image.Image:
    """Download a sprite sheet and open it as an image.

    Args:
        url: Address of the sprite sheet to download.

    Returns:
        The opened sprite sheet image.
    """
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return Image.open(response)

def matches_family(family: str, patterns: list[str]) -> bool:
    """Check whether a unit family is selected by the requested patterns.

    Args:
        family: Unit family name parsed from the stylesheet.
        patterns: Requested family patterns; empty selects every family.

    Returns:
        True when no patterns were requested or any pattern matches the family.
    """
    return not patterns or any(
        fnmatch.fnmatchcase(family, pattern) for pattern in patterns
    )


def get_positions(
    css: str,
    patterns: list[str],
    generations: list[str],
    doctrines: list[str],
) -> dict:
    """Parse the sprite rules for the unit assets the caller asked for.

    Rules that do not match the requested families, generations, and doctrines
    are skipped while the stylesheet is scanned, so unselected sprites are never
    collected in the first place.

    Args:
        css: Stylesheet text to parse.
        patterns: Requested family patterns; empty selects every family.
        generations: Requested generations; empty selects every generation.
        doctrines: Requested doctrines; empty selects every doctrine.

    Returns:
        A mapping of unit family to its list of sprite position entries.
    """
    sprite_pattern = re.compile(
        r"\.units-([a-z0-9_]+?)_([abc]*(?=[^a-z]))_?([a-z]*)_?(\d*)_?big\s*\{(.+?)\}"
    )

    sprites: dict[str, list[dict]] = {}

    for match in sprite_pattern.finditer(css):
        family = match.group(1)
        generation = match.group(2)
        # Variant does exist sometimes, usually as "air", but is insanely inconsistent
        # and not worth trying to actually parse into anything truly meaningful.
        # For consistency with versions that lack generation, we treat it like part of the family.
        variant = match.group(3)
        if variant:
            family += "_" + variant
        doctrine = match.group(4)
        body = match.group(5)

        if not matches_family(family, patterns):
            continue
        if generations and generation not in generations:
            continue
        if doctrines and doctrine not in doctrines:
            continue
        if (body.find("background-position") == -1):
            continue

        # Extract all digit sequences from the body, ignoring minus signs.
        # Expected order: x, y, height, width.
        nums = re.findall(r"\d+", body)
        if len(nums) < 4:
            continue

        entry = sprites.setdefault(family, [])
        entry.append({
            "x": int(nums[0]),
            "y": int(nums[1]),
            "height": int(nums[2]),
            "width": int(nums[3]),
            "generation": generation,
            "doctrine": doctrine
        })

    return sprites


def list_families(sprites: dict[str, list[dict]]) -> None:
    """Print the available unit families and the variants each one contains.

    Args:
        sprites: Mapping of unit family to its sprite position entries.
    """
    for family in sorted(sprites):
        entries = sprites[family]
        generations = sorted({block["generation"] or "-" for block in entries})
        doctrines = sorted({block["doctrine"] or "-" for block in entries})
        print(
            f"{family}: {len(entries)} sprites "
            f"(generations: {', '.join(generations)}; doctrines: {', '.join(doctrines)})"
        )


def main():
    """Fetch, filter, download, and crop the requested unit sprites."""
    args = parse_args()

    print("Fetching CSS...")
    css = fetch_css(BASE_CSS_URL)
    print(f"Fetched {len(css):,} bytes.")

    print("Discovering spritesheets...")
    spritesheets = get_spritesheets(css)
    print(f"Found {len(spritesheets)} sprite sheets.")

    print("Parsing sprite rules...")
    if args.list:
        list_families(get_positions(css, [], [], []))
        return

    patterns = [family.lower() for family in args.families]
    sprites = get_positions(css, patterns, args.generations or [], args.doctrines or [])
    print(f"Parsed {len(sprites)} unit sprite entries.")

    if not sprites:
        print("No sprites matched the given filters.")
        return

    needed_doctrines = {
        block.get("doctrine", "0")
        for entries in sprites.values()
        for block in entries
    }

    output_dir = Path(__file__).with_suffix("").parent / ".." / "output" / "units"

    print("Downloading spritesheets...")
    sheet_images: dict[str, Image.Image] = {}
    for doctrine, url in spritesheets.items():
        if doctrine not in needed_doctrines:
            continue
        print(f"  [{doctrine}] {url}")
        sheet_images[doctrine] = fetch_image(url)

    print("Extracting sprites...")
    total = 0
    for family, entries in sprites.items():
        for block in entries:
            generation = block.get("generation", "")
            doctrine = block.get("doctrine", "0")

            sheet = sheet_images.get(doctrine)
            if sheet is None:
                continue

            x = block["x"]
            y = block["y"]
            w = block["width"]
            h = block["height"]
            sprite = sheet.crop((x, y, x + w, y + h))

            filename = f"{family}"
            if generation:
                filename += f"_{generation}"
            if doctrine:
                filename += f"_{doctrine}"

            sprite_path = output_dir / family / (filename + ".png")
            print(sprite_path)
            sprite_path.parent.mkdir(parents=True, exist_ok=True)
            sprite.save(sprite_path)
            total += 1

    print(f"Wrote {total} sprite images to {output_dir}")


if __name__ == "__main__":
    main()

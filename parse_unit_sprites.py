#!/usr/bin/env python3
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


def fetch_css(url: str) -> str:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def get_spritesheets(css: str) -> dict[str, str]:
    pattern = re.compile(r"\.\./(images/sprites/units-(\d).+?\.png)'")
    sheets: dict[str, str] = {}
    for match in pattern.finditer(css):
        rel = match.group(1)
        doctrine = match.group(2)
        sheets[doctrine] = BASE_URL + rel
    return sheets


def fetch_image(url: str) -> Image.Image:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return Image.open(response)

def get_positions(css: str) -> dict:
    pattern = re.compile(
        r"\.units-([a-z0-9_]+?)_([abc]*(?=[^a-z]))_?([a-z]*)_?(\d*)_?big\s*\{(.+?)\}"
    )

    sprites: dict[str, list[dict]] = {}

    for match in pattern.finditer(css):
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


def main():
    print("Fetching CSS...")
    css = fetch_css(BASE_CSS_URL)
    print(f"Fetched {len(css):,} bytes.")

    print("Discovering spritesheets...")
    spritesheets = get_spritesheets(css)
    print(f"Found {len(spritesheets)} sprite sheets.")

    print("Parsing sprite rules...")
    sprites = get_positions(css)
    print(f"Parsed {len(sprites)} unit sprite entries.")
    print(f"Wrote {OUT_PATH}")

    output_dir = Path(__file__).with_suffix("").parent / ".." / "output" / "units"

    print("Downloading spritesheets...")
    sheet_images: dict[str, Image.Image] = {}
    for doctrine, url in spritesheets.items():
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

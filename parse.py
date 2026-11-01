"""Parse unit sprite rules from the Conflict of Nations widgets stylesheet."""

import fnmatch
import re
from dataclasses import dataclass

BASE_URL = "https://www.conflictnations.com/clients/con-client/con-client_live/"
BASE_CSS_URL = BASE_URL + "css/widgets-built.css"

_SHEET_RE = re.compile(r"\.\./(images/sprites/units-(\d).+?\.png)'")
_SPRITE_RE = re.compile(
    r"\.units-([a-z0-9_]+?)_([abc]*(?=[^a-z]))_?([a-z]*)_?(\d*)_?big\s*\{(.+?)\}"
)


@dataclass(frozen=True)
class Filter:
    """Selects sprite rules; empty fields accept everything."""

    families: tuple[str, ...] = ()
    generations: frozenset[str] = frozenset()
    doctrines: frozenset[str] = frozenset()

    def accepts(self, family: str, generation: str, doctrine: str) -> bool:
        return (
            (
                not self.families
                or any(fnmatch.fnmatchcase(family, p) for p in self.families)
            )
            and (not self.generations or generation in self.generations)
            and (not self.doctrines or doctrine in self.doctrines)
        )


def spritesheets(css: str) -> dict[str, str]:
    """Map each doctrine digit to its absolute sprite sheet URL."""
    return {m.group(2): BASE_URL + m.group(1) for m in _SHEET_RE.finditer(css)}


def positions(css: str, flt: Filter = Filter()) -> dict[str, list[dict]]:
    """Map each unit family to the sprite position entries the filter accepts.

    Entry keys: x, y, width, height, generation, doctrine.
    """
    sprites: dict[str, list[dict]] = {}
    for m in _SPRITE_RE.finditer(css):
        family, generation, variant, doctrine, body = m.groups()
        # Variant exists sometimes, usually as "air", but is insanely inconsistent
        # and not worth parsing into anything meaningful.
        if variant:
            family += "_" + variant

        # Check if this sprite matches the filter criteria.
        if not flt.accepts(family, generation, doctrine):
            continue

        # If there's no background-position, we can't extract the sprite position.
        if "background-position" not in body:
            continue

        nums = re.findall(r"\d+", body)
        # Should always have at least 4 numbers (x, y, width, height)
        if len(nums) < 4:
            continue

        sprites.setdefault(family, []).append({
            "x": int(nums[0]),
            "y": int(nums[1]),
            "height": int(nums[2]),
            "width": int(nums[3]),
            "generation": generation,
            "doctrine": doctrine,
        })
    return sprites

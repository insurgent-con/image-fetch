"""Tests for the sprite rule parser.

Uses a fixed set of spritesheets and rules to test the parser.
"""

import parse

LIVE_CSS = """\
.units-camo_infantry_1_big,.units-camo_ship_1_big{background-image:url('../images/sprites/units-1-sed23dae8d1.png');background-repeat:no-repeat}
.units-bone_crusher_4_big{background-image:url('../images/sprites/units-4-s2adc2c91d5.png');background-repeat:no-repeat}
.units-camo_infantry_1_big{background-position:0 -10138px;height:134px;width:212px}
.units-mercenary_a_big{background-position:-212px -336px;height:134px;width:212px}
.units-air_superiority_fighter_a_1_big{background-position:0 -5180px;height:134px;width:212px}
.units-air_superiority_fighter_a_air_1_big{background-position:0 -5314px;height:134px;width:212px}
.units-camo_infantry_big{background-position:-602px -1px;height:134px;width:212px}
.units-bad_1_big{background-position:-10px -20px}
"""


def test_spritesheets_maps_doctrines_to_absolute_urls():
  """Sheet URLs are resolved against the client base URL per doctrine digit."""
  assert parse.spritesheets(LIVE_CSS) == {
    "1": parse.BASE_URL + "images/sprites/units-1-sed23dae8d1.png",
    "4": parse.BASE_URL + "images/sprites/units-4-s2adc2c91d5.png",
  }


def test_positions_parses_live_rule_format():
  """Rules parse into x, y, height, width entries in the live declaration order."""
  sprites = parse.positions(LIVE_CSS)
  assert sprites["camo_infantry"] == [{
    "x": 0,
    "y": 10138,
    "height": 134,
    "width": 212,
    "generation": "",
    "doctrine": "1",
  }]
  assert sprites["air_superiority_fighter"] == [{
    "x": 0,
    "y": 5180,
    "height": 134,
    "width": 212,
    "generation": "a",
    "doctrine": "1",
  }]


def test_positions_skips_non_sprite_rules():
  """Image-only rules and rules without four numbers are ignored."""
  sprites = parse.positions(LIVE_CSS)
  assert set(sprites) == {
    "camo_infantry",
    "mercenary",
    "air_superiority_fighter",
    "air_superiority_fighter_air",
  }


def test_positions_ignores_rules_without_doctrine_digit():
  """Digit-less rules such as .units-camo_infantry_big are not extracted."""
  assert len(parse.positions(LIVE_CSS)["camo_infantry"]) == 1


def test_positions_folds_variant_into_family():
  """The optional variant segment is appended to the family name."""
  sprites = parse.positions(LIVE_CSS)
  assert sprites["air_superiority_fighter_air"][0]["generation"] == "a"
  assert sprites["air_superiority_fighter_air"][0]["doctrine"] == "1"


def test_positions_filters_by_family_glob():
  """Family patterns match with wildcards and skip unrelated families."""
  sprites = parse.positions(LIVE_CSS, parse.Filter(families=frozenset({"*infantry*"})))
  assert set(sprites) == {"camo_infantry"}


def test_positions_filters_by_generation():
  """Generation filters drop rules without a matching generation."""
  sprites = parse.positions(LIVE_CSS, parse.Filter(generations=frozenset({"a"})))
  assert set(sprites) == {
    "mercenary",
    "air_superiority_fighter",
    "air_superiority_fighter_air",
  }


def test_positions_filters_by_doctrine():
  """Doctrine filters drop rules without a matching doctrine."""
  sprites = parse.positions(LIVE_CSS, parse.Filter(doctrines=frozenset({"1"})))
  assert set(sprites) == {
    "camo_infantry",
    "air_superiority_fighter",
    "air_superiority_fighter_air",
  }


def test_positions_applies_all_filters_together():
  """Family, generation, and doctrine criteria must all match."""
  sprites = parse.positions(LIVE_CSS, parse.Filter(
    families=frozenset({"*fighter*"}),
    generations=frozenset({"a"}),
    doctrines=frozenset({"1"}),
  ))
  assert set(sprites) == {"air_superiority_fighter", "air_superiority_fighter_air"}


def test_filter_accepts_everything_when_empty():
  """An empty filter accepts any rule."""
  assert parse.Filter().accepts("camo_infantry", "", "")


def test_filter_accepts_requires_all_criteria():
  """A populated filter rejects rules that miss any criterion."""
  flt = parse.Filter(
    families=frozenset({"*fighter*"}),
    generations=frozenset({"a"}),
    doctrines=frozenset({"1"}),
  )
  assert flt.accepts("air_superiority_fighter", "a", "1")
  assert not flt.accepts("air_superiority_fighter", "b", "1")
  assert not flt.accepts("air_superiority_fighter", "a", "2")
  assert not flt.accepts("camo_infantry", "a", "1")

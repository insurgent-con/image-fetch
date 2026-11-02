"""Tests for the fetch, list, and crop pipeline in init.py.

The stylesheet fixture mirrors the live rule format (see test_parse), and the
sprite sheet is generated locally so the tests stay offline.
"""

import io
import sys

from PIL import Image

import init
from parse import BASE_CSS_URL

CSS = """\
.units-bone_crusher_4_big,.units-bone_crusher_4_small{background-image:url('../images/sprites/units-4-s2adc2c91d5.png');background-repeat:no-repeat}
.units-bone_crusher_4_big{background-position:0 -134px;height:134px;width:212px}
"""


def make_sheet() -> bytes:
  """Build a sheet whose bone_crusher sprite region is painted red."""
  sheet = Image.new("RGB", (212, 300), "black")
  sheet.paste("red", (0, 134, 212, 268))
  buffer = io.BytesIO()
  sheet.save(buffer, format="PNG")
  return buffer.getvalue()


def fake_fetch(url: str) -> bytes:
  """Serve the stylesheet fixture and a generated sprite sheet."""
  return CSS.encode() if url == BASE_CSS_URL else make_sheet()


def test_parse_args_defaults(monkeypatch):
  """No arguments selects every family with no filters."""
  monkeypatch.setattr(sys, "argv", ["init.py"])
  args = init.parse_args()
  assert args.families == []
  assert args.generations is None
  assert args.doctrines is None
  assert args.list is False


def test_parse_args_collects_filters(monkeypatch):
  """Family patterns and generation/doctrine filters are collected verbatim."""
  monkeypatch.setattr(
    sys, "argv",
    ["init.py", "Infantry", "-g", "a", "b", "-d", "1", "--list"],
  )
  args = init.parse_args()
  assert args.families == ["Infantry"]
  assert args.generations == ["a", "b"]
  assert args.doctrines == ["1"]
  assert args.list is True


def test_list_families_prints_summary(capsys):
  """Each family line reports sprite count, generations, and doctrines."""
  init.list_families({
    "camo_infantry": [
      {"generation": "b", "doctrine": "1"},
      {"generation": "", "doctrine": "2"},
    ],
  })
  assert capsys.readouterr().out == (
    "camo_infantry: 2 sprites (generations: -, b; doctrines: 1, 2)\n"
  )


def test_main_writes_cropped_sprites(tmp_path, monkeypatch):
  """The pipeline crops the sprite region and names the file after the family."""
  monkeypatch.setattr(init, "OUTPUT_DIR", tmp_path)
  monkeypatch.setattr(init, "fetch", fake_fetch)
  monkeypatch.setattr(sys, "argv", ["init.py", "bone_crusher"])

  init.main()

  sprite_path = tmp_path / "bone_crusher" / "bone_crusher_4.png"
  assert sprite_path.exists()
  with Image.open(sprite_path) as sprite:
    assert sprite.size == (212, 134)
    assert sprite.getpixel((0, 0)) == (255, 0, 0)


def test_main_lowercases_family_patterns(tmp_path, monkeypatch):
  """Family patterns from the command line are matched case-insensitively."""
  monkeypatch.setattr(init, "OUTPUT_DIR", tmp_path)
  monkeypatch.setattr(init, "fetch", fake_fetch)
  monkeypatch.setattr(sys, "argv", ["init.py", "BONE_CRUSHER"])

  init.main()

  assert (tmp_path / "bone_crusher" / "bone_crusher_4.png").exists()


def test_main_list_writes_nothing(tmp_path, monkeypatch, capsys):
  """--list prints the family summary and stops before the write phase."""
  monkeypatch.setattr(init, "OUTPUT_DIR", tmp_path)
  monkeypatch.setattr(init, "fetch", fake_fetch)
  monkeypatch.setattr(sys, "argv", ["init.py", "--list"])

  init.main()

  assert "bone_crusher: 1 sprites" in capsys.readouterr().out
  assert list(tmp_path.iterdir()) == []


def test_main_reports_no_matches(tmp_path, monkeypatch, capsys):
  """Unmatched filters print a message and write nothing."""
  monkeypatch.setattr(init, "OUTPUT_DIR", tmp_path)
  monkeypatch.setattr(init, "fetch", fake_fetch)
  monkeypatch.setattr(sys, "argv", ["init.py", "nonexistent"])

  init.main()

  assert "No sprites matched the given filters." in capsys.readouterr().out
  assert list(tmp_path.iterdir()) == []

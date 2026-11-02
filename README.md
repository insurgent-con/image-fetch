# Image Fetch

> [!CAUTION]
>
> Do not use, redistribute, or publish downloaded assets for any purpose unauthorized by Twin Harbor or another party that owns the relevant intellectual property.

This repository contains development tooling for retrieving and processing image assets associated with Conflict of Nations / Supremacy WW3. The current utility extracts unit sprites from the game's published CSS and sprite sheets.

## Status

This is a small development utility, not a complete release or asset-distribution pipeline. Generated output is ignored by Git and should be reviewed before it is copied into another repository or application.

The parser depends on the structure and availability of live upstream CSS and image resources. A change to those resources can cause extraction to fail or produce incomplete output.

## Requirements

- Python 3
- Pillow
- Network access to the configured upstream resources
- Permission to retrieve and process the relevant resources

The standard library handles HTTP requests and filesystem operations; Pillow is used to open and crop sprite sheets, and pytest runs the test suite. Install the dependencies with:

```sh
python3 -m pip install -r requirements.txt
```

## Usage

From this repository:

```sh
python3 init.py
```

The script downloads the CSS and sprite sheets it is configured to use, discovers unit sprite positions, and writes generated images under the repository workspace's `output/units` directory. The generated directory is intentionally ignored by Git.

By default every discovered unit sprite is fetched. To fetch only specific assets, pass unit family names or wildcard patterns as arguments, optionally combined with `--generations` and `--doctrines` filters:

```sh
# List the families that can be fetched, then exit
python3 init.py --list

# Fetch only the infantry and tank families
python3 init.py infantry tank

# Fetch every family whose name contains "infantry"
python3 init.py '*infantry*'

# Fetch only generations a and b of doctrine 1
python3 init.py -g a b -d 1
```

When filters are given, sprite sheets that are not needed for the selected assets are skipped rather than downloaded.

## Testing

Fixtures mirror the rule format of the live stylesheet, and sprite sheets are generated in-memory, so no network access is required:

```sh
python3 -m pytest
```

## License

The repository code is licensed under [AGPL-3.0](LICENSE.txt). That license does not grant rights to third-party game assets downloaded by the scripts.

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

The standard library handles HTTP requests and filesystem operations; Pillow is used to open and crop sprite sheets.

## Usage

From this repository:

```sh
python3 parse_unit_sprites.py
```

The script downloads the CSS and sprite sheets it is configured to use, discovers unit sprite positions, and writes generated images under the repository workspace's `output/units` directory. The generated directory is intentionally ignored by Git.

## Operational Notes

- The source URL and request headers are currently defined by the script.
- The script performs live downloads and may retrieve multiple sprite sheets.
- The output is generated data and should not be committed by default.
- There is currently no asset manifest, checksum inventory, or offline fixture suite.
- Review source provenance and permitted use before copying any output into `api` or `client`.

## Safe Development Practices

Do not commit:

- Credentials or authenticated browser data.
- Private or personal information.
- Unreviewed game-derived assets.
- Generated output that lacks provenance or permission.

When investigating a parser change, keep a small local fixture rather than repeatedly downloading upstream resources where possible. Any fixture intended for the repository must be reviewed for both licensing and redistribution concerns.

## License

The repository code is licensed under [AGPL-3.0](LICENSE.txt). That license does not grant rights to third-party game assets downloaded by the scripts.

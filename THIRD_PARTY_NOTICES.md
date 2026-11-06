# Third-party notices

## Catppuccin palette

`palette/mocha.json` extracts the Mocha `colors.*.hex` values from the official Catppuccin palette.
The generated overlay and the independent test constants reproduce those color values.

- Upstream: https://github.com/catppuccin/palette
- Revision: `07d02aa110ef9eb7e7427afca5c73ba9cf7f8ebd`
- File: `palette.json`
- Recorded original-file SHA-256: `4bc114bb6b3c9a9c9e156564aa84625aef32c5da514d9dd431cf1fcad433a05f`
- License: MIT
- Copyright (c) 2021 Catppuccin

The complete upstream permission notice is in `palette/LICENSE`.
Retain that notice when redistributing the palette or substantial derived material.
The generated CSS includes a short attribution header. That header does not replace the complete license notice.

## AFFiNE and its theme package

This project refers to application token identifiers and version metadata from these sources:

- AFFiNE `0.27.4`, commit `b4c8548c09da21b2898443559a5b846f0ccf5dd8`:
  https://github.com/toeverything/AFFiNE/tree/b4c8548c09da21b2898443559a5b846f0ccf5dd8
- `@toeverything/theme` `1.1.23`, design commit `8851de3927b48eeb23ae374360ca0f97b11cd93b`:
  https://github.com/toeverything/design/tree/8851de3927b48eeb23ae374360ca0f97b11cd93b/packages/theme/src

The public repository does not distribute the full upstream application CSS, JavaScript, HTML, or application data.
It does not relicense AFFiNE, the theme package, or any assets in a locally created bundle.
Those materials keep their own upstream licenses and notices.
The repository's MIT license applies to this project's original work, not to every byte of a derived application bundle.

Keep local source CSS and derived bundles outside version control.
Review the applicable upstream licenses before distributing a bundle.

AFFiNE and Catppuccin names identify compatibility and palette origin.
This project has no claimed endorsement or official affiliation.

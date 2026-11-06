"""Build a dependency-free AFFiNE Mocha UI overlay from a pinned palette.

All application identifiers are checked against @toeverything/theme 1.1.23.
Content palettes, typography, dimensions and media rendering are not overridden.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "affine-catppuccin-mocha.css"
SELECTOR = ':root:root, [data-theme="light"][data-theme], [data-theme="dark"][data-theme]'
# Aliases are deliberately explicit. Do not guess token names or normalize case.
GROUPS = {
    "base": """
        background-primary-color
        v2-layer-background-primary
        v2-layer-background-mobile-primary
        v2-selfhost-layer-background-primary
        v2-centerPeek-background
    """,
    "mantle": """
        background-code-block
        v2-layer-background-codeBlock
        v2-selfhost-layer-background-sidebarBg-sidebarBg
        v2-selfhost-layer-background-secondary
        v2-layer-background-mobile-secondary
        v2-database-filterHeaderFadeIn
    """,
    "surface0": """
        background-secondary-color background-overlay-panel-color tertiary-color
        v2-layer-background-secondary v2-layer-background-overlayPanel
        v2-layer-background-linkedDocOnEdgeless v2-layer-background-mobile-tertiary
        v2-dialog-background-primary v2-centerPeek-buttonBackground
        v2-input-background v2-button-secondary v2-button-iconButtonSolid
        v2-button-signinbutton-background v2-button-mobile-aIActionBackground
        v2-button-grabber-default v2-button-sidebarButton-background
        v2-button-siderbarPrimary-background v2-button-emptyIconBackground
        v2-segment-background v2-slashMenu-background v2-skeleton-skeleton
        v2-switch-switchBackground-background v2-tab-tabBackground-default
        v2-tab-tabBackground-hover v2-toast-cardLayer-second v2-toast-cardLayer-third
        v2-table-headerBackground-default v2-table-headerBackground-headerColor
        v2-tableOfContent-background v2-selfhost-button-disable
        v2-selfhost-button-secondary v2-readwise-quoteBackground
        v2-block-notSupportedBlock-background v2-block-notSupportedBlock-inlineBg-default
        v2-chatBlock-chatBlockBg v2-aI-userTextBackground
    """,
    "surface1": """
        border-color background-tertiary-color hover-color-filled
        v2-layer-insideBorder-border v2-layer-insideBorder-blackBorder
        v2-layer-insideBorder-whiteBorder v2-input-border-default
        v2-button-innerBlackBorder v2-button-buttonOverHover v2-button-grabber-select
        v2-button-actionActive v2-segment-button v2-database-border
        v2-database-buttonBackground v2-database-attachment-fileSolidBackground
        v2-workspacePicker-border v2-workspacePicker-secondaryBackground
        v2-switch-buttonBackground-active v2-switch-buttonBackground-hover
        v2-tab-tabBackground-active v2-tab-divider-divider v2-table-border
        v2-table-indicator-border v2-table-indicator-drag v2-table-indicator-hover
        v2-selfhost-button-sidebarButton-bg-hover v2-selfhost-button-sidebarButton-bg-select
        v2-selfhost-toggle-backgroundDisable v2-toggle-backgroundDisable
        v2-block-notSupportedBlock-inlineBg-hover v2-chatBlock-chatBlockBoder
        v2-backlinks-blockBorder v2-backlinks-blockHover
    """,
    "surface2": """
        divider-color button-gray-color
        v2-pagelist-hoverBorder v2-icon-fileIconBorder
        v2-input-scrollBar-handle v2-toggle-backgroundOff
        v2-selfhost-layer-border-border v2-selfhost-toggle-backgroundOff
        v2-block-divider-divider v2-block-footnote-numberBg
    """,
    "text": """
        black text-primary-color tooltip
        v2-text-primary v2-icon-primary v2-layer-black
        v2-tab-fontColor-active v2-tab-fontColor-hover
        v2-switch-fontColor-primary v2-selfhost-icon-primary
        v2-selfhost-text-sidebar-primary v2-selfhost-progress-primary
        v2-chatBlock-chatBlockText v2-tooltips-foreground
        v2-adjustmentHandle-border
    """,
    "subtext1": """
        icon-color v2-icon-secondary v2-centerPeek-icon
        v2-switch-iconColor-active v2-tab-iconColor-active v2-tab-iconColor-hover
        v2-selfhost-icon-secondary v2-selfhost-text-sidebar-secondary
        v2-chatBlock-chatBlockIcon v2-table-indicator-pointerDefault
    """,
    "subtext0": """
        icon-secondary placeholder-color quote-color list-color text-secondary-color
        v2-text-secondary v2-text-tertiary v2-text-placeholder
        v2-icon-monotone v2-icon-tertiary v2-tab-fontColor-default
        v2-tab-iconColor-default v2-switch-fontColor-secondary
        v2-switch-fontColor-tertiary v2-switch-iconColor-default
        v2-database-textSecondary v2-table-textSecondary
        v2-selfhost-icon-tertiary v2-selfhost-text-placeholder
        v2-block-code-lineNum v2-radio-active-default
    """,
    "overlay0": """
        text-disable-color v2-text-disable v2-icon-disable v2-button-disable
        v2-selfhost-icon-disable v2-radio-disable v2-toggle-foregroundDisable
        v2-selfhost-toggle-foregroundDisable
    """,
    "mauve": """
        brand-color primary-color text-emphasis-color
        v2-button-primary v2-button-checkBox v2-icon-activated
        v2-text-emphasis v2-input-border-active v2-layer-insideBorder-primaryBorder
        v2-tab-divider-indicator v2-radio-active-chekced
        v2-toggle-background v2-selfhost-toggle-backgroundOn
        v2-selfhost-button-primary v2-loading-foreground
        v2-table-focusBorder v2-table-indicator-activated
        v2-readwise-quoteDivider v2-block-footnote-numberBgHover
    """,
    "lavender": "secondary-color v2-text-listDotAndNumber v2-block-list-header",
    "blue": "link-color processing-color v2-text-link v2-toast-iconState-regular v2-badge-free v2-badge-pro",
    "green": "success-color v2-status-success v2-button-success v2-toast-iconState-success",
    "red": """
        error-color v2-status-error v2-button-error v2-toast-iconState-error
        v2-input-border-error v2-button-badgesColor v2-button-mobile-deletedAction
        v2-selfhost-progress-error
    """,
    "yellow": "warning-color v2-others-warnLabel-yellow",
    "crust": """
        white v2-layer-white v2-button-pureWhiteText v2-selfhost-icon-buttonIcon
        v2-selfhost-icon-buttonIconError v2-selfhost-text-button-primary
        v2-selfhost-text-button-error v2-toggle-foreground v2-selfhost-toggle-foreground
        v2-others-warnLabel-black
    """,
}


def rgba(hex_color: str, alpha: float) -> str:
    channels = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    return f"rgba({channels[0]}, {channels[1]}, {channels[2]}, {alpha:g})"


def mappings() -> dict[str, str]:
    tokens: dict[str, str] = {}
    def add(name: str, value: str) -> None:
        key = "--affine-" + name
        if key in tokens:
            raise ValueError(f"Duplicate mapping: {key}")
        tokens[key] = value
    for color, names in GROUPS.items():
        for name in names.split():
            add(name, f"var(--ctp-mocha-{color})")
    colors = json.loads((ROOT / "palette/mocha.json").read_text(encoding="utf-8"))["colors"]
    for prefix, color in (("black", "text"), ("white", "crust")):
        for opacity in (10, 30, 50, 60, 80, 90):
            add(f"{prefix}-{opacity}", rgba(colors[color], opacity / 100))
    for name, color, opacity in (
        ("hover-color", "text", 0.08),
        ("primary-color-04", "mauve", 0.12),
        ("background-modal-color", "crust", 0.72),
        ("v2-layer-background-modal", "crust", 0.72),
        ("v2-layer-background-mobile-modal", "crust", 0.72),
        ("v2-layer-background-modalWhite", "text", 0.10),
        ("v2-layer-background-translucentUI", "mantle", 0.94),
        ("v2-layer-background-hoverOverlay", "text", 0.08),
        ("v2-selfhost-layer-background-hoverOverlay", "text", 0.08),
        ("v2-centerPeek-overlay", "crust", 0.72),
        ("v2-database-cardHover", "text", 0.06),
        ("v2-database-focusBackground", "mauve", 0.12),
        ("v2-table-focusBackground", "mauve", 0.12),
        ("v2-backlinks-blockBackgroundColor", "text", 0.06),
        ("v2-loading-background", "text", 0.12),
        ("v2-loading-backgroundLayer", "surface2", 0.9),
        ("v2-tooltips-secondaryBackground", "text", 0.12),
        ("v2-icon-transparentBlack", "text", 0.72),
        ("v2-database-filterHeaderFadeOut", "base", 0.03),
    ):
        add(name, rgba(colors[color], opacity))
    # Semantic washes are composited on Base, not arbitrary invented colors.
    for status, color in (("success", "green"), ("warning", "yellow"), ("error", "red"), ("processing", "blue")):
        foreground = tuple(int(colors[color][i:i + 2], 16) for i in (1, 3, 5))
        background = tuple(int(colors["base"][i:i + 2], 16) for i in (1, 3, 5))
        wash = "#" + "".join(f"{round(a * .14 + b * .86):02x}" for a, b in zip(foreground, background))
        add(f"background-{status}-color", wash)
        add(f"v2-layer-background-{status}", wash)
    add("v2-tooltips-background", "var(--ctp-mocha-surface1)")
    return tokens


def render() -> str:
    palette = json.loads((ROOT / "palette/mocha.json").read_text(encoding="utf-8"))
    known = set(json.loads((ROOT / "compatibility/upstream-token-names.json").read_text(encoding="utf-8"))["variables"])
    tokens = mappings()
    unknown = sorted(set(tokens) - known)
    if unknown:
        raise ValueError(f"Unverified upstream variables: {unknown}")
    lines = [
        "/*! AFFiNE Catppuccin Mocha v1.0.0 | MIT | Copyright (c) 2026 EiraWalker",
        " * Palette: Copyright (c) 2021 Catppuccin | MIT",
        " * Verified target: AFFiNE 0.27.4 / @toeverything/theme 1.1.23.",
        " * Mocha UI in both native appearances; print and forced colors are untouched.",
        " * Do not override content palettes, fonts, geometry, media, or SVG artwork.",
        " */",
        "@media screen and (forced-colors: none) {",
        f"  {SELECTOR} {{",
        '    --affine-catppuccin-mocha-version: "1.0.0";',
        "    color-scheme: dark !important; /* next-themes sets this inline. */",
    ]
    for name, value in palette["colors"].items():
        lines.append(f"    --ctp-mocha-{name}: {value};")
    for name, value in sorted(tokens.items()):
        lines.append(f"    {name}: {value};")
    lines.extend([
        "  }",
        "  /* Stable application hooks; colors only, never generated class names. */",
        '  :root:root [data-testid="app-sidebar-wrapper"] {',
        "    background-color: var(--ctp-mocha-mantle);",
        "  }",
        "}",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed CSS is stale")
    args = parser.parse_args()
    expected = render().encode("utf-8")
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != expected:
            raise SystemExit("CSS is stale; run python scripts/build.py")
        print(f"CSS is reproducible ({len(mappings())} verified application tokens).")
    else:
        OUTPUT.write_bytes(expected)
        print(f"Built {OUTPUT.name}: {len(mappings())} application tokens, {len(expected)} bytes.")


if __name__ == "__main__":
    main()

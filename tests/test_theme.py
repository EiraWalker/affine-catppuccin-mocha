"""Offline contract tests for the generated overlay. Python standard library only."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mocha_build", ROOT / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

# Independent transcription of mocha.colors.*.hex from the pinned official palette.
OFFICIAL = {
    "rosewater": "#f5e0dc", "flamingo": "#f2cdcd", "pink": "#f5c2e7",
    "mauve": "#cba6f7", "red": "#f38ba8", "maroon": "#eba0ac",
    "peach": "#fab387", "yellow": "#f9e2af", "green": "#a6e3a1",
    "teal": "#94e2d5", "sky": "#89dceb", "sapphire": "#74c7ec",
    "blue": "#89b4fa", "lavender": "#b4befe", "text": "#cdd6f4",
    "subtext1": "#bac2de", "subtext0": "#a6adc8", "overlay2": "#9399b2",
    "overlay1": "#7f849c", "overlay0": "#6c7086", "surface2": "#585b70",
    "surface1": "#45475a", "surface0": "#313244", "base": "#1e1e2e",
    "mantle": "#181825", "crust": "#11111b",
}
SELECTOR = ':root:root, [data-theme="light"][data-theme], [data-theme="dark"][data-theme]'
HOOK = ':root:root [data-testid="app-sidebar-wrapper"]'
VARIABLE = re.compile(r"var\((--[A-Za-z0-9_-]+)\)")


def parse_overlay(css):
    """Accept only the small stylesheet grammar owned by this project."""
    clean = re.sub(r"/\*.*?\*/", "", css, flags=re.S).strip()
    prefix = "@media screen and (forced-colors: none) {"
    if not clean.startswith(prefix) or not clean.endswith("}"):
        raise ValueError("overlay must use the screen/forced-colors boundary")
    inner = clean[len(prefix):-1].strip()
    rules = []
    while inner:
        match = re.match(r"([^{}]+)\{([^{}]*)\}\s*", inner)
        if not match:
            raise ValueError("unexpected nested rule or invalid stylesheet")
        declarations = []
        for item in match[2].split(";"):
            if not item.strip():
                continue
            declaration = re.fullmatch(r"\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*", item, re.S)
            if not declaration:
                raise ValueError("invalid declaration")
            declarations.append(declaration.groups())
        rules.append((match[1].strip(), declarations))
        inner = inner[match.end():]
    return rules


def color(value, variables, seen=()):
    """Resolve the deliberately limited color syntax emitted by build.py."""
    match = VARIABLE.fullmatch(value)
    if match:
        name = match[1]
        if name in seen:
            raise ValueError("cyclic variable: " + name)
        return color(variables[name], variables, (*seen, name))
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)) + (1.0,)
    match = re.fullmatch(r"rgba\((\d+), (\d+), (\d+), (0(?:\.\d+)?|1(?:\.0+)?)\)", value)
    if match:
        channels = tuple(int(match[i]) / 255 for i in (1, 2, 3))
        if any(not 0 <= c <= 1 for c in channels):
            raise ValueError("invalid channel")
        return channels + (float(match[4]),)
    raise ValueError("unsupported color: " + value)


def composite(foreground, background):
    alpha = foreground[3]
    return tuple(alpha * a + (1 - alpha) * b for a, b in zip(foreground[:3], background[:3])) + (1.0,)


def contrast(a, b):
    def luminance(rgb):
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb[:3]]
        return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))
    lighter, darker = sorted((luminance(a), luminance(b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css_bytes = (ROOT / "affine-catppuccin-mocha.css").read_bytes()
        cls.css = cls.css_bytes.decode("utf-8")
        cls.rules = parse_overlay(cls.css)
        cls.variables = dict(cls.rules[0][1])
        cls.palette = json.loads((ROOT / "palette/mocha.json").read_text(encoding="utf-8"))
        cls.upstream = json.loads((ROOT / "compatibility/upstream-token-names.json").read_text(encoding="utf-8"))

    def c(self, name):
        return color(self.variables[name], self.variables, (name,))

    def assert_contrast(self, foreground, background, label, minimum=4.5):
        ratio = contrast(foreground, background)
        self.assertGreaterEqual(ratio, minimum, f"{label}: {ratio:.4f}:1 < {minimum}:1")

    def test_reproducible_bytes_across_processes_and_hash_seeds(self):
        self.assertEqual(self.css_bytes, build.render().encode("utf-8"))
        command = [sys.executable, "-X", "utf8", "-c",
                   "import sys; sys.path.insert(0, 'scripts'); import build; sys.stdout.buffer.write(build.render().encode('utf-8'))"]
        for seed in ("1", "982451653"):
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONHASHSEED": seed},
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, self.css_bytes)
            self.assertEqual(result.stderr, b"")

    def test_build_check_cli_matches_committed_artifact(self):
        result = subprocess.run([sys.executable, "-X", "utf8", "scripts/build.py", "--check"],
                                cwd=ROOT, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        self.assertIn(b"CSS is reproducible", result.stdout)

    def test_official_palette_values_and_recorded_provenance(self):
        self.assertEqual(self.palette["colors"], OFFICIAL)
        self.assertEqual(self.palette["name"], "Catppuccin Mocha")
        self.assertEqual(self.palette["license"], "MIT")
        self.assertEqual(self.palette["source"], {
            "repository": "https://github.com/catppuccin/palette",
            "revision": "07d02aa110ef9eb7e7427afca5c73ba9cf7f8ebd",
            "path": "palette.json",
            "sha256": "4bc114bb6b3c9a9c9e156564aa84625aef32c5da514d9dd431cf1fcad433a05f",
            "extraction": "mocha.colors.*.hex",
        })
        actual = {key.removeprefix("--ctp-mocha-"): value for key, value in self.variables.items()
                  if key.startswith("--ctp-mocha-")}
        self.assertEqual(actual, OFFICIAL)
        notice = (ROOT / "palette/LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2021 Catppuccin", notice)
        self.assertIn("Permission is hereby granted", notice)

    def test_application_mappings_use_only_pinned_upstream_names(self):
        self.assertEqual(self.upstream["affine"], {
            "version": "0.27.4", "revision": "b4c8548c09da21b2898443559a5b846f0ccf5dd8"})
        self.assertEqual(self.upstream["theme"], {
            "package": "@toeverything/theme", "version": "1.1.23",
            "revision": "8851de3927b48eeb23ae374360ca0f97b11cd93b",
            "source": "https://github.com/toeverything/design/tree/8851de3927b48eeb23ae374360ca0f97b11cd93b/packages/theme/src"})
        known = self.upstream["variables"]
        self.assertEqual(len(known), 639)
        self.assertEqual(known, sorted(set(known)))
        actual = {key: value for key, value in self.variables.items()
                  if key.startswith("--affine-") and key != "--affine-catppuccin-mocha-version"}
        self.assertTrue(actual)
        self.assertLessEqual(actual.keys(), set(known))
        self.assertEqual(actual, build.mappings())

    def test_no_duplicate_declarations_or_dangling_or_cyclic_variables(self):
        for selector, declarations in self.rules:
            counts = Counter(name for name, _ in declarations)
            self.assertEqual([name for name, count in counts.items() if count != 1], [], selector)
            for name, value in declarations:
                for reference in VARIABLE.findall(value):
                    self.assertIn(reference, self.variables, (selector, name, reference))
                if name.startswith("--") and name != "--affine-catppuccin-mocha-version":
                    color(value, self.variables, (name,))

    def test_screen_only_selectors_and_one_native_color_scheme_exception(self):
        self.assertEqual([selector for selector, _ in self.rules], [SELECTOR, HOOK])
        self.assertEqual(self.variables["--affine-catppuccin-mocha-version"], '"1.0.0"')
        expected = set(build.mappings()) | {"--ctp-mocha-" + name for name in OFFICIAL}
        expected |= {"--affine-catppuccin-mocha-version", "color-scheme"}
        self.assertEqual(set(self.variables), expected)
        self.assertEqual(self.variables["color-scheme"], "dark !important")
        important = [(name, value) for _, declarations in self.rules for name, value in declarations
                     if re.search(r"!\s*important", value, re.I)]
        self.assertEqual(important, [("color-scheme", "dark !important")])
        self.assertEqual(self.rules[1][1], [("background-color", "var(--ctp-mocha-mantle)")])

    def test_no_resources_geometry_typography_or_global_media_effects(self):
        clean = re.sub(r"/\*.*?\*/", "", self.css, flags=re.S)
        self.assertNotRegex(clean, r"(?i)url\s*\(|@import|@font-face|@namespace|expression\s*\(|javascript:|\\")
        allowed = {"color-scheme", "background-color"}
        for _, declarations in self.rules:
            for name, value in declarations:
                self.assertTrue(name.startswith("--") or name in allowed, (name, value))
        forbidden = re.compile(r"(?i)(?:^--affine-font-|font-(?:family|size|weight)|line-height|editor-width|editor-side-padding|radius|z-index|shadow|cursor|spacing|padding|margin|zoom|scale)")
        for name in build.mappings():
            self.assertIsNone(forbidden.search(name), name)

    def test_preserves_content_palettes_and_semantic_categories(self):
        protected = re.compile(
            r"^--affine-(?:text-highlight-|palette-|note-background-|tag-|card-background-|multi-players-|"
            r"(?:blue|green|grey|magenta|orange|pink|purple|red|teal|yellow)(?:-|$)|"
            r"v2-(?:text-highlight-|edgeless-|block-callout-|block-frame-|chip-label-|chip-tag-|calendar-))")
        preserved = {name for name in self.upstream["variables"] if protected.search(name)}
        self.assertGreater(len(preserved), 100)
        self.assertEqual(set(build.mappings()) & preserved, set())

    def test_primary_text_contrast_on_neutral_layers(self):
        for foreground in ("--affine-text-primary-color", "--affine-v2-text-primary"):
            for background in ("base", "mantle", "crust", "surface0", "surface1", "surface2"):
                with self.subTest(foreground=foreground, background=background):
                    self.assert_contrast(self.c(foreground), self.c("--ctp-mocha-" + background), foreground + "/" + background)

    def test_secondary_and_placeholder_contrast_on_text_and_input_layers(self):
        # Surface1/2 are borders, separators and selected controls, not assumed text surfaces.
        for foreground in ("--affine-text-secondary-color", "--affine-placeholder-color",
                           "--affine-v2-text-secondary", "--affine-v2-text-tertiary",
                           "--affine-v2-text-placeholder", "--affine-v2-selfhost-text-placeholder"):
            for background in ("--affine-background-primary-color", "--affine-background-secondary-color",
                               "--affine-v2-layer-background-primary", "--affine-v2-layer-background-secondary",
                               "--affine-v2-input-background", "--ctp-mocha-mantle", "--ctp-mocha-crust"):
                with self.subTest(foreground=foreground, background=background):
                    self.assert_contrast(self.c(foreground), self.c(background), foreground + "/" + background)

    def test_semantic_foregrounds_on_base_and_corresponding_washes(self):
        for status in ("error", "success", "warning", "processing"):
            foreground = self.c(f"--affine-{status}-color")
            for background in ("--ctp-mocha-base", f"--affine-background-{status}-color",
                               f"--affine-v2-layer-background-{status}"):
                with self.subTest(status=status, background=background):
                    self.assert_contrast(foreground, self.c(background), status + "/" + background)
        for foreground in ("--affine-link-color", "--affine-v2-text-link", "--affine-v2-text-emphasis"):
            for background in ("base", "mantle", "surface0"):
                self.assert_contrast(self.c(foreground), self.c("--ctp-mocha-" + background), foreground + "/" + background)

    def test_filled_button_labels_default_overlay_and_opacity_hover(self):
        text = self.c("--affine-v2-button-pureWhiteText")
        overlay = self.c("--affine-v2-layer-background-hoverOverlay")
        pairs = [("--affine-v2-button-" + kind, text) for kind in ("primary", "error", "success")]
        pairs += [("--affine-v2-selfhost-button-primary", self.c("--affine-v2-selfhost-text-button-primary"))]
        for background_name, label_color in pairs:
            fill = self.c(background_name)
            with self.subTest(button=background_name, state="default"):
                self.assert_contrast(label_color, fill, background_name)
            # Component button uses a hoverOverlay pseudo-element above its fill.
            hover_fill = composite(overlay, fill)
            self.assert_contrast(label_color, hover_fill, background_name + "/overlay-hover")
            # Test the 0.9 fill-alpha hover without incorrectly fading its text.
            # Also check the more conservative whole-control opacity variant.
            for parent_name in ("base", "mantle", "crust", "surface0", "surface1"):
                parent = self.c("--ctp-mocha-" + parent_name)
                alpha_fill = composite(fill[:3] + (0.9,), parent)
                self.assert_contrast(label_color, alpha_fill, background_name + "/fill-alpha-hover/" + parent_name)
                label = composite(label_color[:3] + (0.9,), parent)
                for state, background in (("opacity-hover", fill), ("combined-hover", hover_fill)):
                    background = composite(background[:3] + (0.9,), parent)
                    with self.subTest(button=background_name, state=state, parent=parent_name):
                        self.assert_contrast(label, background, background_name + "/" + state + "/" + parent_name)

    def test_focus_indicators_use_non_text_contrast_threshold(self):
        for foreground in ("--affine-v2-input-border-active", "--affine-v2-layer-insideBorder-primaryBorder",
                           "--affine-v2-input-border-error"):
            for background in ("base", "mantle", "surface0", "surface1"):
                with self.subTest(foreground=foreground, background=background):
                    self.assert_contrast(self.c(foreground), self.c("--ctp-mocha-" + background),
                                         foreground + "/" + background, minimum=3.0)

    def test_contrast_math_reference_and_negative_controls(self):
        black, white = color("#000000", {}), color("#ffffff", {})
        self.assertAlmostEqual(contrast(black, white), 21.0)
        self.assertEqual(contrast(white, white), 1.0)
        self.assertEqual(composite(white[:3] + (0.0,), black), black)
        with self.assertRaises(ValueError):
            color("var(--loop)", {"--loop": "var(--loop)"})
        with self.assertRaises(KeyError):
            color("var(--missing)", {})
        with self.assertRaises(ValueError):
            parse_overlay("@media print { :root { color: red; } }")


if __name__ == "__main__":
    unittest.main()

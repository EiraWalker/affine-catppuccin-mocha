"""Offline bundle safety tests. The input CSS is an explicit synthetic fixture."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = b'''/* Synthetic application CSS, not an upstream distribution. */
:root { --affine-text-primary-color: #eee; --affine-background-primary-color: #141414;
--affine-v2-layer-background-primary: #141414; --affine-v2-button-primary: #123456;
--affine-v2-text-primary: #eeeeee; --affine-font-family: sans-serif; }
body { color: var(--affine-text-primary-color); }
'''


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="affine-mocha-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "original.css"
        self.output = self.directory / "derived.css"
        self.source.write_bytes(SOURCE)
        self.options = {
            "source_sha256": hashlib.sha256(SOURCE).hexdigest(),
            "affine_version": "0.27.4",
            "theme_version": "1.1.23",
        }

    def module(self):
        path = ROOT / "scripts/bundle.py"
        self.assertTrue(path.is_file(), "bundle helper has not been implemented")
        spec = importlib.util.spec_from_file_location("mocha_bundle", path)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / "scripts"))
        self.addCleanup(lambda: sys.path.remove(str(ROOT / "scripts")))
        spec.loader.exec_module(module)
        return module

    def test_appends_original_theme_bytes_without_changing_source(self):
        self.module().create_bundle(self.source, self.output, **self.options)
        theme = (ROOT / "affine-catppuccin-mocha.css").read_bytes()
        self.assertEqual(self.output.read_bytes(), SOURCE + b"\n" + theme)
        self.assertEqual(self.source.read_bytes(), SOURCE)

    def test_rejects_unreviewed_source_digest_before_writing(self):
        self.options["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.module().create_bundle(self.source, self.output, **self.options)
        self.assertFalse(self.output.exists())

    def test_preflight_rejects_wrong_versions_html_broken_css_and_rebundling(self):
        cases = [
            (SOURCE, {"affine_version": "0.28.0"}, "version"),
            (SOURCE, {"theme_version": "1.1.24"}, "version"),
            (b"<!doctype html><html>login</html>", {}, "CSS"),
            (b'{"error":"not found"}', {}, "CSS"),
            (b"body { color: red; }", {}, "CSS"),
            (SOURCE + b"/* never closed", {}, "CSS"),
            (SOURCE + b"body { color: red;", {}, "CSS"),
            (SOURCE + b'body { content: "unterminated; }', {}, "CSS"),
            (SOURCE + b"\x00", {}, "CSS"),
            (SOURCE + b"\xff", {}, "CSS"),
            (SOURCE + b"\n/* AFFiNE Catppuccin Mocha */", {}, "already"),
            (SOURCE + (ROOT / "affine-catppuccin-mocha.css").read_bytes(), {}, "already"),
        ]
        module = self.module()
        for payload, changes, message in cases:
            with self.subTest(changes=changes, payload=payload[:30], message=message):
                self.output.unlink(missing_ok=True)
                self.source.write_bytes(payload)
                options = {**self.options, "source_sha256": hashlib.sha256(payload).hexdigest(), **changes}
                with self.assertRaisesRegex(ValueError, message):
                    module.create_bundle(self.source, self.output, **options)
                self.assertFalse(self.output.exists())
                self.assertEqual(self.source.read_bytes(), payload)

    def test_rejects_existing_output_and_source_alias(self):
        module = self.module()
        self.output.write_bytes(b"keep this existing file")
        with self.assertRaises((ValueError, FileExistsError)):
            module.create_bundle(self.source, self.output, **self.options)
        self.assertEqual(self.output.read_bytes(), b"keep this existing file")
        with self.assertRaises((ValueError, FileExistsError)):
            module.create_bundle(self.source, self.source, **self.options)
        self.assertEqual(self.source.read_bytes(), SOURCE)
        hardlink = self.directory / "hardlink.css"
        try:
            hardlink.hardlink_to(self.source)
        except OSError:
            self.skipTest("filesystem does not support hard links")
        with self.assertRaises((ValueError, FileExistsError)):
            module.create_bundle(self.source, hardlink, **self.options)
        self.assertEqual(self.source.read_bytes(), SOURCE)

    def test_cli_success_and_negative_controls(self):
        command = [sys.executable, "-X", "utf8", str(ROOT / "scripts/bundle.py"),
                   "--source", str(self.source), "--output", str(self.output),
                   "--source-sha256", self.options["source_sha256"],
                   "--affine-version", "0.27.4", "--theme-version", "1.1.23"]
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.output.exists())
        self.assertIn(hashlib.sha256(self.output.read_bytes()).hexdigest().encode(), result.stdout)
        result = subprocess.run(command, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(b"Traceback", result.stderr)
        result = subprocess.run(command[:4], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_stale_theme_in_an_isolated_checkout(self):
        checkout = self.directory / "checkout"
        for item in ("scripts/build.py", "scripts/bundle.py", "palette/mocha.json",
                     "compatibility/upstream-token-names.json", "affine-catppuccin-mocha.css"):
            destination = checkout / item
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / item, destination)
        theme = checkout / "affine-catppuccin-mocha.css"
        theme.write_bytes(theme.read_bytes() + b"/* stale overlay */\n")
        command = [sys.executable, "-X", "utf8", str(checkout / "scripts/bundle.py"),
                   "--source", str(self.source), "--output", str(self.output),
                   "--source-sha256", self.options["source_sha256"],
                   "--affine-version", "0.27.4", "--theme-version", "1.1.23"]
        result = subprocess.run(command, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"stale", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), SOURCE)

    def test_lexical_guard_accepts_quoted_delimiters_but_rejects_comment_only_anchors(self):
        module = self.module()
        payload = SOURCE + b'''body::before { content: " } [ ( /* "; background: url("data:image/svg+xml,<svg/>"); }'''
        self.source.write_bytes(payload)
        options = {**self.options, "source_sha256": hashlib.sha256(payload).hexdigest()}
        module.create_bundle(self.source, self.output, **options)
        self.assertEqual(self.output.read_bytes()[:len(payload)], payload)
        self.output.unlink()
        payload = b"/* " + SOURCE.replace(b"/*", b" ").replace(b"*/", b" ") + b" */ body { color: red; }"
        self.source.write_bytes(payload)
        options["source_sha256"] = hashlib.sha256(payload).hexdigest()
        with self.assertRaisesRegex(ValueError, "declarations"):
            module.create_bundle(self.source, self.output, **options)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()

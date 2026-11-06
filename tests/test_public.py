"""Public packaging checks. No Git, network, or third-party Python modules required."""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = {
    ".gitattributes", ".gitignore", "README.md", "LICENSE", "THIRD_PARTY_NOTICES.md",
    "affine-catppuccin-mocha.css", "palette/mocha.json", "palette/LICENSE",
    "compatibility/upstream-token-names.json", "scripts/build.py", "scripts/bundle.py",
    "tests/test_theme.py", "tests/test_bundle.py", "tests/test_public.py",
    "docs/install.md", "docs/preview.png", "docs/settings.png", ".github/workflows/test.yml",
}


class PublicPackageTests(unittest.TestCase):
    def test_gitignore_is_exact_public_allowlist(self):
        lines = [line.strip() for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.startswith("#")]
        self.assertEqual(lines[0], "*")
        self.assertTrue(all(line.startswith("!/") for line in lines[1:]))
        self.assertTrue(all(not re.search(r"[*?\[\]]", line) for line in lines[1:]))
        allowed = {line[2:] for line in lines[1:] if not line.endswith("/")}
        directories = {line[2:-1] for line in lines[1:] if line.endswith("/")}
        expected_directories = {parent.as_posix() for item in PUBLIC for parent in Path(item).parents
                                if parent != Path(".")}
        self.assertEqual(allowed, PUBLIC)
        self.assertEqual(directories, expected_directories)
        self.assertEqual(len(lines), len(set(lines)))
        for item in PUBLIC:
            self.assertTrue((ROOT / item).is_file(), item)

    def test_complete_mit_notices_are_retained(self):
        own = (ROOT / "LICENSE").read_text(encoding="utf-8")
        palette = (ROOT / "palette/LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 EiraWalker", own)
        self.assertIn("Copyright (c) 2021 Catppuccin", palette)
        permission = "Permission is hereby granted"
        self.assertEqual(own[own.index(permission):], palette[palette.index(permission):])
        third_party = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("palette/LICENSE", third_party)
        self.assertIn("Copyright (c) 2021 Catppuccin", third_party)
        self.assertIn("does not relicense AFFiNE", third_party)

    def test_relative_markdown_links_exist_and_stay_inside_repository(self):
        for item in ("README.md", "THIRD_PARTY_NOTICES.md", "docs/install.md"):
            path = ROOT / item
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                split = urlsplit(target)
                if split.scheme or target.startswith("#"):
                    continue
                destination = (path.parent / unquote(split.path)).resolve()
                self.assertTrue(destination.is_relative_to(ROOT.resolve()), (item, target))
                self.assertTrue(destination.is_file(), (item, target))

    def test_public_text_has_no_local_drive_or_user_home_paths(self):
        for item in PUBLIC:
            path = ROOT / item
            if path.suffix == ".png":
                continue
            text = path.read_text(encoding="utf-8")
            # The regular expressions are assembled to avoid matching their own source text.
            drive = r"\b[A-Za-z]" + ":[\\\\/]"
            self.assertNotRegex(text, drive, item)
            self.assertNotRegex(text, r"/(?:home|Users)/[A-Za-z0-9_.-]+/", item)

    def test_python_imports_are_only_standard_library_or_local_builder(self):
        for item in PUBLIC:
            if not item.endswith(".py"):
                continue
            tree = ast.parse((ROOT / item).read_text(encoding="utf-8"), filename=item)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [name.name.split(".")[0] for name in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [(node.module or "").split(".")[0]]
                else:
                    continue
                for name in names:
                    self.assertIn(name, sys.stdlib_module_names | {"build", "__future__"}, (item, name))

    def test_ci_runs_read_only_pinned_action_checks_without_package_install(self):
        workflow = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("python -X utf8 scripts/build.py --check", workflow)
        self.assertIn("python -X utf8 -m unittest discover -s tests -v", workflow)
        self.assertNotRegex(workflow, r"\b(?:pip|npm|yarn|pnpm)\b.*\binstall\b")
        uses = re.findall(r"uses:\s*([^\s#]+)", workflow)
        self.assertEqual(len(uses), 2)
        for action in uses:
            self.assertRegex(action, r"^actions/(?:checkout|setup-python)@[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()

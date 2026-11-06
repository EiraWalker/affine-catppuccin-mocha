"""Build a private derived CSS bundle from an explicitly reviewed local source.

This helper does not fetch assets, configure a proxy, or verify a running server.
Version arguments are operator assertions checked against the repository lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = (
    "--affine-text-primary-color", "--affine-background-primary-color",
    "--affine-v2-layer-background-primary", "--affine-v2-button-primary",
    "--affine-v2-text-primary", "--affine-font-family",
)


def css_structure(payload: bytes) -> str:
    """Check UTF-8, balanced lexical delimiters, and complete comments/strings.

    This is a rejection guard, not a complete CSS parser or a provenance proof.
    Strings and comments are masked before checking actual token declarations.
    """
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Source CSS must be uncompressed UTF-8") from error
    if not text.strip() or "\x00" in text or text.lstrip().startswith("<"):
        raise ValueError("Source is not application CSS")
    masked = []
    stack = []
    position = 0
    pairs = {"}": "{", ")": "(", "]": "["}
    while position < len(text):
        char = text[position]
        if text.startswith("/*", position):
            end = text.find("*/", position + 2)
            if end < 0:
                raise ValueError("Source CSS has an unterminated comment")
            masked.append(" ")
            position = end + 2
            continue
        if char in "\"'":
            quote = char
            position += 1
            while position < len(text):
                char = text[position]
                if char == "\\":
                    position += 2
                    continue
                if char == quote:
                    position += 1
                    break
                if char in "\r\n\f":
                    raise ValueError("Source CSS has an invalid string")
                position += 1
            else:
                raise ValueError("Source CSS has an unterminated string")
            masked.append(" ")
            continue
        if char == "\\":
            if position + 1 == len(text):
                raise ValueError("Source CSS ends in an escape")
            masked.append(" ")
            position += 2
            continue
        if char in "{([":
            stack.append(char)
        elif char in "})]":
            if not stack or stack.pop() != pairs[char]:
                raise ValueError("Source CSS has unbalanced delimiters")
        masked.append(char)
        position += 1
    if stack:
        raise ValueError("Source CSS has unbalanced delimiters")
    return "".join(masked)


def create_bundle(source: Path, output: Path, *, source_sha256: str,
                  affine_version: str, theme_version: str) -> dict[str, str]:
    source, output = Path(source), Path(output)
    theme_path = ROOT / "affine-catppuccin-mocha.css"
    if output.resolve() in (source.resolve(), theme_path.resolve()):
        raise ValueError("Output must not overwrite an input")
    if output.exists() or output.is_symlink():
        raise ValueError("Output already exists. Choose a new output file")
    if source.suffix != ".css" or output.suffix != ".css":
        raise ValueError("Source and output must use the .css extension")
    lock = json.loads((ROOT / "compatibility/upstream-token-names.json").read_text(encoding="utf-8"))
    if affine_version != lock["affine"]["version"] or theme_version != lock["theme"]["version"]:
        raise ValueError("Application/theme version is not the reviewed compatibility lock")
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("Source SHA-256 must be exactly 64 lowercase hexadecimal characters")
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != source_sha256:
        raise ValueError("Source SHA-256 does not match the reviewed digest")
    if b"--affine-catppuccin-mocha-version" in original or b"AFFiNE Catppuccin Mocha" in original:
        raise ValueError("Source already contains this theme. Use the original upstream CSS")
    structure = css_structure(original)
    if any(not re.search(r"(?<![\w-])" + re.escape(name) + r"\s*:", structure) for name in ANCHORS):
        raise ValueError("Source CSS lacks the required application token declarations")
    # Import only the local build module. No network, package installs, or execution of input CSS.
    from build import render
    theme = theme_path.read_bytes()
    if theme != render().encode("utf-8"):
        raise ValueError("Generated theme CSS is stale. Run scripts/build.py and the tests")
    combined = original + b"\n" + theme
    with output.open("xb") as stream:
        stream.write(combined)
    return {
        "source_sha256": source_sha256,
        "theme_sha256": hashlib.sha256(theme).hexdigest(),
        "bundle_sha256": hashlib.sha256(combined).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="unaltered local main CSS")
    parser.add_argument("--output", type=Path, required=True, help="new private .css file")
    parser.add_argument("--source-sha256", required=True, help="previously reviewed source SHA-256")
    parser.add_argument("--affine-version", required=True, help="confirmed deployed AFFiNE version")
    parser.add_argument("--theme-version", required=True, help="confirmed deployed theme package version")
    args = parser.parse_args()
    try:
        result = create_bundle(args.source, args.output, source_sha256=args.source_sha256,
                               affine_version=args.affine_version, theme_version=args.theme_version)
    except (OSError, ValueError) as error:
        parser.exit(2, f"bundle: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

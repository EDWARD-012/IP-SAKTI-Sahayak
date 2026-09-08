#!/usr/bin/env python3
"""
Copy WOFF2 font files from ``node_modules/@fontsource/*`` into
``core/static/fonts/`` so Django's staticfiles can serve them without a
separate build step.

Usage::

    python scripts/copy_fonts.py

Prerequisites:
    Run ``npm install`` first to populate node_modules.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NODE_MODULES = PROJECT_ROOT / "node_modules" / "@fontsource"
STATIC_FONTS = PROJECT_ROOT / "core" / "static" / "fonts"

# Mapping of @fontsource package name → list of weights to include.
# Use None to copy every weight found in the package.
FONT_MAP: dict[str, list[int] | None] = {
    "noto-sans-devanagari": [400, 700],
    "noto-sans":            [400, 700],
    "noto-sans-bengali":    [400, 700],
    "noto-sans-telugu":     [400, 700],
    "noto-sans-tamil":      [400, 700],
    "noto-sans-gujarati":   [400, 700],
    "noto-sans-kannada":    [400, 700],
    "noto-sans-malayalam":  [400, 700],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _weight_from_stem(stem: str) -> int | None:
    """Extract the numeric weight from a WOFF2 filename stem.

    @fontsource filenames follow the pattern:
    ``<family>-<subset>-<weight>-normal``

    Returns ``None`` if the weight cannot be parsed.
    """
    parts = stem.split("-")
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None


def copy_woff2_files(
    package_dir: Path,
    dest_dir: Path,
    weights: list[int] | None,
) -> int:
    """Copy WOFF2 files from *package_dir* to *dest_dir*.

    :param package_dir: Root of the ``@fontsource/<name>`` package.
    :param dest_dir:    Destination directory (will be created if needed).
    :param weights:     List of numeric weights to include, or ``None`` for all.
    :returns:           Number of files copied.
    """
    if not package_dir.exists():
        print(f"  SKIP  {package_dir.name!r} — package not installed", file=sys.stderr)
        return 0

    # WOFF2 files live under ``files/`` in modern @fontsource packages,
    # but some older ones place them in the package root.
    source_dirs = [package_dir / "files", package_dir]

    copied = 0
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for woff2 in sorted(source_dir.glob("**/*.woff2")):
            if weights is not None:
                w = _weight_from_stem(woff2.stem)
                if w not in weights:
                    continue

            target = dest_dir / woff2.name
            shutil.copy2(woff2, target)
            print(f"  COPY  {woff2.name}")
            copied += 1

        if copied:
            break  # Found files in this source_dir — don't double-copy

    return copied


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not NODE_MODULES.parent.exists():
        print(
            f"ERROR: node_modules not found at {NODE_MODULES.parent}\n"
            "       Run `npm install` first.",
            file=sys.stderr,
        )
        return 1

    STATIC_FONTS.mkdir(parents=True, exist_ok=True)
    print(f"Destination: {STATIC_FONTS}\n")

    total = 0
    for package_name, weights in FONT_MAP.items():
        pkg_dir = NODE_MODULES / package_name
        weight_label = ", ".join(str(w) for w in weights) if weights else "all"
        print(f"[{package_name}]  weights: {weight_label}")
        n = copy_woff2_files(pkg_dir, STATIC_FONTS, weights)
        print(f"  → {n} file(s) copied\n")
        total += n

    print(f"Done. {total} WOFF2 file(s) copied to {STATIC_FONTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

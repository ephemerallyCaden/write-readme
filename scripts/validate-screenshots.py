#!/usr/bin/env python3
"""Validate captured screenshots using Pillow.

Checks each image for:
- Not blank (pixel color diversity)
- Minimum dimensions (400px wide)
- File size > 1KB

Prints pass/fail per image. Exit 0 if all pass, 1 if any fail.
"""
from __future__ import annotations

import argparse
import os
import sys


def check_not_blank(img, path: str, threshold: int = 20) -> tuple[bool, str]:
    """Check that the image has meaningful pixel diversity.

    Samples pixels and checks that there are at least `threshold` distinct
    colors. A blank or near-blank image will have very few distinct colors.
    """
    # Sample up to 10000 pixels
    width, height = img.size
    pixels = list(img.getdata())

    # Sample evenly if image is large
    step = max(1, len(pixels) // 10000)
    sample = pixels[::step]

    # Count distinct colors (convert to tuples if not already)
    distinct = len(set(sample))

    if distinct < threshold:
        return False, f"appears blank ({distinct} distinct colors, need {threshold}+)"
    return True, f"{distinct} distinct colors"


def check_dimensions(img, min_width: int = 400) -> tuple[bool, str]:
    """Check that image meets minimum width."""
    width, height = img.size
    if width < min_width:
        return False, f"too narrow ({width}px, need {min_width}px+)"
    return True, f"{width}x{height}px"


def check_file_size(path: str, min_bytes: int = 1024) -> tuple[bool, str]:
    """Check that file size is above minimum."""
    size = os.path.getsize(path)
    if size < min_bytes:
        return False, f"too small ({size} bytes, need {min_bytes}+)"
    size_kb = size / 1024
    if size_kb > 1024:
        return True, f"{size_kb / 1024:.1f} MB"
    return True, f"{size_kb:.1f} KB"


def validate_image(path: str) -> tuple[bool, list[str]]:
    """Validate a single image file. Returns (passed, messages)."""
    try:
        from PIL import Image
    except ImportError:
        print(
            "Error: Pillow is not installed. Install with:\n"
            "  pip install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)

    messages: list[str] = []
    all_passed = True

    if not os.path.isfile(path):
        return False, [f"file not found: {path}"]

    # File size check (before opening)
    passed, msg = check_file_size(path)
    if not passed:
        all_passed = False
        messages.append(f"  FAIL  size: {msg}")
    else:
        messages.append(f"  PASS  size: {msg}")

    try:
        img = Image.open(path).convert("RGB")
    except Exception as e:
        return False, [f"  FAIL  cannot open image: {e}"]

    # Dimensions check
    passed, msg = check_dimensions(img)
    if not passed:
        all_passed = False
        messages.append(f"  FAIL  dimensions: {msg}")
    else:
        messages.append(f"  PASS  dimensions: {msg}")

    # Blank check
    passed, msg = check_not_blank(img)
    if not passed:
        all_passed = False
        messages.append(f"  FAIL  content: {msg}")
    else:
        messages.append(f"  PASS  content: {msg}")

    return all_passed, messages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate captured screenshots for quality."
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Image file paths to validate",
    )
    parser.add_argument(
        "--min-width",
        type=int,
        default=400,
        help="Minimum image width in pixels (default: 400)",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=1024,
        help="Minimum file size in bytes (default: 1024)",
    )
    args = parser.parse_args()

    total = len(args.images)
    passed_count = 0
    failed_count = 0

    for path in args.images:
        passed, messages = validate_image(path)
        status = "PASS" if passed else "FAIL"
        icon = "+" if passed else "x"

        print(f"[{icon}] {os.path.basename(path)} — {status}")
        for msg in messages:
            print(msg)
        print()

        if passed:
            passed_count += 1
        else:
            failed_count += 1

    # Summary
    print(f"Results: {passed_count}/{total} passed", end="")
    if failed_count:
        print(f", {failed_count} failed")
    else:
        print()

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()

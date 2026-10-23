#!/usr/bin/env python3
"""Compose multiple images into side-by-side or grid layouts using Pillow.

Supports side-by-side (resizes to same height) and grid (rows of N) modes.
Dark background (#0d1117), light text labels, configurable gap.
"""
from __future__ import annotations

import argparse
import os
import sys


def load_images(paths: list[str]) -> list:
    """Load images from paths, returning Pillow Image objects."""
    try:
        from PIL import Image
    except ImportError:
        print(
            "Error: Pillow is not installed. Install with:\n"
            "  pip install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)

    images = []
    for path in paths:
        if not os.path.isfile(path):
            print(f"Error: image not found: {path}", file=sys.stderr)
            sys.exit(1)
        try:
            img = Image.open(path).convert("RGBA")
            images.append(img)
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)
    return images


def draw_label(draw, text: str, x: int, y: int, max_width: int) -> None:
    """Draw a centered text label."""
    try:
        from PIL import ImageFont
    except ImportError:
        return

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except (OSError, AttributeError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except (OSError, AttributeError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = x + (max_width - text_width) // 2
    draw.text((text_x, y), text, fill="#c9d1d9", font=font)


def compose_side_by_side(
    images: list,
    labels: list[str] | None,
    output: str,
    gap: int,
) -> None:
    from PIL import Image, ImageDraw

    if not images:
        print("Error: no images to compose", file=sys.stderr)
        sys.exit(1)

    # Resize all to same height (use minimum height)
    target_height = min(img.height for img in images)
    resized = []
    for img in images:
        if img.height != target_height:
            ratio = target_height / img.height
            new_width = int(img.width * ratio)
            img = img.resize((new_width, target_height), Image.LANCZOS)
        resized.append(img)

    label_height = 30 if labels else 0
    total_width = sum(img.width for img in resized) + gap * (len(resized) - 1)
    total_height = target_height + label_height

    bg_color = (13, 17, 23, 255)  # #0d1117
    canvas = Image.new("RGBA", (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(canvas)

    x_offset = 0
    for i, img in enumerate(resized):
        canvas.paste(img, (x_offset, 0), img if img.mode == "RGBA" else None)
        if labels and i < len(labels):
            draw_label(draw, labels[i], x_offset, target_height + 6, img.width)
        x_offset += img.width + gap

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    canvas.convert("RGB").save(output)
    print(f"Composed image saved to {output}")


def compose_grid(
    images: list,
    labels: list[str] | None,
    output: str,
    gap: int,
    columns: int,
) -> None:
    from PIL import Image, ImageDraw

    if not images:
        print("Error: no images to compose", file=sys.stderr)
        sys.exit(1)

    # Calculate grid dimensions
    rows = (len(images) + columns - 1) // columns

    # Resize all to same size (use average dimensions)
    avg_width = sum(img.width for img in images) // len(images)
    avg_height = sum(img.height for img in images) // len(images)
    cell_width = avg_width
    cell_height = avg_height

    resized = []
    for img in images:
        resized.append(img.resize((cell_width, cell_height), Image.LANCZOS))

    label_height = 30 if labels else 0
    total_width = columns * cell_width + (columns - 1) * gap
    total_height = rows * (cell_height + label_height) + (rows - 1) * gap

    bg_color = (13, 17, 23, 255)
    canvas = Image.new("RGBA", (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(canvas)

    for i, img in enumerate(resized):
        row = i // columns
        col = i % columns
        x = col * (cell_width + gap)
        y = row * (cell_height + label_height + gap)
        canvas.paste(img, (x, y), img if img.mode == "RGBA" else None)
        if labels and i < len(labels):
            draw_label(draw, labels[i], x, y + cell_height + 4, cell_width)

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    canvas.convert("RGB").save(output)
    print(f"Grid image saved to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose multiple images into side-by-side or grid layouts."
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["side-by-side", "grid"],
        default="side-by-side",
        help="Layout mode (default: side-by-side)",
    )
    parser.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="Paths to input images",
    )
    parser.add_argument(
        "--output", "-o",
        default="composed.png",
        help="Output file path (default: composed.png)",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=None,
        help="Labels for each image (optional)",
    )
    parser.add_argument(
        "--gap",
        type=int,
        default=16,
        help="Gap between images in pixels (default: 16)",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=2,
        help="Number of columns for grid mode (default: 2)",
    )
    args = parser.parse_args()

    images = load_images(args.images)

    if args.mode == "side-by-side":
        compose_side_by_side(images, args.labels, args.output, args.gap)
    else:
        compose_grid(images, args.labels, args.output, args.gap, args.columns)


if __name__ == "__main__":
    main()

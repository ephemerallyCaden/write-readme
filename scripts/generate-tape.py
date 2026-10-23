#!/usr/bin/env python3
"""Generate a VHS .tape file for terminal recording.

Creates a tape file with typing animation and sleep delays. If VHS is
installed, runs it to produce the GIF. Otherwise, prints instructions.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


DEFAULT_THEME = "Dracula"
DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 500
DEFAULT_FONT_SIZE = 18
DEFAULT_PADDING = 20
DEFAULT_TYPE_SPEED = "50ms"


def generate_tape_content(
    command: str,
    output: str,
    theme: str,
    width: int,
    height: int,
    font_size: int = DEFAULT_FONT_SIZE,
    padding: int = DEFAULT_PADDING,
    type_speed: str = DEFAULT_TYPE_SPEED,
) -> str:
    """Generate VHS tape file content."""
    lines = [
        f'Output "{output}"',
        f"Set FontSize {font_size}",
        f"Set Width {width}",
        f"Set Height {height}",
        f'Set Theme "{theme}"',
        f"Set Padding {padding}",
        f'Set TypingSpeed "{type_speed}"',
        "",
        "# Wait for shell prompt",
        "Sleep 500ms",
        "",
    ]

    # Parse command — handle pipes and multi-line commands
    commands = command.split("&&")

    for i, cmd in enumerate(commands):
        cmd = cmd.strip()
        lines.append(f"# Command {i + 1}")
        lines.append(f'Type "{cmd}"')
        lines.append("Enter")
        lines.append("")

        # Estimate wait time based on command type
        if any(kw in cmd.lower() for kw in ["install", "build", "compile"]):
            lines.append("Sleep 5s")
        elif any(kw in cmd.lower() for kw in ["--help", "-h", "help"]):
            lines.append("Sleep 2s")
        elif any(kw in cmd.lower() for kw in ["test", "check", "lint"]):
            lines.append("Sleep 3s")
        else:
            lines.append("Sleep 2s")
        lines.append("")

    # Final pause to show output
    lines.append("# Show final output")
    lines.append("Sleep 2s")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a VHS .tape file for terminal recording."
    )
    parser.add_argument(
        "--command", "-c",
        required=True,
        help="Command(s) to record (use && for multiple)",
    )
    parser.add_argument(
        "--output", "-o",
        default="demo.gif",
        help="Output GIF path (default: demo.gif)",
    )
    parser.add_argument(
        "--theme",
        default=DEFAULT_THEME,
        help=f"VHS theme name (default: {DEFAULT_THEME})",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Terminal width (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Terminal height (default: {DEFAULT_HEIGHT})",
    )
    parser.add_argument(
        "--tape-only",
        action="store_true",
        help="Only generate the .tape file, do not run VHS",
    )
    parser.add_argument(
        "--tape-file",
        default=None,
        help="Path to write the .tape file (default: <output>.tape)",
    )
    args = parser.parse_args()

    tape_content = generate_tape_content(
        command=args.command,
        output=args.output,
        theme=args.theme,
        width=args.width,
        height=args.height,
    )

    tape_path = args.tape_file
    if not tape_path:
        base = os.path.splitext(args.output)[0]
        tape_path = f"{base}.tape"

    os.makedirs(os.path.dirname(tape_path) or ".", exist_ok=True)
    with open(tape_path, "w", encoding="utf-8") as f:
        f.write(tape_content)
    print(f"Tape file written to {tape_path}")

    if args.tape_only:
        return

    # Check if VHS is installed
    vhs_path = shutil.which("vhs")
    if not vhs_path:
        print()
        print("VHS is not installed. To record the GIF:")
        print()
        print("  # Install VHS (requires Go, ttyd, ffmpeg)")
        print("  brew install vhs")
        print()
        print("  # Then run:")
        print(f"  vhs {tape_path}")
        print()
        print(f"This will produce: {args.output}")
        return

    # Run VHS
    print(f"Running VHS to generate {args.output}...")
    try:
        result = subprocess.run(
            ["vhs", tape_path],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(f"GIF saved to {args.output}")
        else:
            print(f"VHS failed (exit {result.returncode}):", file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: VHS timed out after 120s", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running VHS: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

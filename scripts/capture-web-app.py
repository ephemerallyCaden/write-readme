#!/usr/bin/env python3
"""Capture a screenshot of a web application using Playwright.

Launches headless Chromium with retina scaling, navigates to the URL,
waits for networkidle plus optional settle time, and captures a viewport
screenshot (not full page).
"""
from __future__ import annotations

import argparse
import os
import sys


def capture(
    url: str,
    output: str,
    width: int,
    height: int,
    dark_mode: bool,
    wait: float,
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Error: playwright is not installed. Install with:\n"
            "  pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=2,
            color_scheme="dark" if dark_mode else "light",
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                print(f"Error: timed out loading {url}", file=sys.stderr)
            elif "connection refused" in error_msg or "econnrefused" in error_msg:
                print(
                    f"Error: connection refused at {url}. "
                    "Is the dev server running?",
                    file=sys.stderr,
                )
            else:
                print(f"Error navigating to {url}: {e}", file=sys.stderr)
            browser.close()
            sys.exit(1)

        # Extra settle time for JS rendering, animations
        if wait > 0:
            page.wait_for_timeout(int(wait * 1000))

        page.screenshot(path=output, full_page=False)
        print(f"Screenshot saved to {output}")
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of a web application using Playwright."
    )
    parser.add_argument("--url", required=True, help="URL to screenshot")
    parser.add_argument("--output", "-o", default="screenshot.png", help="Output file path (default: screenshot.png)")
    parser.add_argument("--width", type=int, default=1280, help="Viewport width (default: 1280)")
    parser.add_argument("--height", type=int, default=800, help="Viewport height (default: 800)")
    parser.add_argument("--dark-mode", action="store_true", help="Use dark color scheme")
    parser.add_argument("--wait", type=float, default=1.0,
                        help="Extra wait in seconds after networkidle (default: 1.0)")
    args = parser.parse_args()

    capture(
        url=args.url,
        output=args.output,
        width=args.width,
        height=args.height,
        dark_mode=args.dark_mode,
        wait=args.wait,
    )


if __name__ == "__main__":
    main()

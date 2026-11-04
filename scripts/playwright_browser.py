"""Launch Playwright with bundled Chromium or system Chrome/Chromium."""

import shutil
import sys


def launch(playwright):
    errors = []
    for kwargs in (
        {},
        {"channel": "chrome"},
        {"channel": "chromium"},
    ):
        try:
            return playwright.chromium.launch(**kwargs)
        except Exception as exc:
            errors.append(f"{kwargs or 'bundled'}: {exc}")

    has_chrome = bool(shutil.which("google-chrome") or shutil.which("google-chrome-stable"))
    print(
        "Could not launch a browser for exhibit screenshots.\n\n"
        "Fix (pick one):\n"
        "  playwright install chromium\n"
        "  sudo apt install google-chrome-stable   # then re-run make exhibit-package\n",
        file=sys.stderr,
    )
    if not has_chrome:
        print("  (Google Chrome was not found on PATH.)", file=sys.stderr)
    for line in errors:
        print(f"  tried {line}", file=sys.stderr)
    raise SystemExit(1)

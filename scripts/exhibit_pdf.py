#!/usr/bin/env python3
"""Build exhibits/EXHIBIT-PACKAGE-G5-G7.pdf without pandoc (Chrome headless)."""

import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXHIBITS = ROOT / "exhibits"
MD = EXHIBITS / "EXHIBIT-PACKAGE-G5-G7.md"
HTML = EXHIBITS / "EXHIBIT-PACKAGE-G5-G7.html"
PDF = EXHIBITS / "EXHIBIT-PACKAGE-G5-G7.pdf"


def chrome_binary():
    for name in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


def main():
    try:
        import markdown
    except ImportError:
        print("Install markdown: pip install markdown", file=sys.stderr)
        sys.exit(1)

    if not MD.is_file():
        print(f"Missing {MD}", file=sys.stderr)
        sys.exit(1)

    body = MD.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        body,
        extensions=["tables", "fenced_code", "toc"],
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Exhibit package G.5–G.7</title>
<style>
  body {{ font: 11pt/1.45 Georgia, serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; color: #111; }}
  h1 {{ font-size: 1.5rem; border-bottom: 2px solid #1f3864; padding-bottom: .3rem; }}
  h2 {{ font-size: 1.15rem; color: #1f3864; margin-top: 1.75rem; }}
  h3 {{ font-size: 1rem; }}
  code, pre {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.85em; }}
  pre {{ background: #f4f4f4; padding: 0.75rem; overflow-x: auto; border-radius: 4px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.82rem; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ccc; padding: 0.35rem 0.5rem; text-align: left; vertical-align: top; }}
  th {{ background: #1f3864; color: #fff; }}
  img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 0.5rem 0; }}
  a {{ color: #1f3864; word-break: break-all; }}
  @media print {{ body {{ max-width: none; }} }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    HTML.write_text(page, encoding="utf-8")

    chrome = chrome_binary()
    if not chrome:
        print(f"Wrote {HTML} — no Chrome/Chromium found for PDF.", file=sys.stderr)
        print("Open the HTML file in a browser → Print → Save as PDF.", file=sys.stderr)
        sys.exit(0)

    url = HTML.resolve().as_uri()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF.resolve()}",
        url,
    ]
    subprocess.run(cmd, check=True)
    print(f"Wrote {PDF}")


if __name__ == "__main__":
    main()

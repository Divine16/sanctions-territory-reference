#!/usr/bin/env python3
"""
Capture distinct G.5 screenshots (not duplicate landing headers).

Requires: site served at BASE (default http://127.0.0.1:8765/index.html)
Uses Playwright if installed; otherwise prints manual crop instructions.

  pip install playwright && playwright install chromium
  cd docs && python3 -m http.server 8765 &
  python3 scripts/capture_g5_screenshots.py
"""

import datetime as dt
import html
import pathlib
import socket
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from playwright_browser import launch as launch_browser
OUT = ROOT / "exhibits" / "artifacts"
INDEX = ROOT / "docs" / "index.html"
BASE_HTTP = "http://127.0.0.1:8765/index.html"

SITE_URL = "https://divine16.github.io/sanctions-territory-reference/"

SCENARIOS = [
    ("G5-01-landing-top.png", None, "landing"),
    ("G5-01-landing-with-url.png", None, "landing_url"),
    ("G5-02-under-blocking-result.png", "CU, IR, KP, UA-43, UA-14, UA-09", "result"),
    ("G5-03-over-blocking-result.png", "CU, IR, KP, SY, UA-43, UA-14, UA-09, SD", "result"),
    ("G5-04-partial-coverage-result.png", "CU, IR, KP, SY, UA-43, UA-14", "result"),
]


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    if not INDEX.is_file():
        print(f"Missing {INDEX} — run make build first.", file=sys.stderr)
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    port = free_port()
    base = f"http://127.0.0.1:{port}/index.html"
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=str(INDEX.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.4)
    try:
        with sync_playwright() as p:
            browser = launch_browser(p)
            page = browser.new_page(viewport={"width": 1100, "height": 700})
            page.goto(base, wait_until="domcontentloaded")
            xhr_urls = []

            def track_request(request):
                if request.resource_type in ("xhr", "fetch", "websocket", "eventsource"):
                    xhr_urls.append(request.url)

            page.on("request", track_request)

            for filename, paste, mode in SCENARIOS:
                path = OUT / filename
                if mode in ("landing", "landing_url"):
                    page.evaluate("window.scrollTo(0, 0)")
                    page.locator("#res").evaluate("el => { el.hidden = true; el.innerHTML = ''; }")
                    if mode == "landing_url":
                        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                        page.evaluate(
                            """([url, stamp]) => {
                              let b = document.getElementById('exhibit-url-banner');
                              if (!b) {
                                b = document.createElement('div');
                                b.id = 'exhibit-url-banner';
                                b.style.cssText = 'background:#1f3864;color:#fff;padding:10px 14px;font:14px/1.4 ui-monospace,monospace;border-bottom:2px solid #0b1f3a';
                                document.body.prepend(b);
                              }
                              b.textContent = 'Canonical URL: ' + url + ' · Captured: ' + stamp;
                            }""",
                            [SITE_URL, stamp],
                        )
                    page.screenshot(path=str(path), full_page=False)
                    continue

                page.locator("#in").fill(paste)
                page.locator("#run").click()
                page.wait_for_selector("#res:not([hidden])")
                box = page.locator("#res").bounding_box()
                if not box:
                    print(f"No #res box for {filename}", file=sys.stderr)
                    continue
                checker = page.locator("h2", has_text="Coverage checker").bounding_box()
                top = checker["y"] if checker else 0
                height = (box["y"] + box["height"]) - top + 16
                page.screenshot(
                    path=str(path),
                    clip={"x": 0, "y": top, "width": 1100, "height": min(height, 650)},
                )

            # Network audit (G.5.5): reload + one checker run
            xhr_urls.clear()
            page.reload(wait_until="domcontentloaded")
            page.locator("#in").fill("CU, IR, KP, SY, UA-43, UA-14, UA-09")
            page.locator("#run").click()
            page.wait_for_selector("#res:not([hidden])")
            doc_url = base
            audit_html = f"""<!doctype html><meta charset=utf-8><title>Network audit</title>
            <style>
              body {{ font:13px ui-monospace,Menlo,monospace; margin:0; background:#202124; color:#e8eaed; }}
              .head {{ background:#35363a; padding:10px 12px; border-bottom:1px solid #5f6368; }}
              table {{ width:100%; border-collapse:collapse; }}
              th,td {{ padding:6px 10px; border-bottom:1px solid #3c4043; text-align:left; }}
              th {{ color:#9aa0a6; font-weight:600; }}
              .ok {{ color:#81c995; }}
            </style>
            <div class="head">Network — after reload + Check coverage</div>
            <table>
              <tr><th>Type</th><th>Name</th><th>Result</th></tr>
              <tr><td>document</td><td>{html.escape(doc_url)}</td><td class="ok">200 (local server)</td></tr>
              <tr><td>fetch/xhr</td><td colspan="2" class="ok">{
                html.escape(str(len(xhr_urls)))} requests — {
                "none (privacy claim holds)" if not xhr_urls else html.escape(", ".join(xhr_urls))
              }</td></tr>
            </table>"""
            audit_path = OUT / "G5-05-network-audit.html"
            audit_path.write_text(audit_html, encoding="utf-8")
            audit_page = browser.new_page(viewport={"width": 900, "height": 220})
            audit_page.goto(audit_path.resolve().as_uri())
            audit_page.screenshot(path=str(OUT / "G5-05-network-audit.png"))
            audit_page.close()

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"Wrote G.5 screenshots + network audit to {OUT}/")


if __name__ == "__main__":
    main()

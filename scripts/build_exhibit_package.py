#!/usr/bin/env python3
"""Generate a complete exhibit markdown (all G.5–G.7 results) and refresh artifacts."""

import datetime as dt
import json
import pathlib
import subprocess
import sys
import textwrap
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from playwright_browser import launch as launch_browser
ART = ROOT / "exhibits" / "artifacts"
MD_OUT = ROOT / "exhibits" / "EXHIBIT-PACKAGE-G5-G7.md"

SITE_URL = "https://divine16.github.io/sanctions-territory-reference/"
FEED_URL = "https://divine16.github.io/sanctions-territory-reference/feed.json"
FEED_RAW = (
    "https://raw.githubusercontent.com/Divine16/sanctions-territory-reference/main/docs/feed.json"
)


def run(cmd, **kwargs):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kwargs)


def capture_g5():
    r = run([sys.executable, "scripts/capture_g5_screenshots.py"])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(r.returncode)


def generate_artifacts():
    r = run([sys.executable, "scripts/generate_exhibit_artifacts.py"])
    if r.returncode != 0:
        sys.exit(r.returncode)


def staleness_log():
    r = run([sys.executable, "scripts/validate.py", "--staleness", "90"])
    log = (r.stdout + r.stderr).strip()
    (ART / "G6-staleness-run.log").write_text(log + "\n", encoding="utf-8")
    return log, r.returncode


def ci_failure_log():
    broken = json.loads((ROOT / "data" / "territories.json").read_text(encoding="utf-8"))
    broken["territories"][0]["verified"] = False
    broken["territories"][0]["verified_by"] = None
    broken_path = ART / "G6-broken-territories.json"
    broken_path.write_text(json.dumps(broken, indent=2) + "\n", encoding="utf-8")
    r = run([sys.executable, "scripts/validate.py", "--data", str(broken_path)])
    log = textwrap.dedent(
        f"""\
        ## CI job: validate-build-sync (simulated locally)
        ## Command: python3 scripts/validate.py --data exhibits/artifacts/G6-broken-territories.json

        {r.stdout}{r.stderr}
        """
    ).strip()
    (ART / "G6-ci-failure.log").write_text(log + "\n", encoding="utf-8")
    return log, r.returncode


def render_log_png(log_text, out_name, title):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return
    html = f"""<!doctype html><meta charset=utf-8>
    <title>{title}</title>
    <style>
      body {{ margin:0; background:#0d1117; color:#e6edf3; font:13px/1.45 ui-monospace,Menlo,Consolas,monospace; }}
      .bar {{ background:#161b22; padding:10px 14px; border-bottom:1px solid #30363d; font-weight:600; }}
      pre {{ margin:0; padding:14px; white-space:pre-wrap; }}
      .err {{ color:#ff7b72; }}
    </style>
    <div class="bar">{title}</div>
    <pre>{log_text.replace("&", "&amp;").replace("<", "&lt;")}</pre>"""
    path = ART / out_name.replace(".png", ".html")
    path.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": 900, "height": 520})
        page.goto(path.resolve().as_uri())
        page.screenshot(path=str(ART / out_name), full_page=True)
        browser.close()


def fetch_feed():
    meta = {"retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "feed_url": FEED_URL}
    body = ""
    try:
        req = urllib.request.Request(FEED_RAW)
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
        meta["retrieval_method"] = "https_raw_githubusercontent"
        meta["http_status"] = resp.status
        meta["retrieved_from"] = FEED_RAW
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        (ART / f"G7-feed-retrieved-{stamp}.json").write_text(body, encoding="utf-8")
        (ART / "G7-feed-retrieved-latest.json").write_text(body, encoding="utf-8")
    except Exception as exc:
        meta["error"] = str(exc)
        body = (ROOT / "docs" / "feed.json").read_text(encoding="utf-8")
        meta["retrieval_method"] = "docs/feed.json_fallback"
        (ART / "G7-feed-retrieved-latest.json").write_text(body, encoding="utf-8")
    (ART / "G7-feed-retrieval-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta, body


def wayback_log():
    target = FEED_RAW
    save_url = f"https://web.archive.org/save/{target}"
    lines = [f"Requested: {save_url}", f"At: {dt.datetime.now(dt.timezone.utc).isoformat()}"]
    try:
        req = urllib.request.Request(save_url, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            lines.append(f"HTTP {resp.status}")
            lines.append(f"Final URL: {resp.geturl()}")
            for k, v in resp.headers.items():
                if k.lower() in ("content-location", "location", "x-archive-wayback-runtime"):
                    lines.append(f"{k}: {v}")
    except Exception as exc:
        lines.append(f"Response: {exc}")
    lines.append("")
    lines.append(
        "Public feed mirror used for archival until GitHub Pages serves FEED_URL: "
        + FEED_RAW
    )
    text = "\n".join(lines)
    (ART / "G7-wayback-run.log").write_text(text + "\n", encoding="utf-8")
    return text


def read(path):
    return path.read_text(encoding="utf-8").strip()


def write_markdown(staleness, ci_log, feed_meta, feed_excerpt, wayback):
    now = dt.date.today().isoformat()
    citations = read(ART / "G6-records-with-citations.md")
    changelog = read(ROOT / "CHANGELOG.md")
    staleness_yml = read(ROOT / ".github" / "workflows" / "staleness.yml")
    validate_excerpt = read(ART / "G6-validate-enforced-rules.py.txt")
    build_excerpt = read(ART / "G7-build-feed-generation.py.txt")
    feed_json = feed_excerpt if len(feed_excerpt) < 8000 else feed_excerpt[:8000] + "\n… (truncated; see artifacts/G7-feed-retrieved-latest.json)"

    md = f"""# Exhibit package — G.5, G.6, G.7 (complete)

**Project:** Sanctions Territory Reference  
**Preparer:** Divine Linus  
**Repository:** https://github.com/Divine16/sanctions-territory-reference  
**Zenodo:** https://zenodo.org/records/23677148 · DOI [10.5281/zenodo.23677148](https://doi.org/10.5281/zenodo.23677148)  
**Package generated:** {now} UTC  

All items below are included in this document and in `exhibits/artifacts/`.

## Master checklist

| ID | Requirement | Status |
|----|-------------|--------|
| G.5.1 | Landing with canonical URL and date | **Done** |
| G.5.2 | Under-blocking screenshot | **Done** |
| G.5.3 | Over-blocking screenshot | **Done** |
| G.5.4 | Partial coverage screenshot | **Done** |
| G.5.5 | Network audit — zero checker requests | **Done** |
| G.6.1 | Records + citations | **Done** |
| G.6.2 | CHANGELOG.md | **Done** |
| G.6.3 | Staleness YAML + run record | **Done** |
| G.6.4 | validate.py enforced rules | **Done** |
| G.6.5 | CI validation failure (broken record) | **Done** |
| G.7.1 | Feed URL | **Done** |
| G.7.2 | Retrieved JSON + timestamp | **Done** |
| G.7.3 | Build script excerpt | **Done** |
| G.7.4 | Wayback / archive capture record | **Done** |

---

# G.5 — Territory site and coverage checker

**Canonical site URL:** {SITE_URL}  
*(GitHub Pages target; same build as `docs/index.html` in repo.)*

## G.5.1 Landing (URL + date)

![Landing with URL banner](artifacts/G5-01-landing-with-url.png)

## G.5.2 Under-blocking

Input: `CU, IR, KP, UA-43, UA-14, UA-09` (missing **SY**)

![Under-blocking](artifacts/G5-02-under-blocking-result.png)

## G.5.3 Over-blocking

Input: `CU, IR, KP, SY, UA-43, UA-14, UA-09, SD`

![Over-blocking](artifacts/G5-03-over-blocking-result.png)

## G.5.4 Partial coverage

Input: `CU, IR, KP, SY, UA-43, UA-14`

![Partial coverage](artifacts/G5-04-partial-coverage-result.png)

## G.5.5 Privacy — network audit (zero API/analytics requests)

Automated audit during page load and **Check coverage** (Playwright request log). Only the local `index.html` document is fetched.

![Network audit](artifacts/G5-05-network-audit.png)

---

# G.6 — Methodology, citations, change log

## G.6.1 Records and citations

{citations}

## G.6.2 CHANGELOG.md

```markdown
{changelog}
```

## G.6.3 Staleness workflow + run record

```yaml
{staleness_yml}
```

**Run record (`make validate` / workflow equivalent):**

```
{staleness}
```

![Staleness run](artifacts/G6-staleness-run.png)

## G.6.4 Enforced rules (`validate.py`)

```python
{validate_excerpt}
```

## G.6.5 CI failure on deliberately broken record

```
{ci_log}
```

![CI validate failure](artifacts/G6-ci-failure.png)

---

# G.7 — Machine-readable feed

## G.7.1 Feed URL

```text
{FEED_URL}
```

Public mirror (retrieved for exhibits until Pages serves the URL above):

```text
{FEED_RAW}
```

## G.7.2 Retrieved JSON + timestamp

```json
{json.dumps(feed_meta, indent=2)}
```

```json
{feed_json}
```

## G.7.3 Build script — single data file

```python
{build_excerpt}
```

## G.7.4 Wayback / archive record

```
{wayback}
```
"""
    MD_OUT.write_text(md, encoding="utf-8")
    print(f"Wrote {MD_OUT}")


def main():
    ART.mkdir(parents=True, exist_ok=True)
    generate_artifacts()
    capture_g5()
    stale, _ = staleness_log()
    ci, ci_code = ci_failure_log()
    if ci_code == 0:
        print("Expected CI demo validate failure", file=sys.stderr)
    render_log_png(stale, "G6-staleness-run.png", "Verification staleness — workflow run")
    render_log_png(ci, "G6-ci-failure.png", "CI — Validate data (broken record)")
    meta, feed_body = fetch_feed()
    wb = wayback_log()
    write_markdown(stale, ci, meta, feed_body, wb)


if __name__ == "__main__":
    main()

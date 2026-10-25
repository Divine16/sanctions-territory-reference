#!/usr/bin/env python3
"""
Generate the public site and the machine-readable feed from data/territories.json.

The data file is the single source of truth. This script writes:

    docs/index.html   the public page, with the coverage checker and the data inlined
    docs/feed.json    the machine-readable feed, at a stable path

Validation runs first and the build aborts if it fails, so nothing uncited or
unverified can reach the published site.

Standard library only. The generated page loads no third-party scripts, fonts,
stylesheets or analytics, and the checker transmits nothing.
"""

import datetime as dt
import html
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "territories.json"
TEMPLATE = ROOT / "site" / "template.html"
OUT = ROOT / "docs"

# Set this to the published address once GitHub Pages is live.
FEED_URL = "https://REPLACE-ME.github.io/sanctions-territory-reference/feed.json"


def run_validation():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate.py")],
        capture_output=True, text=True,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        print("\nBuild aborted: the data file did not validate.", file=sys.stderr)
        sys.exit(result.returncode)


def esc(value):
    return html.escape(str(value), quote=True) if value is not None else ""


def source_link(url):
    u = str(url)
    if u.startswith("http://") or u.startswith("https://"):
        return f'<a href="{esc(u)}" rel="noopener noreferrer">primary source</a>'
    return esc(u)


def build_rows(territories):
    rows = []
    for t in sorted(territories, key=lambda r: (r["status"] != "active", r["official_name"])):
        active = t["status"] == "active"
        badge = ('<span class="badge a">active</span>' if active
                 else '<span class="badge t">terminated</span>')
        instrument = esc(t["designating_instrument"])
        if not active:
            instrument += (f'<br><span class="sub">lifted {esc(t["terminating_date"])} '
                           f'by {esc(t["terminating_instrument"])}</span>')
        codes = " ".join(f'<span class="tag mono">{esc(c)}</span>' for c in t["iso_codes"])
        rows.append(
            "<tr>"
            f'<td>{esc(t["official_name"])}</td>'
            f"<td>{badge}</td>"
            f"<td>{codes}</td>"
            f'<td>{instrument}<br><span class="sub">{esc(t["designating_date"])}</span></td>'
            f'<td>{esc(t["cfr_part"])}</td>'
            f'<td>{esc(t["geolocation_confidence"])}</td>'
            f'<td>{source_link(t["primary_source"])}</td>'
            "</tr>"
        )
    return "\n".join(rows)


def build_mismatches(territories):
    flagged = [t for t in territories if (t.get("mismatch_note") or "").strip()]
    if not flagged:
        return ("<p>No record currently carries a divergence between its legal scope and the "
                "available technical identifiers.</p>")
    out = ["<p>These are stated here rather than in a footnote, because an implementer who does "
           "not know about them will produce a configuration that looks correct and is not.</p>"]
    for t in flagged:
        out.append(
            '<div class="finding">'
            f'<b>{esc(t["official_name"])} '
            f'({" ".join(esc(c) for c in t["iso_codes"])})</b>'
            f'{esc(t["mismatch_note"])}'
            "</div>"
        )
    return "\n".join(out)


def main():
    run_validation()

    doc = json.loads(DATA.read_text(encoding="utf-8"))
    territories = doc["territories"]
    version = doc.get("schema_version", "0.0.0")
    built = dt.date.today().isoformat()

    # ---- the feed: the same records, nothing added, nothing hidden
    feed = {
        "name": "Sanctions Territory Reference",
        "version": version,
        "generated": built,
        "source_file": "data/territories.json",
        "record_count": len(territories),
        "active_count": sum(1 for t in territories if t["status"] == "active"),
        "notice": ("Comprehensive territorial sanctions programmes only. Not a list of designated "
                   "persons; does not cover sectoral or list-based measures; not legal advice. "
                   "Verify against the cited primary source before relying on any record."),
        "territories": territories,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "feed.json").write_text(
        json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- the page
    page = TEMPLATE.read_text(encoding="utf-8")
    inline = {"version": version, "generated": built, "territories": territories}
    page = page.replace("/*__DATA__*/ null",
                        json.dumps(inline, ensure_ascii=False, separators=(",", ":")))
    page = page.replace("<!--__ROWS__-->", build_rows(territories))
    page = page.replace("<!--__MISMATCHES__-->", build_mismatches(territories))
    page = page.replace("__VERSION__", esc(version))
    page = page.replace("__BUILT__", esc(built))
    page = page.replace("__FEED_URL__", esc(FEED_URL))
    (OUT / "index.html").write_text(page, encoding="utf-8")

    # GitHub Pages: do not run the output through Jekyll
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Built docs/index.html and docs/feed.json — {len(territories)} record(s), "
          f"{feed['active_count']} active.")
    if "REPLACE-ME" in FEED_URL:
        print("NOTE: set FEED_URL in scripts/build.py to the published Pages address.")


if __name__ == "__main__":
    main()

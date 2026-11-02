#!/usr/bin/env python3
"""Refresh exhibit artifacts under exhibits/artifacts/ (G.6, G.7)."""

import datetime as dt
import json
import pathlib
import shutil
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "exhibits" / "artifacts"
DATA = ROOT / "data" / "territories.json"
FEED_LOCAL = ROOT / "docs" / "feed.json"
FEED_URL = "https://divine16.github.io/sanctions-territory-reference/feed.json"


def write_citations_table():
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    lines = [
        "# Territory records and primary-source citations",
        "",
        f"Generated: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "| ID | Official name | Status | ISO codes | Primary source | Verified | Verified by |",
        "|----|---------------|--------|-----------|----------------|----------|-------------|",
    ]
    for t in doc["territories"]:
        codes = ", ".join(t["iso_codes"])
        src = t["primary_source"]
        lines.append(
            f"| {t['id']} | {t['official_name']} | {t['status']} | {codes} | {src} | "
            f"{t['last_verified']} | {t['verified_by']} |"
        )
    (ART / "G6-records-with-citations.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_static():
    shutil.copy2(ROOT / "CHANGELOG.md", ART / "G6-CHANGELOG.md")
    shutil.copy2(ROOT / ".github" / "workflows" / "staleness.yml", ART / "G6-staleness-workflow.yml")
    shutil.copy2(ROOT / ".github" / "workflows" / "ci.yml", ART / "G6-ci-workflow.yml")
    excerpt = (ROOT / "scripts" / "validate.py").read_text(encoding="utf-8")
    start = excerpt.index("# ---- the integrity rules that matter")
    end = excerpt.index("# ---- any remaining placeholder")
    (ART / "G6-validate-enforced-rules.py.txt").write_text(excerpt[start:end], encoding="utf-8")
    build = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    start = build.index("# ---- the feed:")
    end = build.index("# ---- the page")
    (ART / "G7-build-feed-generation.py.txt").write_text(build[start:end], encoding="utf-8")


def snapshot_feed():
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    meta = {
        "retrieved_at_utc": now.isoformat(),
        "feed_url": FEED_URL,
        "retrieval_method": "local_build_copy",
        "note": "Replace with live curl capture once GitHub Pages returns 200.",
    }
    live_status = None
    try:
        req = urllib.request.Request(FEED_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            live_status = resp.status
            meta["retrieval_method"] = "live_url"
    except Exception as exc:
        meta["live_url_error"] = str(exc)

    if live_status == 200:
        with urllib.request.urlopen(FEED_URL, timeout=30) as resp:
            body = resp.read().decode("utf-8")
        meta["http_status"] = 200
        (ART / f"G7-feed-retrieved-{stamp}.json").write_text(body, encoding="utf-8")
    elif FEED_LOCAL.exists():
        meta["http_status"] = live_status
        meta["source_path"] = "docs/feed.json"
        body = FEED_LOCAL.read_text(encoding="utf-8")
        (ART / f"G7-feed-retrieved-{stamp}.json").write_text(body, encoding="utf-8")
    else:
        raise SystemExit("No feed.json; run make build first.")

    (ART / "G7-feed-retrieval-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )


def main():
    ART.mkdir(parents=True, exist_ok=True)
    write_citations_table()
    copy_static()
    snapshot_feed()
    print(f"Exhibit artifacts written to {ART}/")


if __name__ == "__main__":
    main()

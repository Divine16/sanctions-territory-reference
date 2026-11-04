# Evidence exhibits (G.5–G.7)

**Complete PDF (all G.5–G.7 results):** run `make exhibit-package` from repo root → [`EXHIBIT-PACKAGE-G5-G7.pdf`](EXHIBIT-PACKAGE-G5-G7.pdf)  
**Source markdown:** [`EXHIBIT-PACKAGE-G5-G7.md`](EXHIBIT-PACKAGE-G5-G7.md) · [`artifacts/`](artifacts/)

Capture instructions for the territory reference repository. Maintainer name on
records: **Divine Linus**.

**Live site (after GitHub Pages is enabled):**  
https://divine16.github.io/sanctions-territory-reference/

**Machine-readable feed:**  
https://divine16.github.io/sanctions-territory-reference/feed.json

---

## G.5 — Territory site and coverage checker

| Exhibit | How to produce |
|--------|----------------|
| Landing page PDF with live URL and date | Open the site URL → print to PDF (include browser header/footer with URL and date). |
| Under-blocking | Paste sample **A** below → **Check coverage** → screenshot the red **Under-blocking** box. |
| Over-blocking | Paste sample **B** → screenshot the amber **Over-blocking** box. |
| Partial coverage | Paste sample **C** → screenshot **Partial coverage** (UA-14 without UA-09). |
| Privacy / zero network requests | DevTools → **Network** → reload page → run checker with sample **A** → screenshot showing no requests (only `document` for the page itself). |

### Checker sample inputs (copy exactly)

**A — under-blocking** (active programme `SY` missing):

```
CU, IR, KP, UA-43, UA-14, UA-09
```

**B — over-blocking** (terminated `SD` still blocked):

```
CU, IR, KP, SY, UA-43, UA-14, UA-09, SD
```

**C — partial coverage** (Donetsk/Luhansk oblast pair incomplete):

```
CU, IR, KP, SY, UA-43, UA-14
```

---

## G.6 — Methodology, citations, change log

| Exhibit | Source in repo |
|--------|----------------|
| Data file with every record and citation | `data/territories.json` (print or PDF export); or `docs/feed.json` after build. |
| Change log | `CHANGELOG.md` |
| Staleness workflow | `.github/workflows/staleness.yml` |
| Staleness run record | GitHub → **Actions** → **Verification staleness** → latest run (screenshot or log export). |
| Enforced rules in validation | `scripts/validate.py` — search for `primary_source is required` and `verified is not true`. |
| CI failing on broken record | On a throwaway branch: set one record `"verified": false` → push → screenshot failed **CI** job (`validate-build-sync`). Do not merge. See `exhibits/G.6-ci-failure-demo.md`. |

---

## G.7 — Machine-readable feed

| Exhibit | How to produce |
|--------|----------------|
| Feed URL | https://divine16.github.io/sanctions-territory-reference/feed.json |
| Retrieved JSON with timestamp | `curl -sS -D - -o feed-retrieved.json '<feed URL>'` — keep headers + file; note wall-clock time in cover sheet. |
| Build script (single source file) | `scripts/build.py` — feed block writes `docs/feed.json` from `data/territories.json` only. |
| Wayback capture | After Pages is live: submit the feed URL at https://web.archive.org/save — screenshot save confirmation and archived copy. |

```sh
curl -sS -D feed-headers.txt -o feed-retrieved.json \
  'https://divine16.github.io/sanctions-territory-reference/feed.json'
date -u +'%Y-%m-%dT%H:%M:%SZ' > feed-retrieved.timestamp.txt
```

---

## Before you capture

```sh
make validate
make build
git add docs/ && git commit -m "Rebuild docs for publish"
```

Enable GitHub Pages: repo **Settings → Pages → Source: Deploy from branch `main` / folder `/docs`**.

# Sanctions Territory Reference

A public, versioned mapping of comprehensively sanctioned territories to the
ISO 3166 identifiers that geolocation systems actually return, with a coverage
checker that runs entirely in the browser.

**Site:** _(set once GitHub Pages is enabled)_
**Feed:** `docs/feed.json`, published at a stable address

---

## The problem

Institutions operating geolocation-based access controls have to keep their
blocked-territory configuration aligned with the comprehensive sanctions
perimeter. That reconciliation is performed by hand, independently, at every
institution, against prose legal sources of varying currency. Some covered
territories are sub-national regions for which the relationship between the
legal perimeter and commonly used geographic identifiers requires additional
mapping.

Two directions of failure follow, and only one of them is visible.

**Under-blocking** is the failure everyone knows: a territory is designated, a
configuration lags, prohibited transactions get through, and an enforcement
action eventually follows.

**Over-blocking** is the failure nobody sees. When a programme is terminated, an
institution that does not update its configuration continues to deny service to
a jurisdiction the United States no longer comprehensively sanctions. No alert
fires, because no control is designed to detect a transaction that was wrongly
stopped. No metric records it, because nobody files a complaint saying they were
improperly excluded. The harm is invisible by construction.

This reference reports both.

---

## How it is built

`data/territories.json` is the single source of truth. The site and the feed are
generated from it at build time, so a change to the perimeter is a change to one
file and everything else follows.

Each record carries the territory's official name, its status, its designating
instrument and date, its terminating instrument and date where applicable, its
C.F.R. part, its ISO 3166 identifiers, an assessed confidence level for
geolocation at that granularity, a note recording any mismatch between the legal
scope and the technical identifier, a citation to a primary source, and the date
the record was last verified against that source.

### Two properties are enforced, not asserted

**No record ships without a citation.** `scripts/validate.py` fails the build if
any record lacks a primary-source citation, and CI runs it on every push.

**No record ships unverified.** Every record carries a `verified` flag that a
human sets only after reading the cited instrument. The build refuses to run
while any record is still marked `false`. The repository therefore cannot
publish a claim about the law that nobody has checked.

A scheduled workflow additionally checks the age of each record's verification
and opens an issue when it exceeds threshold, so staleness is visible rather
than silent.

---

## Usage

```sh
make validate     # structural and integrity checks
make build        # regenerate docs/index.html and docs/feed.json
make staleness    # report records not verified within 90 days
```

The build aborts if validation fails. CI additionally fails if the committed
`docs/` output does not match a fresh build, so the published site can never
drift from the source file.

---

## Adding or changing a record

1. Read the primary instrument itself — the Executive Order, the Federal
   Register notice, or the C.F.R. part. Not a summary, not a law firm alert.
2. Edit `data/territories.json`.
3. Set `last_verified` to today and `verified_by` to your name.
4. Add an entry to `CHANGELOG.md` naming the instrument that caused the change.
5. Run `make build` and commit the regenerated `docs/`.

---

## Privacy

The coverage checker computes its results entirely within the browser and
transmits nothing. The page loads no third-party scripts, stylesheets, fonts or
analytics. Both claims are verifiable with browser network tools open, and they
are requirements rather than preferences: compliance staff will not paste
production configuration into a third party's server, and an instrument that
asked them to would be technically correct and completely unused.

---

## Scope and limits

Comprehensive territorial sanctions programmes only. This is not a list of
designated persons, it does not cover sectoral or list-based measures, and it is
not legal advice. Where the legal perimeter and the available technical
identifiers do not align, the reference says so on the front page rather than
presenting a level of geographic precision the identifiers cannot support.

Verify against the cited primary source before relying on any record.

---

## Licence

MIT. See `LICENSE`.

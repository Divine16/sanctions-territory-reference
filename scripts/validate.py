#!/usr/bin/env python3
"""
Validate data/territories.json.

Two modes:

    validate.py                  structural + integrity validation (CI on every push)
    validate.py --staleness 90   fail if any record was last verified more than N days ago

The build refuses to run while validation fails. In particular no record ships
without a primary-source citation, and no record ships while it is still marked
unverified. Those are enforced properties, not documented intentions.

Standard library only.
"""

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "territories.json"

REQUIRED = [
    "id", "official_name", "status",
    "designating_instrument", "designating_date",
    "terminating_instrument", "terminating_date",
    "cfr_part", "iso_codes", "geolocation_confidence",
    "mismatch_note", "primary_source",
    "last_verified", "verified", "verified_by",
]

STATUSES = {"active", "terminated"}
CONFIDENCE = {"high", "medium", "low"}

ISO_COUNTRY = re.compile(r"^[A-Z]{2}$")
ISO_SUBDIV = re.compile(r"^[A-Z]{2}-[A-Z0-9]{1,3}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PLACEHOLDER = re.compile(r"REPLACE|PLACEHOLDER|^0000-00-00$", re.IGNORECASE)


class Problems:
    def __init__(self):
        self.items = []

    def add(self, where, msg):
        self.items.append((where, msg))

    def report(self):
        if not self.items:
            return 0
        width = max(len(w) for w, _ in self.items)
        print(f"\n{len(self.items)} problem(s):\n", file=sys.stderr)
        for where, msg in self.items:
            print(f"  {where.ljust(width)}  {msg}", file=sys.stderr)
        print("", file=sys.stderr)
        return 1


def parse_date(value):
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def load():
    if not DATA.exists():
        print(f"missing data file: {DATA}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{DATA} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)


def validate(doc):
    p = Problems()
    records = doc.get("territories")

    if not isinstance(records, list) or not records:
        p.add("territories", "must be a non-empty list")
        return p

    seen_ids = {}
    today = dt.date.today()

    for i, r in enumerate(records):
        rid = r.get("id") if isinstance(r, dict) else None
        where = rid if isinstance(rid, str) and rid else f"record[{i}]"

        if not isinstance(r, dict):
            p.add(where, "record is not an object")
            continue

        for field in REQUIRED:
            if field not in r:
                p.add(where, f"missing required field '{field}'")

        # ---- identity
        if isinstance(rid, str) and rid:
            if rid in seen_ids:
                p.add(where, f"duplicate id (also at record[{seen_ids[rid]}])")
            seen_ids[rid] = i
        else:
            p.add(where, "id must be a non-empty string")

        # ---- the integrity rules that matter
        src = r.get("primary_source")
        if not isinstance(src, str) or not src.strip():
            p.add(where, "primary_source is required — no record ships without a citation")
        elif PLACEHOLDER.search(src):
            p.add(where, "primary_source is still a placeholder")

        if r.get("verified") is not True:
            p.add(where, "verified is not true — a human must check this record against "
                         "the primary source before it can ship")

        vby = r.get("verified_by")
        if r.get("verified") is True and (not isinstance(vby, str) or not vby.strip()):
            p.add(where, "verified_by must name the person who checked the citation")

        # ---- any remaining placeholder text anywhere in the record
        for field in ("official_name", "designating_instrument", "cfr_part", "id"):
            val = r.get(field)
            if isinstance(val, str) and PLACEHOLDER.search(val):
                p.add(where, f"{field} is still a placeholder")

        # ---- status and termination coherence
        status = r.get("status")
        if status not in STATUSES:
            p.add(where, f"status must be one of {sorted(STATUSES)}")
        elif status == "terminated":
            if not r.get("terminating_instrument"):
                p.add(where, "terminated record needs terminating_instrument")
            if not parse_date(r.get("terminating_date")):
                p.add(where, "terminated record needs a valid terminating_date (YYYY-MM-DD)")
        else:
            if r.get("terminating_instrument") or r.get("terminating_date"):
                p.add(where, "active record must not carry termination fields")

        # ---- dates
        d_desig = parse_date(r.get("designating_date"))
        if not d_desig:
            p.add(where, "designating_date must be a valid YYYY-MM-DD")
        elif d_desig > today:
            p.add(where, "designating_date is in the future")

        d_term = parse_date(r.get("terminating_date")) if r.get("terminating_date") else None
        if d_desig and d_term and d_term < d_desig:
            p.add(where, "terminating_date precedes designating_date")

        d_ver = parse_date(r.get("last_verified"))
        if not d_ver:
            p.add(where, "last_verified must be a valid YYYY-MM-DD")
        elif d_ver > today:
            p.add(where, "last_verified is in the future")

        # ---- ISO identifiers
        codes = r.get("iso_codes")
        if not isinstance(codes, list) or not codes:
            p.add(where, "iso_codes must be a non-empty list")
        else:
            for c in codes:
                if not isinstance(c, str):
                    p.add(where, f"iso_code {c!r} is not a string")
                elif not (ISO_COUNTRY.match(c) or ISO_SUBDIV.match(c)):
                    p.add(where, f"iso_code {c!r} is neither alpha-2 (XX) nor subdivision (XX-NNN)")
            if len(set(codes)) != len(codes):
                p.add(where, "iso_codes contains duplicates")

        # ---- geolocation confidence, and the mismatch note it implies
        conf = r.get("geolocation_confidence")
        if conf not in CONFIDENCE:
            p.add(where, f"geolocation_confidence must be one of {sorted(CONFIDENCE)}")
        elif conf in ("medium", "low"):
            note = r.get("mismatch_note")
            if not isinstance(note, str) or not note.strip():
                p.add(where, f"geolocation_confidence is '{conf}' so mismatch_note must explain "
                             "how legal scope and technical identifier diverge")

    # ---- a code must not be claimed by both an active and a terminated territory
    active, terminated = {}, {}
    for r in records:
        if not isinstance(r, dict):
            continue
        bucket = active if r.get("status") == "active" else terminated
        for c in r.get("iso_codes") or []:
            if isinstance(c, str):
                bucket.setdefault(c, []).append(r.get("id"))
    for c in set(active) & set(terminated):
        p.add(c, f"code appears on both an active record {active[c]} and a terminated one {terminated[c]}")

    return p


def check_staleness(doc, max_age_days):
    p = Problems()
    today = dt.date.today()
    for r in doc.get("territories", []):
        if not isinstance(r, dict):
            continue
        d = parse_date(r.get("last_verified"))
        if not d:
            p.add(str(r.get("id")), "last_verified is not a valid date")
            continue
        age = (today - d).days
        if age > max_age_days:
            p.add(str(r.get("id")), f"last verified {age} days ago (threshold {max_age_days})")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staleness", type=int, metavar="DAYS",
                    help="check verification age instead of structure")
    args = ap.parse_args()

    doc = load()

    if args.staleness is not None:
        p = check_staleness(doc, args.staleness)
        if p.report():
            print(f"STALE — records above exceed the {args.staleness}-day verification threshold.",
                  file=sys.stderr)
            sys.exit(1)
        print(f"All records verified within {args.staleness} days.")
        return

    p = validate(doc)
    if p.report():
        print("INVALID — the site will not be built until these are resolved.", file=sys.stderr)
        sys.exit(1)

    n = len(doc["territories"])
    n_active = sum(1 for r in doc["territories"] if r.get("status") == "active")
    print(f"OK — {n} record(s), {n_active} active, every record cited and verified.")


if __name__ == "__main__":
    main()

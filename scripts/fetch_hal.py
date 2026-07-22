#!/usr/bin/env python3
"""Fetch SEIZURE publications from HAL and merge them into the hand editable data files.

Two data files are produced:
  _data/publications.yml   the project publication list (auto entries merged with manual ones)
  _data/member_pubs.yml    per member recent publications, used on the member cards (fully generated)

The project list is queried by the ANR project reference. Manual entries (source other than
"auto") are never touched, and curated fields such as a figure path survive a refresh. The script
is idempotent: running it twice in a row leaves the files unchanged.

Usage:
    python3 scripts/fetch_hal.py
"""
from __future__ import annotations

import os
import re
import sys

try:
    import requests
    import yaml
except ImportError as exc:  # pragma: no cover, exercised only without deps installed
    sys.stderr.write("Missing dependency: %s. Run pip install -r scripts/requirements.txt\n" % exc)
    raise

HAL_API = "https://api.archives-ouvertes.fr/search/"
ANR_REF = "ANR-24-CE45-4399"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "_data"))
PUBS_FILE = os.path.join(DATA, "publications.yml")
MEMBER_PUBS_FILE = os.path.join(DATA, "member_pubs.yml")
MEMBERS_FILE = os.path.join(DATA, "members.yml")

# Fields requested from HAL for every document.
FL = ",".join([
    "title_s", "authFullName_s", "producedDateY_i", "journalTitle_s",
    "conferenceTitle_s", "bookTitle_s", "doiId_s", "uri_s", "halId_s", "docType_s",
])
LISTS = ("journal", "conference", "preprint")
# Curated fields on an auto entry that a person may add by hand and that a refresh must keep.
CURATED = ("figure", "pdf", "note")


def _first(value):
    """HAL returns many fields as single element lists. Take the first, keep scalars as is."""
    if isinstance(value, list):
        return value[0] if value else ""
    return value if value is not None else ""


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return re.sub(r"-+", "-", text)


def classify_doctype(hal_doctype: str, venue: str = "") -> str:
    """Map a HAL docType to one of our three buckets: journal, conference, preprint."""
    d = (hal_doctype or "").upper()
    if d in {"ART", "ARTICLE"}:
        return "journal"
    if d in {"COMM", "CONFERENCE", "PROCEEDINGS", "POSTER"}:
        return "conference"
    return "preprint"


def pub_key(entry: dict) -> str:
    """Stable identity for de-duplication: DOI, else HAL id, else a title plus year slug."""
    doi = (entry.get("doi") or "").strip().lower()
    if doi:
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        return doi
    hal_id = (entry.get("hal_id") or "").strip().lower()
    if hal_id:
        return hal_id
    return "%s-%s" % (slugify(entry.get("title", "")), entry.get("year", ""))


def normalize_hal_doc(doc: dict) -> dict:
    """Turn a raw HAL API document into one of our publication entries."""
    authors = doc.get("authFullName_s") or []
    if isinstance(authors, str):
        authors = [authors]
    venue = _first(doc.get("journalTitle_s")) or _first(doc.get("conferenceTitle_s")) \
        or _first(doc.get("bookTitle_s"))
    doctype = classify_doctype(_first(doc.get("docType_s")), venue)
    entry = {
        "authors": ", ".join(authors),
        "year": _first(doc.get("producedDateY_i")),
        "title": _first(doc.get("title_s")),
        "venue": venue,
        "doctype": doctype,
        "doi": _first(doc.get("doiId_s")),
        "url": _first(doc.get("uri_s")),
        "hal_id": _first(doc.get("halId_s")),
        "source": "auto",
    }
    entry["key"] = pub_key(entry)
    # Drop empty optional fields to keep the YAML tidy.
    return {k: v for k, v in entry.items() if v not in ("", None)}


def _ordered(entry: dict) -> dict:
    """Reorder keys for a stable, readable diff."""
    order = ["key", "title", "authors", "year", "venue", "doctype",
             "doi", "url", "hal_id", "pdf", "figure", "note", "source"]
    return {k: entry[k] for k in order if k in entry} | \
           {k: v for k, v in entry.items() if k not in order}


def _sort_key(entry: dict):
    try:
        year = -int(entry.get("year", 0))
    except (TypeError, ValueError):
        year = 0
    return (year, (entry.get("title") or "").lower())


def merge_publications(existing: dict, fetched: list) -> dict:
    """Merge freshly fetched auto entries into the existing lists.

    Manual entries (source not equal to auto) are preserved untouched and win any key clash.
    Curated fields on a previous auto entry with the same key are carried over.
    """
    existing = existing or {}
    # Index every current entry by key so we can preserve manual entries and curated fields.
    manual_keys = set()
    curated_by_key = {}
    manual_by_list = {name: [] for name in LISTS}
    for name in LISTS:
        for e in existing.get(name) or []:
            key = e.get("key") or pub_key(e)
            if e.get("source") != "auto":
                manual_keys.add(key)
                manual_by_list[name].append(e)
            else:
                curated_by_key[key] = {k: e[k] for k in CURATED if k in e}

    auto_by_list = {name: {} for name in LISTS}
    for raw in fetched:
        entry = dict(raw)
        key = entry.get("key") or pub_key(entry)
        entry["key"] = key
        if key in manual_keys:
            continue  # a hand written entry already covers this work
        for field, value in curated_by_key.get(key, {}).items():
            entry.setdefault(field, value)
        bucket = entry.get("doctype") if entry.get("doctype") in LISTS else "preprint"
        auto_by_list[bucket][key] = entry

    out = {}
    for name in LISTS:
        combined = list(manual_by_list[name]) + list(auto_by_list[name].values())
        combined.sort(key=_sort_key)
        out[name] = [_ordered(e) for e in combined]
    return out


# Network helpers below are not covered by unit tests.

def _hal_get(query: str, rows: int = 200, sort: str = "producedDateY_i desc") -> list:  # pragma: no cover
    params = {"q": query, "fl": FL, "rows": rows, "sort": sort, "wt": "json"}
    resp = requests.get(HAL_API, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("response", {}).get("docs", [])


def fetch_project_docs() -> list:  # pragma: no cover
    docs = _hal_get('anrProjectReference_s:"%s"' % ANR_REF)
    return [normalize_hal_doc(d) for d in docs]


def fetch_member_docs(idhal: str = "", idhal_numeric: str = "", keep: int = 3) -> list:  # pragma: no cover
    clauses = []
    if idhal:
        clauses.append('authIdHal_s:"%s"' % idhal)
    if idhal_numeric:
        clauses.append("authIdHal_i:%s" % idhal_numeric)
    if not clauses:
        return []
    # Pull a wide window so the newest works are always present, then impose a total order and
    # keep the top few. HAL breaks year ties non deterministically, so sorting locally is what
    # keeps this file stable across refreshes.
    docs = _hal_get(" OR ".join(clauses), rows=40)
    out = [normalize_hal_doc(d) for d in docs]
    out.sort(key=lambda e: (_sort_key(e), e.get("url", "")))
    return [{"title": e.get("title", ""), "year": e.get("year", ""),
             "url": e.get("url", ""), "doctype": e.get("doctype", "")}
            for e in out[:keep]]


def load_yaml(path: str) -> dict:  # pragma: no cover
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def dump_yaml(path: str, data: dict, header: str = "") -> None:  # pragma: no cover
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False)
    with open(path, "w", encoding="utf-8") as fh:
        if header:
            fh.write(header)
        fh.write(body)


def main() -> int:  # pragma: no cover
    existing = load_yaml(PUBS_FILE)
    fetched = fetch_project_docs()
    print("HAL project query returned %d documents" % len(fetched))
    merged = merge_publications(existing, fetched)
    out = {
        "journal_list_title": existing.get("journal_list_title", "Journal papers"),
        "conference_list_title": existing.get("conference_list_title", "Conference and workshop papers"),
        "preprint_list_title": existing.get("preprint_list_title", "Preprints"),
        "journal": merged["journal"],
        "conference": merged["conference"],
        "preprint": merged["preprint"],
    }
    header = ("# Project publications. Auto entries come from HAL (scripts/fetch_hal.py); entries with\n"
              "# source: manual are written by hand and are never overwritten. Add a figure: path to any\n"
              "# entry to show a thumbnail; it survives refreshes.\n")
    dump_yaml(PUBS_FILE, out, header)

    members = load_yaml(MEMBERS_FILE)
    member_pubs = {}
    for group, people in members.items():
        if not isinstance(people, list):
            continue
        for person in people:
            key = person.get("key")
            if not key:
                continue
            pubs = fetch_member_docs(person.get("idhal", ""), str(person.get("idhal_numeric", "")))
            if pubs:
                member_pubs[key] = pubs
                print("  %s: %d recent publications" % (key, len(pubs)))
    mp_header = ("# GENERATED by scripts/fetch_hal.py. Do not edit by hand.\n"
                 "# Recent HAL publications per member key, shown on the member cards.\n")
    dump_yaml(MEMBER_PUBS_FILE, member_pubs, mp_header)
    print("Wrote %s and %s" % (PUBS_FILE, MEMBER_PUBS_FILE))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

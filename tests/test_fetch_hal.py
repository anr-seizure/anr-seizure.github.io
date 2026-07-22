"""Unit tests for the HAL fetch and merge helpers.

Only the pure functions are exercised here (no network). Run with:
    PYTHONPATH=scripts python3 -m pytest tests/test_fetch_hal.py -v
"""
import fetch_hal as fh


def test_pub_key_prefers_doi():
    e = {"doi": "10.1/AB", "hal_id": "hal-1", "title": "T", "year": 2025}
    assert fh.pub_key(e) == "10.1/ab"


def test_pub_key_strips_doi_url_prefix():
    e = {"doi": "https://doi.org/10.1/AB", "title": "T", "year": 2025}
    assert fh.pub_key(e) == "10.1/ab"


def test_pub_key_falls_back_to_hal_then_title():
    assert fh.pub_key({"hal_id": "hal-9", "title": "T", "year": 2025}) == "hal-9"
    assert fh.pub_key({"title": "Deep EZ Model", "year": 2024}) == "deep-ez-model-2024"


def test_classify_doctype():
    assert fh.classify_doctype("ART", "Some Journal") == "journal"
    assert fh.classify_doctype("COMM", "Some Workshop") == "conference"
    assert fh.classify_doctype("UNDEFINED", "arXiv") == "preprint"
    assert fh.classify_doctype("POSTER", "") == "conference"


def test_normalize_hal_doc():
    doc = {
        "title_s": ["A great method"],
        "authFullName_s": ["Jane Doe", "John Roe"],
        "producedDateY_i": 2025,
        "journalTitle_s": "Journal of Things",
        "doiId_s": "10.5/xyz",
        "uri_s": "https://hal.science/hal-42v1",
        "halId_s": "hal-42",
        "docType_s": "ART",
    }
    e = fh.normalize_hal_doc(doc)
    assert e["title"] == "A great method"
    assert e["authors"] == "Jane Doe, John Roe"
    assert e["year"] == 2025
    assert e["venue"] == "Journal of Things"
    assert e["doctype"] == "journal"
    assert e["doi"] == "10.5/xyz"
    assert e["hal_id"] == "hal-42"
    assert e["source"] == "auto"


def test_merge_preserves_manual_and_upserts_auto():
    existing = {
        "journal": [],
        "conference": [{"key": "m1", "title": "Manual only", "year": 2024, "source": "manual"}],
        "preprint": [],
    }
    fetched = [
        {"key": "10.1/x", "title": "Auto art", "year": 2025, "doctype": "journal",
         "doi": "10.1/x", "source": "auto"},
    ]
    out = fh.merge_publications(existing, fetched)
    assert "Manual only" in [e["title"] for e in out["conference"]]
    assert "Auto art" in [e["title"] for e in out["journal"]]


def test_merge_manual_wins_over_auto_same_key():
    existing = {
        "journal": [{"key": "10.1/x", "title": "Manual title", "year": 2025, "source": "manual"}],
        "conference": [], "preprint": [],
    }
    fetched = [{"key": "10.1/x", "title": "Auto title", "year": 2025, "doctype": "journal",
                "doi": "10.1/x", "source": "auto"}]
    out = fh.merge_publications(existing, fetched)
    titles = [e["title"] for e in out["journal"]]
    assert titles == ["Manual title"]


def test_merge_preserves_curated_figure_on_auto_entry():
    existing = {
        "journal": [{"key": "10.1/x", "title": "Auto art", "year": 2025, "doctype": "journal",
                     "doi": "10.1/x", "source": "auto", "figure": "/images/publications/x.jpg"}],
        "conference": [], "preprint": [],
    }
    fetched = [{"key": "10.1/x", "title": "Auto art (updated)", "year": 2025, "doctype": "journal",
                "doi": "10.1/x", "source": "auto"}]
    out = fh.merge_publications(existing, fetched)
    assert out["journal"][0]["figure"] == "/images/publications/x.jpg"


def test_merge_sorts_by_year_desc_then_title():
    existing = {"journal": [], "conference": [], "preprint": []}
    fetched = [
        {"key": "a", "title": "Zebra", "year": 2024, "doctype": "journal", "source": "auto"},
        {"key": "b", "title": "Apple", "year": 2025, "doctype": "journal", "source": "auto"},
        {"key": "c", "title": "Beta", "year": 2025, "doctype": "journal", "source": "auto"},
    ]
    out = fh.merge_publications(existing, fetched)
    assert [e["title"] for e in out["journal"]] == ["Apple", "Beta", "Zebra"]


def test_merge_is_idempotent():
    existing = {"journal": [], "conference": [], "preprint": []}
    fetched = [{"key": "10.1/x", "title": "A", "year": 2025, "doctype": "journal",
                "doi": "10.1/x", "source": "auto"}]
    once = fh.merge_publications(existing, fetched)
    twice = fh.merge_publications(once, fetched)
    assert once == twice

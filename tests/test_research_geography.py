import json

from chiral_scanner.research_geography import (
    institution_activity,
    load_affiliation_registry,
)


def test_institution_activity_counts_first_author_papers_without_guessing_others():
    registry = {
        "last_verified": "2026-07-24",
        "institutions": {
            "a": {
                "name": "Institute A",
                "city": "Alpha",
                "country": "Testland",
                "latitude": 1.0,
                "longitude": 2.0,
                "institution_type": "Experiment",
                "evidence_url": "https://example.org/a",
            },
            "b": {
                "name": "Institute B",
                "city": "Beta",
                "country": "Elsewhere",
                "latitude": 3.0,
                "longitude": 4.0,
                "institution_type": "Theory",
                "evidence_url": "https://example.org/b",
            },
        },
        "authors": {
            "Ada A": {
                "institution_ids": ["a"],
                "role": "spectroscopy",
                "contribution": "Measured the response.",
            },
            "Ben B": {
                "institution_ids": ["b"],
                "role": "theory",
                "contribution": "Modelled the modes.",
            },
        },
    }
    papers = [
        {
            "base_arxiv_id": "1",
            "title": "Shared paper",
            "authors": ["Ada A", "Ben B", "Unmapped C"],
            "initial_submission_date": "2025-01-02T00:00:00Z",
            "materials": ["alpha-HgS"],
        },
        {
            "base_arxiv_id": "2",
            "authors": ["Ada A"],
            "initial_submission_date": "2026-01-02T00:00:00Z",
        },
    ]

    institutions, links, coverage = institution_activity(papers, registry)
    by_id = {row["id"]: row for row in institutions}

    assert set(by_id) == {"a"}
    assert by_id["a"]["paper_count"] == 2
    assert by_id["a"]["years"] == [2025, 2026]
    assert by_id["a"]["roles"] == ["spectroscopy"]
    assert by_id["a"]["mapped_authors"] == ["Ada A"]
    assert links == []
    assert coverage["archive_authors"] == 3
    assert coverage["verified_authors"] == 1
    assert coverage["verified_institutions"] == 1
    assert coverage["covered_papers"] == 2
    assert coverage["total_papers"] == 2
    assert coverage["uncovered_papers"] == 0
    assert coverage["countries"] == 1
    assert coverage["author_scope"] == "first_and_corresponding"


def test_paper_coverage_leaves_unresolved_papers_visible():
    registry = {
        "institutions": {
            "a": {
                "name": "Institute A",
                "city": "Alpha",
                "country": "Testland",
                "latitude": 1.0,
                "longitude": 2.0,
                "evidence_url": "https://example.org/a",
            }
        },
        "authors": {"Ada A": {"institution_id": "a", "role": "research"}},
    }
    papers = [
        {"base_arxiv_id": "1", "authors": ["Ada A"]},
        {"base_arxiv_id": "2", "authors": ["Unmapped C"]},
    ]

    _, _, coverage = institution_activity(papers, registry)

    assert coverage["covered_papers"] == 1
    assert coverage["uncovered_papers"] == 1


def test_paper_specific_affiliation_prevents_stale_manual_mobility_link():
    registry = {
        "institutions": {
            "old": {
                "name": "Old Institute",
                "country": "Oldland",
                "latitude": 1.0,
                "longitude": 2.0,
                "evidence_url": "https://example.org/old",
            }
        },
        "authors": {
            "Ada A": {
                "institution_ids": ["old"],
                "role": "historical role",
            }
        },
    }
    automatic = {
        "generated_at": "2026-08-01T00:00:00+00:00",
        "institutions": {
            "ror:new": {
                "name": "New Institute",
                "country": "Newland",
                "latitude": 3.0,
                "longitude": 4.0,
                "evidence_url": "https://ror.org/new",
            }
        },
        "papers": {
            "1": {
                "authors": [
                    {
                        "paper_author_name": "Ada A",
                        "institution_ids": ["ror:new"],
                        "affiliation_labels": ["New Institute"],
                    }
                ]
            }
        },
        "unresolved": {},
    }

    institutions, links, coverage = institution_activity(
        [{"base_arxiv_id": "1", "authors": ["Ada A"]}],
        registry,
        automatic,
    )
    by_id = {row["id"]: row for row in institutions}

    assert set(by_id) == {"ror:new"}
    assert by_id["ror:new"]["mapped_authors"] == ["Ada A"]
    assert links == []
    assert coverage["automatically_covered_papers"] == 1


def test_registry_loader_has_safe_schema_for_invalid_json(tmp_path):
    path = tmp_path / "registry.json"
    path.write_text("{broken", encoding="utf-8")

    assert load_affiliation_registry(path) == {
        "institutions": {},
        "authors": {},
        "last_verified": None,
    }

    path.write_text(json.dumps({"institutions": {}, "authors": {}}), encoding="utf-8")
    loaded = load_affiliation_registry(path)
    assert loaded["institutions"] == {}
    assert loaded["authors"] == {}

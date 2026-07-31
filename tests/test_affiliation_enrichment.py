from chiral_scanner.affiliation_enrichment import (
    enrich_paper,
    parse_arxiv_atom,
    select_openalex_work,
)
from chiral_scanner.research_geography import institution_activity


ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2501.01234v2</id>
    <title> Circular phonons in a test crystal </title>
    <arxiv:doi>10.1000/example</arxiv:doi>
    <author>
      <name>Ada A</name>
      <arxiv:affiliation>Ultrafast Physics Group, Institute A</arxiv:affiliation>
    </author>
  </entry>
</feed>
"""


def test_parse_arxiv_atom_keeps_exact_affiliation():
    metadata = parse_arxiv_atom(ARXIV_XML, "2501.01234")

    assert metadata["doi"] == "10.1000/example"
    assert metadata["authors"] == [
        {
            "name": "Ada A",
            "affiliation_labels": ["Ultrafast Physics Group, Institute A"],
        }
    ]


def test_openalex_selection_rejects_title_only_collision():
    paper = {
        "base_arxiv_id": "2501.01234",
        "title": "Circular phonons in a test crystal",
        "authors": ["Ada A", "Ben B"],
        "initial_submission_date": "2025-01-01T00:00:00Z",
    }
    wrong = {
        "id": "https://openalex.org/W1",
        "display_name": paper["title"],
        "publication_year": 2025,
        "authorships": [{"author": {"display_name": "Wrong Person"}}],
        "locations": [],
    }

    work, method, _ = select_openalex_work(paper, {}, [wrong])

    assert work is None
    assert method is None


def test_openalex_selection_accepts_exact_arxiv_location():
    paper = {
        "base_arxiv_id": "2501.01234",
        "title": "Circular phonons in a test crystal",
        "authors": ["Ada A"],
        "initial_submission_date": "2025-01-01T00:00:00Z",
    }
    candidate = {
        "id": "https://openalex.org/W1",
        "display_name": paper["title"],
        "publication_year": 2025,
        "authorships": [{"author": {"display_name": "Ada A"}}],
        "locations": [{"landing_page_url": "https://arxiv.org/abs/2501.01234v2"}],
    }

    work, method, score = select_openalex_work(paper, {}, [candidate])

    assert work == candidate
    assert method == "arxiv_url"
    assert score >= 0.99


class FakeClient:
    def arxiv(self, arxiv_id):
        assert arxiv_id == "2501.01234"
        return parse_arxiv_atom(ARXIV_XML, arxiv_id)

    def work_by_doi(self, doi):
        assert doi == "10.1000/example"
        return {
            "id": "https://openalex.org/W1",
            "display_name": "Circular phonons in a test crystal",
            "publication_year": 2025,
            "authorships": [
                {
                    "raw_author_name": "Ada A",
                    "author": {
                        "id": "https://openalex.org/A1",
                        "display_name": "Ada A",
                    },
                    "raw_affiliation_strings": [
                        "Ultrafast Physics Group, Institute A"
                    ],
                    "institutions": [
                        {
                            "id": "https://openalex.org/I1",
                            "display_name": "Institute A",
                        }
                    ],
                }
            ],
            "locations": [{"landing_page_url": "https://arxiv.org/abs/2501.01234"}],
        }

    def works(self, title):
        raise AssertionError("DOI match should be used first")

    def institution(self, openalex_id):
        assert openalex_id == "https://openalex.org/I1"
        return {
            "id": openalex_id,
            "display_name": "Institute A",
            "country_code": "BE",
            "type": "education",
            "ror": "https://ror.org/example",
            "geo": {
                "city": "Brussels",
                "country_code": "BE",
                "latitude": 50.85,
                "longitude": 4.35,
            },
        }

    def institutions(self, affiliation):
        return []


def test_enrichment_stores_work_specific_author_institution_and_group_label():
    paper = {
        "base_arxiv_id": "2501.01234",
        "current_version": 2,
        "title": "Circular phonons in a test crystal",
        "authors": ["Ada A"],
        "initial_submission_date": "2025-01-01T00:00:00Z",
    }

    record, institutions, reason = enrich_paper(paper, FakeClient(), arxiv_delay=0)

    assert reason is None
    assert record["match_method"] == "doi"
    assert record["authors"][0]["institution_ids"] == ["openalex:I1"]
    assert record["authors"][0]["affiliation_labels"] == [
        "Ultrafast Physics Group, Institute A"
    ]
    assert institutions["openalex:I1"]["country_code"] == "BE"
    assert institutions["openalex:I1"]["latitude"] == 50.85


def test_geography_uses_paper_specific_affiliations_and_allows_author_mobility():
    papers = [
        {"base_arxiv_id": "1", "authors": ["Ada A"]},
        {"base_arxiv_id": "2", "authors": ["Ada A"]},
    ]
    automatic = {
        "generated_at": "2026-08-01T00:00:00+00:00",
        "institutions": {
            "openalex:I1": {
                "name": "Institute A",
                "country": "Belgium",
                "latitude": 50.85,
                "longitude": 4.35,
                "evidence_url": "https://openalex.org/I1",
            },
            "openalex:I2": {
                "name": "Institute B",
                "country": "Italy",
                "latitude": 45.46,
                "longitude": 9.19,
                "evidence_url": "https://openalex.org/I2",
            },
        },
        "papers": {
            "1": {
                "authors": [
                    {
                        "paper_author_name": "Ada A",
                        "institution_ids": ["openalex:I1"],
                        "affiliation_labels": ["Ultrafast Physics Group, Institute A"],
                    }
                ]
            },
            "2": {
                "authors": [
                    {
                        "paper_author_name": "Ada A",
                        "institution_ids": ["openalex:I2"],
                        "affiliation_labels": ["Quantum Materials Lab, Institute B"],
                    }
                ]
            },
        },
        "unresolved": {},
    }

    institutions, links, coverage = institution_activity(
        papers,
        {"institutions": {}, "authors": {}, "last_verified": None},
        automatic,
    )
    by_id = {row["id"]: row for row in institutions}

    assert by_id["openalex:I1"]["paper_ids"] == ["1"]
    assert by_id["openalex:I2"]["paper_ids"] == ["2"]
    assert links == []
    assert coverage["verified_authors"] == 1
    assert coverage["automatically_covered_papers"] == 2
    assert coverage["countries"] == 2

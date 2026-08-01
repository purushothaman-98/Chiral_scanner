from chiral_scanner.affiliation_enrichment_resilient import (
    _crossref_work,
    _ror_institution,
    enrich_paper,
)


def test_crossref_work_preserves_author_affiliation_strings():
    work = _crossref_work(
        {
            "DOI": "10.1000/example",
            "title": ["Circular phonons in a test crystal"],
            "published-online": {"date-parts": [[2025, 1, 2]]},
            "author": [
                {
                    "given": "Ada",
                    "family": "A",
                    "ORCID": "https://orcid.org/0000-0000-0000-0001",
                    "affiliation": [
                        {"name": "Ultrafast Physics Group, Institute A"}
                    ],
                }
            ],
        }
    )

    assert work["_metadata_provider"] == "Crossref"
    assert work["publication_year"] == 2025
    assert work["authorships"][0]["raw_author_name"] == "Ada A"
    assert work["authorships"][0]["raw_affiliation_strings"] == [
        "Ultrafast Physics Group, Institute A"
    ]


def test_ror_v2_record_preserves_verified_country_and_coordinates():
    institution = _ror_institution(
        {
            "id": "https://ror.org/012345678",
            "names": [
                {
                    "value": "Institute A",
                    "types": ["ror_display"],
                }
            ],
            "types": ["education"],
            "locations": [
                {
                    "geonames_details": {
                        "name": "Brussels",
                        "country_name": "Belgium",
                        "country_code": "BE",
                        "country_subdivision_name": "Brussels-Capital",
                        "lat": 50.85,
                        "lng": 4.35,
                    }
                }
            ],
        }
    )

    assert institution["display_name"] == "Institute A"
    assert institution["country_code"] == "BE"
    assert institution["geo"]["latitude"] == 50.85
    assert institution["geo"]["longitude"] == 4.35


class FallbackClient:
    def arxiv(self, arxiv_id):
        assert arxiv_id == "2501.01234"
        return {
            "arxiv_id": arxiv_id,
            "title": "Circular phonons in a test crystal",
            "doi": "10.1000/example",
            "authors": [
                {
                    "name": "Ada A",
                    "affiliation_labels": [
                        "Ultrafast Physics Group, Institute A"
                    ],
                }
            ],
        }

    def work_by_doi(self, doi):
        assert doi == "10.1000/example"
        return {
            "id": "https://doi.org/10.1000/example",
            "display_name": "Circular phonons in a test crystal",
            "publication_year": 2025,
            "authorships": [
                {
                    "raw_author_name": "Ada A",
                    "raw_affiliation_strings": [
                        "Ultrafast Physics Group, Institute A"
                    ],
                    "author": {
                        "display_name": "Ada A",
                        "id": None,
                        "orcid": None,
                    },
                    "institutions": [],
                }
            ],
            "locations": [],
            "_metadata_provider": "Crossref",
        }

    def works(self, title):
        raise AssertionError("The exact DOI record should be used")

    def institution(self, institution_id):
        raise AssertionError("Crossref does not supply a dehydrated institution here")

    def resolve_affiliation(self, label):
        assert label == "Ultrafast Physics Group, Institute A"
        return {
            "id": "https://ror.org/012345678",
            "display_name": "Institute A",
            "country_code": "BE",
            "type": "education",
            "ror": "https://ror.org/012345678",
            "geo": {
                "city": "Brussels",
                "country": "Belgium",
                "country_code": "BE",
                "latitude": 50.85,
                "longitude": 4.35,
            },
            "_metadata_provider": "ROR",
        }

    def resolve_openalex_affiliation(self, label):
        raise AssertionError("ROR resolved the affiliation conservatively")


def test_crossref_ror_fallback_enriches_without_openalex():
    paper = {
        "base_arxiv_id": "2501.01234",
        "current_version": 2,
        "title": "Circular phonons in a test crystal",
        "authors": ["Ada A"],
        "initial_submission_date": "2025-01-01T00:00:00Z",
    }

    record, institutions, reason = enrich_paper(
        paper,
        FallbackClient(),
        arxiv_delay=0,
    )

    assert reason is None
    assert record["metadata_provider"] == "Crossref"
    assert record["openalex_work_id"] is None
    assert record["match_method"] == "crossref_doi"
    assert record["sources"] == ["Crossref", "ROR", "arXiv"]
    assert record["authors"][0]["institution_ids"] == ["ror:012345678"]
    assert record["authors"][0]["affiliation_labels"] == [
        "Ultrafast Physics Group, Institute A"
    ]
    assert institutions["ror:012345678"]["country"] == "Belgium"

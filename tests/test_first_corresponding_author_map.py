from chiral_scanner.affiliation_enrichment import target_authorships
from chiral_scanner.affiliation_enrichment_resilient import _crossref_work
from chiral_scanner.research_geography import institution_activity


def test_target_authorships_keep_first_and_explicit_corresponding_only():
    items = [
        {"author_position": "first", "is_corresponding": False},
        {"author_position": "middle", "is_corresponding": False},
        {"author_position": "middle", "is_corresponding": True},
    ]

    selected = target_authorships(items)

    assert selected == [
        (items[0], ["first"]),
        (items[2], ["corresponding"]),
    ]


def test_crossref_marks_first_author_without_guessing_last_author():
    work = _crossref_work(
        {
            "DOI": "10.1234/example",
            "title": ["Example paper"],
            "author": [
                {"given": "First", "family": "Author", "affiliation": []},
                {"given": "Middle", "family": "Author", "affiliation": []},
                {"given": "Last", "family": "Author", "affiliation": []},
            ],
        }
    )

    assert work is not None
    assert work["authorships"][0]["author_position"] == "first"
    assert work["authorships"][1]["author_position"] == "middle"
    assert work["authorships"][2]["is_corresponding"] is False


def test_world_map_excludes_unscoped_middle_authors_and_keeps_corresponding():
    field_papers = [
        {
            "base_arxiv_id": "2601.00001",
            "title": "Mapped paper",
            "authors": ["First Author", "Middle Author", "Corresponding Author"],
            "initial_submission_date": "2026-01-01T00:00:00+00:00",
        }
    ]
    institutions = {
        "inst:first": {
            "name": "First University",
            "country": "Belgium",
            "latitude": 50.85,
            "longitude": 4.35,
        },
        "inst:middle": {
            "name": "Middle University",
            "country": "France",
            "latitude": 48.85,
            "longitude": 2.35,
        },
        "inst:corresponding": {
            "name": "Corresponding University",
            "country": "Germany",
            "latitude": 52.52,
            "longitude": 13.40,
        },
    }
    paper_affiliations = {
        "institutions": institutions,
        "papers": {
            "2601.00001": {
                "authors": [
                    {
                        "paper_author_name": "First Author",
                        "institution_ids": ["inst:first"],
                    },
                    {
                        "paper_author_name": "Middle Author",
                        "institution_ids": ["inst:middle"],
                    },
                    {
                        "paper_author_name": "Corresponding Author",
                        "author_roles": ["corresponding"],
                        "is_corresponding": True,
                        "institution_ids": ["inst:corresponding"],
                    },
                ]
            }
        },
        "unresolved": {},
    }

    rows, links, coverage = institution_activity(
        field_papers,
        registry={"institutions": {}, "authors": {}},
        paper_affiliations=paper_affiliations,
    )

    assert {row["id"] for row in rows} == {"inst:first", "inst:corresponding"}
    assert links == [
        {
            "institution_1": "inst:corresponding",
            "institution_2": "inst:first",
            "joint_papers": 1,
            "titles": ["Mapped paper"],
            "materials": [],
        }
    ]
    assert coverage["author_scope"] == "first_and_corresponding"
    assert coverage["verified_authors"] == 2

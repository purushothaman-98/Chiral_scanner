from chiral_scanner.research_geography import institution_activity


def test_institution_activity_uses_verified_authors_and_real_paper_links():
    affiliations = [
        {
            "institution": "Institute A",
            "city": "Alpha",
            "country": "Testland",
            "latitude": 1.0,
            "longitude": 2.0,
            "authors": ["Ada A"],
            "evidence_title": "Paper",
            "evidence_url": "https://example.org/a",
        },
        {
            "institution": "Institute B",
            "city": "Beta",
            "country": "Testland",
            "latitude": 3.0,
            "longitude": 4.0,
            "authors": ["Ben B"],
            "evidence_title": "Paper",
            "evidence_url": "https://example.org/b",
        },
    ]
    papers = [
        {
            "base_arxiv_id": "1",
            "authors": ["Ada A", "Ben B", "Unmapped C"],
            "initial_submission_date": "2025-01-02T00:00:00Z",
        },
        {
            "base_arxiv_id": "2",
            "authors": ["Ada A"],
            "initial_submission_date": "2026-01-02T00:00:00Z",
        },
    ]

    institutions, links, coverage = institution_activity(papers, affiliations)

    assert institutions[0]["paper_count"] == 2
    assert institutions[0]["years"] == [2025, 2026]
    assert links == [
        {"institution_1": "Institute A", "institution_2": "Institute B", "joint_papers": 1}
    ]
    assert coverage == {
        "archive_authors": 3,
        "verified_authors": 2,
        "verified_institutions": 2,
    }

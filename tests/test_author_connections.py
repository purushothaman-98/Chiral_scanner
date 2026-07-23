from chiral_scanner.people_map import author_connections


def paper(title, date, authors, materials=None):
    return {
        "title": title,
        "initial_submission_date": date,
        "authors": authors,
        "ai_decision": {"material_or_system_family": materials or []},
    }


def test_author_connections_tracks_years_materials_and_real_coauthorship():
    papers = [
        paper("First", "2023-01-02T00:00:00Z", ["A. Author", "B. Author"], ["Quartz"]),
        paper("Second", "2025-03-04T00:00:00Z", ["A. Author", "B. Author"], ["Tellurium"]),
        paper("Third", "2026-05-06T00:00:00Z", ["A. Author", "C. Author"], ["Tellurium"]),
    ]

    people, links = author_connections(papers)

    lead = people[0]
    assert lead["author"] == "A. Author"
    assert lead["papers"] == 3
    assert lead["years"] == [2023, 2025, 2026]
    assert lead["materials"][0] == "Tellurium"
    assert links[0] == {
        "author_1": "A. Author",
        "author_2": "B. Author",
        "joint_papers": 2,
    }

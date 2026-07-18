from chiral_scanner.history import CONCEPT_STAGES, LANDMARKS


def test_landmark_timeline_is_chronological_and_linked():
    years = [item["year"] for item in LANDMARKS]
    assert years == sorted(years)
    assert all(item["url"].startswith("https://") for item in LANDMARKS)


def test_concept_history_reaches_measurement_and_functionality():
    titles = [title for title, _ in CONCEPT_STAGES]
    assert "Direct verification" in titles
    assert "Functionality" in titles

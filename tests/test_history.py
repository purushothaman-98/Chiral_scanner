from chiral_scanner.history import (
    CONCEPT_STAGES,
    EVIDENCE_LEVELS,
    LANDMARKS,
    MATERIAL_SYSTEMS,
)


def test_history_public_exports_are_available():
    import chiral_scanner.history as history

    for name in ("CONCEPT_STAGES", "EVIDENCE_LEVELS", "LANDMARKS", "MATERIAL_SYSTEMS"):
        assert hasattr(history, name)


def test_landmark_timeline_is_chronological_and_linked():
    years = [item["year"] for item in LANDMARKS]
    assert years == sorted(years)
    assert all(item["url"].startswith("https://") for item in LANDMARKS)


def test_concept_history_reaches_measurement_and_functionality():
    titles = [title for title, _ in CONCEPT_STAGES]
    assert "Direct verification" in titles
    assert "Functionality" in titles


def test_material_map_is_evidence_qualified_and_linked():
    materials = {item["material"] for item in MATERIAL_SYSTEMS}
    assert {"Monolayer WSe₂", "α-HgS (cinnabar)", "α-quartz (SiO₂)", "SrTiO₃"} <= materials
    assert {item["evidence"] for item in MATERIAL_SYSTEMS} <= set(EVIDENCE_LEVELS)
    assert all(item["url"].startswith("https://doi.org/") for item in MATERIAL_SYSTEMS)
    assert all(item["caveat"] for item in MATERIAL_SYSTEMS)


def test_timeline_keeps_multiple_breakthroughs_per_year():
    years = [item["year"] for item in LANDMARKS]
    assert years.count(2023) >= 3
    assert all(item["material"] and item["kind"] for item in LANDMARKS)

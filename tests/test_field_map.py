from chiral_scanner.field_map import (
    ecosystem_areas,
    evidence_stage,
    is_field_paper,
    is_thz_frontier,
)


def paper() -> dict:
    return {
        "title": "THz-driven circular phonons in SrTiO3",
        "abstract": "We measure transient magnetization from circular ionic motion.",
        "ai_decision": {
            "include_in_feed": True,
            "relevance": "Core chiral-phonon paper",
            "research_type": "Theory + Experiment",
            "evidence_level": "Direct magnetic or magneto-optical consequence",
            "research_focus": ["Dynamical multiferroicity / phonomagnetism"],
            "physical_properties": ["Phonon angular momentum"],
        },
    }


def test_paper_can_belong_to_overlapping_ecosystems():
    areas = ecosystem_areas(paper())
    assert "THz & ultrafast control" in areas
    assert "Magnetism & spintronics" in areas
    assert "Fundamental chirality & phonon angular momentum" in areas


def test_thz_frontier_and_evidence_are_researcher_facing():
    assert is_thz_frontier(paper())
    assert evidence_stage(paper()) == "Direct measurement"
    assert is_field_paper(paper())

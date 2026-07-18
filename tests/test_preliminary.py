from chiral_scanner.preliminary import classify_preliminary


def base(title: str, abstract: str) -> dict:
    return {
        "base_arxiv_id": "2401.00002",
        "title": title,
        "abstract": abstract,
        "authors": [],
        "categories": [],
    }


def test_author_actions_identify_experiment():
    result = classify_preliminary(
        base(
            "Chiral phonon detection",
            "We measure helicity-resolved Raman spectra and observe phonon angular momentum.",
        )
    )
    assert result["preliminary_include"] is True
    assert result["preliminary_research_type"] == "Experimental"
    assert "Raman spectroscopy" in result["detected_experimental_methods"]


def test_background_method_does_not_make_computational():
    result = classify_preliminary(
        base(
            "Chiral phonons",
            "Density functional theory has been used previously. We observe the mode experimentally.",
        )
    )
    assert result["preliminary_research_type"] == "Experimental"
    assert result["detected_computational_methods"] == []


def test_false_positive_without_lattice_anchor():
    result = classify_preliminary(
        base("Chiral photon metasurface", "We fabricate a chiral metamaterial for photons.")
    )
    assert result["preliminary_include"] is False

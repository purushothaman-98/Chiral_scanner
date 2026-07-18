from __future__ import annotations

ECOSYSTEM_AREAS = [
    "THz & ultrafast control",
    "Fundamental chirality & phonon angular momentum",
    "Magnetism & spintronics",
    "2D optoelectronics & quantum materials",
    "Transport, Hall & mechanics",
    "Theory & materials discovery",
]


def _text(paper: dict) -> str:
    decision = paper.get("ai_decision") or {}
    values = [paper.get("title", ""), paper.get("abstract", "")]
    for field in (
        "research_focus",
        "chirality_class",
        "generation_mechanisms",
        "experimental_methods",
        "excitation_methods",
        "detection_methods",
        "computational_methods",
        "physical_properties",
        "application_directions",
        "material_or_system_family",
    ):
        value = decision.get(field, [])
        values.extend(value if isinstance(value, list) else [str(value)])
    return " ".join(str(value) for value in values).casefold()


def ecosystem_areas(paper: dict) -> list[str]:
    """Map reviewed papers onto the field's overlapping research communities."""
    text = _text(paper)
    areas: list[str] = []
    rules = {
        "THz & ultrafast control": (
            "terahertz",
            "thz",
            "mid-infrared",
            "ultrafast",
            "pump-probe",
            "coherent",
            "nonlinear phon",
            "dynamical multiferro",
            "phonomagnet",
        ),
        "Fundamental chirality & phonon angular momentum": (
            "phonon angular momentum",
            "pseudo-angular momentum",
            "pseudoangular momentum",
            "true structural/eigenmode chirality",
            "circular/elliptical phonon",
            "chiral phonon",
            "circular ionic",
            "helicity",
        ),
        "Magnetism & spintronics": (
            "magnet",
            "spin",
            "magnon",
            "zeeman",
            "kerr",
            "faraday",
            "barnett",
        ),
        "2D optoelectronics & quantum materials": (
            "two-dimensional",
            "2d ",
            "layered",
            "van der waals",
            "exciton",
            "valley",
            "moiré",
            "moire",
            "polariton",
        ),
        "Transport, Hall & mechanics": (
            "transport",
            "thermal hall",
            "thermal conductivity",
            "seebeck",
            "orbital current",
            "torque",
            "cantilever",
            "einstein-de haas",
            "hall viscosity",
        ),
        "Theory & materials discovery": (
            "first-principles",
            "dft",
            "dfpt",
            "model / theory",
            "model hamiltonian",
            "symmetry analysis",
            "materials discovery",
            "machine learning",
        ),
    }
    for area, terms in rules.items():
        if any(term in text for term in terms):
            areas.append(area)
    return areas or ["Fundamental chirality & phonon angular momentum"]


def evidence_stage(paper: dict) -> str:
    decision = paper.get("ai_decision") or {}
    level = str(decision.get("evidence_level", ""))
    research_type = decision.get("research_type")
    if level.startswith("Direct"):
        return "Direct measurement"
    if level == "Spectroscopic selection-rule evidence":
        return "Experimental evidence"
    if level == "Indirect experimental inference plus modelling":
        return "Experimental indication + modelling"
    if level in {"First-principles prediction", "Model / theory proposal"}:
        return "Prediction / theory"
    if research_type in {"Experimental", "Theory + Experiment"}:
        return "Experimental study"
    if research_type == "Computational / theoretical":
        return "Prediction / theory"
    if decision.get("paper_nature") == "Review / perspective":
        return "Review / perspective"
    return "Evidence not yet resolved"


def is_thz_frontier(paper: dict) -> bool:
    text = _text(paper)
    return any(term in text for term in ("terahertz", "thz", "mid-infrared")) and any(
        term in text
        for term in (
            "chiral phonon",
            "phonon angular momentum",
            "circular phonon",
            "circular ionic",
            "dynamical multiferro",
            "phonomagnet",
            "nonlinear phon",
        )
    )


def is_experimental_evidence(paper: dict) -> bool:
    decision = paper.get("ai_decision") or {}
    return decision.get("research_type") in {"Experimental", "Theory + Experiment"}


def is_field_paper(paper: dict) -> bool:
    decision = paper.get("ai_decision") or {}
    return bool(
        decision
        and decision.get("include_in_feed") is True
        and decision.get("relevance") != "Not relevant"
    )

from __future__ import annotations

import re
from collections.abc import Iterable

from .config import (
    APPLICATION_TERMS,
    AUTHOR_ACTION_PATTERNS,
    EXPERIMENTAL_TERMS,
    FALSE_POSITIVE_TERMS,
    LATTICE_ANCHORS,
    MATERIAL_TERMS,
    PRIMARY_TERMS,
    RELATED_PHENOMENA,
    THEORY_TERMS,
)


def _matches(text: str, terms: Iterable[str]) -> list[str]:
    lowered = text.casefold()
    return [term for term in terms if term.casefold() in lowered]


def _author_action_evidence(text: str, kind: str) -> list[str]:
    evidence: list[str] = []
    for pattern in AUTHOR_ACTION_PATTERNS[kind]:
        evidence.extend(match.group(0) for match in re.finditer(pattern, text, re.IGNORECASE))
    return list(dict.fromkeys(evidence))


def _detect_methods(text: str, terms: list[str], action_evidence: list[str]) -> list[str]:
    if not action_evidence:
        return []
    matches = _matches(text, terms)
    lowered = text.casefold()
    aliases = {
        "Raman spectroscopy": ["raman spectra", "raman scattering", "raman"],
        "resonant inelastic X-ray scattering": ["rixs"],
        "Kerr rotation": ["moke", "magneto-optical kerr"],
        "Faraday rotation": ["faraday effect"],
    }
    for canonical, variants in aliases.items():
        if any(variant in lowered for variant in variants):
            matches.append(canonical)
    return list(dict.fromkeys(matches))


def _paper_nature(text: str) -> str:
    lowered = text.casefold()
    if any(term in lowered for term in ["we review", "this review", "perspective", "roadmap"]):
        return "Review / perspective"
    if any(term in lowered for term in ["software", "code package", "workflow", "methodology", "we introduce a method"]):
        return "Methods / software"
    if any(term in lowered for term in ["dataset", "benchmark database", "high-throughput database"]):
        return "Dataset / benchmark"
    return "Original research"


def classify_preliminary(paper: dict) -> dict:
    text = f'{paper.get("title", "")}\n{paper.get("abstract", "")}'
    primary = _matches(text, PRIMARY_TERMS)
    related = _matches(text, RELATED_PHENOMENA)
    materials = _matches(text, MATERIAL_TERMS)
    applications = _matches(text, APPLICATION_TERMS)
    false_positive = _matches(text, FALSE_POSITIVE_TERMS)
    lattice_anchor = _matches(text, LATTICE_ANCHORS)

    experimental_actions = _author_action_evidence(text, "experimental")
    computational_actions = _author_action_evidence(text, "computational")
    experimental_methods = _detect_methods(text, EXPERIMENTAL_TERMS, experimental_actions)
    computational_methods = _detect_methods(text, THEORY_TERMS, computational_actions)

    if experimental_actions and computational_actions:
        research_type = "Theory + Experiment"
    elif experimental_actions:
        research_type = "Experimental"
    elif computational_actions:
        research_type = "Computational / theoretical"
    else:
        research_type = "Unclassified"

    false_positive_only = bool(false_positive and not lattice_anchor and not primary)
    preliminary_pass = bool(primary or related) and not false_positive_only
    if not preliminary_pass and lattice_anchor and (applications or materials):
        preliminary_pass = True

    matched = list(dict.fromkeys(primary + related + applications + lattice_anchor))
    evidence = {
        "primary_terms": primary,
        "related_terms": related,
        "author_experimental_actions": experimental_actions,
        "author_computational_actions": computational_actions,
        "false_positive_terms": false_positive,
        "lattice_anchors": lattice_anchor,
    }

    return {
        **paper,
        "preliminary_include": preliminary_pass,
        "preliminary_research_type": research_type,
        "preliminary_paper_nature": _paper_nature(text),
        "detected_materials_or_systems": materials,
        "detected_experimental_methods": experimental_methods,
        "detected_computational_methods": computational_methods,
        "detected_physical_properties": list(dict.fromkeys(primary + related)),
        "matched_keywords": matched,
        "classification_evidence": evidence,
    }

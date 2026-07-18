import pytest
from pydantic import ValidationError

from chiral_scanner.ai_classifier import build_system_prompt
from chiral_scanner.models import AIDecision


def test_prompt_separates_field_archetypes():
    prompt = build_system_prompt()
    assert "Intrinsic chiral eigenmodes" in prompt
    assert "Coherently driven circular/axial modes" in prompt
    assert "Structural chirality control" in prompt


VALID = {
    "include_in_feed": True,
    "relevance": "Core chiral-phonon paper",
    "research_type": "Experimental",
    "paper_nature": "Original research",
    "materials_or_systems": ["SrTiO3"],
    "material_or_system_family": ["Perovskite oxides"],
    "research_focus": ["Dynamical multiferroicity / phonomagnetism"],
    "chirality_class": ["Circular/elliptical phonon polarization"],
    "phonon_character": ["Infrared-active", "Polar / ferroelectric soft mode"],
    "generation_mechanisms": ["Circular/elliptical THz resonant drive"],
    "experimental_methods": ["Ultrafast THz pump-probe"],
    "computational_methods": [],
    "physical_properties": ["Transient magnetization"],
    "evidence_level": "Direct magnetic or magneto-optical consequence",
    "evidence_caveats": ["magnetization does not directly establish eigenmode chirality"],
    "application_directions": ["Ultrafast magnetic control"],
    "confidence": 0.94,
    "reason": "The authors directly drive a circular polar phonon and measure magnetization.",
    "supporting_phrases": ["circular polar phonon", "transient magnetization"],
}


def test_valid_ai_output():
    decision = AIDecision.model_validate(VALID)
    assert decision.confidence == 0.94


def test_invalid_confidence_rejected():
    with pytest.raises(ValidationError):
        AIDecision.model_validate({**VALID, "confidence": 1.5})


def test_scientific_axes_remain_separate():
    decision = AIDecision.model_validate(VALID)
    assert decision.chirality_class == ["Circular/elliptical phonon polarization"]
    assert decision.evidence_level == "Direct magnetic or magneto-optical consequence"


def test_invented_method_label_is_rejected_even_without_json_schema():
    with pytest.raises(ValidationError):
        AIDecision.model_validate(
            {**VALID, "experimental_methods": ["Ultrafast quantum chirality imaging"]}
        )

import pytest
from pydantic import ValidationError

from chiral_scanner.models import AIDecision

VALID = {
    "include_in_feed": True,
    "relevance": "Core chiral-phonon paper",
    "research_type": "Experimental",
    "paper_nature": "Original research",
    "materials_or_systems": ["SrTiO3"],
    "material_or_system_family": ["Perovskite oxides"],
    "experimental_methods": ["THz pump-probe"],
    "computational_methods": [],
    "physical_properties": ["Transient magnetization"],
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

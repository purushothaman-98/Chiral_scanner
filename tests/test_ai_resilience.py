import json
import time

import requests

from chiral_scanner.ai_classifier import (
    decision_schema,
    parse_decision,
    retry_after_seconds,
)


def valid_payload() -> dict:
    return {
        "include_in_feed": True,
        "relevance": "Core chiral-phonon paper",
        "research_type": "Experimental",
        "paper_nature": "Original research",
        "materials_or_systems": ["SrTiO3"],
        "material_or_system_family": ["Perovskite oxides"],
        "research_focus": ["Dynamical multiferroicity / phonomagnetism"],
        "chirality_class": ["Circular/elliptical phonon polarization"],
        "phonon_character": ["Infrared-active"],
        "generation_mechanisms": ["Circular/elliptical THz resonant drive"],
        "experimental_methods": ["Ultrafast THz pump-probe"],
        "excitation_methods": ["Circular/elliptical THz excitation"],
        "detection_methods": ["Kerr/Faraday polarimetry"],
        "computational_methods": [],
        "physical_properties": ["Transient magnetization"],
        "evidence_level": "Direct magnetic or magneto-optical consequence",
        "evidence_caveats": [],
        "application_directions": ["Ultrafast magnetic control"],
        "confidence": 0.9,
        "reason": "Direct circular phonon drive and magneto-optical detection.",
        "supporting_phrases": ["circular phonon", "transient magnetization"],
    }


def response_with_headers(headers: dict[str, str]) -> requests.Response:
    response = requests.Response()
    response.status_code = 429
    response.headers.update(headers)
    return response


def test_reason_limit_is_declared_in_provider_schema():
    reason = decision_schema()["schema"]["properties"]["reason"]
    assert reason["maxLength"] == 500


def test_overlong_reason_is_normalized_without_another_api_call():
    payload = valid_payload()
    payload["reason"] = "word " * 150
    decision = parse_decision(json.dumps(payload))
    assert len(decision.reason) <= 500


def test_retry_after_header_takes_priority():
    response = response_with_headers(
        {"Retry-After": "42", "x-ratelimit-reset": str(time.time() + 300)}
    )
    assert retry_after_seconds(response) == 42


def test_rate_limit_reset_is_converted_to_wait_seconds():
    response = response_with_headers({"x-ratelimit-reset": str(time.time() + 30)})
    wait = retry_after_seconds(response)
    assert wait is not None
    assert 25 <= wait <= 30

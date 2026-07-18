from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import requests

from .config import (
    COMPUTATIONAL_METHOD_GROUPS,
    DEFAULT_AI_MODEL,
    EXPERIMENTAL_METHOD_GROUPS,
    MATERIAL_FAMILIES,
    PHYSICAL_PROPERTIES,
    PROMPT_VERSION,
)
from .models import AIDecision
from .storage import fingerprint

LOGGER = logging.getLogger(__name__)
ENDPOINT = "https://models.github.ai/inference/chat/completions"


def build_system_prompt() -> str:
    return f"""You are a scientific abstract classifier for a chiral-phonon research scanner.

Judge the supplied title and complete abstract together. A keyword match alone is insufficient.
Include papers whose scientific focus is chiral phonons, phonon angular momentum, phonon chirality/helicity, dynamical multiferroicity, phonomagnetism, circularly driven lattice modes, angular-momentum transfer involving phonons, or a tightly connected experimental/theoretical mechanism.

Set include_in_feed=false only when the topic is incidental, background-only, metaphorical, or scientifically unrelated. Preserve borderline cases as Uncertain with include_in_feed=true so a human can review them.

Research-type rules:
- Experimental requires original measurements/fabrication/detection reported by the paper's authors.
- Computational / theoretical requires original calculations, derivations, models, or simulations.
- Theory + Experiment requires independent evidence that the same paper reports both original experimental work and original theory/computation.
- Do not call a paper experimental merely because it compares with prior measurements.
- Do not call a paper computational merely because a method is mentioned as background.

Never invent materials, systems, methods, measurements, or properties.
Use normalized canonical groups when supported.
Material/system families: {json.dumps(MATERIAL_FAMILIES)}
Experimental method groups: {json.dumps(EXPERIMENTAL_METHOD_GROUPS)}
Computational method groups: {json.dumps(COMPUTATIONAL_METHOD_GROUPS)}
Physical properties: {json.dumps(PHYSICAL_PROPERTIES)}

Return only valid JSON matching the requested schema. Supporting phrases must be short exact or near-exact phrases from the supplied title/abstract, never fabricated. Prompt version: {PROMPT_VERSION}.
"""


def decision_schema() -> dict:
    return {
        "name": "chiral_phonon_classification",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "include_in_feed",
                "relevance",
                "research_type",
                "paper_nature",
                "materials_or_systems",
                "material_or_system_family",
                "experimental_methods",
                "computational_methods",
                "physical_properties",
                "confidence",
                "reason",
                "supporting_phrases",
            ],
            "properties": {
                "include_in_feed": {"type": "boolean"},
                "relevance": {
                    "type": "string",
                    "enum": [
                        "Core chiral-phonon paper",
                        "Chiral-phonon-adjacent",
                        "Uncertain",
                        "Not relevant",
                    ],
                },
                "research_type": {
                    "type": "string",
                    "enum": [
                        "Experimental",
                        "Computational / theoretical",
                        "Theory + Experiment",
                        "Unclassified",
                    ],
                },
                "paper_nature": {
                    "type": "string",
                    "enum": [
                        "Original research",
                        "Review / perspective",
                        "Methods / software",
                        "Dataset / benchmark",
                        "Uncertain",
                    ],
                },
                "materials_or_systems": {"type": "array", "items": {"type": "string"}},
                "material_or_system_family": {"type": "array", "items": {"type": "string"}},
                "experimental_methods": {"type": "array", "items": {"type": "string"}},
                "computational_methods": {"type": "array", "items": {"type": "string"}},
                "physical_properties": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reason": {"type": "string"},
                "supporting_phrases": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 5,
                    "items": {"type": "string"},
                },
            },
        },
    }


def classify_paper(
    paper: dict,
    *,
    token: str,
    model: str = DEFAULT_AI_MODEL,
    timeout: int = 120,
    retries: int = 3,
) -> dict:
    user_payload = {
        "title": paper.get("title", ""),
        "authors": paper.get("authors", []),
        "abstract": paper.get("abstract", ""),
    }
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "temperature": 0,
        "max_tokens": 1200,
        "response_format": {
            "type": "json_schema",
            "json_schema": decision_schema(),
        },
    }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(ENDPOINT, headers=headers, json=request_body, timeout=timeout)
            if response.status_code in {400, 422} and attempt == 0:
                request_body["response_format"] = {"type": "json_object"}
                response = requests.post(
                    ENDPOINT, headers=headers, json=request_body, timeout=timeout
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = AIDecision.model_validate_json(content)
            return {
                "base_arxiv_id": paper["base_arxiv_id"],
                "fingerprint": fingerprint(paper),
                "prompt_version": PROMPT_VERSION,
                "model": model,
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "decision": parsed.model_dump(),
            }
        except (requests.RequestException, KeyError, ValueError) as exc:
            last_error = exc
            LOGGER.warning("AI classification attempt %s failed: %s", attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep(2**attempt * 3)
    raise RuntimeError(f"AI classification failed after {retries} attempts") from last_error

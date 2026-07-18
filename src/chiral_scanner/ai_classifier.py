from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timezone

import requests

from .config import (
    APPLICATION_DIRECTIONS,
    CHIRALITY_CLASSES,
    COMPUTATIONAL_METHOD_GROUPS,
    DEFAULT_AI_MODEL,
    DETECTION_METHOD_GROUPS,
    EVIDENCE_LEVELS,
    EXCITATION_METHOD_GROUPS,
    EXPERIMENTAL_METHOD_GROUPS,
    GENERATION_MECHANISMS,
    MATERIAL_FAMILIES,
    PHONON_CHARACTERISTICS,
    PHYSICAL_PROPERTIES,
    PROMPT_VERSION,
    RESEARCH_FOCUS_AREAS,
)
from .models import AIDecision
from .scope import has_chiral_phonon_scope
from .storage import fingerprint

LOGGER = logging.getLogger(__name__)
ENDPOINT = "https://models.github.ai/inference/chat/completions"
MAX_RATE_LIMIT_WAIT_SECONDS = 90.0


class RateLimitError(RuntimeError):
    """The provider asked this batch to stop and resume in a later workflow."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def retry_after_seconds(response: requests.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw:
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
    reset = response.headers.get("x-ratelimit-reset")
    if reset:
        try:
            return max(0.0, float(reset) - time.time())
        except ValueError:
            pass
    return None


def parse_decision(content: str) -> AIDecision:
    payload = json.loads(content)
    # Length is presentation metadata, not scientific content. Normalize it locally
    # so an otherwise valid classification never consumes another model request.
    if isinstance(payload, dict) and isinstance(payload.get("reason"), str):
        payload["reason"] = " ".join(payload["reason"].split())[:500].rstrip()
    return AIDecision.model_validate(payload)


def build_system_prompt() -> str:
    return f"""You are a scientific abstract classifier for a chiral-phonon research scanner.

Judge the supplied title and complete abstract together. A keyword match alone is insufficient.
Include papers whose scientific focus is chiral phonons, phonon angular momentum, phonon chirality/helicity, dynamical multiferroicity, phonomagnetism, circularly driven lattice modes, angular-momentum transfer involving phonons, or a tightly connected experimental/theoretical mechanism.

Set include_in_feed=false only when the topic is incidental, background-only, metaphorical, or scientifically unrelated. Preserve borderline cases as Uncertain with include_in_feed=true so a human can review them.

Scope requirement: an included paper must study a phonon, lattice vibration, ionic motion, or vibrational mode together with chirality, helicity, circular motion, angular momentum, phonomagnetism, dynamical multiferroicity, or a directly related phonon effect. Electronic chiral edges, chiral charge-density waves, fermion/QFT chirality, photonic or polaritonic chirality, generic spin-lattice coupling, and thermal Hall papers are not relevant unless the abstract explicitly makes phonons central to the reported result.

Research-type rules:
- Experimental requires original measurements/fabrication/detection reported by the paper's authors.
- Computational / theoretical requires original calculations, derivations, models, or simulations.
- Theory + Experiment requires independent evidence that the same paper reports both original experimental work and original theory/computation.
- Do not call a paper experimental merely because it compares with prior measurements.
- Do not call a paper computational merely because a method is mentioned as background.

Scientific-separation rules:
- Distinguish a truly chiral structural/eigenmode from circular or elliptical ionic motion.
- Do not equate crystal/valley pseudo-angular momentum with real-space phonon angular momentum.
- Distinguish a normal-mode property from a coherently driven superposition or transient state.
- Assign experimental methods only when the paper's authors actually perform them. A technique
  mentioned in motivation, prior work, comparison, or a proposal is not an experimental method.
- Assign a physical property only when the abstract reports, calculates, or explicitly predicts it.
- Choose the strongest evidence level supported by the abstract, not by general field knowledge.
- Use "Claimed or ambiguous chirality" and an evidence caveat when the abstract does not resolve
  whether chirality means true structural chirality, circular polarization, or pseudo-angular momentum.
- Do not infer a wavevector, mode activity, degeneracy, application, or material family from the title alone.

Field-evolution reference rules (use as scientific archetypes, never as keyword shortcuts):
- Intrinsic chiral eigenmodes: finite-q handed eigenvectors tied to broken inversion/chiral
  structure, as in WSe2 valley modes, alpha-HgS, alpha-quartz, tellurium and polar LiNbO3.
- Coherently driven circular/axial modes: two orthogonal mode coordinates in quadrature,
  including THz/mid-IR work in ErFeO3, CeF3, SrTiO3, Bi2Se3 and phonon-polaritons.
- Angular-momentum transfer: phonon-to-spin, spin-to-phonon, phonon-to-phonon or mechanical
  torque, including magnon-phonon hybridization. State the transfer direction when supported.
- Structural chirality control: a driven ferrichiral/chiral structure is adjacent unless the
  work also establishes phonon angular momentum or a chiral phonon eigenmode.
- Direct detection outranks inference only when the abstract reports momentum-resolved
  polarization, phase-resolved ionic trajectories, mechanical torque, or another observable
  that resolves handed lattice motion/angular momentum. Kerr/Faraday signals alone are a
  driven response and may require a caveat about electronic or non-magnetic contributions.
- A paper may be core even when it does not use the phrase "chiral phonon" if phonon angular
  momentum or handed lattice motion is the central measured/calculated quantity.

Never invent materials, systems, methods, measurements, or properties.
For every family and grouped-method field, use only exact labels from the canonical lists.
Material/system families: {json.dumps(MATERIAL_FAMILIES)}
Research focus areas: {json.dumps(RESEARCH_FOCUS_AREAS)}
Chirality classes: {json.dumps(CHIRALITY_CLASSES)}
Phonon characteristics: {json.dumps(PHONON_CHARACTERISTICS)}
Generation mechanisms: {json.dumps(GENERATION_MECHANISMS)}
Experimental method groups: {json.dumps(EXPERIMENTAL_METHOD_GROUPS)}
Excitation method groups: {json.dumps(EXCITATION_METHOD_GROUPS)}
Detection method groups: {json.dumps(DETECTION_METHOD_GROUPS)}
Computational method groups: {json.dumps(COMPUTATIONAL_METHOD_GROUPS)}
Physical properties: {json.dumps(PHYSICAL_PROPERTIES)}
Evidence levels (select exactly one): {json.dumps(EVIDENCE_LEVELS)}
Application directions: {json.dumps(APPLICATION_DIRECTIONS)}

Evidence caveats must be short scientific limitations grounded in the abstract, for example
"chirality inferred rather than directly observed" or "pseudo-angular momentum only". Return an
empty list when no caveat is needed. Supporting phrases must be short exact or near-exact phrases
from the supplied title/abstract, never fabricated. Return only valid JSON matching the requested
schema. Keep reason concise (at most 350 characters). Prompt version: {PROMPT_VERSION}.
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
                "research_focus",
                "chirality_class",
                "phonon_character",
                "generation_mechanisms",
                "experimental_methods",
                "excitation_methods",
                "detection_methods",
                "computational_methods",
                "physical_properties",
                "evidence_level",
                "evidence_caveats",
                "application_directions",
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
                "material_or_system_family": {
                    "type": "array",
                    "items": {"type": "string", "enum": MATERIAL_FAMILIES},
                },
                "research_focus": {
                    "type": "array",
                    "items": {"type": "string", "enum": RESEARCH_FOCUS_AREAS},
                },
                "chirality_class": {
                    "type": "array",
                    "items": {"type": "string", "enum": CHIRALITY_CLASSES},
                },
                "phonon_character": {
                    "type": "array",
                    "items": {"type": "string", "enum": PHONON_CHARACTERISTICS},
                },
                "generation_mechanisms": {
                    "type": "array",
                    "items": {"type": "string", "enum": GENERATION_MECHANISMS},
                },
                "experimental_methods": {
                    "type": "array",
                    "items": {"type": "string", "enum": EXPERIMENTAL_METHOD_GROUPS},
                },
                "excitation_methods": {
                    "type": "array",
                    "items": {"type": "string", "enum": EXCITATION_METHOD_GROUPS},
                },
                "detection_methods": {
                    "type": "array",
                    "items": {"type": "string", "enum": DETECTION_METHOD_GROUPS},
                },
                "computational_methods": {
                    "type": "array",
                    "items": {"type": "string", "enum": COMPUTATIONAL_METHOD_GROUPS},
                },
                "physical_properties": {
                    "type": "array",
                    "items": {"type": "string", "enum": PHYSICAL_PROPERTIES},
                },
                "evidence_level": {"type": "string", "enum": EVIDENCE_LEVELS},
                "evidence_caveats": {
                    "type": "array",
                    "maxItems": 4,
                    "items": {"type": "string"},
                },
                "application_directions": {
                    "type": "array",
                    "items": {"type": "string", "enum": APPLICATION_DIRECTIONS},
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reason": {"type": "string", "minLength": 5, "maxLength": 500},
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
            if response.status_code == 429:
                retry_after = retry_after_seconds(response)
                if (
                    attempt < retries - 1
                    and retry_after is not None
                    and retry_after <= MAX_RATE_LIMIT_WAIT_SECONDS
                ):
                    wait = retry_after + random.uniform(0.5, 2.0)
                    LOGGER.warning("Rate limited; pausing %.1f seconds", wait)
                    time.sleep(wait)
                    continue
                raise RateLimitError(
                    "GitHub Models rate limit reached; resume in the next checkpoint",
                    retry_after=retry_after,
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = parse_decision(content)
            if parsed.include_in_feed and not has_chiral_phonon_scope(
                paper.get("title", ""), paper.get("abstract", "")
            ):
                parsed.include_in_feed = False
                parsed.relevance = "Not relevant"
                parsed.reason = (
                    "Excluded by the independent scope guard: the abstract does not make "
                    "a phonon, lattice vibration, ionic motion, or vibrational mode central "
                    "to the claimed chiral or angular-momentum result."
                )
            return {
                "base_arxiv_id": paper["base_arxiv_id"],
                "fingerprint": fingerprint(paper),
                "prompt_version": PROMPT_VERSION,
                "model": model,
                "classified_at": datetime.now(timezone.utc).isoformat(),
                "decision": parsed.model_dump(),
            }
        except RateLimitError:
            raise
        except (requests.RequestException, KeyError, ValueError) as exc:
            last_error = exc
            LOGGER.warning("AI classification attempt %s failed: %s", attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep((2**attempt * 3) + random.uniform(0.25, 1.25))
    raise RuntimeError(f"AI classification failed after {retries} attempts") from last_error

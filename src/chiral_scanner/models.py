from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from .config import (
    APPLICATION_DIRECTIONS,
    CHIRALITY_CLASSES,
    COMPUTATIONAL_METHOD_GROUPS,
    DETECTION_METHOD_GROUPS,
    EVIDENCE_LEVELS,
    EXCITATION_METHOD_GROUPS,
    EXPERIMENTAL_METHOD_GROUPS,
    GENERATION_MECHANISMS,
    MATERIAL_FAMILIES,
    PHONON_CHARACTERISTICS,
    PHYSICAL_PROPERTIES,
    RESEARCH_FOCUS_AREAS,
)

CANONICAL_LIST_FIELDS = {
    "material_or_system_family": set(MATERIAL_FAMILIES),
    "research_focus": set(RESEARCH_FOCUS_AREAS),
    "chirality_class": set(CHIRALITY_CLASSES),
    "phonon_character": set(PHONON_CHARACTERISTICS),
    "generation_mechanisms": set(GENERATION_MECHANISMS),
    "experimental_methods": set(EXPERIMENTAL_METHOD_GROUPS),
    "excitation_methods": set(EXCITATION_METHOD_GROUPS),
    "detection_methods": set(DETECTION_METHOD_GROUPS),
    "computational_methods": set(COMPUTATIONAL_METHOD_GROUPS),
    "physical_properties": set(PHYSICAL_PROPERTIES),
    "application_directions": set(APPLICATION_DIRECTIONS),
}

ResearchType = Literal[
    "Experimental",
    "Computational / theoretical",
    "Theory + Experiment",
    "Unclassified",
]
PaperNature = Literal[
    "Original research",
    "Review / perspective",
    "Methods / software",
    "Dataset / benchmark",
    "Uncertain",
]
Relevance = Literal[
    "Core chiral-phonon paper",
    "Chiral-phonon-adjacent",
    "Uncertain",
    "Not relevant",
]


class AIDecision(BaseModel):
    include_in_feed: bool
    relevance: Relevance
    research_type: ResearchType
    paper_nature: PaperNature
    materials_or_systems: list[str] = Field(default_factory=list)
    material_or_system_family: list[str] = Field(default_factory=list)
    research_focus: list[str] = Field(default_factory=list)
    chirality_class: list[str] = Field(default_factory=list)
    phonon_character: list[str] = Field(default_factory=list)
    generation_mechanisms: list[str] = Field(default_factory=list)
    experimental_methods: list[str] = Field(default_factory=list)
    excitation_methods: list[str] = Field(default_factory=list)
    detection_methods: list[str] = Field(default_factory=list)
    computational_methods: list[str] = Field(default_factory=list)
    physical_properties: list[str] = Field(default_factory=list)
    evidence_level: str = "Insufficient abstract evidence"
    evidence_caveats: list[str] = Field(default_factory=list)
    application_directions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=5, max_length=500)
    supporting_phrases: list[str] = Field(min_length=2, max_length=5)

    @field_validator(
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
        "evidence_caveats",
        "application_directions",
        "supporting_phrases",
    )
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            item = " ".join(str(value).split()).strip(" ,;.")
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned

    @field_validator(*CANONICAL_LIST_FIELDS)
    @classmethod
    def require_canonical_labels(cls, values: list[str], info: ValidationInfo) -> list[str]:
        allowed = CANONICAL_LIST_FIELDS[info.field_name]
        invalid = sorted(set(values) - allowed)
        if invalid:
            raise ValueError(f"non-canonical {info.field_name}: {', '.join(invalid)}")
        return values

    @field_validator("evidence_level")
    @classmethod
    def require_canonical_evidence_level(cls, value: str) -> str:
        if value not in EVIDENCE_LEVELS:
            raise ValueError(f"non-canonical evidence_level: {value}")
        return value


class ScanSummary(BaseModel):
    scan_timestamp: datetime
    earliest_queried_date: str
    latest_queried_date: str
    fetched: int
    preliminary_passing: int
    newly_added: int = 0
    updated: int = 0
    total_archive_size: int = 0
    query_count: int = 0

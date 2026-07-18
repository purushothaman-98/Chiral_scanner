from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

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
    experimental_methods: list[str] = Field(default_factory=list)
    excitation_methods: list[str] = Field(default_factory=list)
    detection_methods: list[str] = Field(default_factory=list)
    computational_methods: list[str] = Field(default_factory=list)
    physical_properties: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=5, max_length=500)
    supporting_phrases: list[str] = Field(min_length=2, max_length=5)

    @field_validator(
        "materials_or_systems",
        "material_or_system_family",
        "experimental_methods",
        "excitation_methods",
        "detection_methods",
        "computational_methods",
        "physical_properties",
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

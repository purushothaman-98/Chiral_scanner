from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

EXPLICIT_FIELD_TERMS = (
    "chiral phonon",
    "phonon chirality",
    "phonon angular momentum",
    "pseudo-angular momentum",
    "pseudoangular momentum",
    "circular ionic",
    "circularly polarized phonon",
    "elliptically polarized phonon",
    "phonomagnet",
    "dynamical multiferro",
)

FALSE_FRIEND_CONTEXTS = (
    "phonon blockade",
    "phonon laser",
    "phonon lasing",
    "chiral network",
    "chiral edge",
    "chiral waveguide",
    "chiral channel",
)


def _text(paper: dict) -> str:
    return f"{paper.get('title', '')} {paper.get('abstract', '')}".casefold()


def _date(paper: dict) -> datetime | None:
    value = paper.get("initial_submission_date")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def signal_tier(paper: dict) -> str:
    """Conservative researcher-facing tier; it never mutates the stored AI decision."""
    decision = paper.get("ai_decision") or {}
    if decision.get("include_in_feed") is not True:
        return "Discovery archive"
    text = _text(paper)
    explicit = any(term in text for term in EXPLICIT_FIELD_TERMS)
    properties = set(decision.get("physical_properties", []))
    chirality = set(decision.get("chirality_class", []))
    has_scientific_anchor = explicit or bool(
        properties.intersection({"Phonon angular momentum", "Phonon magnetic moment"})
    )
    ambiguous_only = chirality == {"Claimed or ambiguous chirality"}
    false_friend_only = any(term in text for term in FALSE_FRIEND_CONTEXTS) and not explicit
    if has_scientific_anchor and not (ambiguous_only and false_friend_only):
        return "Strong field signal"
    if decision.get("relevance") == "Uncertain" or false_friend_only:
        return "Needs interpretation"
    return "Connected research"


def field_brief(papers: list[dict], *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    reviewed = [paper for paper in papers if paper.get("ai_decision")]
    mapped = [
        paper
        for paper in reviewed
        if (paper.get("ai_decision") or {}).get("include_in_feed") is True
    ]
    strong = [paper for paper in mapped if signal_tier(paper) == "Strong field signal"]
    interpretation = [paper for paper in mapped if signal_tier(paper) == "Needs interpretation"]
    cutoff = now - timedelta(days=30)
    recent = [paper for paper in mapped if (published := _date(paper)) and published >= cutoff]
    experimental = [
        paper
        for paper in strong
        if (paper.get("ai_decision") or {}).get("research_type")
        in {"Experimental", "Theory + Experiment"}
    ]
    direct = [
        paper
        for paper in strong
        if str((paper.get("ai_decision") or {}).get("evidence_level", "")).startswith("Direct")
    ]

    def top_values(field: str, source: list[dict], limit: int = 5) -> list[tuple[str, int]]:
        values: Counter[str] = Counter()
        for paper in source:
            item = (paper.get("ai_decision") or {}).get(field, [])
            values.update(item if isinstance(item, list) else [str(item)])
        return values.most_common(limit)

    return {
        "reviewed": len(reviewed),
        "mapped": len(mapped),
        "strong": len(strong),
        "needs_interpretation": len(interpretation),
        "recent": len(recent),
        "experimental": len(experimental),
        "direct": len(direct),
        "top_materials": top_values("material_or_system_family", strong),
        "top_focus": top_values("research_focus", strong),
        "top_methods": top_values("experimental_methods", experimental),
    }

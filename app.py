from __future__ import annotations

# ruff: noqa: E402 -- source-path bootstrap must precede project imports on Streamlit Cloud.
import hashlib
import hmac
import html
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

# Streamlit Cloud can retain an older editable package between rapid redeploys. Ensure the
# checked-out source tree wins over any stale site-packages copy before project imports.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from chiral_scanner.field_map import (
    ecosystem_areas,
    evidence_stage,
    is_experimental_evidence,
    is_field_paper,
    is_thz_frontier,
)
from chiral_scanner.github_dispatch import dispatch_metadata_scan

try:
    from chiral_scanner.history_v2 import (
        CONCEPT_STAGES,
        EVIDENCE_LEVELS,
        LANDMARKS,
        MATERIAL_SYSTEMS,
    )
except ImportError:
    # Keep the site alive if Streamlit's in-place pull leaves app.py newer than history.py.
    from chiral_scanner.history import CONCEPT_STAGES, LANDMARKS

    EVIDENCE_LEVELS = {}
    MATERIAL_SYSTEMS = []
from chiral_scanner.research_intelligence import (
    FUNDED_PROJECTS,
    FUNDING_WATCH,
    INDUSTRY_SIGNALS,
    NEWS,
)
from chiral_scanner.scope import has_chiral_phonon_scope
from chiral_scanner.storage import empty_archive, load_json
from chiral_scanner.ui import flatten_unique, paginate

DATA = ROOT / "data"

st.set_page_config(
    page_title="Chiral Phonon Research Scanner",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.2rem; max-width: 1440px;}
.topline {color:#a78bfa; font-size:.76rem; font-weight:700; letter-spacing:.13em; margin-bottom:.55rem;}
.hero {padding:1.55rem 1.8rem; border:1px solid rgba(139,92,246,.32); border-radius:20px;
background:radial-gradient(circle at 90% 0%,rgba(124,58,237,.22),transparent 38%),
linear-gradient(135deg,rgba(15,23,42,.97),rgba(17,13,35,.97)); margin-bottom:1rem;}
.hero h1 {margin:0; font-size:2.35rem; letter-spacing:-.04em;}
.hero p {max-width:940px; color:#c4b5fd; font-size:1rem; margin:.55rem 0 0;}
.coverage {padding:.7rem 1rem; border-radius:12px; background:rgba(139,92,246,.08);
border:1px solid rgba(139,92,246,.18); color:#cbd5e1; font-size:.88rem; margin:.65rem 0 1rem;}
.date-row {display:flex; align-items:center; gap:.7rem; margin:1.45rem 0 .25rem;}
.date-row h2 {font-size:1.22rem; margin:0;}
.count-pill {font-size:.74rem; color:#c4b5fd; padding:.15rem .48rem; border-radius:999px;
background:rgba(139,92,246,.14); border:1px solid rgba(139,92,246,.28);}
.paper-title {font-size:1.08rem; font-weight:700; line-height:1.35; margin-bottom:.2rem;}
.paper-title a {color:inherit; text-decoration:none;}
.paper-title a:hover {color:#a78bfa;}
.meta {color:#94a3b8; font-size:.82rem; margin:.2rem 0 .4rem;}
.badge {display:inline-block; padding:.18rem .48rem; margin:.12rem .2rem .12rem 0;
border-radius:999px; background:rgba(124,58,237,.13); border:1px solid rgba(139,92,246,.28);
font-size:.73rem; color:#ddd6fe;}
.status-approved {background:rgba(16,185,129,.12); border-color:rgba(16,185,129,.35); color:#a7f3d0;}
.status-pending {background:rgba(245,158,11,.12); border-color:rgba(245,158,11,.35); color:#fde68a;}
.status-review {background:rgba(244,63,94,.11); border-color:rgba(244,63,94,.32); color:#fecdd3;}
.abstract {color:#d1d5db; line-height:1.55; margin:.55rem 0;}
div[data-testid="stMetric"] {padding:.45rem .2rem;}
div[data-testid="stMetricLabel"] {font-size:.82rem;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=120)
def load_all() -> tuple[dict, list[dict], list[dict], list[dict]]:
    return (
        load_json(DATA / "papers.json", empty_archive()),
        load_json(DATA / "scan_history.json", []),
        load_json(DATA / "events.json", []),
        load_json(DATA / "tools.json", []),
    )


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def short_date(value: str | None) -> str:
    parsed = parse_date(value)
    return parsed.strftime("%d %b %Y") if parsed else "—"


def scope_passes(paper: dict) -> bool:
    return has_chiral_phonon_scope(paper.get("title", ""), paper.get("abstract", ""))


def feed_status(paper: dict) -> str:
    if not paper.get("ai_decision"):
        if paper.get("preliminary_include") is not True and not scope_passes(paper):
            return "Discovery archive"
        return "Awaiting classification"
    decision = paper["ai_decision"]
    if decision.get("relevance") == "Uncertain":
        return "Open interpretation"
    if decision.get("include_in_feed") is True:
        return "Field ecosystem"
    return "Outside current field map"


def is_experimental_study(paper: dict) -> bool:
    return is_field_paper(paper) and is_experimental_evidence(paper)


def badges(values: list[str], status: str | None = None) -> str:
    result: list[str] = []
    for index, value in enumerate(value for value in values if value):
        extra = ""
        if index == 0 and status == "Field ecosystem":
            extra = " status-approved"
        elif index == 0 and status == "Awaiting classification":
            extra = " status-pending"
        elif index == 0 and status == "Open interpretation":
            extra = " status-review"
        result.append(f'<span class="badge{extra}">{html.escape(str(value))}</span>')
    return "".join(result)


def paper_card(paper: dict) -> None:
    decision = paper.get("ai_decision") or {}
    status = feed_status(paper)
    title = html.escape(str(paper.get("title", "Untitled")))
    url = html.escape(str(paper.get("abstract_url", "https://arxiv.org")))
    author_names = ", ".join(str(author) for author in paper.get("authors", [])[:5])
    if len(paper.get("authors", [])) > 5:
        author_names += " et al."
    abstract = str(paper.get("abstract", ""))
    preview = abstract if len(abstract) <= 430 else abstract[:427].rstrip() + "…"
    systems = decision.get("material_or_system_family", []) + decision.get(
        "materials_or_systems", []
    )
    methods = (
        decision.get("experimental_methods", [])
        + decision.get("excitation_methods", [])
        + decision.get("detection_methods", [])
        + decision.get("computational_methods", [])
    )
    scientific_identity = (
        decision.get("research_focus", [])
        + decision.get("chirality_class", [])
        + decision.get("phonon_character", [])
    )
    field_areas = ecosystem_areas(paper) if decision else []
    tags = [status]
    if decision:
        tags.extend([evidence_stage(paper), decision.get("research_type")])

    with st.container(border=True):
        st.markdown(
            f'<div class="paper-title"><a href="{url}" target="_blank">{title}</a></div>'
            f'<div class="meta">{html.escape(author_names)} · Submitted '
            f"{short_date(paper.get('initial_submission_date'))} · "
            f"arXiv:{html.escape(str(paper.get('base_arxiv_id', '')))}</div>"
            f"<div>{badges(tags, status)}{badges((field_areas + scientific_identity + systems)[:5])}</div>"
            f'<div class="abstract">{html.escape(preview)}</div>',
            unsafe_allow_html=True,
        )
        links = st.columns([1, 1, 4])
        links[0].link_button("arXiv page ↗", paper.get("abstract_url", "https://arxiv.org"))
        links[1].link_button("PDF ↗", paper.get("pdf_url", "https://arxiv.org"))
        label_count = len(scientific_identity + systems + methods)
        if label_count > 5:
            links[2].caption(f"+{label_count - 5} additional scientific labels")

        with st.expander("Abstract, complete metadata and classification evidence"):
            st.write(abstract)
            if decision:
                st.markdown(f"**Classification reason:** {decision.get('reason', '—')}")
                st.markdown("**Field ecosystem:** " + ", ".join(field_areas))
                st.markdown(f"**Research maturity:** {evidence_stage(paper)}")
                phrases = decision.get("supporting_phrases", [])
                if phrases:
                    st.markdown("**Evidence from abstract:** " + " · ".join(phrases))
                st.markdown("**Material/system:** " + ", ".join(systems or ["Not specified"]))
                st.markdown(
                    "**Research focus:** "
                    + ", ".join(decision.get("research_focus", []) or ["Not specified"])
                )
                st.markdown(
                    "**Meaning of chirality:** "
                    + ", ".join(decision.get("chirality_class", []) or ["Not established"])
                )
                st.markdown(
                    "**Phonon character:** "
                    + ", ".join(decision.get("phonon_character", []) or ["Not specified"])
                )
                st.markdown(
                    "**Generation mechanism:** "
                    + ", ".join(decision.get("generation_mechanisms", []) or ["Not specified"])
                )
                st.markdown(
                    "**Methods actually performed:** " + ", ".join(methods or ["Not specified"])
                )
                st.markdown(
                    "**Properties:** "
                    + ", ".join(decision.get("physical_properties", []) or ["Not specified"])
                )
                st.markdown(f"**Evidence level:** {decision.get('evidence_level', 'Not assessed')}")
                caveats = decision.get("evidence_caveats", [])
                if caveats:
                    st.warning("Evidence caveats: " + " · ".join(caveats))
                st.markdown(
                    "**Research/application direction:** "
                    + ", ".join(decision.get("application_directions", []) or ["Not claimed"])
                )
            else:
                st.info("This paper is stored safely but has not completed AI review.")
            st.caption("arXiv categories: " + ", ".join(paper.get("categories", [])))


archive, history, events, tools = load_all()
review_history = load_json(DATA / "review_history.json", [])
backfill_state = load_json(DATA / "backfill_state.json", {})
papers = archive.get("papers", [])
statuses = {paper["base_arxiv_id"]: feed_status(paper) for paper in papers}
approved = [p for p in papers if is_field_paper(p)]
pending = [p for p in papers if statuses[p["base_arxiv_id"]] == "Awaiting classification"]
review_queue = [p for p in papers if statuses[p["base_arxiv_id"]] == "Open interpretation"]
rule_excluded = [p for p in papers if statuses[p["base_arxiv_id"]] == "Discovery archive"]
experimental = [p for p in papers if is_experimental_study(p)]
reviewed = [p for p in papers if p.get("ai_decision")]
thz_frontier = [p for p in approved if is_thz_frontier(p)]
direct_evidence = [
    p for p in approved if evidence_stage(p) in {"Direct measurement", "Experimental evidence"}
]

st.markdown(
    '<div class="topline">ARXIV CHIRAL PHONON FEED · DAILY AT 04:00 UTC</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="hero">
<h1>Chiral Phonon Research Scanner</h1>
<p>Track how the chiral-phonon field is evolving across phonon angular momentum,
THz and ultrafast control, magnetism, quantum materials and transport. Direct measurements,
experimental indications and predictions stay distinct without treating an unsettled definition
as a reason to hide useful research.</p>
</div>
""",
    unsafe_allow_html=True,
)

metrics = st.columns(4)
metrics[0].metric(
    "Total papers scanned",
    len(papers),
    help="Every deduplicated paper retrieved by the broad discovery scan.",
)
metrics[1].metric(
    "Scientific analysis complete",
    len(reviewed),
    help="Papers with a stored scientific classification.",
)
metrics[2].metric(
    "Analysis pending",
    len(pending),
    help="Likely field-connected papers waiting for classification.",
)
metrics[3].metric(
    "Papers in field timeline",
    len(approved),
    help="Reviewed papers mapped into the chiral-phonon field timeline.",
)

coverage_dates = [parse_date(p.get("initial_submission_date")) for p in papers]
coverage_dates = [value for value in coverage_dates if value]
coverage = (
    f"Archive coverage: {min(coverage_dates).date()} to {max(coverage_dates).date()}"
    if coverage_dates
    else "Archive coverage unavailable"
)
last_scan = history[-1].get("scan_timestamp") if history else archive.get("updated_at")
st.markdown(
    f'<div class="coverage">{coverage} · Last metadata scan: {short_date(last_scan)} · '
    f"{len(reviewed)} classified · {len(pending)} awaiting classification · "
    f"{len(review_queue)} open-interpretation papers · "
    f"backfill checkpoint: {html.escape(str(backfill_state.get('next_until', 'not started')))}</div>",
    unsafe_allow_html=True,
)

(
    history_tab,
    paper_tab,
    analysis_tab,
    news_tab,
    funding_tab,
    events_tab,
    tools_tab,
    admin_tab,
) = st.tabs(
    [
        "Research evolution",
        "Daily scan",
        "Field analysis",
        "News & breakthroughs",
        "Funding & projects",
        "Opportunities",
        "Sources",
        "Data operations",
    ]
)

with history_tab:
    st.subheader("Experimental materials map")
    st.caption(
        "Materials with published experimental evidence. Labels distinguish observation of the mode itself "
        "from a driven effect or angular-momentum-selective coupling."
    )
    evidence_filter = st.multiselect(
        "Evidence represented",
        list(EVIDENCE_LEVELS),
        default=list(EVIDENCE_LEVELS),
    )
    filtered_materials = [
        material for material in MATERIAL_SYSTEMS if material["evidence"] in evidence_filter
    ]
    st.markdown(" · ".join(f"**{item['material']}**" for item in filtered_materials))
    if not MATERIAL_SYSTEMS:
        st.info(
            "The enriched materials map is waiting for Streamlit Cloud to complete its repository "
            "refresh. The established landmark timeline remains available below."
        )

    with st.expander("How to read the evidence labels", expanded=False):
        for label, meaning in EVIDENCE_LEVELS.items():
            st.markdown(f"**{label}:** {meaning}")

    material_columns = st.columns(2)
    for index, material in enumerate(filtered_materials):
        with material_columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"#### {material['material']}")
                st.caption(f"{material['family']} · {material['year']} · {material['evidence']}")
                st.markdown(f"**What was measured:** {material['finding']}")
                st.write(f"Method: {material['method']}")
                st.warning(f"Interpretation boundary: {material['caveat']}")
                papers = material.get("papers", [("Primary paper", material["url"])])
                with st.expander(f"Papers and records · {len(papers)}"):
                    for label, url in papers:
                        st.markdown(f"- [{label}]({url})")

    st.markdown("### How the concept changed")
    stage_columns = st.columns(3)
    for index, (title, question) in enumerate(CONCEPT_STAGES):
        with stage_columns[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{index + 1}. {title}**")
                st.write(question)

    st.markdown("### Historical timeline")
    st.caption(
        "Multiple papers are retained within breakthrough years so the timeline shows parallel "
        "progress in definitions, measurement and THz-driven effects."
    )
    landmarks_by_year: dict[int, list[dict]] = defaultdict(list)
    for landmark in LANDMARKS:
        landmarks_by_year[landmark["year"]].append(landmark)
    for year in sorted(landmarks_by_year, reverse=True):
        st.markdown(f"## {year}")
        for item in landmarks_by_year[year]:
            with st.container(border=True):
                left, right = st.columns([2, 7])
                left.markdown(f"**{item['stage']}**")
                material = item.get("material", item.get("theme", "Field landmark"))
                kind = item.get("kind", "Research paper")
                left.caption(f"{material} · {kind}")
                right.markdown(f"#### {item['title']}")
                right.write(item["why"])
                right.link_button("Open primary paper ↗", item["url"])

    st.info(
        "Technical boundary: circular polarization, phonon angular momentum and true dynamical "
        "chirality are related but not interchangeable. A Γ-point circular mode can carry angular "
        "momentum without being a propagating chiral object; valley pseudo-angular momentum is a "
        "crystal-symmetry quantum number; true chirality additionally concerns how rotation and "
        "propagation transform under space and time reversal."
    )

with paper_tab:
    st.subheader("Daily research scan")
    st.caption(
        "Newest mapped papers first. Use the THz lens for coherent excitation, nonlinear phononics and ultrafast experiments."
    )
    scan_window = st.radio(
        "Timeline",
        ["Latest 7 days", "Latest 30 days", "All mapped papers"],
        horizontal=True,
    )
    with st.sidebar:
        st.header("Advanced paper filters")
        st.caption("Optional controls for narrowing the Daily scan.")
        view = st.radio(
            "Research lens",
            [
                "Field evolution",
                "THz & ultrafast frontier",
                "Experimental evidence",
                "Phonon angular momentum",
                "Magnetism & spintronics",
                "2D optoelectronics & quantum materials",
                "Transport, Hall & mechanics",
                "Theory & materials discovery",
                "Open questions / interpretation",
            ],
        )
        search = st.text_input("Search", placeholder="Material, method, author, concept…")
        current_decisions = [p for p in papers if p.get("ai_decision")]
        relevance_filter = st.multiselect(
            "Chiral-phonon relevance",
            flatten_unique(current_decisions, ("ai_decision", "relevance")),
        )
        research_filter = st.multiselect(
            "Research type", flatten_unique(current_decisions, ("ai_decision", "research_type"))
        )
        focus_filter = st.multiselect(
            "Research focus", flatten_unique(current_decisions, ("ai_decision", "research_focus"))
        )
        chirality_filter = st.multiselect(
            "Meaning of chirality",
            flatten_unique(current_decisions, ("ai_decision", "chirality_class")),
        )
        phonon_filter = st.multiselect(
            "Phonon character",
            flatten_unique(current_decisions, ("ai_decision", "phonon_character")),
        )
        evidence_filter = st.multiselect(
            "Evidence level", flatten_unique(current_decisions, ("ai_decision", "evidence_level"))
        )
        family_filter = st.multiselect(
            "Material family",
            flatten_unique(current_decisions, ("ai_decision", "material_or_system_family")),
        )
        exp_filter = st.multiselect(
            "Experimental method",
            flatten_unique(current_decisions, ("ai_decision", "experimental_methods")),
        )
        excitation_filter = st.multiselect(
            "Generation mechanism",
            flatten_unique(current_decisions, ("ai_decision", "generation_mechanisms")),
        )
        detection_filter = st.multiselect(
            "Detection", flatten_unique(current_decisions, ("ai_decision", "detection_methods"))
        )
        theory_filter = st.multiselect(
            "Theory / computation",
            flatten_unique(current_decisions, ("ai_decision", "computational_methods")),
        )
        property_filter = st.multiselect(
            "Physical property",
            flatten_unique(current_decisions, ("ai_decision", "physical_properties")),
        )
        application_filter = st.multiselect(
            "Research/application direction",
            flatten_unique(current_decisions, ("ai_decision", "application_directions")),
        )

    if view == "Field evolution":
        candidates = approved
    elif view == "THz & ultrafast frontier":
        candidates = thz_frontier
    elif view == "Experimental evidence":
        candidates = experimental
    elif view == "Open questions / interpretation":
        candidates = review_queue
    else:
        area = (
            "Fundamental chirality & phonon angular momentum"
            if view == "Phonon angular momentum"
            else view
        )
        candidates = [p for p in approved if area in ecosystem_areas(p)]

    mapped_dates = [parse_date(p.get("initial_submission_date")) for p in approved]
    mapped_dates = [value for value in mapped_dates if value]
    if scan_window != "All mapped papers" and mapped_dates:
        days = 7 if scan_window == "Latest 7 days" else 30
        cutoff = max(mapped_dates).date().toordinal() - days + 1
        candidates = [
            paper
            for paper in candidates
            if (parsed := parse_date(paper.get("initial_submission_date")))
            and parsed.date().toordinal() >= cutoff
        ]

    filtered: list[dict] = []
    needle = search.casefold().strip()
    for paper in candidates:
        decision = paper.get("ai_decision") or {}
        searchable = " ".join(
            [
                paper.get("base_arxiv_id", ""),
                paper.get("title", ""),
                paper.get("abstract", ""),
                " ".join(paper.get("authors", [])),
            ]
        ).casefold()
        if needle and needle not in searchable:
            continue
        scalar_filters = [
            (relevance_filter, "relevance"),
            (research_filter, "research_type"),
            (evidence_filter, "evidence_level"),
        ]
        if any(
            selected and decision.get(field) not in selected for selected, field in scalar_filters
        ):
            continue
        list_filters = [
            (family_filter, "material_or_system_family"),
            (focus_filter, "research_focus"),
            (chirality_filter, "chirality_class"),
            (phonon_filter, "phonon_character"),
            (exp_filter, "experimental_methods"),
            (excitation_filter, "generation_mechanisms"),
            (detection_filter, "detection_methods"),
            (theory_filter, "computational_methods"),
            (property_filter, "physical_properties"),
            (application_filter, "application_directions"),
        ]
        if any(
            selected and not set(selected).intersection(decision.get(field, []))
            for selected, field in list_filters
        ):
            continue
        filtered.append(paper)

    filtered.sort(key=lambda p: p.get("initial_submission_date", ""), reverse=True)
    st.subheader(f"{view} · {len(filtered)} papers")
    if view == "Field evolution":
        st.caption(
            "Core results, connected phonon-angular-momentum physics and open interpretations."
        )
    elif view == "THz & ultrafast frontier":
        st.caption(
            "Coherent THz/mid-IR excitation, nonlinear phononics, dynamical multiferroicity and ultrafast readout."
        )
        thz_experimental = [p for p in thz_frontier if is_experimental_evidence(p)]
        thz_direct = [p for p in thz_frontier if evidence_stage(p) == "Direct measurement"]
        thz_metrics = st.columns(3)
        thz_metrics[0].metric("THz-connected papers", len(thz_frontier))
        thz_metrics[1].metric("Experimental", len(thz_experimental))
        thz_metrics[2].metric("Direct measurement", len(thz_direct))
        st.info(
            "Research question: does the paper merely drive a phonon with THz light, "
            "or does it establish circular ionic motion, angular momentum, or a magnetic consequence?"
        )
    elif view == "Experimental evidence":
        st.caption("Original experimental and combined theory–experiment studies.")
    elif view == "Open questions / interpretation":
        st.caption(
            "Boundary cases where the meaning or evidence for phonon chirality remains scientifically unsettled."
        )

    page_size = 20
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.selectbox(
        "Page",
        range(1, total_pages + 1),
        format_func=lambda value: f"Page {value} of {total_pages}",
    )
    page_items, _, _ = paginate(filtered, page, page_size)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for paper in page_items:
        parsed = parse_date(paper.get("initial_submission_date"))
        label = parsed.strftime("%A, %d %B %Y") if parsed else "Date unavailable"
        grouped[label].append(paper)
    for label, items in grouped.items():
        st.markdown(
            f'<div class="date-row"><h2>{html.escape(label)}</h2><span class="count-pill">{len(items)} papers</span></div>',
            unsafe_allow_html=True,
        )
        for paper in items:
            paper_card(paper)
    if not page_items:
        st.info("No papers match this view and filter combination.")

with analysis_tab:
    st.subheader("How the field is evolving")
    st.markdown(
        """
The community does not use one settled definition. This tracker therefore follows the
unifying question—**how lattice motion carries, generates or transfers angular momentum**—and
keeps true eigenmode chirality, driven circular motion and pseudo-angular momentum separate.
"""
    )
    guide = st.columns(4)
    with guide[0]:
        st.markdown("#### 1 · Identify")
        st.write("Resolve symmetry, handedness, circular ionic motion and phonon angular momentum.")
    with guide[1]:
        st.markdown("#### 2 · Generate")
        st.write("Use THz/mid-IR pulses, nonlinear coupling, magnetic order or thermal imbalance.")
    with guide[2]:
        st.markdown("#### 3 · Detect")
        st.write(
            "Distinguish direct motion/torque from Raman selection rules and magneto-optical inference."
        )
    with guide[3]:
        st.markdown("#### 4 · Use")
        st.write(
            "Track transfer into spins, electrons, excitons, orbital currents and heat transport."
        )
    st.caption(
        "Community framing: CECAM Chiral Phonons in Quantum Materials workshop · "
        "magnetism/spintronics · 2D optoelectronics · ultrafast dynamics · transport/Hall effects."
    )
    st.link_button(
        "Open community field map ↗",
        "https://www.cecam.org/workshop-details/chiral-phonons-in-quantum-materials-1202",
    )
    pipeline_metrics = st.columns(4)
    pipeline_metrics[0].metric("Field-map papers", len(approved))
    pipeline_metrics[1].metric("THz & ultrafast", len(thz_frontier))
    pipeline_metrics[2].metric("Experimental", len(experimental))
    pipeline_metrics[3].metric("Direct evidence", len(direct_evidence))
    st.caption(
        "The map follows overlapping research communities rather than forcing one definition "
        "of a chiral phonon. A paper may belong to several areas at once."
    )
    st.subheader("Research landscape")
    st.caption(
        "Reviewed field papers are grouped by ecosystem, evidence maturity, material and method."
    )
    if not approved:
        st.info("Analysis will appear as current AI classifications are completed.")
    else:
        frame = pd.DataFrame(
            {
                "date": [
                    pd.to_datetime(p["initial_submission_date"], utc=True).date() for p in approved
                ],
                "research_type": [p["ai_decision"]["research_type"] for p in approved],
                "relevance": [p["ai_decision"]["relevance"] for p in approved],
            }
        )
        frame["week"] = pd.to_datetime(frame["date"]).dt.to_period("W").dt.start_time
        left, right = st.columns(2)
        left.line_chart(frame.groupby("date").size().rename("field papers"))
        right.line_chart(frame.groupby("week").size().rename("field papers"))

        def distribution(field: str) -> pd.Series:
            values = [value for paper in approved for value in paper["ai_decision"].get(field, [])]
            return pd.Series(values, dtype="object").value_counts().head(15)

        rows = [
            ("Field ecosystems", "_ecosystem"),
            ("Evidence maturity", "_evidence"),
            ("Research focus", "research_focus"),
            ("Meaning of chirality", "chirality_class"),
            ("Phonon character", "phonon_character"),
            ("Material families", "material_or_system_family"),
            ("Experimental methods", "experimental_methods"),
            ("Generation mechanisms", "generation_mechanisms"),
            ("Detection methods", "detection_methods"),
            ("Theory / computation", "computational_methods"),
            ("Physical properties", "physical_properties"),
            ("Application directions", "application_directions"),
        ]
        for start in range(0, len(rows), 3):
            columns = st.columns(3)
            for column, (title, field) in zip(columns, rows[start : start + 3], strict=False):
                column.markdown(f"#### {title}")
                if field == "_ecosystem":
                    values = [value for paper in approved for value in ecosystem_areas(paper)]
                    column.bar_chart(pd.Series(values, dtype="object").value_counts())
                elif field == "_evidence":
                    values = [evidence_stage(paper) for paper in approved]
                    column.bar_chart(pd.Series(values, dtype="object").value_counts())
                else:
                    column.bar_chart(distribution(field))

with news_tab:
    st.subheader("Breakthrough coverage")
    st.caption(
        "Curated journal and research-magazine coverage. This is editorial context, kept separate "
        "from the automated arXiv feed."
    )
    for item in sorted(NEWS, key=lambda value: value["year"], reverse=True):
        with st.container(border=True):
            st.markdown(f"### {item['title']}")
            st.caption(f"{item['outlet']} · {item['year']} · {item['kind']}")
            st.write(item["summary"])
            st.link_button("Read source ↗", item["url"])

with funding_tab:
    st.subheader("Funded chiral-phonon ecosystem")
    st.caption(
        "Verified projects are separated from general funding portals and speculative industry signals."
    )
    st.markdown("### Verified projects and networks")
    for project in FUNDED_PROJECTS:
        with st.container(border=True):
            st.markdown(f"### {project['name']}")
            st.caption(f"{project['scheme']} · {project['host']} · {project['status']}")
            st.write(project["focus"])
            st.write(f"**Lead:** {project['lead']}")
            st.link_button("Official record ↗", project["url"])
    st.markdown("### Funding watch portals")
    funding_columns = st.columns(2)
    for index, source in enumerate(FUNDING_WATCH):
        with funding_columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"#### {source['name']}")
                st.caption(source["region"])
                st.write(source["purpose"])
                st.link_button("Open official portal ↗", source["url"])
    st.markdown("### Industry maturity")
    for signal in INDUSTRY_SIGNALS:
        st.info(f"**{signal['name']} — {signal['signal']}**\n\n{signal['detail']}")

with events_tab:
    st.subheader("Conferences, workshops, schools and networks")
    for event in events:
        with st.container(border=True):
            st.markdown(f"### {event['title']}")
            st.write(event.get("description", ""))
            st.caption(
                " · ".join(
                    value
                    for value in [
                        event.get("event_type"),
                        event.get("organiser"),
                        event.get("location"),
                    ]
                    if value
                )
            )
            if event.get("deadline"):
                st.write(f"**Deadline:** {event['deadline']}")
            st.link_button("Official source ↗", event["url"])

with tools_tab:
    st.subheader("Research tools and official sources")
    for item in tools:
        with st.container(border=True):
            st.markdown(f"### {item['name']}")
            st.write(item.get("description", ""))
            st.caption(" · ".join(item.get("tags", [])))
            st.link_button("Open resource ↗", item["url"])

with admin_tab:
    st.subheader("Archive and review health")
    health = st.columns(4)
    health[0].metric("Retrieved", len(papers))
    health[1].metric("Classified", len(reviewed))
    health[2].metric("Awaiting classification", len(pending))
    health[3].metric("Discovery archive", len(rule_excluded))
    st.caption(
        "Discovery archive means broad search results that are not currently mapped into the field; "
        "it is an operational audit state, not a scientific judgement."
    )
    with st.expander("Review schedule and backfill status"):
        st.write(
            "Metadata 04:00 UTC · AI review every four hours at :40 · historical backfill "
            "02:10, 08:10, 14:10 and 20:10 UTC."
        )
        st.write(f"Backfill next date: {backfill_state.get('next_until', '—')}")
        st.write(
            f"Last review succeeded: {review_history[-1].get('succeeded', 0) if review_history else 0}"
        )
    st.subheader("Owner-only live scan")
    required = ["github_token", "admin_passcode"]
    try:
        owner_controls_ready = all(key in st.secrets for key in required)
    except StreamlitSecretNotFoundError:
        owner_controls_ready = False
    if not owner_controls_ready:
        st.info("Add the owner secrets in Streamlit settings to enable secure manual scans.")
    else:
        passcode = st.text_input("Admin passcode", type="password")
        since_date = st.date_input("Scan from", value=date.today())
        expected = hashlib.sha256(str(st.secrets["admin_passcode"]).encode()).digest()
        supplied = hashlib.sha256(passcode.encode()).digest()
        authenticated = bool(passcode) and hmac.compare_digest(expected, supplied)
        if st.button("Run metadata scan now", type="primary", disabled=not authenticated):
            run_url = dispatch_metadata_scan(
                repo=st.secrets.get("github_repo", "purushothaman-98/Chiral_scanner"),
                token=st.secrets["github_token"],
                since=since_date.isoformat(),
            )
            st.success("Metadata scan dispatched. AI review follows after it succeeds.")
            if run_url:
                st.link_button("Monitor GitHub Actions ↗", run_url)

st.divider()
st.caption(
    "Independent research tool using the official arXiv API. Not affiliated with or endorsed by arXiv. "
    f"Page generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}."
)

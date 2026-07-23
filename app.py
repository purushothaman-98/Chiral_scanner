from __future__ import annotations

# ruff: noqa: E402 -- source-path bootstrap must precede project imports on Streamlit Cloud.
import hashlib
import hmac
import html
import importlib
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
from chiral_scanner.research_insights import field_brief, signal_tier

try:
    import chiral_scanner.history_v2 as history_data

    # Streamlit reruns app.py inside a long-lived process. Reload the curated data module so
    # newly deployed materials and papers appear without requiring a manual server reboot.
    importlib.invalidate_caches()
    history_data = importlib.reload(history_data)
    CONCEPT_STAGES = history_data.CONCEPT_STAGES
    EVIDENCE_LEVELS = history_data.EVIDENCE_LEVELS
    LANDMARKS = history_data.LANDMARKS
    MATERIAL_SYSTEMS = history_data.MATERIAL_SYSTEMS
except ImportError:
    # Keep the site alive if Streamlit's in-place pull leaves app.py newer than history.py.
    from chiral_scanner.history import CONCEPT_STAGES, LANDMARKS

    EVIDENCE_LEVELS = {}
    MATERIAL_SYSTEMS = []

try:
    import chiral_scanner.research_intelligence as intelligence_data

    # Curated intelligence changes more often than the app process restarts. Reload it explicitly,
    # while keeping the renderer compatible with the previous schema during an in-place deploy.
    importlib.invalidate_caches()
    intelligence_data = importlib.reload(intelligence_data)
    FUNDED_PROJECTS = getattr(intelligence_data, "FUNDED_PROJECTS", [])
    FUNDING_WATCH = getattr(intelligence_data, "FUNDING_WATCH", [])
    INDUSTRY_SIGNALS = getattr(intelligence_data, "INDUSTRY_SIGNALS", [])
    NEWS = getattr(intelligence_data, "NEWS", [])
except ImportError:
    # A partial Streamlit Cloud repository refresh must never take down the research feed.
    FUNDED_PROJECTS = []
    FUNDING_WATCH = []
    INDUSTRY_SIGNALS = []
    NEWS = []
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
:root {--violet:#8b5cf6; --cyan:#22d3ee; --ink:#f8fafc; --muted:#94a3b8;
--panel:rgba(15,23,42,.72); --line:rgba(148,163,184,.16);}
.block-container {padding-top:1rem; padding-bottom:2.5rem; max-width:1280px;}
.hero {padding:1.25rem 1.45rem; border:1px solid rgba(139,92,246,.34); border-radius:22px;
background:radial-gradient(circle at 88% 10%,rgba(34,211,238,.12),transparent 25%),
radial-gradient(circle at 72% 0%,rgba(124,58,237,.25),transparent 38%),
linear-gradient(135deg,rgba(15,23,42,.98),rgba(20,14,44,.97)); margin-bottom:.8rem;
box-shadow:0 18px 55px rgba(2,6,23,.22);}
.hero-kicker {display:flex; align-items:center; gap:.45rem; color:#c4b5fd; font-size:.72rem;
font-weight:750; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.55rem;}
.live-dot {width:.48rem; height:.48rem; border-radius:999px; background:#34d399;
box-shadow:0 0 0 4px rgba(52,211,153,.12); display:inline-block;}
.hero h1 {margin:0; font-size:2.12rem; letter-spacing:-.045em; line-height:1.08;}
.hero p {max-width:850px; color:#cbd5e1; font-size:.95rem; line-height:1.55; margin:.55rem 0 .75rem;}
.hero-tags {display:flex; flex-wrap:wrap; gap:.4rem;}
.hero-tag {padding:.22rem .55rem; border:1px solid rgba(196,181,253,.2); border-radius:999px;
color:#ddd6fe; background:rgba(139,92,246,.08); font-size:.72rem;}
.coverage {display:flex; flex-wrap:wrap; gap:.45rem 1.15rem; padding:.65rem .85rem;
border-radius:12px; background:rgba(15,23,42,.62); border:1px solid var(--line);
color:#cbd5e1; font-size:.8rem; margin:.45rem 0 .9rem;}
.coverage strong {color:#f8fafc; font-weight:650;}
.section-kicker {color:#a78bfa; font-size:.7rem; font-weight:750; letter-spacing:.1em;
text-transform:uppercase; margin-bottom:.2rem;}
.section-intro {color:#94a3b8; max-width:850px; font-size:.88rem; line-height:1.55;
margin-top:-.25rem; margin-bottom:.9rem;}
.material-strip {padding:.65rem .8rem; border:1px solid var(--line); border-radius:12px;
background:rgba(15,23,42,.45); color:#cbd5e1; font-size:.82rem; margin:.45rem 0 .75rem;}
.date-row {display:flex; align-items:center; gap:.7rem; margin:1.2rem 0 .2rem;}
.date-row h2 {font-size:1.08rem; margin:0;}
.count-pill {font-size:.7rem; color:#c4b5fd; padding:.13rem .44rem; border-radius:999px;
background:rgba(139,92,246,.12); border:1px solid rgba(139,92,246,.24);}
.paper-title {font-size:1.04rem; font-weight:720; line-height:1.4; margin-bottom:.18rem;}
.paper-title a {color:var(--ink); text-decoration:none;}
.paper-title a:hover {color:#a78bfa;}
.meta {color:#94a3b8; font-size:.78rem; margin:.18rem 0 .38rem;}
.badge {display:inline-block; padding:.16rem .44rem; margin:.1rem .16rem .1rem 0;
border-radius:999px; background:rgba(124,58,237,.1); border:1px solid rgba(139,92,246,.24);
font-size:.68rem; color:#ddd6fe;}
.status-approved {background:rgba(16,185,129,.1); border-color:rgba(16,185,129,.3); color:#a7f3d0;}
.status-pending {background:rgba(245,158,11,.1); border-color:rgba(245,158,11,.3); color:#fde68a;}
.status-review {background:rgba(244,63,94,.1); border-color:rgba(244,63,94,.28); color:#fecdd3;}
.paper-signal {border-left:2px solid rgba(34,211,238,.55); padding:.35rem .65rem;
margin:.55rem 0 .35rem; color:#cbd5e1; font-size:.82rem; line-height:1.5;
background:rgba(34,211,238,.035);}
.brief {padding:.85rem 1rem; border:1px solid rgba(34,211,238,.2); border-radius:14px;
background:linear-gradient(135deg,rgba(34,211,238,.055),rgba(139,92,246,.055));
color:#cbd5e1; line-height:1.55; margin:.65rem 0 1rem;}
.brief strong {color:#f8fafc;}
.abstract {color:#b8c1cf; line-height:1.5; margin:.4rem 0; font-size:.86rem;}
div[data-testid="stMetric"] {padding:.72rem .82rem; background:rgba(15,23,42,.52);
border:1px solid var(--line); border-radius:14px; min-height:92px;}
div[data-testid="stMetricLabel"] {font-size:.76rem; color:#94a3b8;}
div[data-testid="stMetricValue"] {font-size:1.65rem;}
div[data-baseweb="tab-list"] {gap:.25rem; padding:.28rem; border:1px solid var(--line);
border-radius:14px; background:rgba(15,23,42,.5); overflow-x:auto;}
button[data-baseweb="tab"] {border-radius:10px; padding:.45rem .75rem;}
div[data-testid="stExpander"] {border-color:var(--line); border-radius:12px;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line); border-radius:14px;}
.stButton > button, .stLinkButton > a {border-radius:10px;}
@media (max-width:700px) {
  .block-container {padding:.65rem .75rem 2rem;}
  .hero {padding:1rem; border-radius:17px;}
  .hero h1 {font-size:1.65rem;}
  .hero p {font-size:.86rem;}
  .coverage {display:block; line-height:1.65;}
  div[data-testid="stMetric"] {min-height:82px; padding:.55rem .6rem;}
  button[data-baseweb="tab"] {padding:.38rem .55rem; font-size:.78rem;}
}
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


def record_text(
    record: dict, key: str, *, legacy_key: str | None = None, default: str = "Not specified"
) -> str:
    """Read evolving curated records without failing during staggered Streamlit deploys."""
    value = record.get(key)
    if value not in (None, ""):
        return str(value)
    if legacy_key:
        legacy_value = record.get(legacy_key)
        if legacy_value not in (None, ""):
            return str(legacy_value)
    return default


def source_url(record: dict) -> str | None:
    value = record.get("url")
    return str(value) if isinstance(value, str) and value.startswith("https://") else None


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
    preview = abstract if len(abstract) <= 300 else abstract[:297].rstrip() + "…"
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
    tier = signal_tier(paper)
    tags = [tier]
    if decision:
        tags.extend([evidence_stage(paper), decision.get("research_type")])
    visible_science_tags = (field_areas + scientific_identity + systems)[:3]
    reason = str(decision.get("reason", "")).strip()
    signal = reason if len(reason) <= 260 else reason[:257].rstrip() + "…"
    signal_html = (
        f'<div class="paper-signal"><strong>Research signal</strong> · {html.escape(signal)}</div>'
        if signal
        else ""
    )

    with st.container(border=True):
        st.markdown(
            f'<div class="paper-title"><a href="{url}" target="_blank">{title}</a></div>'
            f'<div class="meta">{html.escape(author_names)} · Submitted '
            f"{short_date(paper.get('initial_submission_date'))} · "
            f"arXiv:{html.escape(str(paper.get('base_arxiv_id', '')))}</div>"
            f"<div>{badges(tags, status)}{badges(visible_science_tags)}</div>"
            f"{signal_html}"
            f'<div class="abstract">{html.escape(preview)}</div>',
            unsafe_allow_html=True,
        )
        links = st.columns([1, 1, 4])
        links[0].link_button("arXiv page ↗", paper.get("abstract_url", "https://arxiv.org"))
        links[1].link_button("PDF ↗", paper.get("pdf_url", "https://arxiv.org"))
        label_count = len(field_areas + scientific_identity + systems + methods)
        if label_count > len(visible_science_tags):
            links[2].caption(
                f"{label_count - len(visible_science_tags)} more labels in the evidence panel"
            )

        with st.expander("Evidence, methods and complete metadata"):
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
brief = field_brief(papers)

st.markdown(
    """
<div class="hero">
<div class="hero-kicker"><span class="live-dot"></span> Daily arXiv intelligence · 04:00 UTC</div>
<h1>Chiral phonon field tracker</h1>
<p>A researcher-first map of how the field is changing—from phonon angular momentum and
true dynamical chirality to THz control, magnetism and direct measurement. Evidence,
interpretation and prediction remain visibly distinct.</p>
<div class="hero-tags">
<span class="hero-tag">Field history</span><span class="hero-tag">Latest papers</span>
<span class="hero-tag">Materials & methods</span><span class="hero-tag">THz frontier</span>
</div>
</div>
""",
    unsafe_allow_html=True,
)

metrics = st.columns(4)
metrics[0].metric(
    "Archive",
    len(papers),
    help="Every deduplicated paper retrieved by the broad discovery scan.",
)
metrics[1].metric(
    "Scientifically reviewed",
    len(reviewed),
    help="Papers with a stored scientific classification.",
)
metrics[2].metric(
    "Strong field signal",
    brief["strong"],
    help="Conservative subset with an explicit chiral-phonon or phonon-angular-momentum anchor.",
)
metrics[3].metric(
    "New in 30 days",
    brief["recent"],
    help="Mapped papers submitted during the latest 30-day window.",
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
    f'<div class="coverage"><span><strong>Coverage</strong> · {coverage.removeprefix("Archive coverage: ")}</span>'
    f"<span><strong>Last scan</strong> · {short_date(last_scan)}</span>"
    f"<span><strong>Open interpretation</strong> · {len(review_queue)}</span>"
    f"<span><strong>Backfill checkpoint</strong> · "
    f"{html.escape(str(backfill_state.get('next_until', 'not started')))}</span></div>",
    unsafe_allow_html=True,
)

(
    history_tab,
    paper_tab,
    analysis_tab,
    news_tab,
    ecosystem_tab,
    admin_tab,
) = st.tabs(
    [
        "Field atlas",
        "Latest papers",
        "Research landscape",
        "Breakthroughs",
        "Ecosystem",
        "Pipeline",
    ]
)

with history_tab:
    st.markdown('<div class="section-kicker">Field atlas</div>', unsafe_allow_html=True)
    st.subheader("Evidence, materials and the evolution of the concept")
    st.markdown(
        '<div class="section-intro">Start with what has been observed, then move through how '
        "the definition changed. The atlas separates a mode-resolved observation from "
        "spectroscopic identification, driven response and angular-momentum coupling.</div>",
        unsafe_allow_html=True,
    )
    overview_metrics = st.columns(4)
    overview_metrics[0].metric("Material systems", len(MATERIAL_SYSTEMS))
    overview_metrics[1].metric(
        "Direct mode-resolved",
        sum(item["evidence"] == "Direct mode-resolved" for item in MATERIAL_SYSTEMS),
    )
    overview_metrics[2].metric(
        "Driven responses", sum(item["evidence"] == "Driven response" for item in MATERIAL_SYSTEMS)
    )
    overview_metrics[3].metric("Landmark papers", len(LANDMARKS))
    st.markdown("### Experimental materials map")
    map_controls = st.columns([3, 2])
    with map_controls[0]:
        evidence_filter = st.multiselect(
            "Filter by evidence type",
            list(EVIDENCE_LEVELS),
            default=list(EVIDENCE_LEVELS),
        )
    filtered_materials = [
        material for material in MATERIAL_SYSTEMS if material["evidence"] in evidence_filter
    ]
    with map_controls[1]:
        selected_name = st.selectbox(
            "Open a material record",
            [item["material"] for item in filtered_materials],
            disabled=not filtered_materials,
        )
    if not MATERIAL_SYSTEMS:
        st.info(
            "The enriched materials map is waiting for Streamlit Cloud to complete its repository "
            "refresh. The established landmark timeline remains available below."
        )

    if filtered_materials:
        st.markdown(
            '<div class="material-strip"><strong>Systems in this view</strong> · '
            + " · ".join(html.escape(item["material"]) for item in filtered_materials)
            + "</div>",
            unsafe_allow_html=True,
        )
        material = next(item for item in filtered_materials if item["material"] == selected_name)
        with st.container(border=True):
            record_main, record_context = st.columns([3, 2])
            with record_main:
                st.markdown(f"### {material['material']}")
                st.caption(
                    f"{material['family']} · First report {material['year']} · {material['evidence']}"
                )
                st.markdown(f"**What was established**  \n{material['finding']}")
                st.markdown(f"**Method**  \n{material['method']}")
            with record_context:
                st.warning(f"**Interpretation boundary**\n\n{material['caveat']}")
                material_papers = material.get("papers", [("Primary paper", material["url"])])
                st.markdown("**Primary literature**")
                for label, url in material_papers:
                    st.markdown(f"- [{label}]({url})")

    with st.expander("Evidence-label guide"):
        for label, meaning in EVIDENCE_LEVELS.items():
            st.markdown(f"**{label}** — {meaning}")

    st.markdown("### Six questions that moved the field")
    stage_columns = st.columns(3)
    for index, (title, question) in enumerate(CONCEPT_STAGES):
        with stage_columns[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{index + 1}. {title}**")
                st.write(question)

    st.info(
        "**Definition checkpoint:** circular polarization, phonon angular momentum and true "
        "dynamical chirality are related but not interchangeable. A Γ-point circular mode can "
        "carry angular momentum without being a propagating chiral object; valley pseudo-angular "
        "momentum is a crystal-symmetry quantum number."
    )

    st.markdown("### Landmark timeline")
    st.caption("Recent years open by default; earlier foundations remain one click away.")
    landmarks_by_year: dict[int, list[dict]] = defaultdict(list)
    for landmark in LANDMARKS:
        landmarks_by_year[landmark["year"]].append(landmark)
    for year in sorted(landmarks_by_year, reverse=True):
        year_items = landmarks_by_year[year]
        paper_word = "milestone" if len(year_items) == 1 else "milestones"
        with st.expander(
            f"{year} · {len(year_items)} {paper_word}",
            expanded=year >= 2024,
        ):
            for item in year_items:
                with st.container(border=True):
                    left, right = st.columns([2, 7])
                    left.markdown(f"**{item['stage']}**")
                    landmark_material = item.get("material", item.get("theme", "Field landmark"))
                    kind = item.get("kind", "Research paper")
                    left.caption(f"{landmark_material} · {kind}")
                    right.markdown(f"#### {item['title']}")
                    right.write(item["why"])
                    right.link_button("Primary paper ↗", item["url"])

with paper_tab:
    st.markdown('<div class="section-kicker">Daily discovery</div>', unsafe_allow_html=True)
    st.subheader("Latest mapped research")
    st.markdown(
        '<div class="section-intro">Search the scientifically mapped feed first. Choose a broad '
        "research lens, then open advanced filters only when you need method-, material- or "
        "evidence-level precision.</div>",
        unsafe_allow_html=True,
    )
    quick_filters = st.columns([2, 3])
    with quick_filters[0]:
        view = st.selectbox(
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
    with quick_filters[1]:
        search = st.text_input(
            "Search papers", placeholder="Material, method, author, arXiv ID or concept…"
        )
    scan_window = st.radio(
        "Publication window",
        ["Latest 7 days", "Latest 30 days", "All mapped papers"],
        horizontal=True,
    )
    current_decisions = [p for p in papers if p.get("ai_decision")]
    with st.expander("Advanced scientific filters"):
        st.caption(
            "Combine filters across evidence, physical interpretation, materials and methods. "
            "Empty controls are ignored."
        )
        filter_columns = st.columns(3)
        with filter_columns[0]:
            relevance_filter = st.multiselect(
                "Chiral-phonon relevance",
                flatten_unique(current_decisions, ("ai_decision", "relevance")),
            )
            research_filter = st.multiselect(
                "Research type",
                flatten_unique(current_decisions, ("ai_decision", "research_type")),
            )
            evidence_filter = st.multiselect(
                "Evidence level",
                flatten_unique(current_decisions, ("ai_decision", "evidence_level")),
            )
            focus_filter = st.multiselect(
                "Research focus",
                flatten_unique(current_decisions, ("ai_decision", "research_focus")),
            )
        with filter_columns[1]:
            chirality_filter = st.multiselect(
                "Meaning of chirality",
                flatten_unique(current_decisions, ("ai_decision", "chirality_class")),
            )
            phonon_filter = st.multiselect(
                "Phonon character",
                flatten_unique(current_decisions, ("ai_decision", "phonon_character")),
            )
            family_filter = st.multiselect(
                "Material family",
                flatten_unique(current_decisions, ("ai_decision", "material_or_system_family")),
            )
            property_filter = st.multiselect(
                "Physical property",
                flatten_unique(current_decisions, ("ai_decision", "physical_properties")),
            )
        with filter_columns[2]:
            exp_filter = st.multiselect(
                "Experimental method",
                flatten_unique(current_decisions, ("ai_decision", "experimental_methods")),
            )
            excitation_filter = st.multiselect(
                "Generation mechanism",
                flatten_unique(current_decisions, ("ai_decision", "generation_mechanisms")),
            )
            detection_filter = st.multiselect(
                "Detection method",
                flatten_unique(current_decisions, ("ai_decision", "detection_methods")),
            )
            theory_filter = st.multiselect(
                "Theory / computation",
                flatten_unique(current_decisions, ("ai_decision", "computational_methods")),
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
    active_filter_count = sum(
        bool(value)
        for value in [
            search,
            relevance_filter,
            research_filter,
            focus_filter,
            chirality_filter,
            phonon_filter,
            evidence_filter,
            family_filter,
            exp_filter,
            excitation_filter,
            detection_filter,
            theory_filter,
            property_filter,
            application_filter,
        ]
    )
    st.markdown('<div class="section-kicker">Results</div>', unsafe_allow_html=True)
    st.subheader(f"{view} · {len(filtered)} papers")
    if active_filter_count:
        st.caption(f"{active_filter_count} search or advanced filters active")
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
    if total_pages > 1:
        page = st.selectbox(
            "Results page",
            range(1, total_pages + 1),
            format_func=lambda value: f"Page {value} of {total_pages}",
        )
    else:
        page = 1
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
    st.markdown('<div class="section-kicker">Research landscape</div>', unsafe_allow_html=True)
    st.subheader("How the field is evolving")
    st.markdown(
        '<div class="section-intro">The dashboard follows one unifying question—<strong>how '
        "lattice motion carries, generates or transfers angular momentum</strong>—without "
        "collapsing true eigenmode chirality, driven circular motion and pseudo-angular "
        "momentum into one label.</div>",
        unsafe_allow_html=True,
    )
    evidence_gap = max(brief["strong"] - brief["experimental"], 0)
    st.markdown(
        f'<div class="brief"><strong>Field brief</strong> · The archive contains '
        f"{brief['strong']} strong scientific signals. {brief['experimental']} have original "
        f"experimental evidence and {brief['direct']} are classified as direct measurements. "
        f"The remaining evidence gap is {evidence_gap} prediction, theory or non-direct records. "
        f"{brief['needs_interpretation']} mapped records need careful interpretation rather than "
        "automatic promotion as core results.</div>",
        unsafe_allow_html=True,
    )
    snapshot = st.columns(4)
    snapshot[0].metric("Strong signals", brief["strong"])
    snapshot[1].metric("Experimental", brief["experimental"])
    snapshot[2].metric("Direct measurement", brief["direct"])
    snapshot[3].metric("Needs interpretation", brief["needs_interpretation"])

    st.markdown("### What the collected literature is concentrating on")
    trend_columns = st.columns(3)
    for column, title, values in [
        (trend_columns[0], "Scientific frontiers", brief["top_focus"]),
        (trend_columns[1], "Material families", brief["top_materials"]),
        (trend_columns[2], "Experimental methods", brief["top_methods"]),
    ]:
        with column:
            with st.container(border=True):
                st.markdown(f"#### {title}")
                if values:
                    for label, count in values:
                        st.markdown(f"**{count}** · {label}")
                else:
                    st.caption("Not enough classified evidence yet.")
    guide = st.columns(4)
    with guide[0]:
        with st.container(border=True):
            st.markdown("#### 1 · Identify")
            st.write(
                "Resolve symmetry, handedness, circular ionic motion and phonon angular momentum."
            )
    with guide[1]:
        with st.container(border=True):
            st.markdown("#### 2 · Generate")
            st.write(
                "Use THz/mid-IR pulses, nonlinear coupling, magnetic order or thermal imbalance."
            )
    with guide[2]:
        with st.container(border=True):
            st.markdown("#### 3 · Detect")
            st.write(
                "Distinguish direct motion or torque from selection rules and magneto-optical inference."
            )
    with guide[3]:
        with st.container(border=True):
            st.markdown("#### 4 · Use")
            st.write(
                "Track transfer into spins, electrons, excitons, orbital currents and heat transport."
            )
    st.link_button(
        "Community field map · CECAM ↗",
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

        def distribution(field: str) -> pd.Series:
            values = [value for paper in approved for value in paper["ai_decision"].get(field, [])]
            return pd.Series(values, dtype="object").value_counts().head(15)

        def render_distribution(column, values: pd.Series) -> None:
            if values.empty:
                column.caption("No classified values yet.")
            else:
                column.bar_chart(values)

        def render_group(rows: list[tuple[str, str]]) -> None:
            for start in range(0, len(rows), 2):
                columns = st.columns(2)
                for column, (title, field) in zip(columns, rows[start : start + 2], strict=False):
                    column.markdown(f"#### {title}")
                    if field == "_ecosystem":
                        values = [value for paper in approved for value in ecosystem_areas(paper)]
                        render_distribution(
                            column, pd.Series(values, dtype="object").value_counts()
                        )
                    elif field == "_evidence":
                        values = [evidence_stage(paper) for paper in approved]
                        render_distribution(
                            column, pd.Series(values, dtype="object").value_counts()
                        )
                    else:
                        render_distribution(column, distribution(field))

        growth_view, concepts_view, methods_view = st.tabs(
            ["Growth", "Scientific concepts", "Methods & materials"]
        )
        with growth_view:
            st.caption("Daily and weekly accumulation of reviewed field-map papers.")
            left, right = st.columns(2)
            left.line_chart(frame.groupby("date").size().rename("field papers"))
            right.line_chart(frame.groupby("week").size().rename("field papers"))
        with concepts_view:
            render_group(
                [
                    ("Field ecosystems", "_ecosystem"),
                    ("Evidence maturity", "_evidence"),
                    ("Research focus", "research_focus"),
                    ("Meaning of chirality", "chirality_class"),
                    ("Phonon character", "phonon_character"),
                    ("Physical properties", "physical_properties"),
                ]
            )
        with methods_view:
            render_group(
                [
                    ("Material families", "material_or_system_family"),
                    ("Experimental methods", "experimental_methods"),
                    ("Generation mechanisms", "generation_mechanisms"),
                    ("Detection methods", "detection_methods"),
                    ("Theory / computation", "computational_methods"),
                    ("Application directions", "application_directions"),
                ]
            )

with news_tab:
    st.markdown('<div class="section-kicker">Breakthroughs</div>', unsafe_allow_html=True)
    st.subheader("Breakthrough coverage")
    st.markdown(
        '<div class="section-intro">A concise editorial layer for major experimental and '
        "conceptual milestones. It is curated separately from the automated arXiv feed so "
        "coverage never becomes classification evidence.</div>",
        unsafe_allow_html=True,
    )
    news_columns = st.columns(2)
    for index, item in enumerate(
        sorted(NEWS, key=lambda value: str(value.get("year", "")), reverse=True)
    ):
        with news_columns[index % 2]:
            with st.container(border=True):
                st.caption(
                    " · ".join(
                        [
                            record_text(item, "outlet", default="Source not specified"),
                            record_text(item, "year", default="Date not specified"),
                            record_text(item, "kind", default="Coverage"),
                        ]
                    )
                )
                st.markdown(f"#### {record_text(item, 'title', default='Untitled coverage')}")
                st.write(record_text(item, "summary", default="Summary pending."))
                if url := source_url(item):
                    st.link_button("Read primary source ↗", url)

with ecosystem_tab:
    st.markdown('<div class="section-kicker">Research ecosystem</div>', unsafe_allow_html=True)
    st.subheader("Projects, opportunities and enabling infrastructure")
    st.markdown(
        '<div class="section-intro">Verified projects, open funding portals, community events and '
        "industry-adjacent capabilities are kept in separate views so researchers can distinguish "
        "a funded chiral-phonon programme from a general opportunity or market signal.</div>",
        unsafe_allow_html=True,
    )

    projects_view, funding_view, industry_view, community_view, resources_view = st.tabs(
        ["Verified projects", "Funding watch", "Industry signals", "Community", "Resources"]
    )
    with projects_view:
        st.caption("Named projects and networks with an official record.")
        project_columns = st.columns(2)
        for index, project in enumerate(FUNDED_PROJECTS):
            with project_columns[index % 2]:
                with st.container(border=True):
                    st.caption(
                        " · ".join(
                            [
                                record_text(project, "scheme", default="Scheme not specified"),
                                record_text(project, "status", default="Status not specified"),
                            ]
                        )
                    )
                    st.markdown(f"### {record_text(project, 'name', default='Unnamed project')}")
                    st.write(record_text(project, "focus", default="Project focus pending."))
                    st.write(
                        f"**Lead / host:** {record_text(project, 'lead', default='Not specified')} · "
                        f"{record_text(project, 'host', default='Host not specified')}"
                    )
                    if url := source_url(project):
                        st.link_button("Official record ↗", url)
    with funding_view:
        st.caption("Official portals to monitor; inclusion does not imply a dedicated project.")
        funding_columns = st.columns(2)
        for index, source in enumerate(FUNDING_WATCH):
            with funding_columns[index % 2]:
                with st.container(border=True):
                    st.caption(record_text(source, "region", default="Region not specified"))
                    st.markdown(f"#### {record_text(source, 'name', default='Funding source')}")
                    st.write(record_text(source, "purpose", default="Description pending."))
                    if url := source_url(source):
                        st.link_button("Open official portal ↗", url)
    with industry_view:
        st.info(
            "**Current assessment:** pre-commercial research field. These are adjacent capabilities "
            "and capital signals—not evidence that a listed organization is investing in or "
            "commercializing chiral phonons."
        )
        industry_columns = st.columns(2)
        for index, signal in enumerate(INDUSTRY_SIGNALS):
            with industry_columns[index % 2]:
                with st.container(border=True):
                    st.caption(
                        f"{record_text(signal, 'category', default='Field-level assessment')} · "
                        f"{record_text(signal, 'signal_type', legacy_key='signal', default='Maturity signal')}"
                    )
                    st.markdown(f"#### {record_text(signal, 'name', default='Industry signal')}")
                    st.write(
                        "**Verified activity:** "
                        + record_text(
                            signal, "evidence", legacy_key="detail", default="Review pending."
                        )
                    )
                    st.write(
                        "**Research relevance:** "
                        + record_text(
                            signal,
                            "relevance",
                            default="This record tracks the adjacent technology ecosystem.",
                        )
                    )
                    st.warning(
                        "**Claim boundary:** "
                        + record_text(
                            signal,
                            "boundary",
                            default=(
                                "No dedicated chiral-phonon activity is inferred without a primary source."
                            ),
                        )
                    )
                    if url := source_url(signal):
                        source_name = record_text(
                            signal, "source", default="primary source"
                        ).lower()
                        st.link_button(f"Open {source_name} ↗", url)
    with community_view:
        st.caption("Conferences, workshops, schools and active research networks.")
        event_columns = st.columns(2)
        for index, event in enumerate(events):
            with event_columns[index % 2]:
                with st.container(border=True):
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
                    st.markdown(f"#### {event.get('title', 'Community event')}")
                    st.write(event.get("description", "Description pending."))
                    if event.get("deadline"):
                        st.write(f"**Deadline:** {event['deadline']}")
                    if url := source_url(event):
                        st.link_button("Official source ↗", url)
    with resources_view:
        st.caption("Research tools, databases and official sources used by the field tracker.")
        resource_columns = st.columns(2)
        for index, item in enumerate(tools):
            with resource_columns[index % 2]:
                with st.container(border=True):
                    st.markdown(f"#### {item.get('name', 'Research resource')}")
                    st.write(item.get("description", "Description pending."))
                    st.caption(" · ".join(item.get("tags", [])))
                    if url := source_url(item):
                        st.link_button("Open resource ↗", url)

with admin_tab:
    st.markdown('<div class="section-kicker">Pipeline status</div>', unsafe_allow_html=True)
    st.subheader("Archive health and automation")
    st.markdown(
        '<div class="section-intro">A transparent operational view of what has been retrieved, '
        "reviewed and deferred. These states describe pipeline progress; they are not scientific "
        "quality judgements.</div>",
        unsafe_allow_html=True,
    )
    health = st.columns(4)
    health[0].metric("Retrieved", len(papers))
    health[1].metric("Classified", len(reviewed))
    health[2].metric("Awaiting classification", len(pending))
    health[3].metric("Discovery archive", len(rule_excluded))
    st.caption(
        "Discovery archive means broad search results that are not currently mapped into the field; "
        "it is an operational audit state, not a scientific judgement."
    )
    classified_fraction = len(reviewed) / len(papers) if papers else 0.0
    st.progress(classified_fraction)
    st.caption(f"Scientific classification coverage · {classified_fraction:.0%} of the archive")

    st.markdown("### Automation cadence")
    schedule_columns = st.columns(3)
    with schedule_columns[0]:
        with st.container(border=True):
            st.markdown("#### 04:00 UTC")
            st.caption("Daily metadata scan")
            st.write("Collect and deduplicate the newest arXiv metadata.")
    with schedule_columns[1]:
        with st.container(border=True):
            st.markdown("#### Every 4 hours · :40")
            st.caption("Scientific review")
            st.write("Resume pending classifications with checkpoint preservation.")
    with schedule_columns[2]:
        with st.container(border=True):
            st.markdown("#### 4 windows / day")
            st.caption("Historical backfill")
            st.write("02:10 · 08:10 · 14:10 · 20:10 UTC")

    status_columns = st.columns(2)
    status_columns[0].metric("Backfill next date", backfill_state.get("next_until", "—"))
    status_columns[1].metric(
        "Last review succeeded",
        review_history[-1].get("succeeded", 0) if review_history else 0,
    )

    with st.expander("Owner controls · run a metadata scan"):
        st.caption(
            "Manual dispatch is optional. The scheduled pipeline continues independently of this control."
        )
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

from __future__ import annotations

# ruff: noqa: E402 -- source-path bootstrap must precede project imports on Streamlit Cloud.
import hashlib
import hmac
import html
import importlib
import sys
from collections import Counter, defaultdict
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

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    go = None

from chiral_scanner.field_map import (
    ecosystem_areas,
    evidence_stage,
    is_experimental_evidence,
    is_field_paper,
    is_thz_frontier,
)
from chiral_scanner.github_dispatch import dispatch_metadata_scan
from chiral_scanner.people_map import author_connections
from chiral_scanner.research_geography import institution_activity
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
:root {
  --accent:#4f46e5;
  --accent-strong:#4338ca;
  --accent-soft:#eef1ff;
  --teal:#0d9488;
  --amber:#d97706;
  --ink:#161b2b;
  --muted:#5c6472;
  --surface:#ffffff;
  --soft:#f3f4fa;
  --line:#e4e7f0;
  --success:#047857;
  --warning:#b45309;
  --danger:#be123c;
  --radius:12px;
  --shadow:0 1px 2px rgba(23,26,50,.04), 0 6px 16px rgba(23,26,50,.05);
}
html {color-scheme:light;}
* {scrollbar-color:#c7cbdc transparent;}
.block-container {padding-top:1.1rem; padding-bottom:3rem; max-width:1160px;}
.stApp {background:#f5f6fb; color:var(--ink); font-feature-settings:"ss01";}
header[data-testid="stHeader"] {background:rgba(245,246,251,.92); backdrop-filter:blur(6px);}
.hero {padding:1.35rem 1.5rem; border-radius:16px; margin-bottom:1rem;
background:linear-gradient(135deg,#fff 0%,#f2f1ff 100%); border:1px solid var(--line); box-shadow:var(--shadow);}
.hero-kicker {display:flex; align-items:center; gap:.45rem; color:var(--accent-strong); font-size:.71rem;
font-weight:750; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.5rem;}
.live-dot {width:.46rem; height:.46rem; border-radius:999px; background:#10b981;
box-shadow:0 0 0 4px rgba(16,185,129,.14); display:inline-block;}
.hero h1 {margin:0; color:var(--ink); font-size:2.05rem; letter-spacing:-.04em; line-height:1.1;}
.hero p {max-width:800px; color:var(--muted); font-size:.94rem; line-height:1.55; margin:.5rem 0 .65rem;}
.hero-tags {display:flex; flex-wrap:wrap; gap:.4rem;}
.hero-tag {padding:.22rem .58rem; border:1px solid #d9dcf5; border-radius:999px;
color:var(--accent-strong); background:#fff; font-size:.71rem; font-weight:560;}
.coverage {display:flex; flex-wrap:wrap; gap:.35rem 1.1rem; padding:.55rem .8rem;
border-radius:10px; background:#fff; border:1px solid var(--line); color:var(--muted);
font-size:.78rem; margin:.6rem 0 1.1rem;}
.coverage strong {color:var(--ink); font-weight:640;}
.section-kicker {color:var(--accent-strong); font-size:.68rem; font-weight:750; letter-spacing:.08em;
text-transform:uppercase; margin-bottom:.15rem;}
.section-intro {color:var(--muted); max-width:820px; font-size:.86rem; line-height:1.5;
margin-top:-.2rem; margin-bottom:.75rem;}
.material-strip {padding:.55rem .74rem; border:1px solid var(--line); border-radius:9px;
background:#fff; color:#43485a; font-size:.8rem; margin:.4rem 0 .7rem;}
.date-row {display:flex; align-items:center; gap:.65rem; margin:1.05rem 0 .26rem;}
.date-row h2 {font-size:1rem; color:var(--ink); margin:0; font-weight:650;}
.count-pill {font-size:.68rem; color:var(--accent-strong); padding:.12rem .42rem; border-radius:999px;
background:var(--accent-soft); border:1px solid #d9dcf5;}
.paper-title {font-size:1rem; font-weight:660; line-height:1.4; margin-bottom:.16rem;}
.paper-title a {color:#1c2542; text-decoration:none;}
.paper-title a:hover {color:var(--accent-strong); text-decoration:underline; text-underline-offset:3px;}
.meta {color:#6a7180; font-size:.75rem; margin:.16rem 0 .32rem;}
.badge {display:inline-block; padding:.15rem .42rem; margin:.07rem .12rem .07rem 0;
border-radius:999px; background:#f1f2f7; border:1px solid #dfe1ec; font-size:.65rem; color:#3a3f4f; font-weight:540;}
.status-approved {background:#ecfdf5; border-color:#a7f3d0; color:#047857;}
.status-pending {background:#fffbeb; border-color:#fde68a; color:#92400e;}
.status-review {background:#fff1f2; border-color:#fecdd3; color:#be123c;}
.paper-signal {border-left:3px solid var(--accent); padding:.4rem .65rem; margin:.44rem 0 .3rem;
color:#3a3f52; font-size:.8rem; line-height:1.46; background:var(--accent-soft);}
.brief {padding:.75rem .9rem; border:1px solid #d9dcf5; border-radius:10px;
background:var(--accent-soft); color:#333a52; line-height:1.52; margin:.6rem 0 1rem; font-size:.87rem;}
.brief strong {color:var(--ink);}
.journey-card {height:100%; padding:.85rem .92rem; border:1px solid var(--line); border-radius:10px;
background:#fff;}
.journey-card .number {color:var(--accent-strong); font-size:.7rem; font-weight:750; letter-spacing:.06em;
text-transform:uppercase;}
.journey-card h3 {color:var(--ink); font-size:.98rem; margin:.22rem 0;}
.journey-card p {color:var(--muted); font-size:.8rem; line-height:1.46; margin:0;}
.insight-row {padding:.6rem .75rem; margin:.34rem 0; border-left:3px solid var(--accent);
border-radius:0 8px 8px 0; background:#fff; color:#333a52; font-size:.83rem; border:1px solid var(--line);
border-left-width:3px;}
.abstract {color:#454b5e; line-height:1.5; margin:.4rem 0; font-size:.85rem;}
div[data-testid="stMetric"] {padding:.65rem .78rem; background:#fff; border:1px solid var(--line);
border-radius:11px; min-height:80px; box-shadow:var(--shadow);}
div[data-testid="stMetricLabel"] {font-size:.72rem; color:#6a7180;}
div[data-testid="stMetricValue"] {font-size:1.42rem; color:var(--ink); font-weight:650;}
div[data-baseweb="tab-list"] {gap:.14rem; padding:0; border-bottom:1px solid var(--line);
background:transparent; overflow-x:auto;}
button[data-baseweb="tab"] {border-radius:8px 8px 0 0; padding:.45rem .68rem; color:#5c6472; font-size:.85rem;}
button[data-baseweb="tab"][aria-selected="true"] {color:var(--accent-strong); background:var(--accent-soft); font-weight:600;}
button[data-baseweb="tab"]:focus-visible, .stButton > button:focus-visible,
.stLinkButton > a:focus-visible {outline:3px solid rgba(79,70,229,.35); outline-offset:2px;}
div[data-testid="stExpander"] {border-color:var(--line); border-radius:10px; background:#fff;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line); border-radius:11px; background:#fff;}
.stButton > button, .stLinkButton > a {border-radius:8px;}
.stButton > button[kind="primary"] {background:var(--accent); border-color:var(--accent);}
.stLinkButton > a {text-decoration:none;}
[data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:10px; overflow:hidden;}
hr {border-color:var(--line);}
.tracker-card {padding:1rem 1.1rem; border-radius:12px; background:#fff;
border:1px solid var(--line); box-shadow:var(--shadow); margin:.5rem 0 1rem;}
.tracker-card h4 {margin:0 0 .3rem; color:var(--ink); font-size:1.05rem;}
.tracker-empty {padding:.85rem 1rem; border:1px dashed #c9cce0; border-radius:10px;
background:#fafafe; color:var(--muted); font-size:.84rem; margin:.5rem 0 1rem;}
.geo-chip {display:inline-flex; align-items:center; gap:.3rem; padding:.22rem .6rem; margin:.15rem .25rem .15rem 0;
border-radius:999px; background:#fff7ed; border:1px solid #fdba74; color:#9a3412; font-size:.73rem; font-weight:560;}
.map-note {display:flex; flex-wrap:wrap; gap:.3rem 1rem; color:var(--muted); font-size:.74rem; margin:.35rem 0 .1rem;}
.legend-dot {display:inline-block; width:.6rem; height:.6rem; border-radius:999px; margin-right:.3rem; vertical-align:middle;}
@media (max-width:700px) {
  .block-container {padding:.7rem .65rem 2rem;}
  .hero {padding:1rem 1rem;}
  .hero h1 {font-size:1.6rem;}
  .hero p {font-size:.85rem;}
  .coverage {display:block; line-height:1.65;}
  div[data-testid="stMetric"] {min-height:74px; padding:.5rem .55rem;}
  button[data-baseweb="tab"] {padding:.38rem .5rem; font-size:.76rem;}
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
    """Render a scan-friendly paper summary with full evidence on demand."""
    decision = paper.get("ai_decision") or {}
    status = feed_status(paper)
    title = html.escape(str(paper.get("title", "Untitled")))
    url = html.escape(str(paper.get("abstract_url", "https://arxiv.org")))
    authors = [str(author) for author in paper.get("authors", [])]
    author_names = ", ".join(authors[:3])
    if len(authors) > 3:
        author_names += " et al."
    abstract = str(paper.get("abstract", "")).strip()
    systems = decision.get("material_or_system_family", []) + decision.get(
        "materials_or_systems", []
    )
    methods = (
        decision.get("experimental_methods", [])
        + decision.get("excitation_methods", [])
        + decision.get("detection_methods", [])
        + decision.get("computational_methods", [])
    )
    field_areas = ecosystem_areas(paper) if decision else []
    tier = signal_tier(paper)
    evidence = evidence_stage(paper) if decision else status
    visible_tags = [tier, evidence, decision.get("research_type")]
    if systems:
        visible_tags.append(systems[0])
    reason = str(decision.get("reason", "")).strip()
    if not reason and abstract:
        reason = abstract
    signal = reason if len(reason) <= 190 else reason[:187].rstrip() + "…"

    with st.container(border=True):
        st.markdown(
            f'<div class="paper-title"><a href="{url}" target="_blank">{title}</a></div>'
            f'<div class="meta">{html.escape(author_names)} · '
            f"{short_date(paper.get('initial_submission_date'))} · "
            f"arXiv:{html.escape(str(paper.get('base_arxiv_id', '')))}</div>"
            f"<div>{badges(visible_tags, status)}</div>"
            + (
                f'<div class="paper-signal"><strong>Why it matters</strong> · '
                f"{html.escape(signal)}</div>"
                if signal
                else ""
            ),
            unsafe_allow_html=True,
        )
        actions = st.columns([1, 1, 5])
        actions[0].link_button("arXiv ↗", paper.get("abstract_url", "https://arxiv.org"))
        actions[1].link_button("PDF ↗", paper.get("pdf_url", "https://arxiv.org"))
        actions[2].caption(
            "Open the evidence panel for the abstract, classification basis, methods and caveats."
        )

        with st.expander("Abstract, evidence and methods"):
            if abstract:
                st.write(abstract)
            if decision:
                evidence_columns = st.columns(2)
                with evidence_columns[0]:
                    st.markdown(f"**Evidence maturity:** {evidence_stage(paper)}")
                    st.markdown(
                        "**Research focus:** "
                        + ", ".join(decision.get("research_focus", []) or ["Not specified"])
                    )
                    st.markdown(
                        "**Material/system:** " + ", ".join(systems or ["Not specified"])
                    )
                    st.markdown(
                        "**Field ecosystem:** " + ", ".join(field_areas or ["Not specified"])
                    )
                with evidence_columns[1]:
                    st.markdown(
                        "**Methods performed:** " + ", ".join(methods or ["Not specified"])
                    )
                    st.markdown(
                        "**Generation mechanism:** "
                        + ", ".join(decision.get("generation_mechanisms", []) or ["Not specified"])
                    )
                    st.markdown(
                        "**Physical properties:** "
                        + ", ".join(decision.get("physical_properties", []) or ["Not specified"])
                    )
                    st.markdown(
                        "**Application direction:** "
                        + ", ".join(decision.get("application_directions", []) or ["Not claimed"])
                    )
                phrases = decision.get("supporting_phrases", [])
                if phrases:
                    st.caption("Evidence phrases · " + " · ".join(phrases))
                caveats = decision.get("evidence_caveats", [])
                if caveats:
                    st.warning("Evidence caveats: " + " · ".join(caveats))
                st.caption("Classification basis · " + str(decision.get("reason", "—")))
            else:
                st.info("This paper is stored safely but has not completed scientific review.")
            st.caption("arXiv categories · " + ", ".join(paper.get("categories", [])))


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
    overview_tab,
    paper_tab,
    history_tab,
    analysis_tab,
    people_tab,
    news_tab,
    ecosystem_tab,
    admin_tab,
) = st.tabs(
    [
        "Brief",
        "Papers",
        "Evidence atlas",
        "Trends",
        "Community",
        "Signals",
        "Opportunities",
        "Methods & pipeline",
    ]
)


with overview_tab:
    st.markdown('<div class="section-kicker">Field brief</div>', unsafe_allow_html=True)
    st.subheader("What changed, what is established, and what needs attention")
    st.markdown(
        '<div class="section-intro">A decision-ready starting point for researchers and R&D teams. '
        "Open Papers for daily discovery, Evidence atlas for landmark results, Trends for the "
        "scientific landscape, and Community for institutions and collaborators.</div>",
        unsafe_allow_html=True,
    )
    evidence_gap = max(brief["strong"] - brief["experimental"], 0)
    evidence_metrics = st.columns(4)
    evidence_metrics[0].metric("Experimental studies", brief["experimental"])
    evidence_metrics[1].metric("Direct measurements", brief["direct"])
    evidence_metrics[2].metric("Theory / evidence gap", evidence_gap)
    evidence_metrics[3].metric("Needs interpretation", brief["needs_interpretation"])

    brief_columns = st.columns([3, 2])
    with brief_columns[0]:
        st.markdown("### Latest mapped papers")
        latest_mapped = sorted(
            approved,
            key=lambda paper: paper.get("initial_submission_date", ""),
            reverse=True,
        )[:4]
        if latest_mapped:
            for paper in latest_mapped:
                title = html.escape(str(paper.get("title", "Untitled")))
                url = html.escape(str(paper.get("abstract_url", "https://arxiv.org")))
                signal = signal_tier(paper)
                st.markdown(
                    f'<div class="insight-row"><strong>{short_date(paper.get("initial_submission_date"))}</strong> · '
                    f'<a href="{url}" target="_blank">{title}</a><br><span class="meta">{html.escape(signal)}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Mapped papers will appear here after scientific review.")

    with brief_columns[1]:
        with st.container(border=True):
            st.markdown("#### Leading research directions")
            if brief["top_focus"]:
                for label, count in brief["top_focus"][:5]:
                    st.markdown(f"**{count}** · {label}")
            else:
                st.caption("More classified evidence is needed.")

        with st.container(border=True):
            st.markdown("#### Use the tracker by task")
            st.markdown("**Discover** · Open Papers for the newest mapped work.")
            st.markdown("**Verify** · Use Evidence atlas to inspect landmark claims and caveats.")
            st.markdown("**Compare** · Use Trends for materials, methods and evidence maturity.")
            st.markdown("**Connect** · Use Community for institutions, authors and collaborations.")

        st.info(
            "Evidence rule: circular polarization, phonon angular momentum and true dynamical "
            "chirality remain related but distinct scientific claims."
        )

with history_tab:
    st.markdown('<div class="section-kicker">History & materials</div>', unsafe_allow_html=True)
    st.subheader("Landmark evidence and the evolution of the concept")
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
                "All mapped research",
                "Experiments & measurement",
                "THz & coherent control",
                "Theory & materials",
                "Coupled quantum responses",
                "Open interpretation",
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

    if view == "All mapped research":
        candidates = approved
    elif view == "THz & coherent control":
        candidates = thz_frontier
    elif view == "Experiments & measurement":
        candidates = experimental
    elif view == "Open interpretation":
        candidates = review_queue
    elif view == "Theory & materials":
        candidates = [
            p
            for p in approved
            if (p.get("ai_decision") or {}).get("research_type") in {"Theory", "Computational"}
            or "Theory & materials discovery" in ecosystem_areas(p)
        ]
    else:
        response_areas = {
            "Magnetism & spintronics",
            "2D optoelectronics & quantum materials",
            "Transport, Hall & mechanics",
        }
        candidates = [p for p in approved if response_areas.intersection(ecosystem_areas(p))]

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
    if view == "All mapped research":
        st.caption(
            "Core results, connected phonon-angular-momentum physics and open interpretations."
        )
    elif view == "THz & coherent control":
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
    elif view == "Experiments & measurement":
        st.caption("Original experimental and combined theory–experiment studies.")
    elif view == "Open interpretation":
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
    refresh_columns = st.columns([1, 3])
    with refresh_columns[0]:
        if st.button("🔄 Refresh cached data", help="Clears this app's short-lived data cache and reloads the archive immediately, without affecting the scan, review or backfill pipeline."):
            st.cache_data.clear()
            st.rerun()
    with refresh_columns[1]:
        st.caption(
            "The archive is cached for up to 120 seconds for speed. Use this after a scan or "
            "review run completes if the numbers below still look stale."
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

with people_tab:
    st.markdown('<div class="section-kicker">Research community</div>', unsafe_allow_html=True)
    st.subheader("Researchers, institutions and where the field is being built")
    st.markdown(
        '<div class="section-intro">Search a researcher to see their papers, active span and '
        "verified institution highlighted on the map. Connections below mean verified "
        "co-authorship in the stored papers—not inferred influence or citation.</div>",
        unsafe_allow_html=True,
    )
    people, collaboration_links = author_connections(approved)
    repeat_links = [link for link in collaboration_links if link["joint_papers"] >= 2]
    active_years = sorted(
        {
            parsed.year
            for paper in approved
            if (parsed := parse_date(paper.get("initial_submission_date"))) is not None
        }
    )
    institutions, institution_links, geo_coverage = institution_activity(approved)
    active_institutions = [item for item in institutions if item.get("paper_count", 0)]
    covered_papers = int(geo_coverage.get("covered_papers", 0) or 0)
    total_geo_papers = int(geo_coverage.get("total_papers", len(approved)) or 0)
    country_count = int(
        geo_coverage.get(
            "countries",
            len({item.get("country") for item in active_institutions if item.get("country")}),
        )
        or 0
    )
    paper_coverage = covered_papers / total_geo_papers if total_geo_papers else 0.0

    community_metrics = st.columns(5)
    community_metrics[0].metric("Mapped authors", len(people))
    community_metrics[1].metric(
        "Verified authors", int(geo_coverage.get("verified_authors", 0) or 0)
    )
    community_metrics[2].metric("Verified institutions", len(active_institutions))
    community_metrics[3].metric("Countries", country_count)
    community_metrics[4].metric("Repeated collaborations", len(repeat_links))
    st.progress(
        paper_coverage,
        text=(
            f"{paper_coverage:.1%} of mapped papers ({covered_papers}/{total_geo_papers}) have a "
            "verified institution"
        ),
    )
    registry_timestamp = geo_coverage.get("registry_updated")
    registry_label = short_date(str(registry_timestamp)) if registry_timestamp else "date unavailable"
    st.caption(
        f"Affiliations updated {registry_label} · "
        f"{int(geo_coverage.get('uncovered_papers', 0) or 0)} papers remain unresolved."
    )

    author_institutions: dict[str, list[dict]] = defaultdict(list)
    for institution in active_institutions:
        for author_name in institution.get("mapped_authors", []):
            author_institutions[author_name].append(institution)

    st.markdown("### Track a researcher")
    st.caption(
        "Type a name to jump to it. The profile below and the map in the Geography section both "
        "follow your selection."
    )
    tracker_placeholder = "Select a researcher…"
    tracked_author = st.selectbox(
        "Researcher",
        [tracker_placeholder] + [item["author"] for item in people],
        key="tracked_author",
        label_visibility="collapsed",
    )
    tracked_institutions: list[dict] = []
    if tracked_author != tracker_placeholder:
        profile = next(item for item in people if item["author"] == tracked_author)
        tracked_institutions = author_institutions.get(tracked_author, [])
        with st.container(border=True):
            profile_columns = st.columns([3, 2])
            with profile_columns[0]:
                st.markdown(f"#### {html.escape(tracked_author)}")
                span = (
                    str(profile["first_year"])
                    if profile["first_year"] == profile["latest_year"]
                    else f"{profile['first_year']}–{profile['latest_year']}"
                )
                st.caption(
                    f"{profile['papers']} mapped papers · active {span} · "
                    f"{len(profile['years'])} active years"
                )
                if profile["materials"]:
                    st.caption("Leading materials · " + " · ".join(profile["materials"]))
            with profile_columns[1]:
                st.markdown("**Verified institution**")
                if tracked_institutions:
                    st.markdown(
                        "".join(
                            f'<span class="geo-chip">📍 {html.escape(institution["institution"])}'
                            + (
                                f' · {html.escape(", ".join(v for v in [institution.get("city"), institution.get("country")] if v))}'
                                if institution.get("city") or institution.get("country")
                                else ""
                            )
                            + "</span>"
                            for institution in tracked_institutions
                        ),
                        unsafe_allow_html=True,
                    )
                    st.caption("Shown as an orange marker on the map below.")
                else:
                    st.caption(
                        "No verified institution on record yet — this researcher stays in the "
                        "collaboration data only."
                    )
            st.markdown("**Papers**")
            record_list = profile["records"]
            for record in record_list[:6]:
                title = html.escape(str(record.get("title", "Untitled")))
                url = html.escape(str(record.get("abstract_url", "https://arxiv.org")))
                year = short_date(record.get("initial_submission_date"))
                focus = ecosystem_areas(record)[:2]
                st.markdown(
                    f'<div class="insight-row"><strong>{year}</strong> · '
                    f'<a href="{url}" target="_blank">{title}</a>'
                    f"{' · ' + html.escape(' / '.join(focus)) if focus else ''}</div>",
                    unsafe_allow_html=True,
                )
            if len(record_list) > 6:
                with st.expander(f"Show {len(record_list) - 6} more papers"):
                    for record in record_list[6:]:
                        title = html.escape(str(record.get("title", "Untitled")))
                        url = html.escape(str(record.get("abstract_url", "https://arxiv.org")))
                        year = short_date(record.get("initial_submission_date"))
                        st.markdown(
                            f'<div class="insight-row"><strong>{year}</strong> · '
                            f'<a href="{url}" target="_blank">{title}</a></div>',
                            unsafe_allow_html=True,
                        )
    else:
        st.markdown(
            '<div class="tracker-empty">Choose a researcher above to open their profile and '
            "highlight their institution on the map.</div>",
            unsafe_allow_html=True,
        )

    tracked_institution_ids = {item["id"] for item in tracked_institutions}

    st.markdown("### Research geography")
    st.caption(
        "Locations and roles come only from cited affiliation evidence. Paper activity, "
        "materials and collaboration links are recalculated from the live archive."
    )

    if active_institutions:
        country_stats: dict[str, dict] = {}
        for item in active_institutions:
            country = str(item.get("country") or item.get("country_code") or "Unknown")
            stats = country_stats.setdefault(
                country,
                {"paper_ids": set(), "institutions": 0, "authors": set()},
            )
            stats["institutions"] += 1
            stats["paper_ids"].update(item.get("paper_ids", []))
            stats["authors"].update(item.get("mapped_authors", []))

        country_table = pd.DataFrame(
            [
                {
                    "Country": country,
                    "Unique mapped papers": len(stats["paper_ids"]),
                    "Institutions": stats["institutions"],
                    "Verified authors": len(stats["authors"]),
                }
                for country, stats in country_stats.items()
            ]
        ).sort_values(
            ["Unique mapped papers", "Institutions", "Country"],
            ascending=[False, False, True],
        )

        map_view, countries_view, centres_view = st.tabs(
            ["Map", "Countries", "Institutions"]
        )

        with map_view:
            st.caption(
                "The default map emphasizes established centres. One-paper records and repeated "
                "collaboration links remain available through the controls."
            )
            if tracked_author != tracker_placeholder:
                if tracked_institutions:
                    st.markdown(
                        f'<div class="map-note">📍 <strong>{html.escape(tracked_author)}</strong> is '
                        "highlighted in orange below, regardless of the filters.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(f"{tracked_author} has no verified institution to place on the map.")
            map_controls = st.columns([2, 2, 2, 2])
            country_filter = map_controls[0].selectbox(
                "Country",
                ["All countries"] + sorted(country_stats),
                key="research_geo_country",
            )
            minimum_papers = map_controls[1].select_slider(
                "Minimum mapped papers",
                options=[1, 2, 3, 5],
                value=2,
                key="research_geo_minimum_papers",
            )
            projection_label = map_controls[2].selectbox(
                "Projection",
                ["World map", "Flat 2D map"],
                key="research_geo_projection_compact",
            )
            show_connections = map_controls[3].checkbox(
                "Show repeated links",
                value=False,
                help="Only institution links supported by at least two mapped papers are shown.",
                key="research_geo_connections",
            )

            visible_institutions = [
                item
                for item in active_institutions
                if item.get("paper_count", 0) >= minimum_papers
                and (
                    country_filter == "All countries"
                    or str(item.get("country") or item.get("country_code")) == country_filter
                )
            ]
            st.caption(
                f"Showing {len(visible_institutions)} of {len(active_institutions)} verified institutions."
            )

            if not visible_institutions and not tracked_institution_ids:
                st.info("No institution matches the current country and paper-count filters.")
            elif go is None:
                st.warning(
                    "The interactive map is temporarily unavailable. Country and institution "
                    "summaries remain available in the adjacent tabs."
                )
            else:
                projection = (
                    "natural earth" if projection_label == "World map" else "equirectangular"
                )
                by_id = {item["id"]: item for item in visible_institutions}
                map_figure = go.Figure()

                if show_connections:
                    visible_links = [
                        link
                        for link in institution_links
                        if link.get("joint_papers", 0) >= 2
                        and link.get("institution_1") in by_id
                        and link.get("institution_2") in by_id
                    ]
                    visible_links.sort(
                        key=lambda link: link.get("joint_papers", 0), reverse=True
                    )
                    for link in visible_links[:40]:
                        first = by_id[link["institution_1"]]
                        second = by_id[link["institution_2"]]
                        map_figure.add_trace(
                            go.Scattergeo(
                                lon=[first["longitude"], second["longitude"]],
                                lat=[first["latitude"], second["latitude"]],
                                mode="lines",
                                line={
                                    "width": 0.7 + min(link["joint_papers"], 4) * 0.45,
                                    "color": "rgba(37,99,235,.34)",
                                },
                                opacity=0.32,
                                hoverinfo="text",
                                text=(
                                    f"<b>{first['institution']} ↔ {second['institution']}</b><br>"
                                    f"Repeated mapped papers: {link['joint_papers']}"
                                ),
                                showlegend=False,
                            )
                        )
                    if not visible_links:
                        st.caption(
                            "No repeated institution-level collaboration is present in this view."
                        )

                def hover_fields(item: dict) -> list:
                    return [
                        item["institution"],
                        ", ".join(
                            value for value in [item.get("city"), item.get("country")] if value
                        ),
                        item["paper_count"],
                        item["author_count"],
                        ", ".join(item.get("mapped_authors", [])[:4]) or "—",
                        (
                            "—"
                            if not item["years"]
                            else (
                                str(item["years"][0])
                                if len(item["years"]) == 1
                                else f"{item['years'][0]}–{item['years'][-1]}"
                            )
                        ),
                    ]

                hover_template = (
                    "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                    "Mapped papers: %{customdata[2]}<br>"
                    "Verified authors: %{customdata[3]}<br>"
                    "Leading authors: %{customdata[4]}<br>"
                    "Active years: %{customdata[5]}<extra></extra>"
                )

                map_figure.add_trace(
                    go.Scattergeo(
                        lon=[item["longitude"] for item in visible_institutions],
                        lat=[item["latitude"] for item in visible_institutions],
                        mode="markers",
                        marker={
                            "size": [
                                10 + 5 * min(item["paper_count"] ** 0.5, 3.5)
                                for item in visible_institutions
                            ],
                            "color": [item["paper_count"] for item in visible_institutions],
                            "colorscale": [
                                [0.0, "#a5b4fc"],
                                [0.35, "#818cf8"],
                                [0.65, "#4f46e5"],
                                [1.0, "#1e1b4b"],
                            ],
                            "line": {"color": "#ffffff", "width": 1.1},
                            "opacity": 0.92,
                            "colorbar": {
                                "title": {"text": "Mapped papers", "side": "right"},
                                "thickness": 12,
                                "len": 0.62,
                                "outlinewidth": 0,
                                "tickfont": {"color": "#3a3f52", "size": 11},
                            },
                            "cmin": 1,
                        },
                        customdata=[hover_fields(item) for item in visible_institutions],
                        hovertemplate=hover_template,
                        name="Verified institutions",
                        showlegend=False,
                    )
                )

                highlight_items = [
                    item for item in active_institutions if item["id"] in tracked_institution_ids
                ]
                if highlight_items:
                    map_figure.add_trace(
                        go.Scattergeo(
                            lon=[item["longitude"] for item in highlight_items],
                            lat=[item["latitude"] for item in highlight_items],
                            mode="markers",
                            marker={
                                "size": 22,
                                "symbol": "star",
                                "color": "#f97316",
                                "line": {"color": "#7c2d12", "width": 1.4},
                                "opacity": 1,
                            },
                            customdata=[hover_fields(item) for item in highlight_items],
                            hovertemplate=(
                                f"<b>{html.escape(tracked_author)}</b><br>" + hover_template
                            ),
                            name=tracked_author,
                            showlegend=False,
                        )
                    )

                map_figure.update_geos(
                    projection_type=projection,
                    showland=True,
                    landcolor="#e9ecf3",
                    showocean=True,
                    oceancolor="#f7f8fc",
                    showlakes=True,
                    lakecolor="#f7f8fc",
                    showcountries=True,
                    countrycolor="#b7bcd0",
                    coastlinecolor="#9aa0b8",
                    coastlinewidth=0.6,
                    bgcolor="rgba(0,0,0,0)",
                )
                map_figure.update_layout(
                    height=500,
                    margin={"l": 0, "r": 0, "t": 4, "b": 0},
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#161b2b"},
                )
                st.plotly_chart(
                    map_figure,
                    use_container_width=True,
                    config={"displaylogo": False, "scrollZoom": False},
                )
                st.markdown(
                    '<div class="map-note">'
                    '<span><span class="legend-dot" style="background:#a5b4fc;"></span>Fewer papers</span>'
                    '<span><span class="legend-dot" style="background:#1e1b4b;"></span>More papers</span>'
                    '<span><span class="legend-dot" style="background:#f97316;"></span>Tracked researcher</span>'
                    "</div>",
                    unsafe_allow_html=True,
                )

        with countries_view:
            st.caption(
                "Paper counts are unique within each country; a multi-country paper can appear "
                "once in more than one national total."
            )
            st.dataframe(
                country_table,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Unique mapped papers": st.column_config.ProgressColumn(
                        "Unique mapped papers",
                        min_value=0,
                        max_value=max(country_table["Unique mapped papers"]),
                    )
                },
            )

        with centres_view:
            centre_controls = st.columns([3, 2])
            centre_search = centre_controls[0].text_input(
                "Search institutions",
                placeholder="Institution, city or country…",
                key="research_geo_centre_search",
            )
            centre_country = centre_controls[1].selectbox(
                "Limit to country",
                ["All countries"] + sorted(country_stats),
                key="research_geo_centre_country",
            )
            centre_needle = centre_search.casefold().strip()
            centre_rows = [
                item
                for item in active_institutions
                if (
                    centre_country == "All countries"
                    or str(item.get("country") or item.get("country_code")) == centre_country
                )
                and (
                    not centre_needle
                    or centre_needle
                    in " ".join(
                        [
                            str(item.get("institution", "")),
                            str(item.get("city", "")),
                            str(item.get("country", "")),
                        ]
                    ).casefold()
                )
            ]
            centre_rows.sort(
                key=lambda item: (-item.get("paper_count", 0), item.get("institution", ""))
            )
            centre_table = pd.DataFrame(
                [
                    {
                        "Institution": item["institution"],
                        "Country": item.get("country", "—"),
                        "City": item.get("city", "—"),
                        "Mapped papers": item["paper_count"],
                        "Verified authors": item["author_count"],
                    }
                    for item in centre_rows[:50]
                ]
            )
            st.caption(
                f"{len(centre_rows)} matching institutions · showing the 50 strongest records."
            )
            if centre_table.empty:
                st.info("No institution matches the current search.")
            else:
                st.dataframe(
                    centre_table,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Mapped papers": st.column_config.ProgressColumn(
                            "Mapped papers",
                            min_value=0,
                            max_value=max(item["paper_count"] for item in centre_rows),
                        )
                    },
                )
                selected_institution = st.selectbox(
                    "Open institution record",
                    [item["institution"] for item in centre_rows],
                    key="people_institution_compact",
                )
                institution = next(
                    item
                    for item in centre_rows
                    if item["institution"] == selected_institution
                )
                with st.expander(
                    f"{institution['institution']} · evidence record",
                    expanded=False,
                ):
                    st.caption(
                        " · ".join(
                            value
                            for value in [
                                institution.get("city"),
                                institution.get("country"),
                                institution.get("institution_type", "Research institution"),
                            ]
                            if value
                        )
                    )
                    detail_columns = st.columns(3)
                    detail_columns[0].metric("Mapped papers", institution["paper_count"])
                    detail_columns[1].metric("Verified authors", institution["author_count"])
                    detail_columns[2].metric(
                        "Active span",
                        (
                            "—"
                            if not institution["years"]
                            else (
                                str(institution["years"][0])
                                if len(institution["years"]) == 1
                                else f"{institution['years'][0]}–{institution['years'][-1]}"
                            )
                        ),
                    )
                    st.write(
                        "**Verified authors:** " + ", ".join(institution["mapped_authors"])
                    )
                    if institution.get("materials"):
                        st.write(
                            "**Materials represented:** "
                            + ", ".join(institution["materials"])
                        )
                    if institution.get("directions"):
                        st.write(
                            "**Research directions:** "
                            + ", ".join(institution["directions"])
                        )
                    if institution.get("evidence_url"):
                        st.link_button(
                            "Open affiliation evidence ↗", institution["evidence_url"]
                        )
    else:
        st.info("Verified institution markers will appear when matched authors enter the field map.")

    if int(geo_coverage.get("uncovered_papers", 0) or 0):
        st.info(
            "Unresolved papers stay in the author and co-authorship analysis but are omitted from "
            "the geographic layer until a reliable paper or institutional source is recorded."
        )

    if not people:
        st.info("Author connections will appear as papers complete scientific review.")
    else:
        with st.expander("Field-wide community stats · top authors, yearly trend, repeated pairs"):
            map_columns = st.columns([3, 2])
            with map_columns[0]:
                st.markdown("**Most active authors**")
                top_people = pd.DataFrame(
                    [
                        {
                            "Author": item["author"],
                            "Mapped papers": item["papers"],
                            "Active span": (
                                str(item["first_year"])
                                if item["first_year"] == item["latest_year"]
                                else f"{item['first_year']}–{item['latest_year']}"
                            ),
                        }
                        for item in people[:20]
                    ]
                )
                st.dataframe(
                    top_people,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Mapped papers": st.column_config.ProgressColumn(
                            "Mapped papers",
                            min_value=0,
                            max_value=max(item["papers"] for item in people),
                        )
                    },
                )
            with map_columns[1]:
                yearly_counts = Counter(
                    parsed.year
                    for paper in approved
                    if (parsed := parse_date(paper.get("initial_submission_date"))) is not None
                )
                st.markdown("**Papers by year**")
                st.bar_chart(
                    pd.Series(yearly_counts, dtype="int64").sort_index(),
                    x_label="Year",
                    y_label="Mapped papers",
                )
            st.markdown("**Repeated co-author pairs**")
            st.caption(
                "Ranked by joint mapped papers. Single-paper links are hidden to keep this useful."
            )
            if repeat_links:
                st.dataframe(
                    pd.DataFrame(repeat_links[:30]).rename(
                        columns={
                            "author_1": "Author",
                            "author_2": "Collaborator",
                            "joint_papers": "Joint mapped papers",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No repeated co-author pair is present in the currently mapped archive.")

st.divider()
st.caption(
    "Independent research tool using the official arXiv API. Not affiliated with or endorsed by arXiv. "
    f"Page generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}."
)

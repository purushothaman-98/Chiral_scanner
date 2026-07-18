from __future__ import annotations

import hashlib
import hmac
import html
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from chiral_scanner.config import PROMPT_VERSION
from chiral_scanner.github_dispatch import dispatch_metadata_scan
from chiral_scanner.scope import has_chiral_phonon_scope
from chiral_scanner.storage import empty_archive, load_json
from chiral_scanner.ui import flatten_unique, paginate

ROOT = Path(__file__).parent
DATA = ROOT / "data"

st.set_page_config(
    page_title="Chiral Phonon Research Scanner",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
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


def decision_is_current(paper: dict) -> bool:
    return bool(paper.get("ai_decision"))


def scope_passes(paper: dict) -> bool:
    return has_chiral_phonon_scope(paper.get("title", ""), paper.get("abstract", ""))


def feed_status(paper: dict) -> str:
    if not decision_is_current(paper):
        return "Pending AI review"
    decision = paper["ai_decision"]
    if decision.get("relevance") == "Uncertain":
        return "Needs scientific review"
    if decision.get("include_in_feed") is True and scope_passes(paper):
        return "Approved research feed"
    if decision.get("include_in_feed") is True:
        return "Needs scientific review"
    return "Excluded candidate"


def is_experimental_study(paper: dict) -> bool:
    return feed_status(paper) == "Approved research feed" and (
        paper.get("ai_decision", {}).get("research_type")
        in {"Experimental", "Theory + Experiment"}
    )


def badges(values: list[str], status: str | None = None) -> str:
    result: list[str] = []
    for index, value in enumerate(value for value in values if value):
        extra = ""
        if index == 0 and status == "Approved research feed":
            extra = " status-approved"
        elif index == 0 and status == "Pending AI review":
            extra = " status-pending"
        elif index == 0 and status == "Needs scientific review":
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
    tags = [status]
    if decision_is_current(paper):
        tags.extend([decision.get("relevance"), decision.get("research_type")])

    with st.container(border=True):
        st.markdown(
            f'<div class="paper-title"><a href="{url}" target="_blank">{title}</a></div>'
            f'<div class="meta">{html.escape(author_names)} · Submitted '
            f'{short_date(paper.get("initial_submission_date"))} · '
            f'arXiv:{html.escape(str(paper.get("base_arxiv_id", "")))}</div>'
            f'<div>{badges(tags, status)}{badges((systems + methods)[:4])}</div>'
            f'<div class="abstract">{html.escape(preview)}</div>',
            unsafe_allow_html=True,
        )
        links = st.columns([1, 1, 4])
        links[0].link_button("arXiv page ↗", paper.get("abstract_url", "https://arxiv.org"))
        links[1].link_button("PDF ↗", paper.get("pdf_url", "https://arxiv.org"))
        if len(systems + methods) > 4:
            links[2].caption(f"+{len(systems + methods) - 4} additional scientific labels")

        with st.expander("Abstract, complete metadata and classification evidence"):
            st.write(abstract)
            if decision:
                st.markdown(f"**Classification reason:** {decision.get('reason', '—')}")
                phrases = decision.get("supporting_phrases", [])
                if phrases:
                    st.markdown("**Evidence from abstract:** " + " · ".join(phrases))
                st.markdown("**Material/system:** " + ", ".join(systems or ["Not specified"]))
                st.markdown("**Methods:** " + ", ".join(methods or ["Not specified"]))
                st.markdown(
                    "**Properties:** "
                    + ", ".join(decision.get("physical_properties", []) or ["Not specified"])
                )
            else:
                st.info("This paper is stored safely but has not completed AI review.")
            st.caption("arXiv categories: " + ", ".join(paper.get("categories", [])))


archive, history, events, tools = load_all()
papers = archive.get("papers", [])
statuses = {paper["base_arxiv_id"]: feed_status(paper) for paper in papers}
approved = [p for p in papers if statuses[p["base_arxiv_id"]] == "Approved research feed"]
pending = [p for p in papers if statuses[p["base_arxiv_id"]] == "Pending AI review"]
review_queue = [p for p in papers if statuses[p["base_arxiv_id"]] == "Needs scientific review"]
experimental = [p for p in papers if is_experimental_study(p)]
reviewed = [p for p in papers if decision_is_current(p)]

st.markdown('<div class="topline">ARXIV CHIRAL PHONON FEED · DAILY AT 04:00 UTC</div>', unsafe_allow_html=True)
st.markdown(
    """
<div class="hero">
<h1>Chiral Phonon Research Scanner</h1>
<p>A date-ordered research feed for chiral phonons, phonon angular momentum,
dynamical multiferroicity, phonomagnetism and nonlinear phononics. Every retrieved
candidate is preserved for audit, while the default feed shows only scientifically approved papers.</p>
</div>
""",
    unsafe_allow_html=True,
)

metrics = st.columns(4)
metrics[0].metric("Retrieved candidates", len(papers), help="Every deduplicated arXiv result stored in the archive.")
metrics[1].metric(
    "AI reviewed",
    len(reviewed),
    help=f"Papers with a stored AI decision. New decisions use {PROMPT_VERSION}.",
)
metrics[2].metric("Approved research feed", len(approved), help="AI-approved papers that also pass the independent phonon/lattice scope guard.")
metrics[3].metric("Approved experimental studies", len(experimental), help="Approved Experimental and Theory + Experiment papers; rejected candidates are not counted.")

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
    f'{len(pending)} pending · {len(review_queue)} need scientific review</div>',
    unsafe_allow_html=True,
)

paper_tab, analysis_tab, events_tab, tools_tab, admin_tab = st.tabs(
    ["Research feed", "Analysis", "Opportunities", "Tools & sources", "Owner controls"]
)

with paper_tab:
    with st.sidebar:
        st.header("Explore the archive")
        st.caption("The approved feed is selected by default. Excluded candidates remain auditable.")
        view = st.radio(
            "Feed",
            [
                "Approved research feed",
                "Experimental studies",
                "Pending AI review",
                "Needs scientific review",
                "All retrieved candidates",
            ],
        )
        search = st.text_input("Search", placeholder="Title, abstract, author, arXiv ID…")
        current_decisions = [p for p in papers if decision_is_current(p)]
        relevance_filter = st.multiselect(
            "Chiral-phonon relevance", flatten_unique(current_decisions, ("ai_decision", "relevance"))
        )
        research_filter = st.multiselect(
            "Research type", flatten_unique(current_decisions, ("ai_decision", "research_type"))
        )
        family_filter = st.multiselect(
            "Material family", flatten_unique(current_decisions, ("ai_decision", "material_or_system_family"))
        )
        exp_filter = st.multiselect(
            "Experimental method", flatten_unique(current_decisions, ("ai_decision", "experimental_methods"))
        )
        excitation_filter = st.multiselect(
            "Excitation", flatten_unique(current_decisions, ("ai_decision", "excitation_methods"))
        )
        detection_filter = st.multiselect(
            "Detection", flatten_unique(current_decisions, ("ai_decision", "detection_methods"))
        )
        theory_filter = st.multiselect(
            "Theory / computation", flatten_unique(current_decisions, ("ai_decision", "computational_methods"))
        )
        property_filter = st.multiselect(
            "Physical property", flatten_unique(current_decisions, ("ai_decision", "physical_properties"))
        )

    if view == "Approved research feed":
        candidates = approved
    elif view == "Experimental studies":
        candidates = experimental
    elif view == "Pending AI review":
        candidates = pending
    elif view == "Needs scientific review":
        candidates = review_queue
    else:
        candidates = papers

    filtered: list[dict] = []
    needle = search.casefold().strip()
    for paper in candidates:
        decision = paper.get("ai_decision") or {}
        searchable = " ".join(
            [paper.get("base_arxiv_id", ""), paper.get("title", ""), paper.get("abstract", ""), " ".join(paper.get("authors", []))]
        ).casefold()
        if needle and needle not in searchable:
            continue
        scalar_filters = [(relevance_filter, "relevance"), (research_filter, "research_type")]
        if any(selected and decision.get(field) not in selected for selected, field in scalar_filters):
            continue
        list_filters = [
            (family_filter, "material_or_system_family"),
            (exp_filter, "experimental_methods"),
            (excitation_filter, "excitation_methods"),
            (detection_filter, "detection_methods"),
            (theory_filter, "computational_methods"),
            (property_filter, "physical_properties"),
        ]
        if any(selected and not set(selected).intersection(decision.get(field, [])) for selected, field in list_filters):
            continue
        filtered.append(paper)

    filtered.sort(key=lambda p: p.get("initial_submission_date", ""), reverse=True)
    st.subheader(f"{view} · {len(filtered)} papers")
    if view == "Approved research feed":
        st.caption("Only current AI approvals that independently pass the phonon/lattice scope guard.")
    elif view == "Experimental studies":
        st.caption("Only approved original experimental or combined theory–experiment studies.")

    page_size = 20
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.selectbox("Page", range(1, total_pages + 1), format_func=lambda value: f"Page {value} of {total_pages}")
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
    st.subheader("Approved-feed analysis")
    st.caption("Charts use only the scientifically approved feed; rejected candidates cannot distort the distributions.")
    if not approved:
        st.info("Analysis will appear as current AI classifications are completed.")
    else:
        frame = pd.DataFrame(
            {
                "date": [pd.to_datetime(p["initial_submission_date"], utc=True).date() for p in approved],
                "research_type": [p["ai_decision"]["research_type"] for p in approved],
                "relevance": [p["ai_decision"]["relevance"] for p in approved],
            }
        )
        frame["week"] = pd.to_datetime(frame["date"]).dt.to_period("W").dt.start_time
        left, right = st.columns(2)
        left.line_chart(frame.groupby("date").size().rename("approved papers"))
        right.line_chart(frame.groupby("week").size().rename("approved papers"))

        def distribution(field: str) -> pd.Series:
            values = [value for paper in approved for value in paper["ai_decision"].get(field, [])]
            return pd.Series(values, dtype="object").value_counts().head(15)

        rows = [
            ("Material families", "material_or_system_family"),
            ("Experimental methods", "experimental_methods"),
            ("Excitation methods", "excitation_methods"),
            ("Detection methods", "detection_methods"),
            ("Theory / computation", "computational_methods"),
            ("Physical properties", "physical_properties"),
        ]
        for start in range(0, len(rows), 3):
            columns = st.columns(3)
            for column, (title, field) in zip(columns, rows[start : start + 3], strict=False):
                column.markdown(f"#### {title}")
                column.bar_chart(distribution(field))

with events_tab:
    st.subheader("Conferences, workshops, schools and networks")
    for event in events:
        with st.container(border=True):
            st.markdown(f"### {event['title']}")
            st.write(event.get("description", ""))
            st.caption(" · ".join(value for value in [event.get("event_type"), event.get("organiser"), event.get("location")] if value))
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

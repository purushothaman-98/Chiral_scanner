from __future__ import annotations

import hashlib
import hmac
import html
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from chiral_scanner.github_dispatch import dispatch_metadata_scan
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
.block-container {padding-top: 1.5rem; max-width: 1500px;}
.hero {padding: 1.7rem 1.9rem; border: 1px solid rgba(139,92,246,.35); border-radius: 20px;
background: radial-gradient(circle at top right, rgba(139,92,246,.23), transparent 38%),
linear-gradient(135deg, rgba(17,24,39,.96), rgba(9,11,18,.96)); margin-bottom: 1rem;}
.hero h1 {margin: 0; font-size: 2.45rem; letter-spacing: -.04em;}
.hero p {max-width: 900px; color: #c4b5fd; font-size: 1.03rem; margin-bottom: 0;}
.paper-card {border: 1px solid rgba(255,255,255,.10); border-radius: 16px; padding: 1.1rem 1.2rem;
margin: .8rem 0; background: rgba(21,25,37,.72);}
.paper-card h3 {margin: 0 0 .25rem 0; font-size: 1.15rem;}
.meta {color: #a1a1aa; font-size: .88rem;}
.badge {display: inline-block; padding: .2rem .55rem; margin: .2rem .25rem .2rem 0;
border-radius: 999px; background: rgba(139,92,246,.16); border: 1px solid rgba(139,92,246,.35);
font-size: .78rem; color: #ddd6fe;}
.small-note {color: #a1a1aa; font-size: .85rem;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=120)
def load_all() -> tuple[dict, list[dict], list[dict], list[dict]]:
    archive = load_json(DATA / "papers.json", empty_archive())
    history = load_json(DATA / "scan_history.json", [])
    events = load_json(DATA / "events.json", [])
    tools = load_json(DATA / "tools.json", [])
    return archive, history, events, tools


def format_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y")
    except ValueError:
        return value


def badges(values: list[str]) -> str:
    return "".join(
        f'<span class="badge">{html.escape(str(value))}</span>' for value in values if value
    )


def paper_card(paper: dict) -> None:
    decision = paper.get("ai_decision") or {}
    title = html.escape(str(paper.get("title", "Untitled")))
    author_names = ", ".join(str(author) for author in paper.get("authors", [])[:8])
    if len(paper.get("authors", [])) > 8:
        author_names += " et al."
    authors = html.escape(author_names)
    abstract = str(paper.get("abstract", ""))
    preview_text = abstract if len(abstract) <= 700 else abstract[:697].rstrip() + "…"
    preview = html.escape(preview_text)
    versioned_id = html.escape(str(paper.get("versioned_arxiv_id", "")))
    methods = decision.get("experimental_methods", []) + decision.get("computational_methods", [])
    systems = decision.get("materials_or_systems", []) or paper.get(
        "detected_materials_or_systems", []
    )
    properties = decision.get("physical_properties", [])
    tags = [
        decision.get("relevance") or "Awaiting AI review",
        decision.get("research_type")
        or paper.get("preliminary_research_type", "Unclassified"),
        decision.get("paper_nature")
        or paper.get("preliminary_paper_nature", "Uncertain"),
    ]
    st.markdown(
        f"""
<div class="paper-card">
<h3>{title}</h3>
<div class="meta">{authors}</div>
<div class="meta">Submitted {format_date(paper.get('initial_submission_date'))} · Updated {format_date(paper.get('latest_update_date'))} · {versioned_id}</div>
<div>{badges(tags)}</div>
<p>{preview}</p>
<div>{badges(systems + methods + properties)}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    reason = decision.get("reason")
    if reason:
        st.caption(f"AI reason: {reason}")
    cols = st.columns([1, 1, 4])
    cols[0].link_button(
        "arXiv page", paper.get("abstract_url", "https://arxiv.org"), use_container_width=True
    )
    cols[1].link_button(
        "PDF", paper.get("pdf_url", "https://arxiv.org"), use_container_width=True
    )
    with cols[2]:
        st.caption("Categories: " + ", ".join(paper.get("categories", [])))


archive, history, events, tools = load_all()
papers = archive.get("papers", [])

st.markdown(
    """
<div class="hero">
<h1>Chiral Phonon Research Scanner</h1>
<p>Daily arXiv tracking for chiral phonons, phonon angular momentum, dynamical multiferroicity, phonomagnetism, nonlinear phononics, and spin–lattice angular-momentum transfer.</p>
</div>
""",
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metric_cols[0].metric("Archived papers", len(papers))
metric_cols[1].metric(
    "In research feed",
    sum(bool((p.get("ai_decision") or {}).get("include_in_feed")) for p in papers),
)
metric_cols[2].metric(
    "Experimental",
    sum((p.get("ai_decision") or {}).get("research_type") == "Experimental" for p in papers),
)
metric_cols[3].metric("Last archive update", format_date(archive.get("updated_at")))

paper_tab, trends_tab, events_tab, tools_tab, admin_tab = st.tabs(
    ["Papers", "Trends", "Opportunities", "Tools & sources", "Owner controls"]
)

with paper_tab:
    if not papers:
        st.info("The repository is initialized. Run the metadata workflow to build the first archive.")
    else:
        with st.sidebar:
            st.header("Paper filters")
            search = st.text_input("Search title, author or abstract")
            include_mode = st.selectbox(
                "Feed scope",
                ["Included + uncertain", "Included only", "All candidates"],
            )
            research_options = flatten_unique(papers, ("ai_decision", "research_type"))
            nature_options = flatten_unique(papers, ("ai_decision", "paper_nature"))
            system_options = flatten_unique(papers, ("ai_decision", "materials_or_systems"))
            exp_options = flatten_unique(papers, ("ai_decision", "experimental_methods"))
            comp_options = flatten_unique(papers, ("ai_decision", "computational_methods"))
            property_options = flatten_unique(papers, ("ai_decision", "physical_properties"))
            research_filter = st.multiselect("Research type", research_options)
            nature_filter = st.multiselect("Paper nature", nature_options)
            system_filter = st.multiselect("Material or system", system_options)
            method_filter = st.multiselect("Method", sorted(set(exp_options + comp_options)))
            property_filter = st.multiselect("Physical property", property_options)
            page_size = st.select_slider(
                "Papers per page", options=[10, 20, 40, 80], value=20
            )

        filtered: list[dict] = []
        needle = search.casefold().strip()
        for paper in papers:
            decision = paper.get("ai_decision") or {}
            include = decision.get("include_in_feed")
            relevance = decision.get("relevance")
            if include_mode == "Included only" and include is not True:
                continue
            if include_mode == "Included + uncertain" and not (
                include is True or relevance == "Uncertain" or decision == {}
            ):
                continue
            searchable = " ".join(
                [
                    paper.get("title", ""),
                    paper.get("abstract", ""),
                    " ".join(paper.get("authors", [])),
                ]
            ).casefold()
            if needle and needle not in searchable:
                continue
            if research_filter and decision.get("research_type") not in research_filter:
                continue
            if nature_filter and decision.get("paper_nature") not in nature_filter:
                continue
            if system_filter and not set(system_filter).intersection(
                decision.get("materials_or_systems", [])
            ):
                continue
            all_methods = decision.get("experimental_methods", []) + decision.get(
                "computational_methods", []
            )
            if method_filter and not set(method_filter).intersection(all_methods):
                continue
            if property_filter and not set(property_filter).intersection(
                decision.get("physical_properties", [])
            ):
                continue
            filtered.append(paper)

        filtered.sort(
            key=lambda item: item.get("latest_update_date")
            or item.get("initial_submission_date")
            or "",
            reverse=True,
        )
        st.subheader(f"Newest papers · {len(filtered)} matches")
        total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
        page = st.number_input(
            "Page", min_value=1, max_value=total_pages, value=1, step=1
        )
        page_items, total_pages, safe_page = paginate(filtered, int(page), page_size)
        st.caption(f"Page {safe_page} of {total_pages}")
        for paper in page_items:
            paper_card(paper)

with trends_tab:
    classified = [p for p in papers if p.get("ai_decision")]
    if not classified:
        st.info("Trend charts will appear after AI classification.")
    else:
        frame = pd.DataFrame(
            [
                {
                    "date": pd.to_datetime(p["initial_submission_date"], utc=True).date(),
                    "research_type": p["ai_decision"]["research_type"],
                    "relevance": p["ai_decision"]["relevance"],
                }
                for p in classified
            ]
        )
        frame["week"] = pd.to_datetime(frame["date"]).dt.to_period("W").dt.start_time
        left, right = st.columns(2)
        with left:
            st.subheader("Daily submissions")
            st.line_chart(frame.groupby("date").size().rename("papers"))
            st.subheader("Research type")
            st.bar_chart(frame["research_type"].value_counts())
        with right:
            st.subheader("Weekly submissions")
            st.line_chart(frame.groupby("week").size().rename("papers"))
            st.subheader("Relevance")
            st.bar_chart(frame["relevance"].value_counts())

        def distribution(field: str) -> pd.Series:
            values = [
                value
                for paper in classified
                for value in paper["ai_decision"].get(field, [])
            ]
            return pd.Series(values, dtype="object").value_counts().head(20)

        cols = st.columns(3)
        with cols[0]:
            st.subheader("Materials / systems")
            st.bar_chart(distribution("materials_or_systems"))
        with cols[1]:
            st.subheader("Methods")
            methods = (
                distribution("experimental_methods")
                .add(distribution("computational_methods"), fill_value=0)
                .sort_values(ascending=False)
                .head(20)
            )
            st.bar_chart(methods)
        with cols[2]:
            st.subheader("Physical properties")
            st.bar_chart(distribution("physical_properties"))

        st.subheader("Scan history")
        if history:
            history_frame = pd.DataFrame(history)
            history_frame["scan_timestamp"] = pd.to_datetime(
                history_frame["scan_timestamp"], utc=True
            )
            st.line_chart(
                history_frame.set_index("scan_timestamp")[
                    ["fetched", "newly_added", "updated"]
                ]
            )
        else:
            st.caption("No scan-history records yet.")

with events_tab:
    st.subheader("Conferences, workshops, schools and networks")
    st.caption(
        "Version 1 uses a curated official-source watchlist. Automated event scraping is intentionally excluded while arXiv remains the only automated literature source."
    )
    status_filter = st.multiselect(
        "Status",
        sorted({event.get("status", "watchlist") for event in events}),
        default=sorted({event.get("status", "watchlist") for event in events}),
    )
    for event in events:
        if event.get("status", "watchlist") not in status_filter:
            continue
        with st.container(border=True):
            st.markdown(f"### {event['title']}")
            st.write(event.get("description", ""))
            meta = [event.get("event_type"), event.get("organiser"), event.get("location")]
            st.caption(" · ".join(value for value in meta if value))
            if event.get("start_date"):
                st.write(
                    f"**Dates:** {event.get('start_date')} to "
                    f"{event.get('end_date') or event.get('start_date')}"
                )
            if event.get("deadline"):
                st.write(f"**Deadline:** {event['deadline']}")
            st.link_button("Official source", event["url"])

with tools_tab:
    st.subheader("Research tools and official source directories")
    for item in tools:
        with st.container(border=True):
            st.markdown(f"### {item['name']}")
            st.write(item.get("description", ""))
            st.caption(" · ".join(item.get("tags", [])))
            st.link_button("Open resource", item["url"])

with admin_tab:
    st.subheader("Owner-only live scan")
    required = ["github_token", "admin_passcode"]
    if not all(key in st.secrets for key in required):
        st.info(
            "Add `github_token` and `admin_passcode` in Streamlit Secrets to enable secure manual dispatch. The token must permit Actions: write on this repository."
        )
    else:
        passcode = st.text_input("Admin passcode", type="password")
        since_date = st.date_input("Optional since date", value=date.today())
        expected_hash = hashlib.sha256(str(st.secrets["admin_passcode"]).encode()).digest()
        supplied_hash = hashlib.sha256(passcode.encode()).digest()
        authenticated = bool(passcode) and hmac.compare_digest(expected_hash, supplied_hash)
        if st.button("Run metadata scan now", type="primary", disabled=not authenticated):
            repo = st.secrets.get("github_repo", "purushothaman-98/Chiral_scanner")
            run_url = dispatch_metadata_scan(
                repo=repo,
                token=st.secrets["github_token"],
                since=since_date.isoformat(),
            )
            st.success(
                "Metadata workflow dispatched. AI review starts automatically after it succeeds."
            )
            if run_url:
                st.link_button("Monitor GitHub Actions run", run_url)

st.divider()
st.caption(
    "Independent research tool using the official arXiv API. Not affiliated with or endorsed by arXiv. "
    f"Page generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}."
)

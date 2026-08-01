#!/usr/bin/env python3
"""Apply the light, task-first research-intelligence interface to app.py."""

from __future__ import annotations

from pathlib import Path

APP_PATH = Path("app.py")
DOC_PATH = Path("docs/RESEARCH_PORTAL_UX.md")


def replace_section(text: str, start: str, end: str, replacement: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        raise SystemExit(f"Start marker not found: {start[:80]!r}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise SystemExit(f"End marker not found: {end[:80]!r}")
    return text[:start_index] + replacement + text[end_index:]


text = APP_PATH.read_text(encoding="utf-8")

css_start = 'st.markdown(\n    """\n<style>\n'
css_end = '</style>\n""",\n    unsafe_allow_html=True,\n)\n'
css_block = '''st.markdown(
    """
<style>
:root {
  --accent:#2563eb;
  --accent-strong:#1d4ed8;
  --teal:#0f766e;
  --ink:#172033;
  --muted:#5f6b7a;
  --surface:#ffffff;
  --soft:#f3f6fa;
  --line:#dbe3ec;
  --success:#047857;
  --warning:#a16207;
  --danger:#be123c;
}
html {color-scheme:light;}
.block-container {padding-top:1.25rem; padding-bottom:3rem; max-width:1180px;}
.stApp {background:#f7f9fc; color:var(--ink);}
header[data-testid="stHeader"] {background:rgba(247,249,252,.94);}
.hero {padding:1.15rem 0 1rem; border-bottom:1px solid var(--line); margin-bottom:1rem;}
.hero-kicker {display:flex; align-items:center; gap:.45rem; color:var(--accent); font-size:.72rem;
font-weight:760; letter-spacing:.09em; text-transform:uppercase; margin-bottom:.45rem;}
.live-dot {width:.46rem; height:.46rem; border-radius:999px; background:#10b981;
box-shadow:0 0 0 4px rgba(16,185,129,.12); display:inline-block;}
.hero h1 {margin:0; color:var(--ink); font-size:2.15rem; letter-spacing:-.045em; line-height:1.08;}
.hero p {max-width:820px; color:var(--muted); font-size:.98rem; line-height:1.58; margin:.55rem 0 .7rem;}
.hero-tags {display:flex; flex-wrap:wrap; gap:.4rem;}
.hero-tag {padding:.24rem .58rem; border:1px solid #cbd9ea; border-radius:999px;
color:#29415f; background:#fff; font-size:.72rem;}
.coverage {display:flex; flex-wrap:wrap; gap:.4rem 1rem; padding:.62rem .78rem;
border-radius:10px; background:#fff; border:1px solid var(--line); color:var(--muted);
font-size:.79rem; margin:.45rem 0 1rem; box-shadow:0 1px 2px rgba(15,23,42,.03);}
.coverage strong {color:var(--ink); font-weight:680;}
.section-kicker {color:var(--accent); font-size:.69rem; font-weight:760; letter-spacing:.09em;
text-transform:uppercase; margin-bottom:.18rem;}
.section-intro {color:var(--muted); max-width:850px; font-size:.89rem; line-height:1.56;
margin-top:-.25rem; margin-bottom:.9rem;}
.material-strip {padding:.62rem .76rem; border:1px solid var(--line); border-radius:9px;
background:#fff; color:#435166; font-size:.82rem; margin:.45rem 0 .75rem;}
.date-row {display:flex; align-items:center; gap:.7rem; margin:1.15rem 0 .28rem;}
.date-row h2 {font-size:1.05rem; color:var(--ink); margin:0;}
.count-pill {font-size:.7rem; color:#1d4ed8; padding:.13rem .44rem; border-radius:999px;
background:#eff6ff; border:1px solid #bfdbfe;}
.paper-title {font-size:1.03rem; font-weight:735; line-height:1.42; margin-bottom:.18rem;}
.paper-title a {color:#123b70; text-decoration:none;}
.paper-title a:hover {color:var(--accent); text-decoration:underline; text-underline-offset:3px;}
.meta {color:#667386; font-size:.77rem; margin:.18rem 0 .34rem;}
.badge {display:inline-block; padding:.16rem .43rem; margin:.08rem .14rem .08rem 0;
border-radius:999px; background:#f1f5f9; border:1px solid #d7e0ea; font-size:.67rem; color:#334155;}
.status-approved {background:#ecfdf5; border-color:#a7f3d0; color:#047857;}
.status-pending {background:#fffbeb; border-color:#fde68a; color:#92400e;}
.status-review {background:#fff1f2; border-color:#fecdd3; color:#be123c;}
.paper-signal {border-left:3px solid #60a5fa; padding:.42rem .68rem; margin:.48rem 0 .34rem;
color:#334155; font-size:.82rem; line-height:1.48; background:#f4f8ff;}
.brief {padding:.82rem .95rem; border:1px solid #cfe0f5; border-radius:10px;
background:#f8fbff; color:#334155; line-height:1.55; margin:.65rem 0 1rem;}
.brief strong {color:var(--ink);}
.journey-card {height:100%; padding:.88rem .95rem; border:1px solid var(--line); border-radius:10px;
background:#fff;}
.journey-card .number {color:var(--accent); font-size:.71rem; font-weight:760; letter-spacing:.07em;
text-transform:uppercase;}
.journey-card h3 {color:var(--ink); font-size:1rem; margin:.25rem 0;}
.journey-card p {color:var(--muted); font-size:.82rem; line-height:1.48; margin:0;}
.insight-row {padding:.68rem .78rem; margin:.38rem 0; border-left:3px solid var(--accent);
border-radius:0 8px 8px 0; background:#fff; color:#334155; font-size:.85rem;
box-shadow:0 1px 2px rgba(15,23,42,.03);}
.abstract {color:#465468; line-height:1.5; margin:.4rem 0; font-size:.86rem;}
div[data-testid="stMetric"] {padding:.7rem .8rem; background:#fff; border:1px solid var(--line);
border-radius:10px; min-height:86px; box-shadow:0 1px 2px rgba(15,23,42,.035);}
div[data-testid="stMetricLabel"] {font-size:.75rem; color:#68758a;}
div[data-testid="stMetricValue"] {font-size:1.52rem; color:var(--ink);}
div[data-baseweb="tab-list"] {gap:.16rem; padding:0; border-bottom:1px solid var(--line);
background:transparent; overflow-x:auto;}
button[data-baseweb="tab"] {border-radius:8px 8px 0 0; padding:.48rem .7rem; color:#526176;}
button[data-baseweb="tab"][aria-selected="true"] {color:var(--accent-strong); background:#eef5ff;}
button[data-baseweb="tab"]:focus-visible, .stButton > button:focus-visible,
.stLinkButton > a:focus-visible {outline:3px solid rgba(37,99,235,.38); outline-offset:2px;}
div[data-testid="stExpander"] {border-color:var(--line); border-radius:9px; background:#fff;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:var(--line); border-radius:10px; background:#fff;}
.stButton > button, .stLinkButton > a {border-radius:8px;}
.stLinkButton > a {text-decoration:none;}
[data-testid="stDataFrame"] {border:1px solid var(--line); border-radius:9px; overflow:hidden;}
hr {border-color:var(--line);}
@media (max-width:700px) {
  .block-container {padding:.75rem .72rem 2rem;}
  .hero {padding:.8rem 0 .75rem;}
  .hero h1 {font-size:1.72rem;}
  .hero p {font-size:.88rem;}
  .coverage {display:block; line-height:1.7;}
  div[data-testid="stMetric"] {min-height:78px; padding:.54rem .58rem;}
  button[data-baseweb="tab"] {padding:.4rem .52rem; font-size:.77rem;}
}
</style>
""",
    unsafe_allow_html=True,
)
'''
text = replace_section(text, css_start, css_end, css_block)

paper_start = 'def paper_card(paper: dict) -> None:\n'
paper_end = '\n\narchive, history, events, tools = load_all()'
paper_block = '''def paper_card(paper: dict) -> None:
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
'''
text = replace_section(text, paper_start, paper_end, paper_block)

hero_start = 'st.markdown(\n    """\n<div class="hero">'
hero_end = '\n\nmetrics = st.columns(4)'
hero_block = '''st.markdown(
    f"""
<div class="hero">
<div class="hero-kicker"><span class="live-dot"></span> Evidence-first field intelligence · updated daily</div>
<h1>Chiral phonon research intelligence</h1>
<p>Track new papers, evidence maturity, materials, methods, institutions and unresolved questions
without mixing observation, interpretation and prediction.</p>
<div class="hero-tags">
<span class="hero-tag">{len(approved)} mapped papers</span>
<span class="hero-tag">{brief['direct']} direct measurements</span>
<span class="hero-tag">{len(thz_frontier)} THz-connected studies</span>
<span class="hero-tag">Global affiliation map</span>
</div>
</div>
""",
    unsafe_allow_html=True,
)
'''
text = replace_section(text, hero_start, hero_end, hero_block)

tabs_start = '(\n    overview_tab,\n    history_tab,\n'
tabs_end = '\n\nwith overview_tab:'
tabs_block = '''(
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
'''
text = replace_section(text, tabs_start, tabs_end, tabs_block)

overview_start = 'with overview_tab:\n'
overview_end = '\nwith history_tab:\n'
overview_block = '''with overview_tab:
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
        st.markdown("### Current field signals")
        st.markdown(
            f'<div class="insight-row"><strong>{brief["recent"]} mapped papers</strong> entered '
            "the latest 30-day research window.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="insight-row"><strong>{brief["experimental"]} experimental records</strong> '
            f"are currently balanced against {evidence_gap} theory, prediction or non-direct records.</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="insight-row"><strong>{brief["needs_interpretation"]} records</strong> remain '
            "visible but are not promoted as established evidence.</div>",
            unsafe_allow_html=True,
        )

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
'''
text = replace_section(text, overview_start, overview_end, overview_block)

replacements = {
    '"color": "rgba(103,232,249,.55)"': '"color": "rgba(37,99,235,.34)"',
    '[0.0, "#fde68a"]': '[0.0, "#dbeafe"]',
    '[0.4, "#fb923c"]': '[0.4, "#93c5fd"]',
    '[0.72, "#a78bfa"]': '[0.72, "#3b82f6"]',
    '[1.0, "#22d3ee"]': '[1.0, "#0f766e"]',
    'landcolor="#243248"': 'landcolor="#e8eef5"',
    'oceancolor="#071525"': 'oceancolor="#f8fbff"',
    'lakecolor="#0b2035"': 'lakecolor="#edf5fb"',
    'countrycolor="#64748b"': 'countrycolor="#a7b4c2"',
    'coastlinecolor="#94a3b8"': 'coastlinecolor="#8190a5"',
    'font={"color": "#e2e8f0"}': 'font={"color": "#172033"}',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"Expected map style marker not found: {old}")
    text = text.replace(old, new)

APP_PATH.write_text(text, encoding="utf-8")

DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
DOC_PATH.write_text(
    """# Research portal UX direction\n\n"
    "The interface follows four principles used by mature research-discovery and research-"
    "intelligence products:\n\n"
    "1. **Task-first navigation:** briefing, discovery, evidence, trends, community, opportunities, "
    "and operational detail are separated.\n"
    "2. **Progressive disclosure:** paper abstracts, classification details, methods and caveats "
    "stay available but do not dominate the scan view.\n"
    "3. **Decision-ready summaries:** the opening screen emphasizes what changed, evidence maturity, "
    "research gaps and the latest mapped papers.\n"
    "4. **Accessible light presentation:** high-contrast text, restrained color, visible focus states, "
    "light maps and reduced decorative chrome.\n\n"
    "Reference patterns reviewed:\n\n"
    "- Nielsen Norman Group guidance on succinct web writing, list-entry density and progressive disclosure.\n"
    "- W3C WCAG 2.2 guidance for readable contrast, focus visibility and non-text contrast.\n"
    "- Semantic Scholar and Litmaps patterns for alerts, feeds and scan-friendly discovery.\n"
    "- ResearchRabbit patterns for iterative exploration and collections.\n"
    "- Dimensions patterns for research intelligence, trend analysis and R&D decision support.\n\n"
    "This change is presentation-only. Collection, classification, enrichment, validation, scheduling "
    "and repository data formats remain unchanged.\n",
    encoding="utf-8",
)

print("Applied light research-intelligence UI")

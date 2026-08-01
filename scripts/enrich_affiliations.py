#!/usr/bin/env python3
"""Run enrichment and apply the one-off compact geography interface refinement."""

from __future__ import annotations

import subprocess
from pathlib import Path

from chiral_scanner.affiliation_enrichment_resilient import main

ORIGINAL_LAUNCHER = '''#!/usr/bin/env python3
"""Run the resilient non-AI paper-affiliation enrichment pipeline."""

from chiral_scanner.affiliation_enrichment_resilient import main

if __name__ == "__main__":
    main()
'''


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        capture_output=True,
    )


def apply_compact_geography() -> bool:
    app_path = Path("app.py")
    text = app_path.read_text(encoding="utf-8")
    changed = False

    old_caption = '''    st.caption(
        f"Registry checked {geo_coverage.get('registry_updated') or 'date unavailable'} · "
        f"{int(geo_coverage.get('uncovered_papers', 0) or 0)} papers remain explicitly unresolved."
    )
'''
    new_caption = '''    registry_timestamp = geo_coverage.get("registry_updated")
    registry_label = short_date(str(registry_timestamp)) if registry_timestamp else "date unavailable"
    st.caption(
        f"Affiliations updated {registry_label} · "
        f"{int(geo_coverage.get('uncovered_papers', 0) or 0)} papers remain unresolved."
    )
'''
    if old_caption in text:
        text = text.replace(old_caption, new_caption, 1)
        changed = True

    if '["Map", "Countries", "Institutions"]' not in text:
        start_marker = "    if active_institutions and go is not None:\n"
        end_marker = '    if int(geo_coverage.get("uncovered_papers", 0) or 0):\n'
        start = text.find(start_marker)
        end = text.find(end_marker, start)
        if start < 0 or end < 0:
            raise RuntimeError("Could not locate the existing geography-rendering block")

        replacement = '''    if active_institutions:
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

            if not visible_institutions:
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
                                    "color": "rgba(103,232,249,.55)",
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

                map_figure.add_trace(
                    go.Scattergeo(
                        lon=[item["longitude"] for item in visible_institutions],
                        lat=[item["latitude"] for item in visible_institutions],
                        mode="markers",
                        marker={
                            "size": [
                                9 + 5 * min(item["paper_count"] ** 0.5, 3.5)
                                for item in visible_institutions
                            ],
                            "color": [item["paper_count"] for item in visible_institutions],
                            "colorscale": [
                                [0.0, "#fde68a"],
                                [0.4, "#fb923c"],
                                [0.72, "#a78bfa"],
                                [1.0, "#22d3ee"],
                            ],
                            "line": {"color": "#f8fafc", "width": 0.9},
                            "opacity": 0.88,
                            "colorbar": {"title": "Papers", "thickness": 10},
                            "cmin": 1,
                        },
                        customdata=[
                            [
                                item["institution"],
                                ", ".join(
                                    value
                                    for value in [item.get("city"), item.get("country")]
                                    if value
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
                            for item in visible_institutions
                        ],
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                            "Mapped papers: %{customdata[2]}<br>"
                            "Verified authors: %{customdata[3]}<br>"
                            "Leading authors: %{customdata[4]}<br>"
                            "Active years: %{customdata[5]}<extra></extra>"
                        ),
                        showlegend=False,
                    )
                )
                map_figure.update_geos(
                    projection_type=projection,
                    showland=True,
                    landcolor="#243248",
                    showocean=True,
                    oceancolor="#071525",
                    showlakes=True,
                    lakecolor="#0b2035",
                    showcountries=True,
                    countrycolor="#64748b",
                    coastlinecolor="#94a3b8",
                    coastlinewidth=0.7,
                    bgcolor="rgba(0,0,0,0)",
                )
                map_figure.update_layout(
                    height=500,
                    margin={"l": 0, "r": 0, "t": 4, "b": 0},
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#e2e8f0"},
                )
                st.plotly_chart(
                    map_figure,
                    use_container_width=True,
                    config={"displaylogo": False, "scrollZoom": False},
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

'''
        text = text[:start] + replacement + text[end:]
        changed = True

    compile(text, "app.py", "exec")
    if changed:
        app_path.write_text(text, encoding="utf-8")
    return changed


def clean_temporary_files() -> bool:
    changed = False
    for filename in [
        ".github/ui-refine-trigger",
        ".github/workflows/compact-geography-ui.yml",
        ".github/workflows/dispatch-compact-geography-ui.yml",
    ]:
        candidate = Path(filename)
        if candidate.exists():
            candidate.unlink()
            changed = True
    launcher = Path(__file__)
    if launcher.read_text(encoding="utf-8") != ORIGINAL_LAUNCHER:
        launcher.write_text(ORIGINAL_LAUNCHER, encoding="utf-8")
        changed = True
    return changed


def commit_refinement() -> None:
    run_git("config", "user.name", "github-actions[bot]")
    run_git(
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    run_git("add", "-A", "--", "app.py", "scripts/enrich_affiliations.py", ".github")
    staged = run_git("diff", "--cached", "--quiet", check=False)
    if staged.returncode == 0:
        return
    run_git(
        "commit",
        "-m",
        "Make research geography focused and explorable [skip ci]",
    )
    pushed = run_git("push", "origin", "HEAD:main", check=False)
    if pushed.returncode != 0:
        run_git("pull", "--rebase", "origin", "main")
        run_git("push", "origin", "HEAD:main")


if __name__ == "__main__":
    ui_changed = apply_compact_geography()
    cleanup_changed = clean_temporary_files()
    if ui_changed or cleanup_changed:
        commit_refinement()
    main()

import importlib

from streamlit.testing.v1 import AppTest

import chiral_scanner.research_intelligence as intelligence_data


def test_all_dashboard_tabs_render_without_an_exception():
    app = AppTest.from_file("app.py", default_timeout=15).run(timeout=15)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Research evolution",
        "Daily scan",
        "Field analysis",
        "News & breakthroughs",
        "Projects & opportunities",
        "Operations",
    ]


def test_legacy_industry_record_does_not_break_later_tabs(monkeypatch):
    monkeypatch.setattr(
        intelligence_data,
        "INDUSTRY_SIGNALS",
        [
            {
                "name": "No verified dedicated chiral-phonon company yet",
                "signal": "Emerging research, not a mature commercial category",
                "detail": "Track adjacent enabling technologies without making an investment claim.",
            }
        ],
    )
    monkeypatch.setattr(importlib, "reload", lambda module: module)

    app = AppTest.from_file("app.py", default_timeout=15).run(timeout=15)

    assert not app.exception

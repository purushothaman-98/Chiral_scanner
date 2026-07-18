from streamlit.testing.v1 import AppTest


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

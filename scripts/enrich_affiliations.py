#!/usr/bin/env python3
"""Apply the verified UI migration once, then run normal affiliation enrichment."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "apply_research_intelligence_ui.py"
WORKFLOW = ROOT / ".github" / "workflows" / "light-research-intelligence-ui.yml"
LOG = Path("/tmp/chiral-streamlit-ui-smoke.log")

ORIGINAL_LAUNCHER = '''#!/usr/bin/env python3
"""Run the resilient non-AI paper-affiliation enrichment pipeline."""

from chiral_scanner.affiliation_enrichment_resilient import main

if __name__ == "__main__":
    main()
'''

FINAL_THEME = '''[theme]
base = "light"
primaryColor = "#2563EB"
backgroundColor = "#F7F9FC"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#172033"
font = "sans serif"

[server]
headless = true
'''

UX_NOTE = '''# Research portal UX direction

The interface follows four principles used by mature research-discovery and research-intelligence products:

1. **Task-first navigation:** briefing, discovery, evidence, trends, community, opportunities, and operational detail are separated.
2. **Progressive disclosure:** paper abstracts, classification details, methods and caveats stay available but do not dominate the scan view.
3. **Decision-ready summaries:** the opening screen emphasizes what changed, evidence maturity, research gaps and the latest mapped papers.
4. **Accessible light presentation:** high-contrast text, restrained color, visible focus states, light maps and reduced decorative chrome.

Reference patterns reviewed:

- Nielsen Norman Group guidance on succinct web writing, list-entry density and progressive disclosure.
- W3C WCAG 2.2 guidance for readable contrast, focus visibility and non-text contrast.
- Semantic Scholar and Litmaps patterns for alerts, feeds and scan-friendly discovery.
- ResearchRabbit patterns for iterative exploration and collections.
- Dimensions patterns for research intelligence, trend analysis and R&D decision support.

This change is presentation-only. Collection, classification, enrichment, validation, scheduling and repository data formats remain unchanged.
'''


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def repair_patch_source() -> None:
    """Replace the malformed temporary UX-note writer before executing the migration."""
    source = PATCH.read_text(encoding="utf-8")
    start = source.find("DOC_PATH.write_text(")
    end = source.find('\n\nprint("Applied light research-intelligence UI")', start)
    if start < 0 or end < 0:
        raise RuntimeError("Unable to locate the temporary UX-note writer")
    replacement = (
        "DOC_PATH.write_text(UX_NOTE, encoding=\"utf-8\")"
        if "UX_NOTE =" in source
        else "DOC_PATH.write_text(" + repr(UX_NOTE) + ", encoding=\"utf-8\")"
    )
    PATCH.write_text(source[:start] + replacement + source[end:], encoding="utf-8")


def smoke_test() -> None:
    with LOG.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.headless",
                "true",
                "--server.port",
                "8501",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=ROOT,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    try:
        for _ in range(40):
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:8501/_stcore/health", timeout=2
                ) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(1)
        raise RuntimeError(LOG.read_text(encoding="utf-8", errors="replace"))
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def apply_ui_once() -> None:
    if not PATCH.exists():
        return

    repair_patch_source()
    run(sys.executable, str(PATCH))
    (ROOT / ".streamlit" / "config.toml").write_text(FINAL_THEME, encoding="utf-8")

    run(sys.executable, "-m", "py_compile", "app.py")
    run(sys.executable, "-m", "pytest", "-q")
    run(sys.executable, "scripts/validate_data.py")
    smoke_test()

    Path(__file__).write_text(ORIGINAL_LAUNCHER, encoding="utf-8")
    PATCH.unlink(missing_ok=True)
    WORKFLOW.unlink(missing_ok=True)

    run("git", "config", "user.name", "github-actions[bot]")
    run(
        "git",
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    run(
        "git",
        "add",
        "-A",
        "--",
        "app.py",
        ".streamlit/config.toml",
        "docs/RESEARCH_PORTAL_UX.md",
        "scripts/apply_research_intelligence_ui.py",
        "scripts/enrich_affiliations.py",
        ".github/workflows/light-research-intelligence-ui.yml",
    )
    run(
        "git",
        "commit",
        "-m",
        "Redesign tracker as a light research intelligence portal [skip ci]",
    )
    run("git", "push", "origin", "HEAD:main")


if __name__ == "__main__":
    apply_ui_once()
    from chiral_scanner.affiliation_enrichment_resilient import main

    main()

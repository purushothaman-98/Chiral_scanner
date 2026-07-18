# Chiral Phonon Research Scanner

A topic-specific Streamlit research scanner for **chiral phonons and angular-momentum phononics**. It follows the official arXiv API daily, preserves paper-version history, applies transparent preliminary rules, and runs a cached GitHub Models abstract review.

## Scientific scope

The scanner covers:

- direct chiral phonons and phonon chirality/helicity;
- phonon angular and pseudo-angular momentum;
- dynamical multiferroicity and phonomagnetism;
- phonon inverse-Faraday, Barnett, Zeeman, Faraday and Einstein–de Haas effects;
- nonlinear/helical phononics and phonon–phonon angular-momentum transfer;
- spin–phonon and magnon–phonon angular-momentum coupling;
- topological phonons, thermal Hall effects and chiral phonon polaritons;
- experimental THz, Raman, RIXS, diffraction, Kerr/Faraday and transport studies.

The detailed topic taxonomy is retained in `topic_research_notes.md` and implemented in `src/chiral_scanner/config.py`.

## Architecture

- `scripts/scan_arxiv.py`: official arXiv Atom API ingestion with overlapping windows or safe yearly initialization batches.
- `src/chiral_scanner/preliminary.py`: transparent title-and-abstract extraction using author-action language.
- `scripts/classify_ai.py`: GitHub Models structured abstract classification, cached by paper/version/content/prompt fingerprint.
- `scripts/merge_scan.py` and `scripts/merge_ai.py`: stable-ID merges that preserve old records and prevent blind JSON replacement.
- `app.py`: Streamlit feed, archive, filters, distributions, scan history, opportunities, tools and owner dispatch.
- `.github/workflows/`: daily metadata scan, automatic follow-on AI review, and Python 3.12 tests.

## Daily schedule

The metadata workflow runs at **04:00 UTC every day** and queries an overlapping **14-day submitted-or-updated window**, so delayed records and new versions are revisited. Manual workflow dispatch accepts bounded `since` and `until` dates. AI classification starts as a separate workflow after a successful metadata scan.

## First archive build

The default initial date is **2017-01-01**. From GitHub Actions, run **Scan arXiv metadata**, enable `initial`, and leave `since` empty. The script queries safe yearly batches and respects a delay between arXiv API pages.

For a smaller first build, provide a later `since` date and keep `initial` disabled.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=src streamlit run app.py
```

Run checks:

```bash
ruff check .
pytest -q
PYTHONPATH=src python scripts/validate_data.py
```

## Streamlit Community Cloud deployment

1. Connect Streamlit Community Cloud to GitHub.
2. Create an app from `purushothaman-98/Chiral_scanner`.
3. Use branch `main` and entrypoint `app.py`.
4. Add the optional owner-control secrets below.

```toml
admin_passcode = "choose-a-long-unique-passcode"
github_token = "fine-grained-token-with-actions-write"
github_repo = "purushothaman-98/Chiral_scanner"
```

The GitHub token stays server-side in Streamlit Secrets. It is never committed or returned to the browser. The manual control dispatches `metadata-scan.yml`; the separate AI workflow follows automatically.

## GitHub Models

The AI workflow uses the repository `GITHUB_TOKEN` with `models: read`. Enable GitHub Models for the repository if required. The default model is `openai/gpt-4.1-mini`; override it with the repository variable `GITHUB_MODELS_MODEL`.

## Data files

- `data/papers.json`: permanent deduplicated archive.
- `data/scan_history.json`: per-run counts and query windows.
- `data/events.json`: curated official conference/network watchlist.
- `data/tools.json`: research tools and official directories.

Ordinary scans never delete older papers. A new arXiv version updates the existing base-ID record and adds the new version to `versions_seen`.

## First-version boundaries

This version intentionally excludes PDF chat, accounts, comments, citation networks, automatic PDF summarization and embeddings. Automated literature ingestion uses only the official arXiv API. The opportunities page is a curated official-source watchlist rather than an event scraper.

## Attribution

This is an independent research tool using arXiv data. It is not affiliated with or endorsed by arXiv.

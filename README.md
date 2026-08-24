# Chiral Phonon Research Scanner

A topic-specific Streamlit research scanner for **chiral phonons and angular-momentum phononics**. It follows the official arXiv API daily, preserves paper-version history, applies transparent preliminary rules, and runs a cached Anthropic-powered abstract review.

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
- `scripts/classify_ai.py`: Anthropic Messages API structured abstract classification (forced tool-use), cached by paper/version/content/prompt fingerprint.
- `scripts/merge_scan.py` and `scripts/merge_ai.py`: stable-ID merges that preserve old records and prevent blind JSON replacement.
- `app.py`: Streamlit feed, archive, filters, distributions, scan history, opportunities, tools and owner dispatch.
- `.github/workflows/`: daily metadata scan, automatic follow-on AI review, and Python 3.12 tests.

## Daily schedule

The metadata workflow runs at **04:00 UTC every day** and queries an overlapping **14-day submitted-or-updated window**, so delayed records and new versions are revisited. Manual workflow dispatch accepts bounded `since` and `until` dates. AI classification starts as a separate workflow after a successful metadata scan.

The pipeline also uses a rate-safe 24-hour work cycle:

- AI review runs every four hours at `00:40`, `04:40`, `08:40`, `12:40`, `16:40` and `20:40` UTC, with at most 20 eligible abstracts per run.
- Historical collection runs at `02:10`, `08:10`, `14:10` and `20:10` UTC. Each run scans one checkpointed 30-day window backwards from 1 June 2026 toward 1 January 2017.
- Daily scans, historical scans and AI commits share the `chiral-archive-writes` concurrency group with cancellation disabled. They queue instead of modifying the archive simultaneously.
- Obvious rule-excluded candidates remain searchable but do not consume Anthropic API requests. Failed individual AI reviews are deferred for a later scheduled run without discarding successful decisions from the same batch.

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

## AI classification provider

GitHub Models (the previous provider) was fully retired on 2026-07-30 and has no successor
endpoint, so classification now runs on the **Anthropic Messages API**. This requires one
repository secret that GitHub Models never needed, since it used to run for free on the
repo's own `GITHUB_TOKEN`:

1. In the repo, go to **Settings → Secrets and variables → Actions → New repository secret**.
2. Add `ANTHROPIC_API_KEY` with a key from <https://console.anthropic.com/>.

The default model is `claude-haiku-4-5-20251001`; override it with the repository variable
`ANTHROPIC_MODEL`. Without the secret, `scripts/classify_ai.py` now exits non-zero and the
**AI classify arXiv papers** workflow fails loudly (a red run) instead of silently deferring
every paper the way it did against the retired GitHub Models endpoint.

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

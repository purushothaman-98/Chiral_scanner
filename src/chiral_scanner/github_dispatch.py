from __future__ import annotations

import time
from datetime import datetime, timezone

import requests


def dispatch_metadata_scan(
    *,
    repo: str,
    token: str,
    since: str | None = None,
    workflow: str = "metadata-scan.yml",
    ref: str = "main",
) -> str | None:
    api = f"https://api.github.com/repos/{repo}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    requested_at = datetime.now(timezone.utc)
    inputs = {}
    if since:
        inputs["since"] = since
    response = requests.post(
        f"{api}/actions/workflows/{workflow}/dispatches",
        headers=headers,
        json={"ref": ref, "inputs": inputs},
        timeout=30,
    )
    response.raise_for_status()

    # Dispatch returns 204 without a run ID. Resolve the newest matching manual run.
    for _ in range(5):
        time.sleep(2)
        runs = requests.get(
            f"{api}/actions/workflows/{workflow}/runs",
            headers=headers,
            params={"event": "workflow_dispatch", "per_page": 5},
            timeout=30,
        )
        runs.raise_for_status()
        for run in runs.json().get("workflow_runs", []):
            created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            if created >= requested_at:
                return run.get("html_url")
    return f"https://github.com/{repo}/actions/workflows/{workflow}"

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone

from chiral_scanner.storage import atomic_write_json, load_json


def next_window(state: dict) -> tuple[date, date] | None:
    target = date.fromisoformat(state["target_date"])
    until = date.fromisoformat(state["next_until"])
    if state.get("completed") or until <= target:
        return None
    since = max(target, until - timedelta(days=int(state.get("window_days", 30))))
    return since, until


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="data/backfill_state.json")
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--advance", action="store_true")
    args = parser.parse_args()

    state = load_json(args.state, {})
    window = next_window(state)
    if args.emit:
        payload = {"completed": window is None}
        if window:
            payload.update({"since": window[0].isoformat(), "until": window[1].isoformat()})
        print(json.dumps(payload))
        return
    if args.advance:
        if window:
            state["next_until"] = window[0].isoformat()
            state["windows_completed"] = int(state.get("windows_completed", 0)) + 1
            state["last_run_at"] = datetime.now(timezone.utc).isoformat()
            state["completed"] = window[0] <= date.fromisoformat(state["target_date"])
            atomic_write_json(args.state, state)
        return
    parser.error("choose --emit or --advance")


if __name__ == "__main__":
    main()

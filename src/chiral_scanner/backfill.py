from __future__ import annotations

from datetime import date, timedelta


def next_window(state: dict) -> tuple[date, date] | None:
    target = date.fromisoformat(state["target_date"])
    until = date.fromisoformat(state["next_until"])
    if state.get("completed") or until <= target:
        return None
    since = max(target, until - timedelta(days=int(state.get("window_days", 30))))
    return since, until

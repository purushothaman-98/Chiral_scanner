from datetime import date

from chiral_scanner.backfill import next_window


def test_backfill_moves_back_one_bounded_window() -> None:
    assert next_window(
        {
            "target_date": "2017-01-01",
            "next_until": "2026-06-01",
            "window_days": 30,
            "completed": False,
        }
    ) == (date(2026, 5, 2), date(2026, 6, 1))


def test_backfill_clamps_to_target() -> None:
    assert next_window(
        {
            "target_date": "2017-01-01",
            "next_until": "2017-01-12",
            "window_days": 30,
            "completed": False,
        }
    ) == (date(2017, 1, 1), date(2017, 1, 12))


def test_completed_backfill_makes_no_query_window() -> None:
    assert next_window(
        {
            "target_date": "2017-01-01",
            "next_until": "2017-01-01",
            "window_days": 30,
            "completed": True,
        }
    ) is None

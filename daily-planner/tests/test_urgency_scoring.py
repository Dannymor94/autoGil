"""Tests for urgency_scoring — RED→GREEN per SPEC."""

import pytest
from src.urgency_scoring import DEFAULT_CONFIG, score_task
from src.yougile_client import Deadline, Task

MS = 86_400_000  # ms per day

# Fixed "now" for all tests: 2026-06-30 00:00 UTC
NOW_MS = 1782777600000  # 2026-06-30 00:00 UTC


def _task(
    id: str = "t",
    created_days_ago: float = 0,
    deadline_days: float | None = None,
) -> Task:
    created_at = NOW_MS - int(created_days_ago * MS)
    deadline = None
    if deadline_days is not None:
        dl_ms = NOW_MS + int(deadline_days * MS)
        deadline = Deadline(deadline_ms=dl_ms, start_date_ms=None, with_time=False)
    return Task(
        id=id, title=id, project_id="p", board_id="b",
        column_id="c", created_at_ms=created_at,
        deadline=deadline, plan_hours=None, completed=False,
    )


# ---------------------------------------------------------------------------
# Overdue
# ---------------------------------------------------------------------------

def test_overdue_score_is_high_and_on_fire():
    t = _task(created_days_ago=5, deadline_days=-1)  # expired yesterday
    s = score_task(t, NOW_MS)
    assert s.is_overdue is True
    assert s.on_fire is True
    assert s.deadline_score == 1.0
    assert s.score > 0.5


# ---------------------------------------------------------------------------
# Fresh task without deadline
# ---------------------------------------------------------------------------

def test_fresh_no_deadline_low_score():
    t = _task(created_days_ago=0)
    s = score_task(t, NOW_MS)
    assert s.deadline_score == 0.0
    assert s.age_score == 0.0
    assert s.score == 0.0
    assert s.on_fire is False


# ---------------------------------------------------------------------------
# Old task without deadline → on fire by age
# ---------------------------------------------------------------------------

def test_old_no_deadline_on_fire_by_age():
    t = _task(created_days_ago=25)  # age_score = 25/30 = 0.833 >= 0.8
    s = score_task(t, NOW_MS)
    assert s.age_score >= 0.8
    assert s.on_fire is True
    assert s.deadline_score == 0.0


# ---------------------------------------------------------------------------
# Boundary: exactly FLAME_DAYS
# ---------------------------------------------------------------------------

def test_exactly_flame_days_is_on_fire():
    t = _task(created_days_ago=1, deadline_days=3)  # days_to_deadline == 3
    s = score_task(t, NOW_MS)
    assert s.on_fire is True


def test_one_day_past_flame_not_on_fire_by_deadline():
    t = _task(created_days_ago=1, deadline_days=4)
    s = score_task(t, NOW_MS)
    # age_score = 1/30 ~0.033 < 0.8, not overdue, days_to > FLAME_DAYS
    assert s.on_fire is False


# ---------------------------------------------------------------------------
# Boundary: exactly AGE_CAP
# ---------------------------------------------------------------------------

def test_age_cap_clamps_to_1():
    t = _task(created_days_ago=30)
    s = score_task(t, NOW_MS)
    assert s.age_score == pytest.approx(1.0)


def test_beyond_age_cap_clamps():
    t = _task(created_days_ago=60)
    s = score_task(t, NOW_MS)
    assert s.age_score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Deadline within HORIZON
# ---------------------------------------------------------------------------

def test_deadline_in_7_days_partial_score():
    t = _task(created_days_ago=0, deadline_days=7)
    s = score_task(t, NOW_MS)
    # deadline_score = (14-7)/14 = 0.5; age=0; score = 0.7*0.5 = 0.35
    assert s.deadline_score == pytest.approx(0.5)
    assert s.score == pytest.approx(0.35)
    assert s.on_fire is False


# ---------------------------------------------------------------------------
# Deadline beyond HORIZON → deadline_score = 0
# ---------------------------------------------------------------------------

def test_deadline_beyond_horizon_zero_deadline_score():
    t = _task(created_days_ago=0, deadline_days=20)
    s = score_task(t, NOW_MS)
    assert s.deadline_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Custom config
# ---------------------------------------------------------------------------

def test_custom_config_weights():
    cfg = {**DEFAULT_CONFIG, "W_D": 0.0, "W_A": 1.0}
    t = _task(created_days_ago=15, deadline_days=1)
    s = score_task(t, NOW_MS, cfg)
    # With W_D=0 score depends only on age
    assert s.score == pytest.approx(s.age_score)

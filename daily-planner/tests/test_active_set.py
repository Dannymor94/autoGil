"""Tests for active_set."""

from src.active_set import ACTIVE_SET_SIZE, build_project_buckets
from src.urgency_scoring import ScoredTask
from src.yougile_client import Deadline, Task

NOW_MS = 1782777600000  # 2026-06-30 00:00 UTC
MS = 86_400_000


def _st(id: str, project_id: str, created_days_ago: float, deadline_days: float | None = None) -> ScoredTask:
    created_at = NOW_MS - int(created_days_ago * MS)
    deadline = None
    if deadline_days is not None:
        deadline = Deadline(deadline_ms=NOW_MS + int(deadline_days * MS), start_date_ms=None, with_time=False)
    task = Task(
        id=id, title=id, project_id=project_id, board_id="b",
        column_id="c", created_at_ms=created_at,
        deadline=deadline, plan_hours=None, completed=False,
    )
    return ScoredTask(task=task, age_score=0, deadline_score=0, score=0, is_overdue=False, on_fire=False)


def test_active_set_top3_by_deadline_asc():
    items = [
        _st("t1", "p1", created_days_ago=10, deadline_days=5),
        _st("t2", "p1", created_days_ago=5, deadline_days=2),
        _st("t3", "p1", created_days_ago=3, deadline_days=10),
        _st("t4", "p1", created_days_ago=1, deadline_days=20),
    ]
    buckets = build_project_buckets(items)
    active_ids = [s.task.id for s in buckets["p1"].active]
    assert active_ids == ["t2", "t1", "t3"]
    assert [s.task.id for s in buckets["p1"].pool] == ["t4"]


def test_no_deadline_goes_to_end():
    items = [
        _st("nodl", "p1", created_days_ago=10, deadline_days=None),
        _st("dl", "p1", created_days_ago=1, deadline_days=5),
    ]
    buckets = build_project_buckets(items)
    active_ids = [s.task.id for s in buckets["p1"].active]
    assert active_ids[0] == "dl"
    assert "nodl" in active_ids


def test_same_deadline_older_task_first():
    items = [
        _st("new", "p1", created_days_ago=1, deadline_days=5),
        _st("old", "p1", created_days_ago=10, deadline_days=5),
    ]
    buckets = build_project_buckets(items)
    assert buckets["p1"].active[0].task.id == "old"


def test_fewer_than_3_all_in_active():
    items = [_st("t1", "p1", created_days_ago=5), _st("t2", "p1", created_days_ago=2)]
    buckets = build_project_buckets(items)
    assert len(buckets["p1"].active) == 2
    assert buckets["p1"].pool == []


def test_multiple_projects_isolated():
    items = [
        _st("a1", "proj-a", created_days_ago=5),
        _st("a2", "proj-a", created_days_ago=3),
        _st("b1", "proj-b", created_days_ago=1),
    ]
    buckets = build_project_buckets(items)
    assert "proj-a" in buckets
    assert "proj-b" in buckets
    assert len(buckets["proj-a"].active) == 2
    assert len(buckets["proj-b"].active) == 1

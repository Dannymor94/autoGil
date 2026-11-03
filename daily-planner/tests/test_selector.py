"""Tests for selector."""

from src.active_set import ProjectBucket
from src.selector import MAX_SLOTS, select
from src.urgency_scoring import ScoredTask
from src.yougile_client import Task


def _st(id: str, score: float, project_id: str = "p") -> ScoredTask:
    task = Task(
        id=id, title=id, project_id=project_id, board_id="b",
        column_id="c", created_at_ms=0, deadline=None,
        plan_hours=None, completed=False,
    )
    return ScoredTask(task=task, age_score=0, deadline_score=0,
                      score=score, is_overdue=False, on_fire=False)


def _bucket(pid: str, active: list[ScoredTask]) -> ProjectBucket:
    return ProjectBucket(project_id=pid, active=active, pool=[])


def test_sorted_by_score_descending():
    buckets = {
        "p1": _bucket("p1", [_st("low", 0.1), _st("high", 0.9)]),
    }
    result = select(buckets)
    assert [s.task.id for s in result] == ["high", "low"]


def test_capped_at_8_slots():
    items = [_st(f"t{i}", score=float(i)) for i in range(12)]
    buckets = {"p1": _bucket("p1", items)}
    result = select(buckets)
    assert len(result) == MAX_SLOTS
    assert result[0].task.id == "t11"


def test_merges_multiple_projects():
    buckets = {
        "p1": _bucket("p1", [_st("a", 0.8, "p1"), _st("b", 0.3, "p1")]),
        "p2": _bucket("p2", [_st("c", 0.9, "p2")]),
    }
    result = select(buckets)
    assert [s.task.id for s in result] == ["c", "a", "b"]


def test_fewer_than_8_returns_all():
    buckets = {"p1": _bucket("p1", [_st("x", 0.5), _st("y", 0.2)])}
    assert len(select(buckets)) == 2


def test_empty_buckets():
    assert select({}) == []

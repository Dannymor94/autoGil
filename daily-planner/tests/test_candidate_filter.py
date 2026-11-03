"""Tests for candidate_filter."""

from src.candidate_filter import get_candidates
from src.yougile_client import Task


def _task(id: str, completed: bool, column_id: str) -> Task:
    return Task(
        id=id, title=id, project_id="p", board_id="b",
        column_id=column_id, created_at_ms=1748736000000,
        deadline=None, plan_hours=None, completed=completed,
    )


FINAL = {"col-done", "col-archive"}


def test_excludes_completed():
    tasks = [_task("t1", completed=True, column_id="col-todo")]
    assert get_candidates(tasks, FINAL) == []


def test_excludes_final_column():
    tasks = [_task("t1", completed=False, column_id="col-done")]
    assert get_candidates(tasks, FINAL) == []


def test_includes_active():
    t = _task("t1", completed=False, column_id="col-inprogress")
    assert get_candidates([t], FINAL) == [t]


def test_mixed_list():
    active = _task("active", completed=False, column_id="col-todo")
    done = _task("done", completed=True, column_id="col-todo")
    archived = _task("arch", completed=False, column_id="col-archive")
    result = get_candidates([active, done, archived], FINAL)
    assert result == [active]


def test_empty_final_columns():
    tasks = [_task("t1", completed=False, column_id="col-done")]
    assert get_candidates(tasks, set()) == tasks

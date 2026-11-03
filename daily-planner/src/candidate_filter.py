"""Filter tasks to planning candidates."""

from __future__ import annotations

from .yougile_client import Task


def get_candidates(tasks: list[Task], final_columns: set[str]) -> list[Task]:
    """Return tasks eligible for planning: not completed and not in final columns."""
    return [
        t for t in tasks
        if not t.completed and t.column_id not in final_columns
    ]

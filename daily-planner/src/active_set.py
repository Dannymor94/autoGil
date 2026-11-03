"""Build per-project active set (top-3) and pool from scored candidates."""

from __future__ import annotations

from dataclasses import dataclass

from .urgency_scoring import ScoredTask

ACTIVE_SET_SIZE = 3


@dataclass
class ProjectBucket:
    project_id: str
    active: list[ScoredTask]
    pool: list[ScoredTask]


def _sort_key(st: ScoredTask):
    """deadline ASC (None → last), then createdAt ASC."""
    dl = st.task.deadline
    dl_ms = dl.deadline_ms if (dl and dl.deadline_ms is not None) else float("inf")
    return (dl_ms, st.task.created_at_ms)


def build_project_buckets(scored: list[ScoredTask]) -> dict[str, ProjectBucket]:
    by_project: dict[str, list[ScoredTask]] = {}
    for st in scored:
        by_project.setdefault(st.task.project_id, []).append(st)

    buckets: dict[str, ProjectBucket] = {}
    for pid, items in by_project.items():
        ordered = sorted(items, key=_sort_key)
        active = ordered[:ACTIVE_SET_SIZE]
        pool = ordered[ACTIVE_SET_SIZE:]
        buckets[pid] = ProjectBucket(project_id=pid, active=active, pool=pool)

    return buckets

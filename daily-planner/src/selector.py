"""Selector: merge active sets from all projects into a ranked list of ≤ 8 tasks."""

from __future__ import annotations

from .active_set import ProjectBucket
from .urgency_scoring import ScoredTask

MAX_SLOTS = 8


def select(buckets: dict[str, ProjectBucket]) -> list[ScoredTask]:
    """Return up to MAX_SLOTS tasks sorted by score descending."""
    candidates: list[ScoredTask] = []
    for bucket in buckets.values():
        candidates.extend(bucket.active)

    candidates.sort(key=lambda s: s.score, reverse=True)
    return candidates[:MAX_SLOTS]

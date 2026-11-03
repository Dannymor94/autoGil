"""Deterministic urgency scoring. All thresholds in config dict."""

from __future__ import annotations

from dataclasses import dataclass

from .yougile_client import Task

DEFAULT_CONFIG: dict[str, float] = {
    "AGE_CAP": 30.0,
    "HORIZON": 14.0,
    "FLAME_DAYS": 3.0,
    "W_D": 0.7,
    "W_A": 0.3,
}

MS_PER_DAY = 86_400_000.0


@dataclass
class ScoredTask:
    task: Task
    age_score: float
    deadline_score: float
    score: float
    is_overdue: bool
    on_fire: bool


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def score_task(task: Task, now_ms: int, cfg: dict[str, float] = DEFAULT_CONFIG) -> ScoredTask:
    age_cap = cfg["AGE_CAP"]
    horizon = cfg["HORIZON"]
    flame_days = cfg["FLAME_DAYS"]
    w_d = cfg["W_D"]
    w_a = cfg["W_A"]

    days_since_created = (now_ms - task.created_at_ms) / MS_PER_DAY
    age_score = _clamp(days_since_created / age_cap, 0.0, 1.0)

    is_overdue = False
    days_to_deadline: float | None = None
    deadline_score = 0.0

    if task.deadline and task.deadline.deadline_ms is not None:
        days_to_deadline = (task.deadline.deadline_ms - now_ms) / MS_PER_DAY
        if days_to_deadline < 0:
            is_overdue = True
            deadline_score = 1.0
        else:
            deadline_score = _clamp((horizon - days_to_deadline) / horizon, 0.0, 1.0)

    score = w_d * deadline_score + w_a * age_score

    on_fire = (
        is_overdue
        or (days_to_deadline is not None and days_to_deadline <= flame_days)
        or age_score >= 0.8
    )

    return ScoredTask(
        task=task,
        age_score=age_score,
        deadline_score=deadline_score,
        score=score,
        is_overdue=is_overdue,
        on_fire=on_fire,
    )


def score_tasks(tasks: list[Task], now_ms: int, cfg: dict[str, float] = DEFAULT_CONFIG) -> list[ScoredTask]:
    return [score_task(t, now_ms, cfg) for t in tasks]

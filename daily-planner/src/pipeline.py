"""Main daily-planner pipeline: fetch → filter → score → select → PDF."""

from __future__ import annotations

import time
from pathlib import Path

from .active_set import build_project_buckets
from .candidate_filter import get_candidates
from .plan_pdf import render_pdf
from .selector import select
from .urgency_scoring import score_tasks
from .yougile_client import get_user_tasks


def run(
    api_key: str,
    final_columns: set[str],
    output_dir: Path,
    scoring_cfg: dict | None = None,
) -> Path:
    now_ms = int(time.time() * 1000)

    tasks = get_user_tasks(api_key)
    candidates = get_candidates(tasks, final_columns)
    scored = score_tasks(candidates, now_ms, scoring_cfg or {})
    buckets = build_project_buckets(scored)
    slots = select(buckets)
    return render_pdf(slots, output_dir, now_ms)

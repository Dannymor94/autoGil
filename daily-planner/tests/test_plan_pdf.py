"""Tests for plan_pdf — checks file creation and PDF magic bytes."""

import tempfile
from pathlib import Path

from src.plan_pdf import render_pdf
from src.urgency_scoring import ScoredTask
from src.yougile_client import Deadline, Task

NOW_MS = 1782777600000  # 2026-06-30 00:00 UTC
MS = 86_400_000


def _st(id: str, score: float = 0.5, on_fire: bool = False, deadline_days: int | None = None) -> ScoredTask:
    deadline = None
    if deadline_days is not None:
        deadline = Deadline(deadline_ms=NOW_MS + deadline_days * MS, start_date_ms=None, with_time=False)
    task = Task(
        id=id, title=f"Task {id}", project_id="proj-test", board_id="b",
        column_id="c", created_at_ms=NOW_MS - 5 * MS,
        deadline=deadline, plan_hours=None, completed=False,
    )
    return ScoredTask(task=task, age_score=0.1, deadline_score=0.5,
                      score=score, is_overdue=False, on_fire=on_fire)


def test_pdf_file_created():
    with tempfile.TemporaryDirectory() as tmp:
        slots = [_st("t1"), _st("t2")]
        path = render_pdf(slots, Path(tmp), NOW_MS)
        assert path.exists()
        assert path.suffix == ".pdf"


def test_pdf_magic_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        path = render_pdf([_st("t1")], Path(tmp), NOW_MS)
        assert path.read_bytes()[:4] == b"%PDF"


def test_pdf_filename_contains_date():
    with tempfile.TemporaryDirectory() as tmp:
        path = render_pdf([_st("t1")], Path(tmp), NOW_MS)
        assert "2026-06-30" in path.name


def test_pdf_with_fire_and_deadline():
    with tempfile.TemporaryDirectory() as tmp:
        slots = [
            _st("overdue", score=0.9, on_fire=True, deadline_days=-1),
            _st("future", score=0.4, on_fire=False, deadline_days=7),
        ]
        path = render_pdf(slots, Path(tmp), NOW_MS)
        assert path.exists()


def test_pdf_empty_slots():
    with tempfile.TemporaryDirectory() as tmp:
        path = render_pdf([], Path(tmp), NOW_MS)
        assert path.exists()

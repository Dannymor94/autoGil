"""Tests for yougile_client — mock-first, fixtures from real API shape."""

import json
from pathlib import Path

import httpx
import pytest
import respx

from src.yougile_client import Deadline, Task, get_user_tasks, group_by_project

FIXTURES = Path(__file__).parent / "fixtures"
API_KEY = "test-key"
TASKS_URL = "https://yougile.com/api-v2/tasks"


def _fixture_response() -> dict:
    return json.loads((FIXTURES / "get_user_tasks_response.json").read_text())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_single_page(respx_mock, payload: dict):
    respx_mock.get(TASKS_URL).mock(return_value=httpx.Response(200, json=payload))


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

@respx.mock
def test_task_with_deadline_and_plan():
    payload = _fixture_response()
    _mock_single_page(respx, payload)

    tasks = get_user_tasks(API_KEY)
    t = next(t for t in tasks if t.id == "task-001")

    assert t.title == "Написать отчёт"
    assert t.project_id == "proj-alpha"
    assert t.board_id == "board-alpha"
    assert t.column_id == "col-inprogress"
    assert t.completed is False
    assert isinstance(t.deadline, Deadline)
    assert t.deadline.deadline_ms == 1751500800000
    assert t.plan_hours == 2.5


@respx.mock
def test_task_without_deadline():
    payload = _fixture_response()
    _mock_single_page(respx, payload)

    tasks = get_user_tasks(API_KEY)
    t = next(t for t in tasks if t.id == "task-003")

    assert t.deadline is None
    assert t.plan_hours is None
    assert t.completed is False


@respx.mock
def test_completed_task_mapped():
    payload = _fixture_response()
    _mock_single_page(respx, payload)

    tasks = get_user_tasks(API_KEY)
    t = next(t for t in tasks if t.id == "task-002")

    assert t.completed is True
    assert t.deadline is None
    assert t.plan_hours is None


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

@respx.mock
def test_group_by_project_multiple_projects():
    payload = _fixture_response()
    _mock_single_page(respx, payload)

    tasks = get_user_tasks(API_KEY)
    groups = group_by_project(tasks)

    assert set(groups.keys()) == {"proj-alpha", "proj-beta", "proj-personal"}
    assert len(groups["proj-alpha"]) == 2
    assert len(groups["proj-beta"]) == 1
    assert len(groups["proj-personal"]) == 1


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

@respx.mock
def test_pagination_fetches_all_pages():
    page1 = {
        "content": [
            {
                "id": f"t{i}",
                "title": f"Task {i}",
                "projectId": "p1",
                "boardId": "b1",
                "columnId": "c1",
                "createdAt": 1748736000000,
                "deadline": None,
                "timeTracking": {},
                "completed": False,
            }
            for i in range(50)
        ]
    }
    page2 = {
        "content": [
            {
                "id": "t50",
                "title": "Task 50",
                "projectId": "p1",
                "boardId": "b1",
                "columnId": "c1",
                "createdAt": 1748736000000,
                "deadline": None,
                "timeTracking": {},
                "completed": False,
            }
        ]
    }

    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=page1 if call_count == 1 else page2)

    respx.get(TASKS_URL).mock(side_effect=side_effect)

    tasks = get_user_tasks(API_KEY)
    assert len(tasks) == 51
    assert call_count == 2


# ---------------------------------------------------------------------------
# 429 back-off (no real sleep — monkeypatch)
# ---------------------------------------------------------------------------

@respx.mock
def test_429_retries(monkeypatch):
    call_count = 0
    slept: list[float] = []
    monkeypatch.setattr("src.yougile_client.time.sleep", lambda s: slept.append(s))

    payload = _fixture_response()

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json=payload)

    respx.get(TASKS_URL).mock(side_effect=side_effect)

    tasks = get_user_tasks(API_KEY)
    assert call_count == 2
    assert slept == [2.0]
    assert len(tasks) == 4

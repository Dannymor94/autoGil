"""YouGile API v2 read-only client."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

BASE_URL = "https://yougile.com/api-v2"
_DEFAULT_TIMEOUT = 30.0
_RETRY_AFTER_DEFAULT = 5


@dataclass
class Deadline:
    deadline_ms: int | None
    start_date_ms: int | None
    with_time: bool


@dataclass
class Task:
    id: str
    title: str
    project_id: str
    board_id: str
    column_id: str
    created_at_ms: int
    deadline: Deadline | None
    plan_hours: float | None
    completed: bool


def _map_task(raw: dict[str, Any]) -> Task:
    dl_raw = raw.get("deadline")
    deadline: Deadline | None = None
    if dl_raw:
        deadline = Deadline(
            deadline_ms=dl_raw.get("deadline"),
            start_date_ms=dl_raw.get("startDate"),
            with_time=bool(dl_raw.get("withTime", False)),
        )

    tt = raw.get("timeTracking") or {}
    plan_hours: float | None = tt.get("plan")

    return Task(
        id=raw["id"],
        title=raw["title"],
        project_id=raw.get("projectId", ""),
        board_id=raw.get("boardId", ""),
        column_id=raw.get("columnId", ""),
        created_at_ms=raw.get("createdAt", 0),
        deadline=deadline,
        plan_hours=plan_hours,
        completed=bool(raw.get("completed", False)),
    )


def _fetch_all_tasks(api_key: str, http: httpx.Client) -> list[dict[str, Any]]:
    """Fetch all user tasks with pagination and 429 back-off."""
    results: list[dict[str, Any]] = []
    offset = 0
    limit = 50

    while True:
        resp = http.get(
            f"{BASE_URL}/tasks",
            params={"assigned-to-me": "true", "offset": offset, "count": limit},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_DEFAULT_TIMEOUT,
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", _RETRY_AFTER_DEFAULT))
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        page: list[dict[str, Any]] = body.get("content", [])
        results.extend(page)

        if len(page) < limit:
            break
        offset += limit

    return results


def get_user_tasks(api_key: str, *, http: httpx.Client | None = None) -> list[Task]:
    """Return all non-paginated user tasks mapped to Task dataclasses."""
    own_client = http is None
    client = http or httpx.Client()
    try:
        raw_tasks = _fetch_all_tasks(api_key, client)
    finally:
        if own_client:
            client.close()

    return [_map_task(r) for r in raw_tasks]


def group_by_project(tasks: list[Task]) -> dict[str, list[Task]]:
    """Group tasks by project_id."""
    groups: dict[str, list[Task]] = {}
    for task in tasks:
        groups.setdefault(task.project_id, []).append(task)
    return groups

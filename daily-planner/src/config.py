"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from .urgency_scoring import DEFAULT_CONFIG


def load() -> dict:
    return {
        "api_key": os.environ["YOUGILE_API_KEY"],
        "final_columns": set(
            c.strip() for c in os.environ.get("FINAL_COLUMNS", "").split(",") if c.strip()
        ),
        "output_dir": Path(os.environ.get("OUTPUT_DIR", "output")),
        "scoring": {
            **DEFAULT_CONFIG,
        },
    }

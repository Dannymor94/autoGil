#!/usr/bin/env python3
"""Entry point for the daily planner cron job."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load
from src.pipeline import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    cfg = load()
    log.info("Starting daily planner pipeline")
    pdf_path = run(
        api_key=cfg["api_key"],
        final_columns=cfg["final_columns"],
        output_dir=cfg["output_dir"],
        scoring_cfg=cfg["scoring"],
    )
    log.info("PDF written to %s", pdf_path)


if __name__ == "__main__":
    main()

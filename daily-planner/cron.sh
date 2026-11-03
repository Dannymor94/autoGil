#!/bin/bash
# Wrapper for cron — sets up env, activates venv, runs pipeline.
# Called by: 0 3 * * * /path/to/daily-planner/cron.sh >> /path/to/daily-planner/output/cron.log 2>&1
# 06:00 MSK = 03:00 UTC

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Load secrets from .env if present
if [[ -f "$DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DIR/.env"
    set +a
fi

export OUTPUT_DIR="${OUTPUT_DIR:-$DIR/output}"

"$DIR/.venv/bin/python3" "$DIR/run.py"

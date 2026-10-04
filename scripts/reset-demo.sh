#!/usr/bin/env bash
# Wipe the demo database and seed it again, in one command.
#
#   scripts/reset-demo.sh
#
# Works with the demo running: there is no need to stop scripts/start-demo.sh
# first, and the next page load shows the four showcase cases (#1-#4) and the
# 29 history cases. A copy of the old database goes to
# pipeline/backend/backups/ first.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/pipeline/backend"
exec uv run python -m app.reset_demo

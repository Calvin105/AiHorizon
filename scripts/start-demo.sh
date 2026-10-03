#!/usr/bin/env bash
# Start everything the live demo needs, in one terminal.
#
#   scripts/start-demo.sh             backend + production frontend
#   scripts/start-demo.sh --reset     rebuild the demo database first
#   LLM_ENABLED=false scripts/start-demo.sh    no network needed at all
#
# The backend stays on localhost. The frontend listens on every interface
# and forwards /api to the backend, so a phone on the same Wi-Fi or hotspot
# can open the printed URL (or scan the QR code) and use the camera.
# Ctrl+C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/pipeline/backend"
FRONTEND="$ROOT/pipeline/frontend"

if [[ "${1:-}" == "--reset" ]]; then
  echo "Rebuilding the demo database (the old one goes to pipeline/backend/backups/)..."
  (cd "$BACKEND" && uv run python -m app.reset_demo)
fi

# Bring the database's schema up to date. Does nothing when it already is;
# it matters after pulling a change that adds a table, as rule edits did.
if ! (cd "$BACKEND" && uv run alembic upgrade head) >/dev/null 2>&1; then
  echo "Could not upgrade the database. Run: cd pipeline/backend && uv run alembic upgrade head"
  exit 1
fi

if [[ ! -f "$FRONTEND/.next/BUILD_ID" ]]; then
  echo "No production build yet — building the frontend once..."
  (cd "$FRONTEND" && pnpm build)
fi

cleanup() {
  trap - INT TERM EXIT
  echo
  echo "Stopping the demo servers..."
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

(cd "$BACKEND" && exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8001) &
BACKEND_PID=$!
(cd "$FRONTEND" && exec pnpm exec next start -H 0.0.0.0 -p 3001) &
FRONTEND_PID=$!

for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:3001/api/health >/dev/null 2>&1; then break; fi
  sleep 0.5
done

LLM_STATE="on if pipeline/backend/.env has a GROQ_API_KEY"
[[ "${LLM_ENABLED:-}" == "false" ]] && LLM_STATE="off (LLM_ENABLED=false) — fully offline"

echo
echo "  AI Dispensing Defect Detective is running"
echo "  On this laptop:   http://localhost:3001"
for ip in $(hostname -I 2>/dev/null); do
  case "$ip" in 172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) continue ;; esac  # container bridges
  echo "  From a phone:     http://$ip:3001"
  PHONE_URL="${PHONE_URL:-http://$ip:3001}"
done
echo "  LLM steps:        $LLM_STATE"
echo "  API docs:         http://localhost:8001/docs"
if [[ -n "${PHONE_URL:-}" ]]; then
  echo
  uv run --quiet --with qrcode python -c "
import qrcode, sys
q = qrcode.QRCode(border=1)
q.add_data(sys.argv[1])
q.print_ascii(invert=True)" "$PHONE_URL" 2>/dev/null || true
fi
echo
echo "  Ctrl+C to stop."
wait

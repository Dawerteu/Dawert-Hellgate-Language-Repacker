#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPACKER_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$REPACKER_DIR/repacker.py" --interactive
elif command -v python >/dev/null 2>&1; then
  exec python "$REPACKER_DIR/repacker.py" --interactive
else
  echo "Python 3 is required. Install python3 and run this again." >&2
  exit 1
fi

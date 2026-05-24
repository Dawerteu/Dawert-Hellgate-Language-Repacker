#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/dawert-launcher.conf"

load_saved_language() {
  if [[ -f "$CONFIG_FILE" ]]; then
    local value
    value="$(sed -n 's/^language=//p' "$CONFIG_FILE" | tail -n 1)"
    if [[ -n "$value" ]]; then
      printf '%s\n' "$value"
      return 0
    fi
  fi
  printf '%s\n' czech
}

save_language() {
  local value="$1"
  printf 'language=%s\n' "$value" > "$CONFIG_FILE"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

find_python() {
  if need_cmd python3; then
    printf '%s\n' python3
  elif need_cmd python; then
    printf '%s\n' python
  else
    return 1
  fi
}

find_game_dir() {
  local candidates=(
    "${GAME_DIR:-}"
    "${HELLGATE_DIR:-}"
    "$SCRIPT_DIR/../london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$SCRIPT_DIR/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$PWD/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$HOME/.local/share/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$HOME/.local/share/london2038/wineprefix/drive_c/London2038"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" ]] || continue
    if [[ -d "$candidate/Data" && -f "$candidate/Launcher.exe" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

echo "Dawert official updater"
echo "======================="
echo "This verifies official checksums, downloads official changed files, refreshes backup, then can reinstall language."
echo

PYTHON_BIN="$(find_python)" || {
  echo "Python 3 is required. Run setup-linux.sh first." >&2
  exit 1
}

GAME_DIR_VALUE="$(find_game_dir || true)"
if [[ -z "$GAME_DIR_VALUE" ]]; then
  read -r -p "Hellgate London folder containing Data: " GAME_DIR_VALUE
fi

if [[ ! -d "$GAME_DIR_VALUE/Data" || ! -f "$GAME_DIR_VALUE/Launcher.exe" ]]; then
  echo "Invalid game folder or missing Launcher.exe:" >&2
  echo "  $GAME_DIR_VALUE" >&2
  exit 1
fi

echo
SAVED_LANGUAGE="$(load_saved_language)"
read -r -p "Language to install after update [$SAVED_LANGUAGE]: " LANGUAGE_VALUE
LANGUAGE_VALUE="${LANGUAGE_VALUE:-$SAVED_LANGUAGE}"
save_language "$LANGUAGE_VALUE"

echo
echo "Running checksum updater..."
"$PYTHON_BIN" "$SCRIPT_DIR/repacker.py" \
  --game-dir "$GAME_DIR_VALUE" \
  --action checksum-update \
  --language "$LANGUAGE_VALUE" \
  --quiet-decrypt-log

echo
echo "Done. For normal play, use play-linux.sh."

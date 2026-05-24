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
  return 0
}

load_saved_launch_mode() {
  if [[ -f "$CONFIG_FILE" ]]; then
    local value
    value="$(sed -n 's/^launch_mode=//p' "$CONFIG_FILE" | tail -n 1)"
    if [[ "$value" == "normal" || "$value" == "desktop" ]]; then
      printf '%s\n' "$value"
      return 0
    fi
  fi
  printf '%s\n' desktop
}

save_settings() {
  local value="$1"
  local launch_mode="$2"
  {
    printf 'language=%s\n' "$value"
    printf 'launch_mode=%s\n' "$launch_mode"
  } > "$CONFIG_FILE"
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
    if [[ -d "$candidate/Data" && -f "$candidate/Launcher.exe" && -f "$candidate/MP_x64/London2038_dx9_x64.exe" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

desktop_size() {
  if command -v xrandr >/dev/null 2>&1; then
    xrandr 2>/dev/null | awk '/\*/ { print $1; exit }'
  fi
}

echo "Dawert direct play launcher"
echo "==========================="
echo "Normal play bypasses Launcher.exe so it cannot overwrite localized archives."
echo

PYTHON_BIN="$(find_python)" || {
  echo "Python 3 is required. Run setup-linux.sh first." >&2
  exit 1
}

GAME_DIR_VALUE="$(find_game_dir || true)"
if [[ -z "$GAME_DIR_VALUE" ]]; then
  read -r -p "Hellgate London folder containing Data: " GAME_DIR_VALUE
fi

if [[ ! -d "$GAME_DIR_VALUE/Data" || ! -f "$GAME_DIR_VALUE/Launcher.exe" || ! -f "$GAME_DIR_VALUE/MP_x64/London2038_dx9_x64.exe" ]]; then
  echo "Invalid game folder or missing Launcher.exe / MP_x64/London2038_dx9_x64.exe:" >&2
  echo "  $GAME_DIR_VALUE" >&2
  exit 1
fi

SAVED_LANGUAGE="$(load_saved_language)"
if [[ -n "$SAVED_LANGUAGE" ]]; then
  read -r -p "Language to apply before launch [$SAVED_LANGUAGE]: " LANGUAGE_VALUE
  LANGUAGE_VALUE="${LANGUAGE_VALUE:-$SAVED_LANGUAGE}"
else
  while [[ -z "${LANGUAGE_VALUE:-}" ]]; do
    read -r -p "Language to apply before launch: " LANGUAGE_VALUE
  done
fi

if ! need_cmd wine; then
  echo "Wine was not found. Repack applied, but the game cannot be launched from this script." >&2
  exit 1
fi

SAVED_LAUNCH_MODE="$(load_saved_launch_mode)"
echo
echo "Launch window mode:"
echo "  1. Wine virtual desktop - safer when the game jumps back to taskbar"
echo "  2. Normal Wine fullscreen/window"
if [[ "$SAVED_LAUNCH_MODE" == "normal" ]]; then
  DEFAULT_LAUNCH_CHOICE=2
else
  DEFAULT_LAUNCH_CHOICE=1
fi
read -r -p "Choose [$DEFAULT_LAUNCH_CHOICE]: " LAUNCH_CHOICE
LAUNCH_CHOICE="${LAUNCH_CHOICE:-$DEFAULT_LAUNCH_CHOICE}"
if [[ "$LAUNCH_CHOICE" == "2" ]]; then
  LAUNCH_MODE="normal"
else
  LAUNCH_MODE="desktop"
fi
save_settings "$LANGUAGE_VALUE" "$LAUNCH_MODE"

if [[ -z "${WINEPREFIX:-}" && "$GAME_DIR_VALUE" == *"/drive_c/"* ]]; then
  export WINEPREFIX="${GAME_DIR_VALUE%%/drive_c/*}"
  echo "Using WINEPREFIX:"
  echo "  $WINEPREFIX"
fi

echo
echo "Mode:"
echo "  1. Play now - repack language and start game directly"
echo "  2. Official checksum update - verify/download official files, then repack again"
read -r -p "Choose [1]: " MODE_VALUE
MODE_VALUE="${MODE_VALUE:-1}"

if [[ "$MODE_VALUE" == "2" ]]; then
  echo
  echo "Running official checksum updater..."
  "$PYTHON_BIN" "$SCRIPT_DIR/repacker.py" \
    --game-dir "$GAME_DIR_VALUE" \
    --action checksum-update \
    --language "$LANGUAGE_VALUE" \
    --quiet-decrypt-log
  read -r -p "Start the game directly now? [Y/n]: " CONTINUE_VALUE
  if [[ "$CONTINUE_VALUE" =~ ^[Nn] ]]; then
    echo "Done. Run play-linux.sh when you want to play with translation."
    exit 0
  fi
  SKIP_REPACK=1
fi

if [[ "${SKIP_REPACK:-0}" != "1" ]]; then
  echo
  echo "Applying language repack: $LANGUAGE_VALUE"
  "$PYTHON_BIN" "$SCRIPT_DIR/repacker.py" \
    --game-dir "$GAME_DIR_VALUE" \
    --language "$LANGUAGE_VALUE" \
    --exclude none \
    --quiet-decrypt-log
fi

echo
echo "Starting game directly:"
echo "  $GAME_DIR_VALUE/MP_x64/London2038_dx9_x64.exe"
cd "$GAME_DIR_VALUE/MP_x64"
if [[ "$LAUNCH_MODE" == "desktop" ]]; then
  DESKTOP_SIZE_VALUE="${LONDON2038_DESKTOP_SIZE:-$(desktop_size)}"
  DESKTOP_SIZE_VALUE="${DESKTOP_SIZE_VALUE:-1920x1080}"
  echo "Wine virtual desktop: $DESKTOP_SIZE_VALUE"
  exec wine explorer "/desktop=London2038,$DESKTOP_SIZE_VALUE" "London2038_dx9_x64.exe"
fi
exec wine "London2038_dx9_x64.exe"

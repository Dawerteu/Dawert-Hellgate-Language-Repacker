#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPACKER_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
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

load_installed_language() {
  local game_dir="$1"
  local file="$game_dir/Data/dawertrepacker/installed-language.txt"
  if [[ -f "$file" ]]; then
    local value
    value="$(sed -n '1p' "$file" | tr -d '\r\n')"
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

is_game_dir() {
  local path="$1"
  [[ -d "$path/Data" && -f "$path/Launcher.exe" ]] && find_game_exe "$path" >/dev/null
}

find_game_dir() {
  local candidates=(
    "${GAME_DIR:-}"
    "${HELLGATE_DIR:-}"
    "$REPACKER_DIR/../london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$REPACKER_DIR/../london2038/wineprefix/drive_c/London2038"
    "$REPACKER_DIR/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$REPACKER_DIR/london2038/wineprefix/drive_c/London2038"
    "$PWD/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$PWD/london2038/wineprefix/drive_c/London2038"
    "$HOME/.local/share/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London"
    "$HOME/.local/share/london2038/wineprefix/drive_c/London2038"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" ]] || continue
    if is_game_dir "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  find_game_dir_by_scan
}

find_game_dir_by_scan() {
  local roots=(
    "$REPACKER_DIR/.."
    "$PWD"
    "$HOME/.local/share/london2038"
    "$HOME/.local/share"
  )
  local root launcher candidate
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r launcher; do
      candidate="$(dirname "$launcher")"
      if is_game_dir "$candidate"; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done < <(find "$root" -maxdepth 8 -type f -name Launcher.exe 2>/dev/null)
  done
  return 1
}

resolve_game_dir_input() {
  local value="$1"
  local candidate current launcher
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  if [[ "$value" == "~"* ]]; then
    value="${value/#\~/$HOME}"
  fi
  [[ -n "$value" ]] || return 1
  if [[ -f "$value" ]]; then
    value="$(dirname "$value")"
  fi

  current="$value"
  while [[ -n "$current" && "$current" != "/" ]]; do
    if is_game_dir "$current"; then
      printf '%s\n' "$current"
      return 0
    fi
    current="$(dirname "$current")"
  done

  if [[ -d "$value" ]]; then
    while IFS= read -r launcher; do
      candidate="$(dirname "$launcher")"
      if is_game_dir "$candidate"; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done < <(find "$value" -maxdepth 8 -type f -name Launcher.exe 2>/dev/null)
  fi
  return 1
}

print_game_dir_help() {
  local value="$1"
  echo "Invalid game folder:" >&2
  echo "  $value" >&2
  echo >&2
  echo "Expected the Hellgate/London2038 install root folder containing:" >&2
  echo "  Launcher.exe" >&2
  echo "  Data/" >&2
  echo "  MP_x64/London2038_dx9_x64.exe or MP_x86/London2038_dx9_x86.exe" >&2
  echo >&2
  echo "Example:" >&2
  echo "  /DATA/hellgate/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London" >&2
  echo >&2
  echo "You may also enter a folder inside the Hellgate install, such as Data or MP_x64;" >&2
  echo "the launcher will walk upward and scan below that folder for Launcher.exe." >&2
}

find_game_exe() {
  local game_dir="$1"
  local exe
  local candidates=(
    "$game_dir/MP_x64/London2038_dx9_x64.exe"
    "$game_dir/MP_x86/London2038_dx9_x86.exe"
  )
  for exe in "${candidates[@]}"; do
    if [[ -f "$exe" ]]; then
      printf '%s\n' "$exe"
      return 0
    fi
  done
  return 1
}

require_installed_language() {
  local saved="$1"
  if [[ -n "$saved" ]]; then
    echo "Installed language: $saved" >&2
    printf '%s\n' "$saved"
    return 0
  fi

  echo "No installed language is saved for direct play." >&2
  echo "Install a language first with:" >&2
  echo "  ./linux/start-linux.sh" >&2
  echo "or run the installer language menu:" >&2
  echo "  ./install-linux.sh --language-menu" >&2
  exit 1
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

GAME_DIR_VALUE="$(find_game_dir || true)"
if [[ -z "$GAME_DIR_VALUE" ]]; then
  read -r -p "Hellgate London folder containing Data: " GAME_DIR_VALUE
fi
GAME_DIR_VALUE="$(resolve_game_dir_input "$GAME_DIR_VALUE" || true)"

if [[ -z "$GAME_DIR_VALUE" ]] || ! is_game_dir "$GAME_DIR_VALUE"; then
  print_game_dir_help "${GAME_DIR_VALUE:-"(empty)"}"
  exit 1
fi

SAVED_LANGUAGE="$(load_saved_language)"
if [[ -z "$SAVED_LANGUAGE" ]]; then
  SAVED_LANGUAGE="$(load_installed_language "$GAME_DIR_VALUE")"
  if [[ -n "$SAVED_LANGUAGE" ]]; then
    echo "Found installed language from game data: $SAVED_LANGUAGE"
  fi
fi
LANGUAGE_VALUE="$(require_installed_language "$SAVED_LANGUAGE")"

if ! need_cmd wine; then
  echo "Wine was not found; the game cannot be launched from this script." >&2
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
echo "Starting game directly:"
GAME_EXE="$(find_game_exe "$GAME_DIR_VALUE")" || exit 1
echo "  $GAME_EXE"
cd "$(dirname "$GAME_EXE")"
GAME_EXE_NAME="$(basename "$GAME_EXE")"
if [[ "$LAUNCH_MODE" == "desktop" ]]; then
  DESKTOP_SIZE_VALUE="${LONDON2038_DESKTOP_SIZE:-$(desktop_size)}"
  DESKTOP_SIZE_VALUE="${DESKTOP_SIZE_VALUE:-1920x1080}"
  echo "Wine virtual desktop: $DESKTOP_SIZE_VALUE"
  exec wine explorer "/desktop=London2038,$DESKTOP_SIZE_VALUE" "$GAME_EXE_NAME"
fi
exec wine "$GAME_EXE_NAME"

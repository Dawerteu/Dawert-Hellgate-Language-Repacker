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

save_language() {
  local value="$1"
  printf 'language=%s\n' "$value" > "$CONFIG_FILE"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

is_game_dir() {
  local path="$1"
  [[ -d "$path/Data" && -f "$path/Launcher.exe" ]]
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
  echo >&2
  echo "Example:" >&2
  echo "  /DATA/hellgate/london2038/wineprefix/drive_c/Program Files/Flagship Studios/Hellgate London" >&2
  echo >&2
  echo "You may also enter a folder inside the Hellgate install, such as Data or MP_x64;" >&2
  echo "the updater will walk upward and scan below that folder for Launcher.exe." >&2
}

echo "Dawert official updater"
echo "======================="
echo "This verifies official checksums, downloads official changed files, refreshes backup, then can reinstall language."
echo

PYTHON_BIN="$(find_python)" || {
  echo "Python 3 is required. Run linux/setup-linux.sh first." >&2
  exit 1
}

GAME_DIR_VALUE="$(find_game_dir || true)"
if [[ -z "$GAME_DIR_VALUE" ]]; then
  read -r -p "Hellgate London folder containing Data: " GAME_DIR_VALUE
fi
GAME_DIR_VALUE="$(resolve_game_dir_input "$GAME_DIR_VALUE" || true)"

if [[ -z "$GAME_DIR_VALUE" ]] || ! is_game_dir "$GAME_DIR_VALUE"; then
  print_game_dir_help "${GAME_DIR_VALUE:-"(empty)"}"
  exit 1
fi

echo
SAVED_LANGUAGE="$(load_saved_language)"
if [[ -n "$SAVED_LANGUAGE" ]]; then
  read -r -p "Language to install after update [$SAVED_LANGUAGE]: " LANGUAGE_VALUE
  LANGUAGE_VALUE="${LANGUAGE_VALUE:-$SAVED_LANGUAGE}"
else
  while [[ -z "${LANGUAGE_VALUE:-}" ]]; do
    read -r -p "Language to install after update: " LANGUAGE_VALUE
  done
fi
save_language "$LANGUAGE_VALUE"

echo
echo "Running checksum updater..."
"$PYTHON_BIN" "$REPACKER_DIR/repacker.py" \
  --game-dir "$GAME_DIR_VALUE" \
  --action checksum-update \
  --language "$LANGUAGE_VALUE" \
  --quiet-decrypt-log

echo
echo "Done. For normal play, use linux/play-linux.sh."

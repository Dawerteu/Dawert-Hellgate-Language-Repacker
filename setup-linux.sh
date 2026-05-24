#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

python_ok() {
  local py="${1:-python3}"
  "$py" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 8) else 1)
PY
}

run_with_privileges() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif need_cmd sudo; then
    sudo "$@"
  else
    echo "This setup needs root privileges to install Python." >&2
    echo "Install Python 3.8+ manually, then rerun this setup." >&2
    exit 1
  fi
}

install_python_linux() {
  if need_cmd apt-get; then
    run_with_privileges apt-get update
    run_with_privileges apt-get install -y python3
  elif need_cmd dnf; then
    run_with_privileges dnf install -y python3
  elif need_cmd yum; then
    run_with_privileges yum install -y python3
  elif need_cmd pacman; then
    run_with_privileges pacman -Sy --needed --noconfirm python
  elif need_cmd zypper; then
    run_with_privileges zypper --non-interactive install python3
  elif need_cmd apk; then
    run_with_privileges apk add python3
  elif need_cmd xbps-install; then
    run_with_privileges xbps-install -Sy python3
  elif need_cmd eopkg; then
    run_with_privileges eopkg install -y python3
  elif need_cmd emerge; then
    run_with_privileges emerge --ask=n dev-lang/python
  else
    echo "Unsupported Linux package manager." >&2
    echo "Install Python 3.8+ manually, then run start-linux.sh." >&2
    exit 1
  fi
}

install_python_macos() {
  if need_cmd brew; then
    brew install python
  else
    echo "Homebrew was not found." >&2
    echo "Install Python 3.8+ from https://www.python.org/downloads/ or install Homebrew, then rerun." >&2
    exit 1
  fi
}

echo "Dawert Language Repacker setup"
echo "=============================="
echo "Detected OS: $(uname -s)"
echo

if need_cmd python3 && python_ok python3; then
  echo "Python 3.8+ found: $(python3 --version)"
elif need_cmd python && python_ok python; then
  echo "Python 3.8+ found: $(python --version)"
else
  echo "Python 3.8+ not found. Installing dependency..."
  case "$(uname -s)" in
    Linux) install_python_linux ;;
    Darwin) install_python_macos ;;
    *)
      echo "Unsupported OS for this setup script. Use setup-windows.bat on Windows." >&2
      exit 1
      ;;
  esac
fi

if need_cmd python3 && python_ok python3; then
  PYTHON_BIN="python3"
elif need_cmd python && python_ok python; then
  PYTHON_BIN="python"
else
  echo "Python install did not complete correctly." >&2
  exit 1
fi

echo
echo "Verifying repacker..."
"$PYTHON_BIN" "$SCRIPT_DIR/repacker.py" --help >/dev/null
chmod +x "$SCRIPT_DIR/start-linux.sh" "$SCRIPT_DIR/setup-linux.sh" 2>/dev/null || true

echo
echo "Setup complete."
echo "Start with:"
echo "  $SCRIPT_DIR/start-linux.sh"

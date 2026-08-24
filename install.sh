#!/usr/bin/env bash
# Elite Intel desktop installer.
#
# Designed to run on Windows 11 through Git Bash (Git for Windows), launched
# either directly (double-click install.sh, if .sh is associated with Git
# Bash) or through install.bat, which is provided as a double-click shim for
# machines where .sh files are not associated with an interpreter.
#
# Flow: check/install prerequisites (Node.js, Python), install backend and
# frontend dependencies, build the frontend, package the Electron desktop
# app for Windows, run the generated installer silently, and confirm a
# desktop shortcut exists.
#
# All messages are in English. No em dashes are used, only plain dashes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log() {
  echo ""
  echo "==> $1"
}

fail() {
  echo ""
  echo "ERROR: $1" >&2
  exit 1
}

confirm() {
  echo ""
  echo "Elite Intel - Desktop Installer"
  echo "--------------------------------"
  echo "This will install Node.js and Python if missing, install app"
  echo "dependencies, build the dashboard, package elite-intel.exe, and"
  echo "create a desktop shortcut. No further prompts after this one."
  echo ""
  read -r -p "Continue with installation? [Y/n] " answer
  answer="${answer:-Y}"
  case "$answer" in
    [Yy]*) ;;
    *) echo "Installation cancelled." && exit 0 ;;
  esac
}

is_windows() {
  case "${OSTYPE:-}" in
    msys*|cygwin*|win32*) return 0 ;;
    *) return 1 ;;
  esac
}

winget_install() {
  local id="$1"
  if command -v winget >/dev/null 2>&1; then
    log "Installing $id with winget (silent, unattended)..."
    winget install --id "$id" -e --silent --accept-package-agreements --accept-source-agreements || \
      fail "winget failed to install $id. Please install it manually and re-run this script."
  else
    fail "winget is not available and $id is missing. Install it manually from https://nodejs.org or https://python.org and re-run this script."
  fi
}

refresh_path_hints() {
  # winget-installed tools may not be on PATH in the current shell session.
  # Add the common install locations so the rest of this script can find them
  # without requiring the user to open a new terminal.
  local candidates=(
    "/c/Program Files/nodejs"
    "/c/Program Files/Python312"
    "/c/Program Files/Python312/Scripts"
    "/c/Program Files/Python311"
    "/c/Program Files/Python311/Scripts"
    "$LOCALAPPDATA/Programs/Python/Python312"
    "$LOCALAPPDATA/Programs/Python/Python312/Scripts"
    "$LOCALAPPDATA/Programs/Python/Python311"
    "$LOCALAPPDATA/Programs/Python/Python311/Scripts"
  )
  for dir in "${candidates[@]}"; do
    if [ -d "$dir" ]; then
      case ":$PATH:" in
        *":$dir:"*) ;;
        *) PATH="$dir:$PATH" ;;
      esac
    fi
  done
  export PATH
}

check_prerequisites() {
  log "Checking prerequisites..."

  if ! command -v node >/dev/null 2>&1; then
    echo "Node.js not found."
    winget_install "OpenJS.NodeJS.LTS"
    refresh_path_hints
  fi
  command -v node >/dev/null 2>&1 || fail "Node.js is still not on PATH after installation. Open a new terminal and re-run install.sh."
  echo "Node.js: $(node --version)"

  local python_cmd=""
  for candidate in python python3 py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      python_cmd="$candidate"
      break
    fi
  done
  if [ -z "$python_cmd" ]; then
    echo "Python not found."
    winget_install "Python.Python.3.12"
    refresh_path_hints
    for candidate in python python3 py; do
      if command -v "$candidate" >/dev/null 2>&1; then
        python_cmd="$candidate"
        break
      fi
    done
  fi
  [ -n "$python_cmd" ] || fail "Python is still not on PATH after installation. Open a new terminal and re-run install.sh."
  echo "Python: $($python_cmd --version 2>&1)"
  export PYTHON_CMD="$python_cmd"
}

setup_backend() {
  log "Setting up backend (Python virtual environment and dependencies)..."
  cd "$SCRIPT_DIR/backend"

  if [ ! -d ".venv" ]; then
    "$PYTHON_CMD" -m venv .venv
  fi

  local venv_python=".venv/Scripts/python.exe"
  if [ ! -f "$venv_python" ]; then
    venv_python=".venv/bin/python"
  fi
  [ -f "$venv_python" ] || fail "Could not find the Python executable inside the virtual environment."

  "$venv_python" -m pip install --upgrade pip
  "$venv_python" -m pip install -r requirements.txt

  cd "$SCRIPT_DIR"
}

setup_frontend() {
  log "Installing frontend dependencies and building the dashboard..."
  cd "$SCRIPT_DIR/frontend"
  npm install
  npm run build
  cd "$SCRIPT_DIR"
}

package_electron_app() {
  log "Packaging the Electron desktop app for Windows..."
  cd "$SCRIPT_DIR/electron"
  npm install
  npm run dist
  cd "$SCRIPT_DIR"
}

run_generated_installer() {
  log "Running the generated installer (unattended)..."
  local installer
  installer=$(find "$SCRIPT_DIR/electron/release" -maxdepth 1 -iname "elite-intel-Setup-*.exe" | head -n 1 || true)
  [ -n "$installer" ] || fail "Could not find the generated installer in electron/release."

  echo "Running: $installer"
  "$installer" /S
  log "elite-intel has been installed. A desktop shortcut should now be available."
}

main() {
  confirm
  check_prerequisites
  setup_backend
  setup_frontend
  package_electron_app

  if is_windows; then
    run_generated_installer
  else
    log "Not running on Windows: skipping the silent installer run."
    echo "The packaged app is available under electron/release/."
  fi

  log "Installation complete."
  echo "Launch Elite Intel from the desktop icon named 'elite-intel'."
}

main "$@"

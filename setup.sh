#!/usr/bin/env bash
# setup.sh
# Cross-platform (macOS/Linux) setup helper with robust error handling.
# - Checks Python 3.8+
# - Creates venv if missing
# - Activates venv
# - Installs dependencies using python -m pip

set -euo pipefail

MIN_MAJOR=3
MIN_MINOR=8

err() {
  echo "ERROR: $*" >&2
}

check_python() {
  if command -v python3 >/dev/null 2>&1; then
    PY=python3
  elif command -v python >/dev/null 2>&1; then
    PY=python
  else
    err "Python 3.8+ is required but not found in PATH."
    return 1
  fi

  local ver
  ver=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
  if [[ -z "${ver}" ]]; then
    err "Unable to determine Python version."
    return 1
  fi
  local maj=${ver%%.*}
  local min=${ver##*.}
  if (( maj < MIN_MAJOR || (maj == MIN_MAJOR && min < MIN_MINOR) )); then
    err "Python ${MIN_MAJOR}.${MIN_MINOR}+ is required. Found: ${ver}"
    return 1
  fi
  echo "Using Python: $PY (version ${ver})"
}

create_venv() {
  if [[ -d venv ]]; then
    echo "venv already exists."
    return 0
  fi
  echo "Creating virtual environment..."
  "$PY" -m venv venv || { err "Failed to create virtual environment."; return 1; }
}

activate_venv() {
  if [[ -f "venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "venv/bin/activate" || { err "Failed to activate venv."; return 1; }
  else
    err "Activation script not found at venv/bin/activate"
    return 1
  fi
}

install_deps() {
  echo "Installing dependencies..."
  python -m pip install -r requirements.txt || { err "pip install failed."; return 1; }
}

main() {
  check_python
  create_venv
  activate_venv
  install_deps
  echo "Setup completed successfully. You can now run:"
  echo "  python verify_setup.py"
}

main "$@"

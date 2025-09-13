#!/usr/bin/env python3
"""
install_deps.py
- Verifies that a virtual environment is active
- Installs dependencies from requirements.txt using `python -m pip`
- Exits non-zero with clear messages on failure
"""
import os
import subprocess
import sys
from pathlib import Path


def ensure_venv_active() -> None:
    # Detect if inside a venv via sys.base_prefix comparison or VIRTUAL_ENV
    in_venv = getattr(sys, 'base_prefix', sys.prefix) != sys.prefix or bool(os.environ.get('VIRTUAL_ENV'))
    if not in_venv:
        print("ERROR: A Python virtual environment is not active.")
        print("Hint: Activate the venv first. Try: \n  - Windows CMD:        venv\\Scripts\\activate\n  - Windows PowerShell: venv\\Scripts\\Activate.ps1\n  - macOS/Linux:        source venv/bin/activate")
        sys.exit(1)


def install_requirements() -> None:
    req = Path(__file__).resolve().parent / 'requirements.txt'
    if not req.exists():
        print(f"ERROR: requirements.txt not found at {req}")
        sys.exit(1)
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(req)])
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)


def main() -> None:
    ensure_venv_active()
    install_requirements()
    print("Dependencies installed successfully.")


if __name__ == '__main__':
    main()

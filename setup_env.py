#!/usr/bin/env python3
"""
setup_env.py
- Checks Python version (>= 3.8)
- Creates a virtual environment in ./venv if missing
- Prints next steps for activation and dependency installation

Exits non-zero on failure with clear messages.
"""
import os
import subprocess
import sys
from pathlib import Path

MIN_VERSION = (3, 8)


def check_python_version() -> None:
    if sys.version_info[:2] < MIN_VERSION:
        print(f"ERROR: Python {MIN_VERSION[0]}.{MIN_VERSION[1]}+ is required. Found: {sys.version.split()[0]}")
        sys.exit(1)


def create_venv(venv_path: Path) -> None:
    if venv_path.exists():
        print(f"Virtual environment already exists at: {venv_path}")
        return
    print("Creating virtual environment in ./venv ...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        sys.exit(1)


def main() -> None:
    check_python_version()
    venv_path = Path(__file__).resolve().parent / "venv"
    create_venv(venv_path)
    print("\nNext steps:")
    print("  1) Activate the environment (see suggested command):")
    if os.name == "nt":
        print("     - CMD:          venv\\Scripts\\activate")
        print("     - PowerShell:   venv\\Scripts\\Activate.ps1 (Set-ExecutionPolicy -Scope Process Bypass -Force if needed)")
    else:
        print("     - Bash/Zsh:     source venv/bin/activate")
        print("     - Fish:         source venv/bin/activate.fish")
    print("  2) Install dependencies:")
    print("     python -m pip install -r requirements.txt")
    print("  3) Verify setup:")
    print("     python verify_setup.py")


if __name__ == "__main__":
    main()

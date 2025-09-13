#!/usr/bin/env python3
"""
activate_env.py
- Detects OS and prints the correct activation command for the local ./venv
- Warns and exits non-zero if ./venv is missing
"""
import os
import sys
from pathlib import Path

venv_path = Path(__file__).resolve().parent / "venv"
if not venv_path.exists():  
    print("ERROR: No virtual environment found at ./venv. Run: \n  python setup_env.py")
    sys.exit(1)

print("Activation instructions for this project (./venv):\n")
if os.name == "nt":
    print("- CMD:        venv\\Scripts\\activate")
    print("- PowerShell: venv\\Scripts\\Activate.ps1  (If needed: Set-ExecutionPolicy -Scope Process Bypass -Force)")
else:
    print("- Bash/Zsh:   source venv/bin/activate")
    print("- Fish:       source venv/bin/activate.fish")

sys.exit(0)

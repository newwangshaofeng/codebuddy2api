# CodeBuddy2API Setup Guide

This guide provides a reliable, cross-platform setup for Windows, macOS, and Linux. It complements `README.md` and the Windows `start.bat` script with robust scripts and verification steps.

## Prerequisites

- Python 3.8 or higher
- Git (optional, for cloning)

## Quick Start

1) Create a virtual environment and install dependencies.

- Windows (CMD/PowerShell):
  ```bat
  python setup_env.py
  python activate_env.py  # prints how to activate venv on your shell
  ````
  Then activate the environment as instructed and run:
  ```bat
  python install_deps.py
  ```

- macOS / Linux:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

2) Verify your environment:
```bash
python verify_setup.py
```

3) Configure environment variables:
- Copy `.env.example` to `.env` and set at least `CODEBUDDY_PASSWORD`.

4) Start the service:
```bash
python web.py
```
Or on Windows simply run `start.bat`.

## Details

### setup_env.py
- Ensures Python >= 3.8.
- Creates `./venv` if missing.
- Prints next steps for activation and installation.

### activate_env.py
- Detects host OS and prints the correct activation command for `./venv`.

### install_deps.py
- Verifies that a virtual environment is active.
- Installs dependencies using `python -m pip install -r requirements.txt`.

### verify_setup.py
- Confirms Python version.
- Imports key packages: `fastapi`, `hypercorn`, `httpx`, `pydantic`.

### setup.sh (macOS/Linux)
- Automates `python3 -m venv venv && source venv/bin/activate && python -m pip install -r requirements.txt` with error checks.

## Troubleshooting

- Missing Python / Wrong version:
  - Ensure `python --version` (Windows) or `python3 --version` (macOS/Linux) shows 3.8+.

- PowerShell activation policy:
  - If activation fails on Windows PowerShell, run:
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
    ```

- Dependencies fail to install:
  - Ensure your virtual environment is active.
  - Try upgrading pip:
    ```bash
    python -m pip install --upgrade pip
    ```

- venv activation script missing on Windows:
  - Delete the `venv` folder and re-run `python setup_env.py`.

- Verify everything:
  - Run `python verify_setup.py` and check all items show `[OK]`.

@echo off
echo Starting CodeBuddy2API...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Enforce Python 3.8+ version requirement
python -c "import sys; exit(0 if sys.version_info[:2] >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
  for /f "tokens=2 delims= " %%v in ('python -V 2^>^&1') do set PY_VER=%%v
  echo Python 3.8+ is required. Found: %PY_VER%
  exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
)

REM Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo Activation script missing. Recreating virtual environment...
    rmdir /S /Q venv
    if errorlevel 1 (
        echo Failed to remove existing venv directory.
        exit /b 1
    )
    python -m venv venv
    if errorlevel 1 (
        echo Failed to recreate virtual environment.
        exit /b 1
    )
)
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies with pip.
    exit /b 1
)

REM Check environment variables and load from .env if exists
if not defined CODEBUDDY_PASSWORD (
    if exist ".env" (
        echo Loading configuration from .env file...
        for /f "tokens=1,2 delims==" %%a in (.env) do (
            if "%%a"=="CODEBUDDY_PASSWORD" set CODEBUDDY_PASSWORD=%%b
        )
    )
    if not defined CODEBUDDY_PASSWORD (
        echo WARNING: CODEBUDDY_PASSWORD environment variable is not set
        echo Please set it in .env file or as environment variable
        set /p CODEBUDDY_PASSWORD="Enter password for API access: "
    ) else (
        echo Using password from .env file
    )
)

REM Start service
echo Starting CodeBuddy2API service...
python web.py
echo Starting CodeBuddy2API service ok...
pause
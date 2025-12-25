@echo off
TITLE Auto-Installer & Launcher for MT5 Labeler

:: ========================================================
:: CONFIGURATION
:: ========================================================
:: Direct link to Python 3.11 Installer (Stable)
set PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe
set PYTHON_INSTALLER=python_installer.exe
set VENV_DIR=venv
:: ========================================================

echo ---------------------------------------------------
echo      MT5 Labeler App - Auto Setup Script
echo ---------------------------------------------------

:: 1. CHECK IF PYTHON IS INSTALLED
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [CHECK] Python is already installed.
    goto :SETUP_VENV
)

echo [INFO] Python not found!
echo [INFO] Downloading Python 3.11 (This may take a minute)...

:: 2. DOWNLOAD PYTHON INSTALLER (Using PowerShell)
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"

IF NOT EXIST "%PYTHON_INSTALLER%" (
    echo [ERROR] Failed to download Python. Please check your internet connection.
    pause
    exit
)

:: 3. INSTALL PYTHON SILENTLY
echo [INFO] Installing Python... (Please wait, this runs in background)
:: Arguments: /quiet = no UI, PrependPath=1 = Add to CMD, Include_test=0 = lighter install
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Clean up the installer file
del "%PYTHON_INSTALLER%"

:: Verify installation
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python installation failed.
    echo You may need to run this script as Administrator.
    pause
    exit
)
echo [SUCCESS] Python installed successfully!

:: ========================================================
:: :SETUP_VENV
:: ========================================================
:SETUP_VENV

:: 4. CREATE VIRTUAL ENVIRONMENT
IF NOT EXIST "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: 5. ACTIVATE & INSTALL LIBRARIES
echo [INFO] Checking required libraries...
call %VENV_DIR%\Scripts\activate

:: Upgrade pip just in case
python -m pip install --upgrade pip --quiet

:: Install packages one by one to ensure they exist
pip install dash pandas plotly --quiet

:: 6. RUN THE APP
echo.
echo ===================================================
echo    LAUNCHING APP...
echo    Please open your browser to: http://127.0.0.1:8050
echo ===================================================
echo.

python labeler_final.py

pause
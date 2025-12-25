@echo off
TITLE Debug Installer
COLOR 0A

echo [DEBUG] Script has started.
echo [DEBUG] Checking for Python...
PAUSE

:: -----------------------------------------------------------
:: 1. CHECK IF PYTHON IS INSTALLED
:: -----------------------------------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [DEBUG] Python found! Skipping install.
    goto :SETUP_ENVIRONMENT
)

echo [DEBUG] Python NOT found. Attempting download...
PAUSE

:: -----------------------------------------------------------
:: 2. DOWNLOAD PYTHON (Robust Method)
:: -----------------------------------------------------------
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
set "INSTALLER=python_installer.exe"

echo [DEBUG] Downloading from %PYTHON_URL%
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'"

IF NOT EXIST "%INSTALLER%" (
    echo [ERROR] Download failed. The installer file was not found.
    echo Possible causes: No internet, or Antivirus blocked the download.
    PAUSE
    EXIT /B
)

echo [DEBUG] Download successful. Installing now...
PAUSE

:: -----------------------------------------------------------
:: 3. INSTALL PYTHON
:: -----------------------------------------------------------
:: Attempt install. If this fails, it might ask for Admin password in a popup.
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:: Clean up
del "%INSTALLER%"

:: Re-check
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was installed but the command is not working yet.
    echo [FIX] Please Restart your computer and run this again.
    PAUSE
    EXIT /B
)

:: -----------------------------------------------------------
:: 4. SETUP ENVIRONMENT
:: -----------------------------------------------------------
:SETUP_ENVIRONMENT
echo [DEBUG] Setting up Virtual Environment...
PAUSE

IF NOT EXIST "venv" (
    python -m venv venv
)

call venv\Scripts\activate

echo [DEBUG] Installing libraries (dash, pandas, plotly)...
pip install dash pandas plotly --quiet

echo [DEBUG] Launching App...
PAUSE

:: Open Browser
start http://127.0.0.1:8050/

:: Run Code
python label.py

PAUSE
@echo off
TITLE Auto-Installer & Launcher for MT5 Labeler
CLS

echo =========================================================
echo    MT5 LABELER APP - ONE CLICK SETUP
echo =========================================================
echo.

:: -----------------------------------------------------------
:: 1. CHECK INTERNET (Needed for first run)
:: -----------------------------------------------------------
ping www.google.com -n 1 -w 1000 >nul
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] No Internet connection detected.
    echo If this is the FIRST time running this, it will fail.
    echo If you have already run this before, it might work.
    echo.
)

:: -----------------------------------------------------------
:: 2. CHECK IF PYTHON IS INSTALLED
:: -----------------------------------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Python is already installed.
    goto :SETUP_ENVIRONMENT
)

echo [INFO] Python not found. Starting automatic installation...
echo        This may take 1-3 minutes. Please do not close this window.

:: -----------------------------------------------------------
:: 3. DOWNLOAD PYTHON 3.11 (Stable)
:: -----------------------------------------------------------
set PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe
set INSTALLER=python_installer.exe

echo [DOWNLOADING] Fetching Python installer...
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'"

IF NOT EXIST "%INSTALLER%" (
    echo [ERROR] Failed to download Python. Check your internet connection.
    pause
    exit
)

:: -----------------------------------------------------------
:: 4. INSTALL PYTHON SILENTLY
:: -----------------------------------------------------------
echo [INSTALLING] Installing Python... (Accept any Pop-ups)
:: /quiet = No UI
:: PrependPath=1 = Add to command line (Crucial)
:: InstallAllUsers=0 = Install just for this user (No Admin needed usually)
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

:: Clean up
del "%INSTALLER%"

:: Refresh environment variables so we can use 'python' immediately
set PATH=%PATH%;%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python install seemed to work, but command not found.
    echo Please restart your computer and try again.
    pause
    exit
)
echo [SUCCESS] Python installed successfully!

:: -----------------------------------------------------------
:: 5. SETUP VIRTUAL ENVIRONMENT & DEPENDENCIES
:: -----------------------------------------------------------
:SETUP_ENVIRONMENT

IF NOT EXIST "venv" (
    echo [SETUP] Creating isolated workspace (venv)...
    python -m venv venv
)

echo [SETUP] Checking libraries...
call venv\Scripts\activate

:: This command installs pandas, dash, and plotly automatically
:: It skips download if they are already installed
pip install dash pandas plotly --quiet

:: -----------------------------------------------------------
:: 6. LAUNCH THE APP
:: -----------------------------------------------------------
CLS
echo =========================================================
echo    READY! APP IS STARTING...
echo =========================================================
echo.
echo    1. Your browser should open automatically.
echo    2. If not, go to: http://127.0.0.1:8050/
echo    3. Keep this black window OPEN while using the app.
echo.

:: Opens the browser automatically after 5 seconds
timeout /t 5 >nul
start http://127.0.0.1:8050/

:: Run the Python Code
python labeler_final.py

pause
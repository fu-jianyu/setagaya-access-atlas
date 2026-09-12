@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(sys.version_info < (3,10))" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0server.py"
  goto finished
)
python -c "import sys; sys.exit(sys.version_info < (3,10))" >nul 2>&1
if not errorlevel 1 (
  python "%~dp0server.py"
  goto finished
)
python3 -c "import sys; sys.exit(sys.version_info < (3,10))" >nul 2>&1
if not errorlevel 1 (
  python3 "%~dp0server.py"
  goto finished
)
echo Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/ and enable Add Python to PATH.
echo Then double-click this file again.
pause
exit /b 1
:finished
if errorlevel 1 pause
endlocal

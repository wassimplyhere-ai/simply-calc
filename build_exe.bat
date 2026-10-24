@echo off
REM Builds calculator.exe from calculator.py.
REM Put this file in the same folder as calculator.py, then double-click it.
REM Python must already be installed (from python.org, with "Add python.exe to PATH" ticked).

echo Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto failed

echo Building calculator.exe...
python -m PyInstaller --onefile --windowed --name calculator calculator.py
if errorlevel 1 goto failed

echo.
echo Done. Your program is at dist\calculator.exe
pause
exit /b 0

:failed
echo.
echo Build failed. Check that Python is installed and added to PATH,
echo and that calculator.py is in this folder.
pause
exit /b 1

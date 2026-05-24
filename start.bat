@echo off

echo ============================================
echo  Launching SwiftDiffusion...
echo ============================================

echo [START] Activating venv...
call .venv\Scripts\activate.bat

echo [START] Launching python main.py...
python main.py

echo.
echo Press any key to exit...
pause >nul

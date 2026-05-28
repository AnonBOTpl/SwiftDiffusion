@echo off

echo ============================================
echo  Launching SwiftDiffusion (UV venv)...
echo ============================================

echo [START] Activating .venv-uv...
call .venv-uv\Scripts\activate.bat

echo [START] Launching python main.py...
python main.py

echo.
echo Press any key to exit...
pause >nul

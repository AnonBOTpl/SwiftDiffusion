@echo off

echo ============================================
echo  Launching SwiftDiffusion...
echo ============================================

call .venv\Scripts\activate.bat
python main.py

echo.
echo Press any key to exit...
pause >nul

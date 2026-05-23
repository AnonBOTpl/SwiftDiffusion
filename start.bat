@echo off
setlocal enabledelayedexpansion

REM === Try to detect language from settings.ini ===
set LANG=en
if exist settings.ini (
    for /f "tokens=2 delims==" %%a in ('findstr /b "language" settings.ini') do set LANG=%%a
    set LANG=!LANG: =!
)

if "%LANG%"=="pl" (
    echo ============================================
    echo  Uruchamianie SwiftDiffusion...
    echo ============================================
) else (
    echo ============================================
    echo  Launching SwiftDiffusion...
    echo ============================================
)

call .venv\Scripts\activate.bat
python main.py

if "%LANG%"=="pl" (
    echo.
    echo Nacisnij dowolny klawisz, aby zakonczyc...
) else (
    echo.
    echo Press any key to exit...
)
pause >nul

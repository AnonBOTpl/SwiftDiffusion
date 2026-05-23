@echo off
setlocal enabledelayedexpansion

REM === Detect language from settings.ini ===
set LANG=en
if exist settings.ini (
    for /f "tokens=2 delims==" %%a in ('findstr /b "language" settings.ini') do set LANG=%%a
    set LANG=!LANG: =!
)

if "%LANG%"=="pl" goto pl_start
echo ============================================
echo  Launching SwiftDiffusion...
echo ============================================
goto start_app
:pl_start
echo ============================================
echo  Uruchamianie SwiftDiffusion...
echo ============================================
:start_app

call .venv\Scripts\activate.bat
python main.py

if "%LANG%"=="pl" goto pl_end
echo.
echo Press any key to exit...
goto end_end
:pl_end
echo.
echo Nacisnij dowolny klawisz, aby zakonczyc...
:end_end
pause >nul

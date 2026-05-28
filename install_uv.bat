@echo off
set VENV_DIR=.venv-uv

echo ============================================
echo   SwiftDiffusion UV Installer
echo ============================================
echo.
echo [1/5] Sprawdzanie / instalowanie uv...
where uv >nul 2>&1
if not errorlevel 1 goto uv_ok
echo uv nie znaleziony. Instalowanie via powershell...
powershell -ExecutionPolicy Bypass -c "& {[System.Net.ServicePointManager]::SecurityProtocol = 3072; Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression}"
:uv_ok

echo [2/5] Tworzenie srodowiska wirtualnego...
if not exist "%VENV_DIR%" uv venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate.bat

echo [3/5] Instalowanie PyTorch (CUDA 12.8)...
uv pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128

echo [4/5] Instalowanie xformers...
uv pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps

echo [5/5] Instalowanie bibliotek z requirements-uv.txt...
uv pip install -r requirements-uv.txt
uv pip install compel --no-deps

echo.
echo ============================================
echo  Instalacja UV zakonczona!
echo ============================================
echo.
echo  NOTE: First launch may take up to 3 minutes.
echo  PyTorch needs to build its kernel cache on a fresh venv.
echo  Subsequent launches will be 3-5 seconds.
echo.
echo  Uruchom / Run: start-uv.bat
echo ============================================
pause

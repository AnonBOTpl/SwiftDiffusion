@echo off
set VENV_DIR=.venv

REM === Language selection ===
echo[
echo ============================================
echo        SwiftDiffusion Installer
echo ============================================
echo[
echo [1] English
echo [2] Polski
echo[
choice /c 12 /m "Select language / Wybierz jezyk: "
if errorlevel 2 goto set_pl
if errorlevel 1 goto set_en

:set_pl
set LANG=pl
goto continue

:set_en
set LANG=en
goto continue

:continue
echo[
if "%LANG%"=="en" (
    echo ============================================
    echo  Step 0/4: Creating virtual environment...
    echo ============================================
) else (
    echo ============================================
    echo  Krok 0/4: Tworzenie srodowiska wirtualnego...
    echo ============================================
)

if not exist "%VENV_DIR%" (
    python -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate.bat

echo[
if "%LANG%"=="en" (
    echo Step 1/4: Installing PyTorch (CUDA 12.8)...
) else (
    echo Krok 1/4: Instalowanie PyTorcha (CUDA 12.8)...
)
python -m pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128

echo[
if "%LANG%"=="en" (
    echo Step 2/4: Installing xformers...
) else (
    echo Krok 2/4: Instalowanie xformers...
)
python -m pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps

echo[
if "%LANG%"=="en" (
    echo Step 3/4: Installing remaining libraries...
) else (
    echo Krok 3/4: Instalowanie reszty bibliotek...
)
python -m pip install -r requirements.txt

echo[
if "%LANG%"=="en" (
    echo ============================================
    echo  Step 4/4: Writing settings file...
    echo ============================================
) else (
    echo ============================================
    echo  Krok 4/4: Zapisywanie pliku konfiguracyjnego...
    echo ============================================
)

if not exist settings.ini (
    (
        echo [Paths]
        echo models_sd = models/stable_diffusion
        echo models_lora = models/lora
        echo models_controlnet = models/controlnet
        echo models_inpaint = models/inpaint
        echo models_vae = models/vae
        echo models_facerestore = models/facerestore
        echo models_facedetection = models/facedetection
        echo models_upscalers = models/upscalers
        echo output_txt2img = output/txt2img
        echo output_inpaint = output/inpaint
        echo output_controlnet = output/controlnet
        echo output_upscaled = output/upscaled
        echo docs = docs
        echo.
        echo [UI]
        echo theme = Dark
        echo accent_color = #00d4ff
        echo language = %LANG%
        echo.
        echo [Generation]
        echo default_sampler = DPM++ 2M
        echo default_scheduler = Normal
        echo default_vae = Domyślne ^(z modelu^)
        echo.
        echo [Performance]
        echo vram_slicing = False
        echo attention_slicing = False
        echo cpu_offload = False
        echo auto_clear_vram = False
        echo.
        echo [Preview]
        echo enabled = False
        echo interval = 5
        echo.
        echo [Integration]
        echo hf_token =
        echo civitai_api_key =
    ) > settings.ini
    if "%LANG%"=="en" (
        echo Settings file created.
    ) else (
        echo Plik konfiguracyjny utworzony.
    )
) else (
    REM Update only the language line in existing settings.ini
    findstr /b "language" settings.ini >nul
    if not errorlevel 1 (
        powershell -Command "(gc settings.ini) -replace '^language = .*', 'language = %LANG%' | Out-File -Encoding utf8 settings.ini"
    )
    if "%LANG%"=="en" (
        echo Settings file updated with language: %LANG%.
    ) else (
        echo Plik konfiguracyjny zaktualizowany na jezyk: %LANG%.
    )
)

echo[
echo[
if "%LANG%"=="en" (
    echo ============================================
    echo  Installation complete!
    echo ============================================
    choice /c YN /m "Launch now / Uruchomic teraz? (Y/N): "
) else (
    echo ============================================
    echo  Instalacja zakonczona!
    echo ============================================
    choice /c YN /m "Uruchomic teraz / Launch now? (Y/N): "
)

if errorlevel 2 goto end
python main.py

:end
if "%LANG%"=="en" (
    echo Press any key to exit...
) else (
    echo Nacisnij dowolny klawisz, aby zakonczyc...
)
pause >nul

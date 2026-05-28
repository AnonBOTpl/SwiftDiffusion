@echo off
set VENV_DIR=.venv

REM === Language selection ===
echo.
echo ============================================
echo        SwiftDiffusion Installer
echo ============================================
echo.
echo [1] English
echo [2] Polski
echo.
choice /c 12 /m "Select language / Wybierz jezyk: "
if errorlevel 2 set LANG=pl
if errorlevel 1 set LANG=en

REM === Step 0/4: Virtual environment ===
echo.
if "%LANG%"=="en" goto en_0
echo ============================================
echo  Krok 0/4: Tworzenie srodowiska wirtualnego...
echo ============================================
goto end_0
:en_0
echo ============================================
echo  Step 0/4: Creating virtual environment...
echo ============================================
:end_0

py -3.12 --version >nul 2>&1
if not errorlevel 1 goto py_found
echo.
if "%LANG%"=="en" goto en_py_err
echo  BLAD: Python 3.12 nie jest zainstalowany.
echo  Pobierz i zainstaluj: https://www.python.org/downloads/release/python-31210/
goto end
:en_py_err
echo  ERROR: Python 3.12 is not installed.
echo  Download from: https://www.python.org/downloads/release/python-31210/
goto end
:py_found
if not exist "%VENV_DIR%" py -3.12 -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate.bat

REM === Step 1/4: PyTorch ===
echo.
if "%LANG%"=="en" goto en_1
echo Krok 1/4: Instalowanie PyTorcha (CUDA 12.8)...
goto end_1
:en_1
echo Step 1/4: Installing PyTorch (CUDA 12.8)...
:end_1
python -m pip install torch==2.7.1+cu128 torchvision==0.22.1+cu128 --extra-index-url https://download.pytorch.org/whl/cu128

REM === Step 2/4: xformers ===
echo.
if "%LANG%"=="en" goto en_2
echo Krok 2/4: Instalowanie xformers...
goto end_2
:en_2
echo Step 2/4: Installing xformers...
:end_2
python -m pip install xformers==0.0.31.post1 --extra-index-url https://download.pytorch.org/whl/cu128 --no-deps

REM === Step 3/4: Requirements ===
echo.
if "%LANG%"=="en" goto en_3
echo Krok 3/4: Instalowanie reszty bibliotek...
goto end_3
:en_3
echo Step 3/4: Installing remaining libraries...
:end_3
python -m pip install -r requirements.txt
python -m pip install compel --no-deps

REM === Step 4/4: Settings file ===
echo.
if "%LANG%"=="en" goto en_4
echo ============================================
echo  Krok 4/4: Zapisywanie pliku konfiguracyjnego...
echo ============================================
goto end_4
:en_4
echo ============================================
echo  Step 4/4: Writing settings file...
echo ============================================
:end_4

if exist settings.ini goto update_settings
goto create_settings

:create_settings
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
    echo default_vae = Domyslne ^(z modelu^)
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
if "%LANG%"=="en" goto cs_en
echo Plik konfiguracyjny utworzony.
goto settings_done
:cs_en
echo Settings file created.
goto settings_done

:update_settings
findstr /b "language" settings.ini >nul
if errorlevel 1 goto settings_done
powershell -Command "(gc settings.ini) -replace '^language = .*', 'language = %LANG%' | Out-File -Encoding utf8 settings.ini"
if "%LANG%"=="en" goto us_en
echo Plik konfiguracyjny zaktualizowany na jezyk: %LANG%.
goto settings_done
:us_en
echo Settings file updated with language: %LANG%.
:settings_done

REM === Done ===
echo.
if "%LANG%"=="en" goto en_done
echo ============================================
echo  Instalacja zakonczona!
echo ============================================
echo.
choice /c YN /m "Uruchomic teraz / Launch now? (Y/N): "
goto end_done
:en_done
echo ============================================
echo  Installation complete!
echo ============================================
echo.
choice /c YN /m "Launch now / Uruchomic teraz? (Y/N): "
:end_done

if errorlevel 2 goto end
python main.py

:end
if "%LANG%"=="en" goto en_end
echo Nacisnij dowolny klawisz, aby zakonczyc...
goto end_end
:en_end
echo Press any key to exit...
:end_end
pause >nul

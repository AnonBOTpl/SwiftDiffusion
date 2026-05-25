[🇬🇧 English](README.md)
# 🎨 SwiftDiffusion — Stable Diffusion GUI

<p align="center">
    <br><br>
  <b>Koniec z konsolą. Zacznij tworzyć.</b>
  <br>
  <i>Przejrzysty, szybki i oszczędny dla VRAM interfejs do Stable Diffusion 1.5 — zbudowany w PyQt6.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/AnonBOTpl/SwiftDiffusion?color=blue" alt="Licencja">
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey" alt="Platforma">
  <a href="https://ko-fi.com/anonbotpl"><img src="https://img.shields.io/badge/wsparcie-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
</p>

---

## 🖼️ Zrzuty ekranu

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20main.png" alt="Główne okno" width="700">
  <br><i>Główne okno generowania</i>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20adetailer.png" alt="ADetailer" width="700">
  <br><i>ADetailer — automatyczna poprawa twarzy</i>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20downloader.png" alt="Pobieracz modeli" width="700">
  <br><i>Wbudowany pobieracz modeli z CivitAI i HuggingFace</i>
</p>

---

## 🚀 Co potrafi?

### ✍️ Narzędzia promptowania

- **Wildcards** — użyj składni `__token__` w prompcie; zastępowana losową linią z `wildcards/token.txt` przy każdym generowaniu
- **Prompt Builder** — komponuj prompty wizualnie z kategorii tagów (quality, style, lighting, artists) jednym kliknięciem
- **Prompt weighting (compel)** — precyzyjnie kontroluj wagę słów i fraz standardową składnią `(word:1.2)`, bez dodatkowej konfiguracji
- **Embeddingi Textual Inversion** — wrzuć pliki `.pt` / `.bin` / `.safetensors` do `models/embeddings/`; pojawiają się automatycznie w Prompt Builderze i są gotowe do użycia po załadowaniu modelu
- **Prompt Builder** — wbudowany menedżer tagów z kategoriami (pozytywne i negatywne), podglądem na żywo dla obu i kopiowaniem jednym kliknięciem do T2I. Zapisuj i przywracaj kombinacje tagów przez **historię** (`prompts_history.json`, ostatnie 20) i **ulubione** (`prompts_favorites.json`, bez limitu). Osobne akcje Wczytaj/Kopiuj/Usuń na wpis dla obu zestawów. 🎲 Przycisk Losuj wybiera konfigurowalną liczbę tagów na kategorię.

### 🖌️ Tryby generowania

| Tryb | Do czego służy |
|---|---|
| **Text2Image** | Generowanie z promptu — pełna kontrola nad samplerem, schedulerem, CFG, krokami i wymiarami |
| **Img2Img** | Transformacja istniejącego obrazu sterowana promptem |
| **Inpainting** | Narysuj maskę na dowolnym obszarze i wygeneruj tylko tę część — pełne Undo/Redo (Ctrl+Z/Y) |
| **ControlNet (Canny)** | Steruj generowaniem na podstawie krawędzi obrazu referencyjnego |
| **ADetailer** | Automatyczne wykrywanie i poprawa twarzy przez YOLOv8 — bez dodatkowych kosztów VRAM |
| **Upscaler** | Powiększanie obrazów wysokiej jakości przez bibliotekę `spandrel` |

### ⚙️ Inteligentne ustawienia

- **Kreator powitalny** — wybierz język i motyw zanim cokolwiek inne
- **7 ciemnych motywów** — Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean — z opcjonalnym własnym kolorem akcentu
- **Kontrola wydajności** — VRAM Slicing, Attention Slicing, Tiled VAE, CPU Offloading, auto czyszczenie VRAM
- **Pełna wielojęzyczność** — dodaj dowolny język, wrzucając plik JSON do folderu `locales/`

### 📦 Zarządzanie modelami

- **URL Downloader** — wklej link z CivitAI lub HuggingFace, resztą zajmuje się SwiftDiffusion: pobiera, kategoryzuje i udostępnia model od razu
- **Live refresh** — dodaj model lub embedding do folderu i UI wykrywa go automatycznie, bez restartu (`QFileSystemWatcher`)
- **Latent Mixology Station** — łącz do 5 adapterów LoRA jednocześnie z wizualnym mikserem wag
- **Automatyczne wykrywanie** formatów `.safetensors`, `.pth`, `.onnx` i innych

### 🖼️ Galeria i metadane PNG

- Przeglądaj wygenerowane obrazy w wbudowanym eksploratorze
- **Recall jednym kliknięciem** — odczytaj prompt, seed i wszystkie ustawienia z metadanych PNG i przywróć je do potoku natychmiast
- Pływające okna z dokumentacją HTML do ControlNet i Inpaintingu

### ⚠️ Znane ograniczenia
- **SDXL** został przetestowany, ale usunięty — `from_single_file()` crashuje na 6 GB GPU bez komunikatu błędu. SwiftDiffusion jest zoptymalizowany i testowany wyłącznie dla **SD 1.5**.

### 📊 Monitor zasobów na żywo

VRAM, RAM, obciążenie i temperatura GPU — widoczne w pasku bocznym przez cały czas.

---

## 🛠️ Instalacja

### Windows (zalecane)

```
1. Pobierz lub sklonuj repozytorium
2. Uruchom install.bat
3. Uruchom start.bat
```

`install.bat` automatycznie tworzy środowisko wirtualne, instaluje PyTorch z obsługą CUDA 12.8 i pobiera wszystkie zależności.

### Linux

```bash
pip install -r requirements.txt
python main.py
```

---

## 📋 Wymagania

| | |
|---|---|
| **Python** | 3.12.10 |
| **GPU** | Kompatybilna z CUDA, zalecane min. 6 GB VRAM (GTX 1060 lub lepsza) |
| **System** | Windows / Linux (wymagany PyQt6) |

---

## 📂 Struktura projektu

```
SwiftDiffusion/
├── main.py                    # Szkielet UI i punkt wejścia
├── boot.py                    # CUDA health check przy imporcie
├── engine.py                  # Logika pipeline'ów dyfuzji
├── worker.py                  # Wątki QThread działające w tle
├── model_manager.py           # Ładowanie modeli, LoRA, file watchery
├── generation_controller.py   # T2I / Img2Img / Upscale
├── mode_controllers.py        # Inpaint / ControlNet / ADetailer
├── config.py                  # Ustawienia i loader i18n
├── widgets/                   # Pakiet komponentów UI
│   ├── __init__.py
│   ├── dialogs.py             # Okna dialogowe (settings, galeria, about)
│   ├── inpaint_canvas.py      # Edytor maski
│   ├── widgets_common.py      # ClickableLabel, suwaki, LoRA
│   ├── model_downloader.py    # Pobieracze z CivitAI / HF
│   ├── flow_layout.py         # FlowLayout dla Prompt Builder
│   ├── prompt_builder.py      # Zakładka Prompt Builder
│   └── resource_monitor.py    # Monitor VRAM/RAM na żywo
├── models_registry.py         # Skaner i rejestr modeli
├── url_downloader.py          # Pomocnicze pobieranie
├── scraper.py                 # Wyszukiwarka modeli
├── install.bat                # Instalator Windows (dwujęzyczny)
├── start.bat                  # Launcher Windows
├── locales/                   # Pliki tłumaczeń (en, pl, …)
├── wildcards/                 # Pliki tekstowe wildcardów
├── tags/                      # Kategorie tagów Prompt Buildera
└── docs/                      # Pływające okna z dokumentacją HTML
```

---

## ☕ Wsparcie

Jeśli SwiftDiffusion oszczędza Ci czas, rozważ postawienie mi kawy:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/anonbotpl)

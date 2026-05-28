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
- **Wyszukiwarka tagów** — filtruj wszystkie przyciski tagów (pozytywne i negatywne) wpisując tekst w polu wyszukiwania. Pasujące wyniki pojawiają się w dedykowanej zakładce z zsynchronizowanym stanem przełączania.
- **Zakładka Wildcards** — przeglądaj i przełączaj wildcardy z folderu `wildcards/` bezpośrednio w Prompt Builderze. Każdy plik `.txt` to klikalny przycisk; tooltip pokazuje pierwsze 5 linii. Wybrane wildcardy używają składni `__nazwa__` i są przywracane z historii/ulubionych.
- **Własne kategorie tagów** — wrzuć własny plik `.json` do `tags/` z `{"label": "Moje Tagi", "tags": ["tag1", "tag2"]}` i pojawi się jako nowa zakładka natychmiast, bez restartu. Wbudowane kategorie zachowują swoją kolejność; twoje pliki dodawane są alfabetycznie poniżej.
- **Style Presets** — gotowe zestawy tagów w `tags/presets/`. Każdy plik to jeden preset: `{"name": "Mój Styl", "icon": "✨", "tags": ["tag1", "tag2"]}`. Dodawaj lub usuwaj pliki w dowolnym momencie — zmiany widoczne od razu. Presety są ekskluzywne (wybranie jednego zastępuje poprzedni).
- **Batch generation** — generuj do 10 obrazów sekwencyjnie jednym kliknięciem. Każdy element używa innego seeda. Auto upscale stosowany per-item. Po zakończeniu przewijany pasek miniatur pozwala przeglądać wyniki i porównywać wersję przed i po upscale.
- **CLIP Interrogator** — wbudowane reverse engineering promptu. Załaduj model CLIP (ViT-B/32 lub ViT-L/14), wrzuć dowolny obraz i otrzymaj ranking dopasowanych terminów w 8 kategoriach — jakość, kolory, medium, artysta, styl, oświetlenie, efekty, kompozycja. Obsługa własnych plików `.json`. Przełącznik GPU/CUDA. Kopiowanie jednym kliknięciem do Text2Image.

### 🖌️ Tryby generowania

| Tryb | Do czego służy |
|---|---|
| **Text2Image** | Generowanie z promptu — pełna kontrola nad samplerem, schedulerem, CFG, krokami i wymiarami |
| **Img2Img** | Transformacja istniejącego obrazu sterowana promptem |
| **Inpainting** | Narysuj maskę na dowolnym obszarze i wygeneruj tylko tę część — pełne Undo/Redo (Ctrl+Z/Y) |
| **ControlNet (Canny)** | Steruj generowaniem na podstawie krawędzi obrazu referencyjnego |
| **ADetailer** | Automatyczne wykrywanie i poprawa twarzy przez YOLOv8 — bez dodatkowych kosztów VRAM |
| **Upscaler** | Powiększanie obrazów wysokiej jakości przez bibliotekę `spandrel` |
| **CLIP Interrogator** | Analizuj dowolny obraz i odtwórz jego prompt — wykrywa jakość, kolory, medium, artystę, styl, oświetlenie, efekty i kompozycję |
| **Photo Restoration** | Odnawiaj stare, zniszczone lub czarno-białe zdjęcia — koloruj B&W, usuwaj rysy/zagniecenia, powiększaj i poprawiaj twarze w potoku dwuprzebiegowym |

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

Wybierz instalator:

| Instalator | Szybkość | Venv |
|------------|----------|------|
| `install.bat` | Standardowy (pip) | `.venv` |
| `install_uv.bat` | **Szybszy** (uv, w Rust) | `.venv-uv` |

```
1. Pobierz lub sklonuj repozytorium
2. Uruchom install.bat (pip) LUB install_uv.bat (uv — 10-50× szybciej)
3. Uruchom start.bat (dla pip) LUB start-uv.bat (dla uv)
```

Oba instalatory automatycznie tworzą środowisko wirtualne, instalują PyTorch z obsługą CUDA 12.8 i pobierają wszystkie zależności. Instalator uv sam pobiera `uv` jeśli nie jest zainstalowany. Venv są niezależne — możesz mieć oba.

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
├── restoration_engine.py      # Silnik Photo Restoration (usuwanie rys, upscale, poprawa twarzy, kolorowanie)
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
│   ├── resource_monitor.py    # Monitor VRAM/RAM na żywo
│   ├── clip_interrogator.py   # Zakładka CLIP Interrogator
│   └── restoration.py         # Zakładka Photo Restoration
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

---

## 🖼️ Instrukcja renowacji zdjęć

Zakładka **Photo Restoration** umożliwia odnawianie starych, zniszczonych lub czarno-białych zdjęć. Używa dwuprzebiegowego potoku łączącego usuwanie rys, kolorowanie, powiększanie i poprawę twarzy.

### Podstawowy przepis

1. **Wczytaj obraz** — kliknij przycisk folderu, aby wczytać JPEG/PNG
2. **Włącz opcje:**
   - **Auto usuwanie rys/zagnieceń** — usuwa rysy, zagniecenia, kurz i fakturę papieru
   - **Koloruj** (tylko zdjęcia B&W) — używa **OpenCV DNN** dla szybkich efektów
   - **Extra upscale** (widoczny gdy zaznaczone zarówno kolorowanie jak i scratch) — dodaje drugie powiększenie dla większego obrazu wyjściowego
3. **Kliknij "Restore"** — potok uruchamia się automatycznie i pokazuje wynik
4. **Otwórz wynik** — kliknij "Otwórz wynik", aby zobaczyć zapisany plik w Eksploratorze

### Co dzieje się pod maską

| Krok | Narzędzie | Opis |
|------|-----------|------|
| Kolorowanie | OpenCV DNN | Dodaje kolor do zdjęć B&W (tylko Przebieg 1) |
| Upscale | Real-ESRGAN x4plus | 2× powiększenie (Przebieg 1; Przebieg 2 jeśli extra upscale włączone) |
| Poprawa twarzy | GFPGAN v1.4 | Odtwarza szczegóły twarzy (oba przebiegi) |
| Usuwanie rys | OpenCV inpainting (NS) | Usuwa rysy, zagniecenia, artefakty (tylko Przebieg 2) |

### Wskazówki

- **Najlepsze efekty ze zdjęciami B&W** które mają dobry kontrast i widoczną zmienność tonalną dla kolorowania
- **Dla zdjęć kolorowych** — wyłącz kolorowanie, włącz scratch + upscale
- **Duże oryginały** — usuwanie rys działa w pełnej rozdzielczości; dwuprzebiegowy potok może dać plik kilkukrotnie większy od oryginału
- **Pierwsze uruchomienie** — modele pobierane są automatycznie (RealESRGAN ~67 MB, GFPGAN ~340 MB, modele kolorowania ~129 MB). Jeśli pobieranie przerwie się w połowie, może być potrzebny restart aplikacji.

## ☕ Wsparcie

Jeśli SwiftDiffusion oszczędza Ci czas, rozważ postawienie mi kawy:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/anonbotpl)

# 🎨 SwiftDiffusion — Stable Diffusion GUI

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/projects-files/main/sd_logo.png" alt="AnonGen Logo" width="200">
  <br>
  <b>Nowoczesny, minimalistyczny interfejs graficzny dla Stable Diffusion 1.5.</b>
  <br>
  <i>Zaprojektowany w PyQt6 z myślą o wygodzie, estetyce i ochronie VRAM.</i>
</p>

---

## 🚀 Kluczowe Funkcje

### 🖌️ Inteligentne Tryby Generowania

- **Text2Image** — Pełna kontrola nad procesem dyfuzji: sampler, scheduler, CFG, kroki i wymiary.
- **Img2Img** — Generowanie obraz-na-obraz z transformacją sterowaną promptem.
- **Inpainting (Edycja)** — Interaktywne płótno do rysowania precyzyjnych masek binarnych (`QGraphicsView`). Pełna historia Undo/Redo (Ctrl+Z, Ctrl+Y). Obsługa dedykowanych modeli oraz trybu współdzielenia komponentów (oszczędność VRAM).
- **ControlNet (Canny)** — Generowanie oparte na krawędziach obrazu referencyjnego z inteligentnym skalowaniem i detekcją krawędzi OpenCV.
- **ADetailer** — Automatyczna poprawa twarzy z użyciem YOLOv8 + inpainting, zero-copy VRAM.
- **Upscaler** — Powiększanie obrazów z użyciem biblioteki `spandrel`.

### ⚙️ Zaawansowane Ustawienia (settings.ini)

- **Kreator powitalny** — Konfiguracja języka i motywu przy pierwszym uruchomieniu.
- **Modułowa Konfiguracja** — Pełna swoboda w definiowaniu ścieżek modeli i folderów zapisu.
- **7 ciemnych motywów** — Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean — każdy z własnym akcentem. Opcjonalny własny kolor akcentu.
- **Performance Tweaks** — VRAM Slicing, Attention Slicing, Model CPU Offloading, auto czyszczenie VRAM.
- **System i18n (Wielojęzyczność)** — Aplikacja przygotowana do obsługi wielu języków (JSON). Obecnie wspiera polski i angielski.

### 📦 Zarządzanie Zasobami

- **URL Downloader** — Wklej link z CivitAI lub HuggingFace, aby automatycznie pobrać i skategoryzować model (LoRA, VAE, ControlNet, checkpoint). Zintegrowane wyszukiwanie w obu platformach.
- **Autonomiczne Odświeżanie** — Dzięki `QFileSystemWatcher` interfejs automatycznie reaguje na dodanie nowych modeli/LoRA na dysku bez resetowania aplikacji.
- **Latent Mixology Station** — Mikser do 5 adapterów LoRA jednocześnie z wizualnym equalizerem wag.
- **Inteligentny Skaner** — Automatyczne wykrywanie modeli `.safetensors`, `.pth`, `.onnx` i innych.
- **Zero-Copy Memory** — Wydajna konwersja obrazów między silnikiem AI a interfejsem bez zbędnego obciążania CPU.

### 🖼️ Galeria i PNG Info

- Przeglądaj swoje dzieła wbudowanym eksploratorem.
- **Parametry Recall** — Odczytuj prompt, seed i ustawienia bezpośrednio z metadanych PNG i przywracaj je do potoku jednym kliknięciem.
- **Floating Tips** — Interaktywne okna z dokumentacją HTML.

### 📊 Monitor Zasobów

- Podgląd VRAM, RAM, obciążenia i temperatury GPU w panelu bocznym, z konfigurowalnym interwałem odświeżania.

---

## 📂 Struktura Projektu

```text
SwiftDiffusion/
    CHANGELOG.md
    config.py
    engine.py
    install.bat
    LICENSE
    main.py
    models_registry.py
    README.md
    README-pl.md
    requirements.txt
    scraper.py
    start.bat
    test_engine.py
    url_downloader.py
    utils.py
    widgets.py
    worker.py
    docs/
        tips_controlnet.html
        tips_inpaint.html
    locales/
        en.json
        pl.json
```

---

## 🛠️ Instalacja

### Szybki Start (Windows)

Uruchom plik `install.bat`, który automatycznie skonfiguruje środowisko wirtualne, zainstaluje PyTorch z obsługą CUDA 12.8 i wszystkie niezbędne biblioteki.

### Uruchomienie

Po instalacji wystarczy kliknąć `start.bat`.

---

## 📋 Wymagania Techniczne

- **Python:** 3.10+
- **GPU:** Kompatybilna z CUDA (zalecane min. 6 GB VRAM)
- **System:** Windows / Linux (z obsługą PyQt6)

---

<p align="center">
  <i>Opracowane jako zadanie przebudowy interfejsu GUI Stable Diffusion.</i>
</p>

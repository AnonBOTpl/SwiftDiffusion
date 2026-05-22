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
- **Inpainting (Edycja)** — Interaktywne płótno do rysowania precyzyjnych masek binarnych. Obsługa dedykowanych modeli oraz trybu współdzielenia komponentów (oszczędność VRAM).
- **ControlNet (Canny)** — Generowanie oparte na krawędziach obrazu referencyjnego z inteligentnym skalowaniem i detekcją krawędzi OpenCV.

### ⚙️ Zaawansowane Ustawienia (settings.ini)
- **Modułowa Konfiguracja** — Pełna swoboda w definiowaniu ścieżek modeli i folderów zapisu.
- **Dynamiczne Motywy** — Płynne przełączanie między trybem **Ciemnym** i **Jasnym** z możliwością wyboru własnego koloru akcentu.
- **Performance Tweaks** — Opcjonalny VRAM Slicing i VAE Tiling dla kart z małą ilością pamięci (np. 6GB).
- **System i18n (Wielojęzyczność)** — Aplikacja przygotowana do obsługi wielu języków (JSON). Obecnie wspiera polski i angielski dla panelu bocznego.

### 📦 Zarządzanie Zasobami
- **Autonomiczne Odświeżanie** — Dzięki `QFileSystemWatcher` interfejs automatycznie reaguje na dodanie nowych modeli/LoRA na dysku bez resetowania aplikacji.
- **Latent Mixology Station** — Mikser do 5 adapterów LoRA jednocześnie z wizualnym equalizerem wag.
- **Inteligentny Skaner** — Automatyczne wykrywanie modeli `.safetensors`, `.pth`, `.onnx` i innych.

### 📊 VRAM Oracle & Optymalizacja
- Szacowanie zużycia pamięci GPU w czasie rzeczywistym z kolorowymi ostrzeżeniami.
- **Auto-Optimizer** — Jeden przycisk do przywrócenia bezpiecznych ustawień rozdzielczości.
- **Zero-Copy Memory** — Wydajna konwersja obrazów między silnikiem AI a interfejsem bez zbędnego obciążania CPU.

### 🖼️ Galeria i PNG Info
- Przeglądaj swoje dzieła wbudowanym eksploratorem.
- **Parametry Recall** — Odczytuj prompt, seed i ustawienia bezpośrednio z metadanych PNG i przywracaj je do potoku jednym kliknięciem.

---

## 📂 Struktura Projektu

```text
SwiftDiffusion/
├── main.py          # Entry point i logika okna głównego
├── engine.py        # Serce aplikacji: Stable Diffusion & ControlNet
├── worker.py        # Asynchroniczne wątki robocze (QThread)
├── widgets.py       # Customowe komponenty UI i okna dialogowe
├── config.py        # Zarządzanie ustawieniami i arkusze stylów
├── utils.py         # Zero-Copy Image Helpers
├── settings.ini     # Twoja lokalna konfiguracja
├── requirements.txt # Lista zależności
└── docs/            # Interaktywne wskazówki HTML
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

# Changelog

## [2.15.0] - 2026-05-21
### Dodano
- **Moduł ADetailer:** Wdrożenie natywnej poprawy twarzy przy użyciu detekcji YOLOv8 i inpaintingu (Zero-Copy VRAM).
- **Interfejs ADetailer:** Nowa zakładka "ADetailer" z pełnym zestawem parametrów (prompt, denoise, dilation, confidence).
- **Logika "Wyślij do ADetailer":** Możliwość bezpośredniego przenoszenia wygenerowanych obrazów z Text2Image do ADetailera.
### Usunięto
- **Moduł Face Restore:** Rezygnacja z bibliotek `facexlib` oraz `basicsr` na rzecz wydajniejszej architektury ADetailera.

## [2.14.0] - 2026-05-21
### Dodano
- **Moduł Face Restore (Legacy):** Wdrożenie zaawansowanej rekonstrukcji twarzy z wykorzystaniem `CodeFormer` (ładowany przez `spandrel`) oraz `facexlib`. Dodano manualne i automatyczne tryby przetwarzania oraz dedykowany trzeci podgląd w interfejsie.

## [2.13.0] - 2026-05-21
### Dodano
- **Obsługa niestandardowych VAE:** Dodano możliwość ładowania zewnętrznych plików VAE (.safetensors, .pt). Nowy panel wyboru w panelu bocznym oraz opcja domyślnego VAE w ustawieniach.

## [2.12.0] - 2026-05-21
### Dodano
- **Zaawansowana Optymalizacja VRAM:** Dodano nowe opcje w ustawieniach: Attention Slicing, Model CPU Offloading oraz automatyczne czyszczenie VRAM po generacji. Pozwala to na jeszcze stabilniejszą pracę na kartach 6GB.

## [2.11.0] - 2026-05-21
### Usunięto
- **Moduł VRAM Oracle:** Całkowite usunięcie wskaźnika zużycia VRAM oraz przycisku Auto-Optimizer z panelu bocznego. Zmiana podyktowana przygotowaniami pod nową architekturę Resource Monitora.

## [2.10.0] - 2026-05-21
### Dodano
- **Automatyczne Odświeżanie List:** Wdrożenie `QFileSystemWatcher` do asynchronicznego monitorowania folderów z modelami. Listy w interfejsie aktualizują się automatycznie po dodaniu lub usunięciu plików na dysku.
- **Inteligentna Pamięć Wyboru:** System zachowuje aktualnie wybrany model/LoRA podczas automatycznego odświeżania list, zapobiegając resetom ComboBoxów.

## [2.9.0] - 2026-05-21
### Dodano
- **System i18n (Tłumaczenia):** Wdrożenie architektury wielojęzyczności opartej na plikach JSON (`locales/`).
- **Wsparcie Językowe:** Dodano pełne tłumaczenia dla panelu bocznego (PL/EN).
- **Dynamiczny Translator:** Globalna funkcja `tr()` z automatycznym ładowaniem słownika na podstawie ustawień.

## [2.8.0] - 2026-05-21
### Dodano
- **Zaawansowany Inpaint Canvas:** Przebudowa płótna na `QGraphicsView` i `QGraphicsScene`.
- **System Undo/Redo:** Pełna historia pędzla z obsługą skrótów klawiaturowych (Ctrl+Z, Ctrl+Y).
- **Centrowanie Obrazu:** Poprawiono logikę wyświetlania obrazu na środku pola edycji.

## [2.7.0] - 2026-05-21
### Dodano
- **Optymalizacja Zero-Copy:** Wdrożenie wydajnego mechanizmu konwersji obrazów między PIL a QImage, opartego na bezpośrednich widokach pamięci.
- **Stabilność Pamięci:** Mechanizm zapobiegający SegFault poprzez jawne zachowanie referencji do bajtów obrazu.

## [2.6.0] - 2026-05-21
### Dodano
- **First Launch Wizard:** Kreator powitalny ułatwiający wstępną konfigurację (język, motyw).
- **Zarządzanie LoRA:** Automatyczne przeładowywanie aktywnych adapterów LoRA po zmianie modelu głównego.
- **Poprawki UI:** Rozbudowane style dla trybu jasnego (Light Mode) oraz ulepszone renderowanie list rozwijanych.

## [2.5.0] - 2026-05-21
### Dodano
- **System Ustawień:** Wdrożenie `settings.ini` zarządzanego przez `SettingsManager`.
- **Panel Konfiguracyjny:** Nowe okno ustawień pozwalające na zmianę ścieżek, kolorów i parametrów wydajności.
- **VRAM Slicing:** Możliwość włączenia optymalizacji VAE Slicing i Tiling dla kart 6GB.
- **Dynamiczne Style:** Całkowite przejście na generowany arkusz CSS.

## [2.4.0] - 2026-05-21
### Dodano
- **Fizyczne Wyładowywanie LoRA:** Dodano metodę `unload_lora`, rozwiązującą błąd `ValueError: Adapter name already in use`.

## [2.3.0] - 2026-05-21
### Dodano
- **Galeria:** Nowa zakładka do przeglądania wygenerowanych obrazów.
- **PNG Info:** Zapis i odczyt parametrów generacji z metadanych plików PNG.
- **Floating Tips:** System pływających okien z dokumentacją (docs/tips).

## [2.2.0] - 2026-05-21
### Dodano
- **ControlNet Canny:** Integracja modułu ControlNet z automatycznym preprocesingiem obrazu.
- **Upscaler:** Obsługa powiększania obrazów za pomocą biblioteki `spandrel`.
- **Modularna Architektura:** Podział projektu na pliki `main`, `widgets`, `config`, `utils`.

## [2.1.0] - 2026-05-21
### Dodano
- **Latent Mixology Station:** Możliwość ładowania do 5 LoRA jednocześnie.
- **VRAM Oracle:** Real-time monitoring zużycia pamięci GPU.
- **UI Modern Dark:** Całkowita przebudowa interfejsu na nowoczesny styl.

## [1.0.0] - 2024-05-22
- Wersja początkowa.

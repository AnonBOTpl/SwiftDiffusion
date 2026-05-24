# Changelog

## [2.20.0] - 2026-05-24 – Wildcards, Tiled VAE, Prompt Builder, Prompt weighting (compel), Embeddingi Textual Inversion
### Dodano
- **Wildcards:** Składnia `__token__` zastępowana losową linią z `wildcards/token.txt`. Tooltip przy polach promptu wyjaśnia użycie.
- **Tiled VAE:** Nowy checkbox w Ustawienia → Wydajność, niezależny od VRAM Slicing. `enable_tiling()` / `disable_tiling()` stosowane oddzielnie.
- **Prompt Builder:** Osobna zakładka z `FlowLayout` i przełączanymi przyciskami tagów z `tags/*.json`. Podgląd + przycisk "Kopiuj do Text2Image". Kategorie: quality, style, lighting, artists.
- **Prompt weighting (compel):** Biblioteka `compel` zintegrowana. `_encode_prompt()` z `try/except ImportError` fallback; status w nagłówku T2I pokazuje dostępność compel.
- **Embeddingi Textual Inversion:** Skanowanie `models/embeddings/` przy ładowaniu modelu. `_load_embeddings()` + `scan_embeddings()` obsługują `.pt`, `.bin`, `.safetensors`. Dynamiczna zakładka Embeddingów w Prompt Builderze, auto-odświeżana przez `QFileSystemWatcher`.
- **Tooltip na zakładce Embeddingów** – hover pokazuje opis.
- **Połączone komunikaty** dla pustej listy embeddingów.
### Poprawiono
- **Brakujący newline w `widgets.py`** powodujący `SyntaxError` podczas importu.

## [2.19.0] - 2026-05-24 – Przycisk STOP, podział podglądów, proporcje obrazu, usunięto SDXL
### Dodano
- **Przycisk STOP dla wszystkich zakładek:** Każdy przycisk generowania zmienia się na "STOP" (czerwony) podczas pracy; kliknięcie przerywa generowanie.
- **Podział podglądu Inpaint:** Lewa strona = edytor maski, prawa = wynik (zamiast popupu).
- **Podział podglądu ControlNet:** Lewa strona = obraz referencyjny, prawa = wynik (zamiast popupu).
- **Czystsze zamykanie:** Zamknięcie okna czyści VRAM przed wyjściem.
- **Health check CUDA przy starcie:** Test w subprocess przed importem engine (zapobiega zawieszeniu na zablokowanym sterowniku GPU).
- **Klucz `btn_stop`** w plikach locale EN/PL.
### Poprawiono
- **Proporcje obrazu w Inpaint/ADetailer:** Wynik generowania dopasowuje się do wymiarów obrazu wejściowego zamiast wymuszać 512×512.
- **Błąd nieskończonego powiększania ControlNet:** `setMinimumSize(1,1)` + polityka `Expanding` na `cn_preview`.
- **Nieskończone powiększanie ClickableLabel:** Usunięto zbędne `setPixmap(original)` przed `update_scaling()`.
- **Jakość InpaintCanvas:** Dodano `SmoothTransformation` + hint renderowania `SmoothPixmapTransform`.
- **Kontrola sanity `detect_model_type`:** Odrzuca nagłówki >50 MB aby zapobiec OOM.
### Zmieniono
- **Maksymalna rozdzielczość:** Zachowano suwaki 256–2048 (wprowadzone wraz z SDXL, pozostawione po jego usunięciu).
- **Usunięto `detect_model_type()`** – engine zawsze używa pipeline'ów SD 1.5.
- **Logowanie engine** zmienione z polskiego na angielski.
- **`install.bat` przepisany** – dwujęzyczny, bez bloków `if-else`.
### Usunięto
- **Cały kod SDXL:** `StableDiffusionXLPipeline` / `XLInpaint` / `XLControlNet` / `XLImg2Img`, śledzenie `model_type`, `VramWarningDialog`, `_check_vram_warning()`, `_update_model_type_ui()`, `dont_ask_vram` – wszystko usunięte. SDXL powodował ciche zamykanie procesu na 6 GB GPU (`from_single_file()` wychodzi bez błędu przy OOM). Projekt skupia się na SD 1.5, gdzie jest w pełni przetestowany i stabilny.

## [2.18.1] - 2026-05-24 – Skalowanie obrazu i logowanie startowe
### Poprawiono
- **Podgląd Upscale:** Obraz dopasowuje się natychmiast (`ClickableLabel.update_scaling()` wywoływane zaraz po `set_image()`).
- **InpaintCanvas:** Zastąpiono twarde 512×512 funkcją `fitInView()`; dodano `resizeEvent` do ponownego dopasowania przy zmianie rozmiaru okna.
- **Podgląd ControlNet:** Nie jest już skalowany do 512×512 przed wyświetleniem – oryginalna rozdzielczość zachowana.
- **Przełączanie zakładek:** Dodano handler `_on_tab_changed` odświeżający wszystkie podglądy.
- **Zmiana rozmiaru okna:** Podglądy ADetailer i ControlNet teraz aktualizowane (brakowało ich w `MainWindow.resizeEvent`).
### Dodano
- **Logowanie startowe:** Komunikaty `[STARTUP]` i `[UI]` pokazują każdy krok inicjalizacji.
### Poprawiono
- **Kolor akcentu:** Każdy motyw ma domyślny akcent zamiast globalnego #00d4ff. W ustawieniach checkbox "Własny akcent" – gdy odznaczony, używa koloru wbudowanego w motyw.
- **Fade-in na zakładkach (usunięty):** `QGraphicsOpacityEffect` powodował znikanie wszystkich kontrolek – przywrócono błyskawiczne przełączanie.
- **Pola Negative:** Wysokość zwiększona z 30→50 px we wszystkich zakładkach (Inpaint, ControlNet, ADetailer, T2I). Tekst placeholdera nie był w pełni widoczny.
- **Marginesy:** Zmniejszony prawy margines w Inpaint i ControlNet z 20→16 px dla lepszego wykorzystania szerokości.

## [2.17.3] - 2026-05-23 – UI Polish
### Dodano
- **7 motywów kolorystycznych:** Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean – wybór w ustawieniach zamiast dark/light. Kolor akcentu niezależny.
- **Gradient w sidebarze:** Płynne przejście koloru zamiast płaskiego tła.
- **Cienie na panelach:** Drop shadow na ramce opcji i monitorze zasobów – głębia i warstwy.
- **Pulsująca ramka podczas generowania:** Live preview pulsuje kolorem akcentu w trakcie pracy.
- **Fade-in przy przełączaniu zakładek:** Delikatne pojawianie się treści (QGraphicsOpacityEffect).
- **Animowany progress bar:** Płynne wypełnianie zamiast skoków (QPropertyAnimation + easing).
- **Efekty hover:** Gradient na GenerateBtn, podświetlenie na checkboxach/sliderach/listach.
- **Zakładka About w ustawieniach:** Informacje o aplikacji, środowisku, GPU, linki i licencja z użyciem koloru akcentu.
- **Scrollbary w dark/light theme:** Cienkie 8px, stylowane na kolor tła.
- **Separatory w sidebarze:** Cienkie linie między sekcjami Model/VAE, Sampling, LoRA, Upscaler.
- **Grupowanie opcji:** `check_auto` i `check_vram` objęte subtelną ramką.
### Poprawiono
- **Progress bary:** Wysokość 4→8px, zaokrąglone rogi.
- **Tryb jasny:** Usunięty – wszystkie motywy są dark.
- **Panel ustawień:** Szerokość min. zwiększona z 600→920 px.
- **Klucze locale:** `sidebar_monitor`, `settings_tab_about` dodane w obu językach.
- **Tytuł okna:** `Swift Diffusion v2.17.3`.

## [2.17.2] - 2026-05-23 – Bezpieczeństwo i porządki
### Poprawiono
- **6x `except:` → `except Exception:`** w `main.py`, `models_registry.py`, `worker.py` – zapobiega połykaniu `KeyboardInterrupt`/`SystemExit`.
### Usunięto
- **Martwy kod:** `import requests` z `widgets.py`, `translator` z importu w `main.py`, `ImageModelDescriptor` z `engine.py`.
- **Klasa `SourceSearchPanel`** (~260 linii) – nieużywana, zastąpiona nowym URL Downloaderem.

## [2.17.1] - 2026-05-23 – Naprawa krytycznych błędów (crash na starcie)
### Poprawiono
- **Brakujące metody:** Dodano `refresh_base_models`, `refresh_vae_models`, `refresh_upscalers`, `browse_model`, `add_lora_dialog`, `open_settings`, `apply_settings_ui`, `refresh_all_comboboxes`, `refresh_inpaint_models`, `explicit_load_inpaint_model`, `refresh_cn_models`.
- **Brakujące zakładki:** Galeria i Downloader przywrócone w `init_ui`.
- **Brakujące elementy ADetailer:** Dodano `adet_prompt`, `adet_neg`, `v_adet_in`, `v_adet_out`, `adet_progress`.
- **`__init__`:** `apply_settings_ui()`, `refresh_gallery()`, timer i `showMaximized()` były tylko w bloku `is_first_run` – przywrócone.
- **Import `get_style`:** Przywrócony (usunięty podczas audytu).
- **Klucze locale:** Dodano `label_result`, `dlg_select_model`, `dlg_select_lora`.

## [2.17.0] - 2026-05-23 – Nowa funkcjonalność
### Dodano
- **URL Downloader (`url_downloader.py`):** Nowy system pobierania modeli przez wklejenie linku (CivitAI / HuggingFace). Parsuje URL, pobiera metadata przez REST API, automatycznie kategoryzuje (LoRA→models_lora, VAE→models_vae, ControlNet→models_controlnet), strumieniowo pobiera z throttlingiem 0.15s.
- **Zintegrowane wyszukiwanie:** Wyszukiwarka w zakładce Downloader przeszukująca równocześnie CivitAI + HuggingFace API, wyniki w QTreeWidget (Name, Source, Arch, Type, Author), kliknięcie → wypełnia URL → auto-analiza.
- **Szperacz (zakładka Browse):** Eksperymentalna zakładka używająca `duckduckgo_search` + fallback do API. Przycisk "Send to Downloader" przekazuje URL do zakładki pobierania.
- **Przycisk "Open in browser":** W panelu informacji o modelu otwiera URL modelu w przeglądarce.
### Poprawiono
- **CivitAI pagination:** Zmiana z `page` na `cursor` – API blokuje `page` przy `query`.
- **Timeout CivitAI/HF:** Zwiększony z 15s do 30s dla fetch API, 60s dla stream downloadu.
- **Przyciski Generowania:** Wyłączone do momentu załadowania modelu (`_disable_until_model_loaded`).

## [2.16.0] - 2026-05-21
### Dodano
- **Asynchroniczne Ładowanie Modelu:** Modele główne i LoRA są teraz wczytywane w tle, co zapobiega zamarzaniu interfejsu (GUI).
- **Monitor Zasobów:** Interaktywny panel boczny wyświetlający realne zużycie VRAM, RAM oraz obciążenie i temperaturę GPU (NVIDIA).
- **Pasek Postępu Ładowania:** Animowany, minimalistyczny wskaźnik pracy w tle przy ładowaniu modelu.
### Poprawiono
- **Płynność UI:** Odblokowanie wątku głównego podczas ciężkich operacji dyskowych.

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

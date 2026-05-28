# Changelog

## [2.20.9] - 2026-05-26 – CLIP Interrogator, zależność hf_xet
### Dodano
- **Zakładka CLIP Interrogator** — reverse engineering promptu z dowolnego obrazu. Załaduj modele ViT-B/32 lub ViT-L/14 przez przycisk Download, następnie analizuj obraz, aby otrzymać ranking dopasowanych terminów w 8 kategoriach (jakość, kolory, medium, artysta, styl, oświetlenie, efekty, kompozycja). Kopiuj wynik do Text2Image jednym kliknięciem.
- **Baza kandydatów CLIP** — `clip_data/candidates.json` z ~120 terminami w 8 kategoriach. Obsługuje własne pliki `.json` dla niestandardowych kandydatów.
- **Dynamiczne wykrywanie formatu CLIP** — `ClipDownloadWorker` używa `HfApi.list_repo_files` do sprawdzenia obecności `.safetensors`; pobiera tylko format PyTorch (safetensors lub bin) + configi, pomija Flax/TF.
- `hf_xet==1.1.1` do `requirements.txt` — przyspiesza pobieranie z HuggingFace Hub poprzez protokół Xet dla dużych plików (modele, LoRA, ControlNet).

## [2.20.8] - 2026-05-25 – Batch generation, tryb sekwencyjny, galeria miniatur
### Dodano
- **Batch generation** — QSpinBox (1–10) nad przyciskiem Generuj. Generuje N obrazów sekwencyjnie, każdy z innym seedem. Pasek postępu pokazuje postęp per-item z etykietą "Batch 2/3...".
- **Pasek miniatur batcha** — po zakończeniu wszystkich obrazów batcha, przewijany `BatchThumbnailBar` (miniatury 100 px) pojawia się pod paskiem postępu. Kliknij miniaturę, aby zobaczyć odpowiedni surowy obraz (przed upscalem) w lewym panelu i wersję po upscale (jeśli auto upscale był włączony) w prawym panelu.
- **Sekwencyjny upscale per-item** — gdy auto upscale jest włączony, każdy obraz batcha jest powiększany natychmiast po wygenerowaniu. Miniatura pokazuje końcowy wynik po upscale.
- **Podział przed/po** — `v_orig` pokazuje zawsze obraz przed upscalem, `v_ups` wersję po upscale (ukryty jeśli auto upscale wyłączony). Działa zarówno dla batch=1 jak i batch>1.
- Klucze locale: `batch_label`, `batch_tooltip`, `batch_thumbnails` (EN + PL).

## [2.20.7] - 2026-05-25 – Prompt Builder: wyszukiwarka tagów i zakładka Wildcards
### Dodano
- **Wyszukiwarka tagów** — `QLineEdit` z przyciskiem czyszczenia między obszarem tagów a Style Presets. Wpisywanie filtruje wszystkie przyciski tagów pozytywnych i negatywnych na dedykowanej stronie wyników w `QStackedWidget`. Kliknięcie wyniku przełącza zarówno oryginalny przycisk, jak i przycisk wyszukiwania. Etykieta gdy brak wyników.
- **Zakładka Wildcards** — nowa kategoria w wewnętrznym `QTabWidget` Prompt Buildera (między Embeddings a wyszukiwarką). Każdy plik `.txt` w `wildcards/` staje się klikalnym przyciskiem. Kliknięcie przełącza `__nazwa__` w `_selected` (widoczne w podglądzie). Tooltip pokazuje pierwsze 5 linii pliku. Wybrane wildcardy są zachowywane przy `refresh_tags()`. Pomijane przez przycisk Losuj i wyszukiwarkę.
- **Obserwator wildcardów** — `QFileSystemWatcher` na `wildcards/` automatycznie odświeża zakładkę przy zmianach plików.
- **Wildcardy w historii/ulubionych** — `_set_tags()` przywraca wpisy `__nazwa__` z zapisanych promptów. `_clear_all()` resetuje przyciski wildcardów.
- Klucze locale: `tag_search_placeholder`, `tag_search_no_results`, `pb_wildcards`, `pb_wildcards_empty` (EN + PL).

## [2.20.6] - 2026-05-25 – Style Presets, podgląd obok siebie, presety ekskluzywne, zmiana struktury plików
### Dodano
- **Style Presets** — `QGroupBox("Style Presets")` poniżej zakładek z przyciskami presetów jednym kliknięciem. Każdy preset w osobnym pliku `tags/presets/{nazwa}.json` z formatem `{"name": "...", "icon": "🎬", "tags": [...]}`. Nowy plik → nowy preset natychmiast przez `QFileSystemWatcher`. 6 wbudowanych presetów.
- **Presety ekskluzywne** — `_active_preset` śledzi aktywny preset; kliknięcie innego zastępuje poprzedni; kliknięcie tego samego odznacza.
- **Podgląd obok siebie** — pola QTextEdit dla pozytywnych i negatywnych tagów umieszczone obok siebie (50/50, oba 70px stała wysokość) zamiast pionowo.
- **Tagi bez kategorii** — tagi presetów dodawane do `_selected` nawet jeśli nie mają przycisku w kategoriach (pojawiają się w podglądzie).
- **Folder `tags/presets/`** monitorowany przez `QFileSystemWatcher`.
- Klucz locale: `pb_presets` (EN + PL).
### Zmieniono
- **Struktura presetów** — `tags/presets.json` zastąpiony folderem `tags/presets/` z jednym plikiem na preset. `_load_presets()` skanuje folder zamiast czytać jeden plik.

## [2.20.5] - 2026-05-25 – Prompt Builder: tagi negatywne, rozszerzona historia/ulubione, przycisk losowania
### Dodano
- **Tagi negatywne** — osobna kategoria w górnym QTabBar (czerwone przyciski). `tags/negative.json` z 30 tagami.
- **Dwa pola podglądu** — pozytywne i negatywne QTextEdit ułożone pionowo (oba stała wysokość 60px).
- **Historia/Ulubione przechowują negative_tags** — wstecznie kompatybilne przez `.get("negative_tags", [])`. Wczytywanie przywraca oba zestawy tagów.
- **🎲 Przycisk Losuj** — losuje konfigurowalną liczbę tagów na kategorię (Ustawienia → Prompt Builder → "Losowych tagów na kategorię", QSpinBox 1–5, domyślnie 1). Śledzi wylosowane tagi w `_random_selected`; drugie kliknięcie zastępuje zestaw.
- **Sygnał `neg_prompt_ready`** — Kopiuj do Text2Image kopiuje również tagi negatywne do pola negative prompt.
- Klucze locale: `pb_random`, `pb_random_count`, `settings_tab_pb` (EN + PL).
### Zmieniono
- **Układ Prompt Buildera** — przyciski tagów negatywnych przeniesione z osobnego panelu na dole do głównego QTabBar obok Quality, Style, Lighting, Artists. Podgląd negatywny zawsze widoczny.
- **Pojedynczy przycisk Kopiuj** kopiuje jednocześnie pozytywny i negatywny prompt.

## [2.20.4] - 2026-05-24 – Prompt Builder: historia i ulubione
### Dodano
- **Historia promptów** — każde kliknięcie "Kopiuj do Text2Image" zapisuje zaznaczone tagi do `prompts_history.json` (max 20, najnowsze na górze). Przycisk "📜 Historia" otwiera dialog z akcjami Wczytaj/Kopiuj.
- **Ulubione prompty** — "★ Zapisz" zapisuje obecne tagi z własną nazwą do `prompts_favorites.json` (bez limitu). "★ Ulubione" pokazuje wszystkie zapisane presety z akcjami Wczytaj/Kopiuj/Usuń.
- Klucze locale: `pb_history`, `pb_history_load`, `pb_history_empty`, `pb_favorites`, `pb_fav_save`, `pb_fav_name`, `pb_fav_saved`, `pb_fav_load`, `pb_fav_delete`, `pb_fav_empty` (EN + PL).
### Zmieniono
- **Prompt Builder → T2I** — `_on_prompt_ready()` teraz **nadpisuje** pole promptu zamiast scalać.
- **`install.bat`** — walidacja Pythona 3.12 przez `py -3.12 --version` przed tworzeniem venv; używa `py -3.12 -m venv` zamiast `python -m venv`; wyświetla link do pobrania w razie braku.

## [2.20.3] - 2026-05-24 – Refactor phase 3: ekstrakcja kontrolerów generacji i trybów
### Zmieniono
- **`generation_controller.py`** — nowa klasa `GenerationController` obsługująca T2I/Img2Img, upscaling, animację podglądu, zarządzanie seedem (~180 linii).
- **`mode_controllers.py`** — nowe klasy `InpaintController`, `ControlNetController`, `ADetailerController` obsługujące generację, ładowanie obrazów i wyniki dla każdego trybu (~210 linii).
- **`main.py`** zredukowany z 536→317 linii (**-41%**, **-64%** od 881 linii przed refaktorem).
- Wszystkie połączenia przycisków przekierowane przez kontrolery.
- Wyczyszczono nieużywane importy (`logging`, `qimage_to_pil`, `UrlDownloaderTab`, klasy workerów).

## [2.20.2] - 2026-05-24 – Refactor phase 2: ekstrakcja boot, monitora, managera modeli
### Zmieniono
- **`boot.py`** wyodrębniony z `main.py` — health check CUDA + test torch w subprocess przy imporcie.
- **`widgets/resource_monitor.py`** — nowa klasa `ResourceMonitor(QWidget)` z własnym timerem, NVML init/shutdown, zastępuje inline kod monitora w `MainWindow` (~60 linii mniej).
- **`model_manager.py`** — nowa klasa `ModelManager` obsługująca ładowanie modeli, skanowanie, odświeżanie, LoRA, file watchery i stan przycisków (~240 linii przeniesionych z `MainWindow`).
- **`main.py`** zredukowany z 881→536 linii (**-39%**).
### Poprawiono
- **Import `QGraphicsDropShadowEffect`** — był w `PyQt6.QtGui`, należy do `PyQt6.QtWidgets`.
- **Import `QFileSystemWatcher`** — był w `PyQt6.QtWidgets`, należy do `PyQt6.QtCore`.

## [2.20.1] - 2026-05-24 – Refactor phase 1: podział widgets.py na pakiet
### Zmieniono
- **`widgets.py` (1297 linii) podzielony na pakiet `widgets/`** z 6 modułami: `dialogs.py`, `inpaint_canvas.py`, `widgets_common.py`, `model_downloader.py`, `flow_layout.py`, `prompt_builder.py` + `__init__.py` re-eksportujacy wszystkie klasy.
- **Zero zmian w `main.py`, `engine.py`, `worker.py`, `config.py`** – wszystkie importy zachowane przez `__init__.py`.
### Poprawiono
- **Brakujący import `QRect`** w `widgets_common.py` powodujący `NameError` w `LoRAVisualizer.paintEvent`.

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

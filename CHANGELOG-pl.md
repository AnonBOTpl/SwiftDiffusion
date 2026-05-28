# Changelog

## [2.20.9] - 2026-05-26 – CLIP Interrogator, zależność hf_xet
### Dodano
- **Zakładka CLIP Interrogator** — reverse engineering promptu z dowolnego obrazu. Załaduj modele ViT-B/32 lub ViT-L/14 przez przycisk Download, następnie analizuj obraz, aby otrzymać ranking dopasowanych terminów w 8 kategoriach (jakość, kolory, medium, artysta, styl, oświetlenie, efekty, kompozycja). Kopiuj wynik do Text2Image jednym kliknięciem.
- **Baza kandydatów CLIP** — `clip_data/candidates.json` z ~120 terminami w 8 kategoriach. Obsługuje własne pliki `.json` dla niestandardowych kandydatów.
- **Dynamiczne wykrywanie formatu CLIP** — `ClipDownloadWorker` używa `HfApi.list_repo_files` do sprawdzenia obecności `.safetensors`; pobiera tylko format PyTorch (safetensors lub bin) + configi, pomija Flax/TF.
- `hf_xet==1.1.1` do `requirements.txt` — przyspiesza pobieranie z HuggingFace Hub poprzez protokół Xet dla dużych plików (modele, LoRA, ControlNet).
### Naprawiono
- **Zbyt krótki timeout CUDA w boot.py** — zwiększony timeout subprocesu z 15s do 45s i timeout wątku health-check z 8s do 30s. Pierwszy `import torch` na świeżym systemie/sterowniku może trwać 20+ sekund, co powodowało fałszywy błąd "GPU driver in bad state".
- **Nadmiarowe zależności compel** — `compel` miał `notebook` w `Requires`, ciągnąc cały ekosystem JupyterLab (~40 pakietów). Usunięto `compel` z `requirements.txt`; `install.bat` instaluje go teraz z `--no-deps`.

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
- **Wildcards w historii/ulubionych** — `_set_tags()` wykrywa wzór `__nazwa__` i przywraca przez `_toggle_wildcard()` zamiast `_toggle_tag()`.
- Klucze locale: `pb_wildcards`, `pb_wildcards_empty`, `pb_search_placeholder` (EN + PL).

## [2.20.6] - 2026-05-24 – Style Presets, podgląd obok siebie
### Dodano
- **Style Presets** — katalog `tags/presets/` z jednym plikiem `.json` na preset. 6 wbudowanych presetów (cinematic, anime, oil painting, photography, dark fantasy, watercolor). Ekskluzywne przełączanie przez `_active_preset`.
- **Podgląd obok siebie** — dwa `QTextEdit` w `QHBoxLayout` (50/50, fixedHeight 70 px). Pozytywny po lewej, negatywny po prawej z czerwoną ramką.
- **Poprawka RuntimeError** — wszystkie `btn.setChecked()` w `_clear_all` i `_randomize` owinięte w `try/except RuntimeError` dla usuniętych obiektów C++ po `refresh_tags()`.
- **Zakładka Embeddings odtwarzana w `refresh_tags()`** — `_emb_page` + `_emb_flow` budowane od nowa, aby zapobiec błędom usuniętych obiektów C++.
- **Obsługa negatywnych w `_set_tags()`** — `_set_tags()` przywraca teraz również negatywne tagi z historii/ulubionych.

## [2.20.5] - 2026-05-24 – Negatywne tagi, przycisk Losuj, własne kategorie
### Dodano
- **Negatywne tagi** — `tags/negative.json` z 30 tagami. Osobna lista `_neg_selected`, mapa `_tag_btns_neg`, sygnał `neg_prompt_ready`.
- **Wsparcie negatywnych w historii/ulubionych** — oba przechowują pole `negative_tags` na wpis; `.get("negative_tags", [])` wsteczna kompatybilność; Load przywraca oba zestawy.
- **🎲 Przycisk Losuj** — lista `_random_selected`; konfigurowalna liczba tagów na kategorię przez `settings.get('PromptBuilder','random_tags_count', fallback='1')` (QSpinBox 1–5 w Settings → Prompt Builder).
- **Własne kategorie tagów** — `_load_tags()` używa ustalonej kolejności wbudowanych (quality→style→lighting→artists) + pliki użytkownika alfabetycznie; `QFileSystemWatcher` na `tags/` wyzwala `refresh_tags()`.
- Klucze locale: `pb_negative`, `pb_neg_color`, `pb_random`, `pb_random_label` (EN + PL).

## [2.20.4] - 2026-05-24 – Prompt Builder: historia i ulubione
### Dodano
- **Historia promptów** — każde "Kopiuj do Text2Image" zapisuje wybór tagów do `prompts_history.json` (max 20, najnowsze pierwsze). Przycisk "📜 Historia" otwiera QDialog z akcjami Wczytaj/Kopiuj.
- **Ulubione prompty** — przycisk "★ Zapisz" zapisuje bieżące tagi z nazwą do `prompts_favorites.json` (bez limitu). Okno "★ Ulubione" pokazuje wszystkie zapisane z akcjami Wczytaj/Kopiuj/Usuń.
- Klucze locale: `pb_history`, `pb_history_title`, `pb_favorites`, `pb_fav_title`, `pb_save_fav`, `pb_fav_name`, `pb_load`, `pb_copy`, `pb_delete`, `pb_no_history`, `pb_no_fav` (EN + PL).

## [2.20.3] - 2026-05-24 – Refactor phase 3: wydzielenie kontrolerów
### Zmieniono
- Wydzielono `generation_controller.py` (~180 linii) — orkiestracja T2I/Img2Img/Upscale oddzielona od głównego okna.
- Wydzielono `mode_controllers.py` (~210 linii) — kontrolery Inpaint, ControlNet, ADetailer.
- `main.py` zmniejszone z 536 do 317 linii (-41%, -64% z 881).
- Wszystkie połączenia przycisków idą przez kontrolery.
- Usunięto nieużywane importy i `UrlDownloaderTab`.
- Oczyszczono import `qimage_to_pil`.

## [2.20.2] - 2026-05-24 – Refactor phase 2: boot, ResourceMonitor, ModelManager
### Zmieniono
- `boot.py`, `ResourceMonitor`, `ModelManager` wydzielone z `main.py`.
- `main.py` zmniejszone z 881 do 536 linii (-39%).
- Dodano czyszczenie VRAM w ścieżce błędu `on_model_loaded()`.

## [2.20.1] - 2026-05-24 – Refactor phase 1: podział widgets package
### Zmieniono
- `widgets.py` (1297 linii) podzielone na pakiet `widgets/` z 6 modułami + `__init__.py`.

## [2.20.0] - 2026-05-24 – Wildcards, Tiled VAE, Prompt weighting, Textual Inversion
### Dodano
- **Wildcards** — folder `wildcards/` z 4 przykładowymi plikami `.txt`; `resolve_wildcards()` regex `__word__` → losowa linia; wywoływane we wszystkich 5 workerach dla prompt + neg_prompt.
- **Tiled VAE** — checkbox w Ustawienia → Wydajność, niezależny od VRAM Slicing.
- **Prompt weighting (compel)** — `_encode_prompt()` z try/except fallback; warunkowe `prompt_embeds=` / `negative_prompt_embeds=` w 5 miejscach wywołania pipeline'u.
- **Embeddingi Textual Inversion** — skanowanie `models/embeddings/` dla `.pt`/`.bin`/`.safetensors`; ładowane po modelu; dynamiczna zakładka "Embeddings" w Prompt Builder z `QFileSystemWatcher` auto-odświeżaniem.

## [2.19.0] - 2026-05-24 – Usunięto VramWarningDialog, czyszczenie SDXL
### Usunięto
- Klasy pipeline'ów SDXL, VramWarningDialog, `_check_vram_warning()`, klucz konfiguracyjny `dont_ask_vram`.
- Ścieżki wag XL i obsługa skali LoRA.

## [2.18.3] - 2026-05-23 – Przycisk Stop, czyste zamykanie
### Dodano
- **Przycisk Stop** dla wszystkich zakładek generowania — każdy przycisk Generuj zmienia się w "STOP" (czerwony). `engine._stop_flag` sprawdzane w callbackach postępu; `RuntimeError("STOPPED")` łapane w workerach.
- **Czyste zamykanie** — `closeEvent` wywołuje `engine._clear_vram()` a następnie `resource_monitor.shutdown()`.
- **Poprawka proporcji Inpaint/ADetailer** — szerokość/wysokość z wymiarów obrazu wejściowego (zaokrąglone w dół do wielokrotności 8).

## [2.18.2] - 2026-05-23 – Poprawka ControlNet infinite-enlarge, podzielone podglądy
### Naprawiono
- ControlNet preview `setMinimumSize(1,1)` + `setSizePolicy(Expanding, Expanding)` aby zapobiec nieskończonemu powiększaniu.
### Zmieniono
- Inpaint podzielony podgląd: lewo = canvas_scroll (maska), prawo = v_inpaint_out (wynik).
- ControlNet podzielony podgląd: lewo = cn_preview (referencja), prawo = v_cn_out (wynik).
- Usunięto podgląd ImageViewer z handlerów zakończenia generowania.

## [2.18.1] - 2026-05-22 – Poprawka skalowania obrazów
### Naprawiono
- `ClickableLabel` + `InpaintCanvas` prawidłowe skalowanie w `resizeEvent`.
- Podglądy ADetailer/ControlNet w `resizeEvent`.
- Brakujący handler `_on_tab_changed` podłączony.

## [2.18.0] - 2026-05-22 – Locale, log, skalowanie, CUDA health check
### Dodano
- I18n: ~80 nowych kluczy w obu plikach locale (batch + clip).
- Logowanie silnika zmienione z polskiego na angielski.
- Logowanie uruchamiania: dodano znaczniki `[STARTUP]` i `[UI]`.
- CUDA health check przy starcie: subproces z 15s timeoutem testuje `import torch` + CUDA.
- Zwiększono maksymalną rozdzielczość: suwaki szerokości/wysokości 256–2048.
- `detect_model_type` sanity check: `header_len > 50 MB` zwraca `"sd15"`.

## [2.17.3] - 2026-05-22 – 7 ciemnych motywów, efekty wizualne
### Dodano
- 7 ciemnych motywów: Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean — każdy z 12 kolorami + gradientem sidebaru.
- Usunięto tryb jasny.
- Efekty wizualne: cienie, pulsująca ramka na live preview, płynny pasek postępu, gradient na GenerateBtn, stany hover, stylowane scrollbary.
- Domyślny kolor akcentu per-motyw.
- Zakładka About, okno Settings poszerzone do 920 px, paski postępu 8 px, monitor w sidebarze.
- WelcomeDialog zaktualizowany dla 7 motywów.
- `install.bat` przepisany dwujęzycznie.
- `start.bat` uproszczony — tylko angielski, usunięto `taskkill`.

## [2.17.2] - 2026-05-22 – Naprawy crashy
### Naprawiono
- Przywrócono brakujące metody, elementy UI, `__init__`.
- Naprawiono `except:` → `except Exception:`.
- Usunięto martwy kod.

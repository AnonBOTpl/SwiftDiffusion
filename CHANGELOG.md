# Changelog

## [2.20.9] - 2026-05-26 – CLIP Interrogator, hf_xet dependency
### Added
- **CLIP Interrogator tab** — reverse-engineer prompts from any image. Load ViT-B/32 or ViT-L/14 models via Download button, then analyze an image to get ranked matching terms across 8 categories (quality, colors, medium, artist, style, lighting, effects, composition). Copy result to Text2Image with one click.
- **CLIP candidate database** — `clip_data/candidates.json` with ~120 curated terms across 8 categories. Supports user-provided `.json` files for custom candidates.
- **Dynamic CLIP format detection** — `ClipDownloadWorker` uses `HfApi.list_repo_files` to check for `.safetensors`; downloads only PyTorch format (safetensors or bin) + configs, skips Flax/TF.
- `hf_xet==1.1.1` to `requirements.txt` — accelerates HuggingFace Hub downloads with the Xet protocol for large files (models, LoRAs, ControlNet).
### Fixed
- **boot.py CUDA timeout too short** — increased subprocess timeout from 15s to 45s and health-check thread timeout from 8s to 30s. First `import torch` on a fresh system/driver can take 20+ seconds, causing a false "GPU driver in bad state" error.

## [2.20.8] - 2026-05-25 – Batch generation, sequential mode, thumbnail gallery
### Added
- **Batch generation** — QSpinBox (1–10) above the Generate button. Generates N images sequentially, each with a different seed. Progress bar shows per-item progress with "Batch 2/3..." label.
- **Batch thumbnail bar** — after all batch items complete, a scrollable `BatchThumbnailBar` (100 px thumbnails) appears below the progress bar. Click any thumbnail to view the corresponding raw (pre-upscale) image in the left panel and the upscaled version (if auto upscale was on) in the right panel.
- **Sequential upscale per item** — when auto upscale is enabled, each batch item is upscaled immediately after generation. The thumbnail shows the final upscaled result.
- **Before/after split preview** — `v_orig` now always shows the pre-upscale raw image, `v_ups` shows the upscaled version (hidden if auto upscale is off). Works for both batch=1 and batch>1.
- Locale keys: `batch_label`, `batch_tooltip`, `batch_thumbnails` (EN + PL).

## [2.20.7] - 2026-05-25 – Prompt Builder: tag search & wildcards tab
### Added
- **Tag search** — `QLineEdit` with `setClearButtonEnabled(True)` between tag area and Style Presets. Typing filters all positive and negative tag buttons into a dedicated search results page in `QStackedWidget`. Clicking a search result toggles both the original button and the search button in sync. No-results label when nothing matches.
- **Wildcards tab** — new category tab in Prompt Builder's internal `QTabWidget` (between Embeddings and search). Each `.txt` file in `wildcards/` becomes a checkable button. Clicking toggles `__name__` in `_selected` (appears in preview). Tooltip shows first 5 lines of the file. Selected wildcards are preserved across `refresh_tags()`. Skip by Random button and tag search.
- **Wildcards watcher** — `QFileSystemWatcher` on `wildcards/` auto-rebuilds the tab when files change.
- **Wildcards in history/favorites** — `_set_tags()` restores `__name__` entries from saved prompts. `_clear_all()` resets wildcard buttons.
- Locale keys: `tag_search_placeholder`, `tag_search_no_results`, `pb_wildcards`, `pb_wildcards_empty` (EN + PL).

## [2.20.6] - 2026-05-25 – Style Presets, side-by-side preview, exclusive presets, refactored file structure
### Added
- **Style Presets** — `QGroupBox("Style Presets")` below tag tabs with one-click preset buttons. Each preset lives in its own file under `tags/presets/{name}.json` with format `{"name": "...", "icon": "🎬", "tags": [...]}`. Drop a new file → new preset appears instantly via `QFileSystemWatcher`. 6 built-in presets.
- **Exclusive presets** — `_active_preset` tracking: selecting a new preset replaces the previous one; clicking the same preset deselects it.
- **Side-by-side preview** — positive and negative QTextEdit fields placed next to each other (50/50 split, both 70px fixed height) instead of stacked vertically.
- **Unguarded tags** — preset tags are added to `_selected` even if no corresponding button exists in the tag categories (they still appear in the preview).
- **`tags/presets/` directory** watched by `QFileSystemWatcher` alongside `tags/`.
- Locale key: `pb_presets` (EN + PL).
### Changed
- **Preset file structure** — `tags/presets.json` replaced by `tags/presets/` folder with one file per preset. `_load_presets()` scans the directory instead of reading a single file.

## [2.20.5] - 2026-05-25 – Prompt Builder: negative tags, history/favorites extended, random button
### Added
- **Negative tags** — separate tab category in the top QTabBar (red-styled buttons). `tags/negative.json` with 30 tags.
- **Two-preview layout** — positive and negative QTextEdit fields stacked (both 60px fixed height).
- **History/Favorites now store negative_tags** — backward-compatible with old entries via `.get("negative_tags", [])`. Load restores both positive and negative tag sets.
- **🎲 Random button** — picks user-configurable number of tags per category (Settings → Prompt Builder → "Random tags per category", QSpinBox 1–5, default 1). Tracks random tags in `_random_selected`; second click replaces the set.
- **`neg_prompt_ready` signal** — Copy to Text2Image now also copies negative tags to the T2I negative prompt field.
- Locale keys: `pb_random`, `pb_random_count`, `settings_tab_pb` (EN + PL).
### Changed
- **Prompt Builder layout** — negative tag buttons moved from a separate bottom panel into the main QTabBar alongside Quality, Style, Lighting, Artists. Negative preview is always visible.
- **Single Copy button** copies both positive and negative prompts simultaneously.

## [2.20.4] - 2026-05-24 – Prompt Builder: history & favorites
### Added
- **Prompt history** — every "Copy to Text2Image" saves the tag selection to `prompts_history.json` (max 20, newest first). "📜 History" button opens a dialog with Load/Copy actions.
- **Prompt favorites** — "★ Save" saves current tags with a custom name to `prompts_favorites.json` (no limit). "★ Favorites" dialog shows all saved presets with Load/Copy/Delete actions.
- Locale keys: `pb_history`, `pb_history_load`, `pb_history_empty`, `pb_favorites`, `pb_fav_save`, `pb_fav_name`, `pb_fav_saved`, `pb_fav_load`, `pb_fav_delete`, `pb_fav_empty` (EN + PL).
### Changed
- **Prompt Builder → T2I** — `_on_prompt_ready()` now **replaces** the T2I prompt instead of appending.
- **`install.bat`** — validates Python 3.12 via `py -3.12 --version` before creating venv; uses `py -3.12 -m venv` instead of `python -m venv` to ensure correct version; shows download link if missing.

## [2.20.3] - 2026-05-24 – Refactor phase 3: extract generation & mode controllers
### Changed
- **`generation_controller.py`** — new `GenerationController` class handling T2I/Img2Img generation, upscaling, preview animation, seed management (~180 lines).
- **`mode_controllers.py`** — new `InpaintController`, `ControlNetController`, `ADetailerController` classes handling each mode's generation, image loading, and results (~210 lines total).
- **`main.py`** reduced from 536→317 lines (**-41%**, **-64%** from pre-refactor 881 lines).
- All button connections (`btn_gen_t2i`, `btn_gen_inp`, `btn_gen_cn`, `btn_gen_adet`, `btn_up`, `btn_copy`, `btn_face`, `btn_to_inpaint`, `btn_load_i`, `btn_load_cn`, `btn_load_adet`) now routed through controllers.
- Unused imports cleaned up (`logging`, `qimage_to_pil`, `UrlDownloaderTab`, worker classes).

## [2.20.2] - 2026-05-24 – Refactor phase 2: extract boot, resource monitor, model manager
### Changed
- **`boot.py`** extracted from `main.py` — CUDA health check + subprocess torch test run at import time, keeps `main.py` clean.
- **`widgets/resource_monitor.py`** — new `ResourceMonitor(QWidget)` class with own timer, NVML init/shutdown, replacing inline monitor code in `MainWindow` (~60 lines removed).
- **`model_manager.py`** — new `ModelManager` class handling model loading, scanning, refresh, LoRA management, file watchers, and generate button state (~240 lines moved out of `MainWindow`).
- **`main.py`** reduced from 881→536 lines (**-39%**).
### Fixed
- **`QGraphicsDropShadowEffect`** import — was in `PyQt6.QtGui`, belongs in `PyQt6.QtWidgets`.
- **`QFileSystemWatcher`** import — was in `PyQt6.QtWidgets`, belongs in `PyQt6.QtCore`.

## [2.20.1] - 2026-05-24 – Refactor phase 1: widgets.py split into package
### Changed
- **`widgets.py` (1297 lines) split into `widgets/` package** with 6 modules: `dialogs.py`, `inpaint_canvas.py`, `widgets_common.py`, `model_downloader.py`, `flow_layout.py`, `prompt_builder.py` + `__init__.py` re-exporting all classes.
- **Zero changes to `main.py`, `engine.py`, `worker.py`, `config.py`** – all imports preserved via `__init__.py`.
### Fixed
- **Missing `QRect` import** in `widgets_common.py` causing `NameError` in `LoRAVisualizer.paintEvent`.

## [2.20.0] - 2026-05-24 – Wildcards, Tiled VAE, Prompt Builder, Prompt weighting (compel), Textual Inversion embeddings
### Added
- **Wildcards:** `__token__` syntax replaced with a random line from `wildcards/token.txt`. Tooltip near prompt fields explains usage.
- **Tiled VAE:** New checkbox in Settings → Performance, independent from VRAM Slicing. `enable_tiling()` / `disable_tiling()` applied separately.
- **Prompt Builder:** Dedicated tab with `FlowLayout` and toggleable tag buttons loaded from `tags/*.json`. Preview pane + "Copy to Text2Image" button. Categories: quality, style, lighting, artists.
- **Prompt weighting (compel):** `compel` library integrated. `_encode_prompt()` with `try/except ImportError` fallback; status label in T2I header shows whether compel is available.
- **Textual Inversion embeddings:** `models/embeddings/` scanned at model load. `_load_embeddings()` + `scan_embeddings()` support `.pt`, `.bin`, `.safetensors`. Dynamic Embeddings tab in Prompt Builder auto-refreshed via `QFileSystemWatcher`.
- **Embeddings tab tooltip** – hover shows description.
- **Tooltip on Prompt Builder Embeddings tab** and merged empty-state message for clarity.
### Fixed
- **Missing newline in `widgets.py`** causing `SyntaxError` during import.

## [2.19.0] - 2026-05-24 – Stop button, split previews, aspect ratio fix, SDXL removed
### Added
- **Stop button for all tabs:** Each generate button toggles to "STOP" (red) when running; clicking stops generation mid-way.
- **Inpaint split preview:** Left = mask editor, right = result (was popup-only).
- **ControlNet split preview:** Left = reference image, right = result (was popup-only).
- **Clean shutdown:** Closing the window clears VRAM before exit.
- **CUDA health check at boot:** Subprocess test before importing engine (prevents hang on stuck GPU driver).
- **`btn_stop` key** in EN/PL locale files.
### Fixed
- **Inpaint/ADetailer aspect ratio:** Output now matches input image dimensions instead of forcing 512×512.
- **ControlNet infinite-enlarge bug:** `setMinimumSize(1,1)` + `Expanding` policy on `cn_preview`.
- **ClickableLabel infinite enlargement:** Removed redundant `setPixmap(original)` before `update_scaling()`.
- **InpaintCanvas quality:** `SmoothTransformation` + `SmoothPixmapTransform` render hint.
- **`detect_model_type` sanity check:** Rejects headers >50 MB to prevent OOM.
### Changed
- **Max resolution sliders** kept at 256–2048 (introduced alongside SDXL support, retained after SDXL removal).
- **`detect_model_type()` removed** – engine always uses SD 1.5 pipelines.
- **Engine logging** changed from Polish to English.
- **`install.bat` rewritten** – bilingual, no `if-else` blocks.

## [2.18.1] - 2026-05-24 – Image scaling & startup logging
### Fixed
- **Upscaled preview:** Image now fits immediately into the preview widget (`ClickableLabel.update_scaling()` called right after `set_image()`), no longer waiting for manual window resize.
- **InpaintCanvas:** Replaced hardcoded 512×512 with `fitInView()` – image fills available space; added `resizeEvent` to re-apply fit on window resize.
- **ControlNet preview:** No longer pre-scaled to 512×512 before display – original resolution preserved in `pixmap_cached`.
- **Tab switching:** Added `_on_tab_changed` handler that refreshes all previews (ClickableLabel + InpaintCanvas).
- **Window resize:** ADetailer and ControlNet previews now updated on resize (were missing from `MainWindow.resizeEvent`).
### Added
- **Startup logging:** `[STARTUP]` and `[UI]` console messages show each initialization step (NVML, engine, folders, watchers, every UI tab).

## [2.18.0] - 2026-05-23 – Theme & UI fixes
### Fixed
- **Accent color:** Each theme now has a built-in default accent instead of a global #00d4ff. Settings checkbox "Custom accent" – when unchecked, uses the theme's default color.
- **Tab fade animation (removed):** `QGraphicsOpacityEffect` caused all tab controls to disappear – reverted to instant tab switching.
- **Negative prompt fields:** Height increased from 30→50 px across all tabs (Inpaint, ControlNet, ADetailer, T2I). Placeholder text was not fully visible.
- **Margins:** Reduced right margin in Inpaint and ControlNet from 20→16 px for better space usage.

## [2.17.3] - 2026-05-23 – UI Polish
### Added
- **7 color themes:** Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean – selectable in settings instead of dark/light toggle. Independent accent color.
- **Sidebar gradient:** Smooth color transition instead of flat background.
- **Panel shadows:** Drop shadow on options frame and resource monitor – depth and layering.
- **Pulsating border on live preview:** Pulsates with accent color during generation.
- **Fade-in on tab switch:** Gentle content reveal (QGraphicsOpacityEffect) – later removed in 2.18.0.
- **Animated progress bar:** Smooth filling instead of jumps (QPropertyAnimation + easing).
- **Hover effects:** Gradient on GenerateBtn, highlights on checkboxes/sliders/lists.
- **About tab in settings:** App info, environment, GPU details, links and license using accent color.
- **Dark/light scrollbars:** Thin 8px, styled to match background color.
- **Sidebar separators:** Thin lines between Model/VAE, Sampling, LoRA, Upscaler sections.
- **Option grouping:** `check_auto` and `check_vram` wrapped in a subtle bordered frame.
### Fixed
- **Progress bars:** Height 4→8px, rounded corners.
- **Light mode:** Removed – all themes are dark-only.
- **Settings panel:** Min width increased from 600→920 px.
- **Locale keys:** `sidebar_monitor`, `settings_tab_about` added in both languages.
- **Window title:** `Swift Diffusion v2.17.3`.

## [2.17.2] - 2026-05-23 – Safety & cleanup
### Fixed
- **6x `except:` → `except Exception:`** in `main.py`, `models_registry.py`, `worker.py` – prevents swallowing `KeyboardInterrupt`/`SystemExit`.
### Removed
- **Dead code:** `import requests` from `widgets.py`, `translator` import in `main.py`, `ImageModelDescriptor` from `engine.py`.
- **`SourceSearchPanel` class** (~260 lines) – unused, replaced by URL Downloader.

## [2.17.1] - 2026-05-23 – Critical startup crash fix
### Fixed
- **Missing methods:** Restored `refresh_base_models`, `refresh_vae_models`, `refresh_upscalers`, `browse_model`, `add_lora_dialog`, `open_settings`, `apply_settings_ui`, `refresh_all_comboboxes`, `refresh_inpaint_models`, `explicit_load_inpaint_model`, `refresh_cn_models`.
- **Missing tabs:** Gallery and Downloader restored in `init_ui`.
- **Missing ADetailer elements:** Added `adet_prompt`, `adet_neg`, `v_adet_in`, `v_adet_out`, `adet_progress`.
- **`__init__`:** `apply_settings_ui()`, `refresh_gallery()`, timer and `showMaximized()` were only in `is_first_run` block – now unconditional.
- **`get_style` import:** Restored (was removed during code audit).
- **Locale keys:** Added `label_result`, `dlg_select_model`, `dlg_select_lora`.

## [2.17.0] - 2026-05-23 – New features
### Added
- **URL Downloader (`url_downloader.py`):** New model download system – paste a CivitAI / HuggingFace link, parses URL, fetches metadata via REST API, auto-categorizes (LoRA→models_lora, VAE→models_vae, ControlNet→models_controlnet), streams download with 0.15s throttling.
- **Integrated search:** Search tab querying CivitAI + HuggingFace simultaneously, results in QTreeWidget (Name, Source, Arch, Type, Author), click → fills URL → auto-analyze.
- **Browse tab:** Experimental tab using `duckduckgo_search` + API fallback. "Send to Downloader" button passes URL to the download tab.
- **"Open in browser" button:** Opens model URL in default browser from the model info panel.
### Fixed
- **CivitAI pagination:** Changed from `page` to `cursor` – API blocks `page` when `query` is set.
- **CivitAI/HF timeout:** Increased from 15s to 30s for API fetch, 60s for stream download.
- **Generate buttons:** Disabled until model is loaded (`_disable_until_model_loaded`).

## [2.16.0] - 2026-05-21
### Added
- **Asynchronous Model Loading:** Main models and LoRAs now load in the background, preventing UI freezes.
- **Resource Monitor:** Interactive sidebar panel showing real-time VRAM, RAM usage, GPU load and temperature (NVIDIA).
- **Loading progress bar:** Animated, minimal indicator for background model loading.
### Fixed
- **UI smoothness:** Main thread unblocked during heavy disk operations.

## [2.15.0] - 2026-05-21
### Added
- **ADetailer module:** Native face enhancement using YOLOv8 detection + inpainting (Zero-Copy VRAM).
- **ADetailer UI:** Dedicated tab with full parameter set (prompt, denoise, dilation, confidence).
- **"Send to ADetailer" logic:** Direct transfer of generated images from Text2Image to ADetailer.
### Removed
- **Face Restore module:** Dropped `facexlib` and `basicsr` dependencies in favor of the more efficient ADetailer architecture.

## [2.14.0] - 2026-05-21
### Added
- **Face Restore module (Legacy):** Advanced face reconstruction using `CodeFormer` (loaded via `spandrel`) and `facexlib`. Manual and automatic processing modes with a dedicated third preview panel.

## [2.13.0] - 2026-05-21
### Added
- **Custom VAE support:** External VAE files (.safetensors, .pt) can now be loaded. New VAE selection panel in sidebar + default VAE option in settings.

## [2.12.0] - 2026-05-21
### Added
- **Advanced VRAM Optimization:** New settings options: Attention Slicing, Model CPU Offloading, and auto VRAM clearing after generation. Enables stable operation on 6GB cards.

## [2.11.0] - 2026-05-21
### Removed
- **VRAM Oracle module:** Complete removal of the VRAM usage indicator and Auto-Optimizer button from the sidebar. Preparation for new Resource Monitor architecture.

## [2.10.0] - 2026-05-21
### Added
- **Auto-refresh lists:** `QFileSystemWatcher` for asynchronous monitoring of model folders. UI lists update automatically when files are added or removed on disk.
- **Smart selection memory:** System preserves the currently selected model/LoRA during auto-refresh, preventing ComboBox resets.

## [2.9.0] - 2026-05-21
### Added
- **i18n system (translations):** Multi-language architecture based on JSON files (`locales/`).
- **Language support:** Full sidebar translations (PL/EN).
- **Dynamic Translator:** Global `tr()` function with auto-loading dictionary based on settings.

## [2.8.0] - 2026-05-21
### Added
- **Advanced Inpaint Canvas:** Rewritten canvas using `QGraphicsView` and `QGraphicsScene`.
- **Undo/Redo system:** Full brush history with keyboard shortcuts (Ctrl+Z, Ctrl+Y).
- **Image centering:** Improved image display centering in the editing area.

## [2.7.0] - 2026-05-21
### Added
- **Zero-Copy optimization:** Efficient image conversion between PIL and QImage using direct memory views.
- **Memory stability:** Mechanism preventing SegFaults by explicitly retaining image byte references.

## [2.6.0] - 2026-05-21
### Added
- **First Launch Wizard:** Welcome wizard for initial configuration (language, theme).
- **LoRA management:** Auto-reloading active LoRA adapters when switching base models.
- **UI improvements:** Expanded light mode styles and improved dropdown rendering.

## [2.5.0] - 2026-05-21
### Added
- **Settings system:** `settings.ini` managed by `SettingsManager`.
- **Configuration panel:** New settings dialog for paths, colors, and performance options.
- **VRAM Slicing:** VAE Slicing and Tiling options for 6GB cards.
- **Dynamic styles:** Full CSS-based styling engine.

## [2.4.0] - 2026-05-21
### Added
- **Physical LoRA unloading:** New `unload_lora` method, fixing `ValueError: Adapter name already in use`.

## [2.3.0] - 2026-05-21
### Added
- **Gallery:** New tab for browsing generated images.
- **PNG Info:** Read/write generation parameters in PNG metadata.
- **Floating Tips:** Floating documentation windows (`docs/tips`).

## [2.2.0] - 2026-05-21
### Added
- **ControlNet Canny:** ControlNet integration with automatic image preprocessing.
- **Upscaler:** Image upscaling using `spandrel` library.
- **Modular architecture:** Code split into `main`, `widgets`, `config`, `utils`.

## [2.1.0] - 2026-05-21
### Added
- **Latent Mixology Station:** Up to 5 simultaneous LoRA adapters.
- **VRAM Oracle:** Real-time GPU memory monitoring.
- **UI Modern Dark:** Complete UI redesign with modern dark style.

## [1.0.0] - 2024-05-22
- Initial release.

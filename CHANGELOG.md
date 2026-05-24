# Changelog

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

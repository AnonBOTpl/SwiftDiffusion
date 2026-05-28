# Changelog

## [2.20.9] - 2026-05-26 – CLIP Interrogator, hf_xet dependency
### Added
- **CLIP Interrogator tab** — reverse-engineer prompts from any image. Load ViT-B/32 or ViT-L/14 models via Download button, then analyze an image to get ranked matching terms across 8 categories (quality, colors, medium, artist, style, lighting, effects, composition). Copy result to Text2Image with one click.
- **CLIP candidate database** — `clip_data/candidates.json` with ~120 curated terms across 8 categories. Supports user-provided `.json` files for custom candidates.
- **Dynamic CLIP format detection** — `ClipDownloadWorker` uses `HfApi.list_repo_files` to check for `.safetensors`; downloads only PyTorch format (safetensors or bin) + configs, skips Flax/TF.
- `hf_xet==1.1.1` to `requirements.txt` — accelerates HuggingFace Hub downloads with the Xet protocol for large files (models, LoRAs, ControlNet).
### Fixed
- **boot.py CUDA timeout too short** — increased subprocess timeout from 15s to 45s and health-check thread timeout from 8s to 30s. First `import torch` on a fresh system/driver can take 20+ seconds, causing a false "GPU driver in bad state" error.
- **compel dependency bloating** — `compel` had `notebook` in its `Requires`, pulling the entire JupyterLab ecosystem (~40 packages). Removed `compel` from `requirements.txt`; `install.bat` now installs it with `--no-deps`.

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
- **Wildcards in history/favorites** — `_set_tags()` detects `__name__` pattern and restores via `_toggle_wildcard()` instead of `_toggle_tag()`.
- Locale keys: `pb_wildcards`, `pb_wildcards_empty`, `pb_search_placeholder` (EN + PL).

## [2.20.6] - 2026-05-24 – Style Presets, side-by-side preview
### Added
- **Style Presets** — `tags/presets/` directory with one `.json` file per preset. 6 built-in presets (cinematic, anime, oil painting, photography, dark fantasy, watercolor). Exclusive toggling via `_active_preset`.
- **Side-by-side preview** — two `QTextEdit` in `QHBoxLayout` (50/50, fixedHeight 70 px). Positive left, negative right with red border.
- **RuntimeError fix** — all `btn.setChecked()` in `_clear_all` and `_randomize` wrapped in `try/except RuntimeError` for deleted C++ objects after `refresh_tags()`.
- **Embeddings tab recreated in `refresh_tags()`** — `_emb_page` + `_emb_flow` rebuilt from scratch to prevent deleted C++ object errors.
- **`_set_tags()` negative support** — `_set_tags()` now also restores negative tags from history/favorites.

## [2.20.5] - 2026-05-24 – Negative tags, Random button, custom categories
### Added
- **Negative tags** — `tags/negative.json` with 30 negative tags. Separate `_neg_selected` list, `_tag_btns_neg` map, `neg_prompt_ready` signal.
- **History/Favorites negative tag support** — both store `negative_tags` field per entry; `.get("negative_tags", [])` backward compat; Load restores both sets.
- **🎲 Random button** — `_random_selected` list; configurable per-category count via `settings.get('PromptBuilder','random_tags_count', fallback='1')` (QSpinBox 1–5 in Settings → Prompt Builder).
- **Custom tag categories** — `_load_tags()` uses fixed built-in order (quality→style→lighting→artists) + alphabetical user files; `QFileSystemWatcher` on `tags/` triggers `refresh_tags()`.
- Locale keys: `pb_negative`, `pb_neg_color`, `pb_random`, `pb_random_label` (EN + PL).

## [2.20.4] - 2026-05-24 – Prompt Builder: history & favorites
### Added
- **Prompt history** — every "Copy to Text2Image" saves tag selection to `prompts_history.json` (max 20, newest first). "📜 History" button opens QDialog with Load/Copy actions.
- **Prompt favorites** — "★ Save" saves current tags with custom name to `prompts_favorites.json` (no limit). "★ Favorites" dialog shows all presets with Load/Copy/Delete actions.
- Locale keys: `pb_history`, `pb_history_title`, `pb_favorites`, `pb_fav_title`, `pb_save_fav`, `pb_fav_name`, `pb_load`, `pb_copy`, `pb_delete`, `pb_no_history`, `pb_no_fav` (EN + PL).

## [2.20.3] - 2026-05-24 – Refactor phase 3: controllers extracted
### Changed
- **`generation_controller.py`** extracted (~180 lines) — T2I/Img2Img/Upscale orchestration separated from main window.
- **`mode_controllers.py`** extracted (~210 lines) — Inpaint, ControlNet, ADetailer controllers.
- **`main.py`** reduced 536→317 lines (-41%, -64% from 881).
- All button connections now routed through controllers.
- Unused imports and `UrlDownloaderTab` removed.
- `qimage_to_pil` import cleaned.

## [2.20.2] - 2026-05-24 – Refactor phase 2: boot, ResourceMonitor, ModelManager
### Changed
- `boot.py`, `ResourceMonitor`, `ModelManager` extracted from `main.py`.
- `main.py` reduced from 881 to 536 lines (-39%).
- VRAM clearing added to failure path of `on_model_loaded()`.

## [2.20.1] - 2026-05-24 – Refactor phase 1: widgets package split
### Changed
- `widgets.py` (1297 lines) split into `widgets/` package with 6 modules + `__init__.py`.

## [2.20.0] - 2026-05-24 – Wildcards, Tiled VAE, Prompt weighting, Textual Inversion
### Added
- **Wildcards** — `wildcards/` folder with 4 example `.txt` files; `resolve_wildcards()` regex `__word__` → random line; called in all 5 workers for prompt + neg_prompt.
- **Tiled VAE** — checkbox in Settings → Performance, independent from VRAM Slicing.
- **Prompt weighting (compel)** — `_encode_prompt()` with try/except fallback; conditional `prompt_embeds=` / `negative_prompt_embeds=` in 5 pipeline call sites.
- **Textual Inversion embeddings** — `models/embeddings/` scanned for `.pt`/`.bin`/`.safetensors`; loaded after model load; dynamic "Embeddings" tab in Prompt Builder with `QFileSystemWatcher` auto-refresh.

## [2.19.0] - 2026-05-24 – VramWarningDialog removed, SDXL cleanup
### Removed
- SDXL pipeline classes, VramWarningDialog, `_check_vram_warning()`, `dont_ask_vram` config key.
- XL-specific weight paths and LoRA scale handling.

## [2.18.3] - 2026-05-23 – Stop button, clean shutdown
### Added
- **Stop button** for all generation tabs — each Generate button toggles to "STOP" (red). `engine._stop_flag` checked in progress callbacks; `RuntimeError("STOPPED")` caught in workers.
- **Clean shutdown** — `closeEvent` calls `engine._clear_vram()` then `resource_monitor.shutdown()`.
- **Inpaint/ADetailer aspect ratio fix** — width/height from input image dimensions (rounded down to multiple of 8).

## [2.18.2] - 2026-05-23 – ControlNet infinite-enlarge fix, split previews
### Fixed
- ControlNet preview `setMinimumSize(1,1)` + `setSizePolicy(Expanding, Expanding)` to prevent infinite enlargement.
### Changed
- Inpaint tab split preview: left = canvas_scroll (mask input), right = v_inpaint_out (result).
- ControlNet tab split preview: left = cn_preview (reference), right = v_cn_out (result).
- ImageViewer popup removed from generation finished handlers.

## [2.18.1] - 2026-05-22 – Image scaling fix
### Fixed
- `ClickableLabel` + `InpaintCanvas` proper scaling in `resizeEvent`.
- ADetailer/ControlNet previews in `resizeEvent`.
- Missing `_on_tab_changed` handler connected.

## [2.18.0] - 2026-05-22 – Locale, log, scaling, CUDA health check
### Added
- I18n: ~80 new keys across both locale files (batch + clip).
- Engine logging changed from Polish to English.
- Startup logging: `[STARTUP]` and `[UI]` markers added.
- CUDA health check at boot: subprocess with 15s timeout tests `import torch` + CUDA.
- Max resolution increased: all width/height sliders 256–2048.
- `detect_model_type` sanity check: `header_len > 50 MB` returns `"sd15"`.

## [2.17.3] - 2026-05-22 – 7 dark themes, visual effects
### Added
- 7 dark themes: Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean — each with 12 colors + sidebar gradient.
- Light mode removed.
- Visual effects: drop shadows, pulsing border on live preview, smooth progress bar, gradient on GenerateBtn, hover states, styled scrollbars.
- Accent color default per-theme.
- About tab, Settings dialog widened to 920 px, progress bars 8 px, monitor in sidebar.
- WelcomeDialog updated with 7 themes.
- `install.bat` rewritten bilingual.
- `start.bat` simplified — English only, `taskkill` removed.

## [2.17.2] - 2026-05-22 – Crash fixes
### Fixed
- Restored missing methods, UI elements, `__init__`.
- Fixed `except:` → `except Exception:`.
- Removed dead code.

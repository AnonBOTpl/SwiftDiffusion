# 🎨 SwiftDiffusion — Stable Diffusion GUI

[🇵🇱 Polski](README-pl.md)

<p align="center">
    <br><br>
  <b>Stop wrestling with the command line. Start creating.</b>
  <br>
  <i>A clean, fast, VRAM-friendly GUI for Stable Diffusion 1.5 — built with PyQt6.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/AnonBOTpl/SwiftDiffusion?color=blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey" alt="Platform">
  <a href="https://ko-fi.com/anonbotpl"><img src="https://img.shields.io/badge/support-Ko--fi-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
</p>

---

## 🖼️ Screenshots

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20main.png" alt="Main Window" width="700">
  <br><i>Main generation window</i>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20adetailer.png" alt="ADetailer" width="700">
  <br><i>ADetailer — automatic face enhancement</i>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/SwiftDiffusion/main/screens/screen%20downloader.png" alt="Model Downloader" width="700">
  <br><i>Built-in model downloader for CivitAI & HuggingFace</i>
</p>

---

## 🚀 What can it do?

### ✍️ Prompting Tools

- **Wildcards** — use `__token__` syntax in your prompt; replaced with a random line from `wildcards/token.txt` each generation
- **Prompt Builder** — compose prompts visually from tag categories (quality, style, lighting, artists) with a single click
- **Prompt weighting (compel)** — fine-tune the influence of words and phrases using standard `(word:1.2)` syntax, no extra setup required
- **Textual Inversion embeddings** — drop `.pt` / `.bin` / `.safetensors` files into `models/embeddings/`; they appear automatically in the Prompt Builder and are ready to use after model load
- **Prompt Builder** — built-in tag manager with categorized tags (positive and negative), live preview for both, and one-click copy to T2I. Save and restore prompt combinations via **history** (`prompts_history.json`, last 20) and **favorites** (`prompts_favorites.json`, unlimited). Separate Load/Copy/Delete actions per entry per both tag sets. 🎲 Random button picks configurable tags per positive category.
- **Tag search** — filter all tag buttons (positive and negative) by typing in a search field. Matching results appear in a dedicated tab with synced toggle state.
- **Wildcards tab** — browse and toggle wildcards from the `wildcards/` folder directly in Prompt Builder. Each `.txt` file appears as a checkable button; tooltip previews the first 5 lines. Selected wildcards use `__name__` syntax and are restored from history/favorites.
- **Custom tag categories** — drop your own `.json` file into `tags/` with `{"label": "My Tags", "tags": ["tag1", "tag2"]}` and it appears as a new tab immediately, no restart needed. Built-in categories stay in their original order; your files are added alphabetically below them.
- **Style Presets** — one-click tag sets in `tags/presets/`. Each file is one preset: `{"name": "My Style", "icon": "✨", "tags": ["tag1", "tag2"]}`. Add or remove files anytime — changes appear instantly. Presets are exclusive (selecting one replaces the other).
- **Batch generation** — generate up to 10 images sequentially with a single click. Each item uses a different seed. Auto upscale is applied per-item. After completion, a scrollable thumbnail bar lets you browse all results and compare raw vs upscaled versions.
- **CLIP Interrogator** — built-in prompt reverse engineering. Load a CLIP model (ViT-B/32 or ViT-L/14), drop any image, and get a ranked list of matching terms across 8 categories — quality, colors, medium, artist, style, lighting, effects, composition. Custom `.json` candidate files supported. GPU/CUDA toggle. One-click copy to Text2Image.

### 🖌️ Generation Modes

| Mode | What it's for |
|---|---|
| **Text2Image** | Generate from a prompt with full control over sampler, scheduler, CFG, steps, and dimensions |
| **Img2Img** | Transform an existing image guided by your prompt |
| **Inpainting** | Paint a mask over any area and regenerate just that part — with full Undo/Redo (Ctrl+Z/Y) |
| **ControlNet (Canny)** | Guide generation using the edge structure of a reference image |
| **ADetailer** | Automatically detect and enhance faces using YOLOv8 — zero extra VRAM cost |
| **Upscaler** | High-quality upscaling via the `spandrel` library |
| **CLIP Interrogator** | Analyze any image and reverse-engineer its prompt — detects quality, colors, medium, artist, style, lighting, effects, and composition |
| **Photo Restoration** | Restore old, damaged, or black-and-white photos — colorize B&W, remove scratches/creases, upscale, and enhance faces in a two-pass pipeline |

### ⚙️ Smart Settings

- **First Launch Wizard** — choose your language and theme before anything else
- **7 dark themes** — Dark, Amber, Nord, Dracula, Monokai, Forest, Ocean — with optional custom accent color
- **Performance controls** — VRAM Slicing, Attention Slicing, Tiled VAE, CPU Offloading, auto VRAM clear
- **Fully translatable** — add any language by dropping a JSON file into `locales/`

### 📦 Model Management

- **URL Downloader** — paste a CivitAI or HuggingFace link and SwiftDiffusion handles the rest: downloads, categorizes, and makes the model available instantly
- **Live refresh** — add a model or embedding to disk and the UI picks it up automatically, no restart needed (`QFileSystemWatcher`)
- **Latent Mixology Station** — blend up to 5 LoRA adapters simultaneously with a visual weight mixer
- **Auto-detects** `.safetensors`, `.pth`, `.onnx`, and other common formats

### 🖼️ Gallery & PNG Metadata

- Browse generated images in the built-in file explorer
- **One-click recall** — read prompt, seed, and all settings from PNG metadata and restore them to the pipeline instantly
- Floating HTML guides for ControlNet and Inpainting

### ⚠️ Known limitations
- **SDXL** was evaluated but dropped — `from_single_file()` crashes on 6 GB GPUs without an error message. SwiftDiffusion is optimized and tested exclusively for **SD 1.5**.

### 📊 Live Resource Monitor

Real-time VRAM, RAM, GPU load, and temperature — visible in the sidebar at all times.

---

## 🛠️ Installation

### Windows (recommended)

Choose your installer:

| Installer | Speed | Venv |
|-----------|-------|------|
| `install.bat` | Standard (pip) | `.venv` |
| `install_uv.bat` | **Faster** (uv, Rust-based) | `.venv-uv` |

```
1. Clone or download this repo
2. Run install.bat (pip) OR install_uv.bat (uv — 10-50× faster)
3. Run start.bat (for pip) OR start-uv.bat (for uv)
```

Both installers set up a virtual environment, install PyTorch with CUDA 12.8 support, and pull all dependencies automatically. The uv installer auto-downloads `uv` if not present. Venvs are independent — you can keep both.

### Linux

```bash
pip install -r requirements.txt
python main.py
```

---

## 📋 Requirements

| | |
|---|---|
| **Python** | 3.12.10 |
| **GPU** | CUDA-compatible, 6 GB VRAM recommended (GTX 1060 or better) |
| **OS** | Windows / Linux (PyQt6 required) |

---

## 📂 Project Structure

```
SwiftDiffusion/
├── main.py                    # UI skeleton & entry point
├── boot.py                    # CUDA health check on import
├── engine.py                  # Diffusion pipeline logic
├── restoration_engine.py      # Photo Restoration engine (scratch removal, upscale, face enhance, colorization)
├── worker.py                  # Background QThread workers
├── model_manager.py           # Model loading, LoRA, file watchers
├── generation_controller.py   # T2I / Img2Img / Upscale orchestration
├── mode_controllers.py        # Inpaint / ControlNet / ADetailer controllers
├── config.py                  # Settings & i18n loader
├── widgets/                   # UI component package
│   ├── __init__.py
│   ├── dialogs.py             # Settings, gallery, about dialogs
│   ├── inpaint_canvas.py      # Mask editor canvas
│   ├── widgets_common.py      # ClickableLabel, sliders, LoRA items
│   ├── model_downloader.py    # CivitAI / HF downloaders
│   ├── flow_layout.py         # Custom FlowLayout for Prompt Builder
│   ├── prompt_builder.py      # Prompt Builder tab
│   ├── resource_monitor.py    # Live VRAM/RAM monitor widget
│   ├── clip_interrogator.py   # CLIP Interrogator tab
│   └── restoration.py         # Photo Restoration tab
├── models_registry.py         # Model scanner & registry
├── url_downloader.py          # Legacy downloader helpers
├── scraper.py                 # Model search scraper
├── install.bat                # Windows installer (bilingual)
├── start.bat                  # Windows launcher
├── locales/                   # Translation files (en, pl, …)
├── wildcards/                 # Wildcard text files
├── tags/                      # Prompt Builder tag categories
└── docs/                      # Floating HTML guides
```

---

---

## 🖼️ Photo Restoration Guide

The **Photo Restoration** tab can restore old, damaged, or black-and-white photos. It uses a two-pass pipeline combining scratch removal, colorization, upscaling, and face enhancement.

### Basic workflow

1. **Load an image** — click the folder button to load a JPEG/PNG
2. **Enable options:**
   - **Auto scratch removal** — removes scratches, creases, dust, and paper texture
   - **Colorize** (B&W photos only) — uses **OpenCV DNN** for fast results
   - **Extra upscale** (visible when both colorize and scratch are on) — adds a second upscale pass for larger output
3. **Click "Restore"** — the pipeline runs automatically and shows the result
4. **Open result** — click "Open result" to view the saved file in Explorer

### What happens under the hood

| Step | Tool | What it does |
|------|------|-------------|
| Colorize | OpenCV DNN | Adds color to B&W photos (Pass 1 only) |
| Upscale | Real-ESRGAN x4plus | 2× upscaling (Pass 1; Pass 2 if extra upscale checked) |
| Face enhance | GFPGAN v1.4 | Restores facial details (both passes) |
| Scratch removal | OpenCV inpainting (NS) | Removes scratches, creases, artifacts (Pass 2 only) |

### Tips

- **Best results with B&W photos** that have good contrast and visible luminance variation for colorization
- **For color photos** — disable colorize, enable scratch + upscale
- **Large originals** — scratch removal runs at full resolution; the two-pass pipeline may produce a file several times the original dimensions
- **First run** — models are downloaded automatically (RealESRGAN ~67 MB, GFPGAN ~340 MB, colorization models ~129 MB). A restart may be needed if downloads fail mid-way.

## ☕ Support

If SwiftDiffusion saves you time, consider buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/anonbotpl)

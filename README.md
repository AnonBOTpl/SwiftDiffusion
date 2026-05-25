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
- **Prompt Builder** — built-in tag manager with categorized tags, live preview, and one-click copy to T2I. Save and restore prompt combinations via **history** (`prompts_history.json`, last 20) and **favorites** (`prompts_favorites.json`, unlimited). Separate Load/Copy/Delete actions per entry.

### 🖌️ Generation Modes

| Mode | What it's for |
|---|---|
| **Text2Image** | Generate from a prompt with full control over sampler, scheduler, CFG, steps, and dimensions |
| **Img2Img** | Transform an existing image guided by your prompt |
| **Inpainting** | Paint a mask over any area and regenerate just that part — with full Undo/Redo (Ctrl+Z/Y) |
| **ControlNet (Canny)** | Guide generation using the edge structure of a reference image |
| **ADetailer** | Automatically detect and enhance faces using YOLOv8 — zero extra VRAM cost |
| **Upscaler** | High-quality upscaling via the `spandrel` library |

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

```
1. Clone or download this repo
2. Run install.bat
3. Run start.bat
```

`install.bat` sets up a virtual environment, installs PyTorch with CUDA 12.8 support, and pulls all dependencies automatically.

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
│   └── resource_monitor.py    # Live VRAM/RAM monitor widget
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

## ☕ Support

If SwiftDiffusion saves you time, consider buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/anonbotpl)

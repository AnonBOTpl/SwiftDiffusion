# 🎨 SwiftDiffusion — Stable Diffusion GUI

[🇵🇱 Polski](README-pl.md)

<p align="center">
  <img src="https://raw.githubusercontent.com/AnonBOTpl/projects-files/main/sd_logo.png" alt="AnonGen Logo" width="200">
  <br>
  <b>Nowoczesny, minimalistyczny interfejs graficzny dla Stable Diffusion 1.5.</b>
  <br>
  <i>Zaprojektowany w PyQt6 z myślą o wygodzie, estetyce i ochronie VRAM.</i>
</p>

---

## 🚀 Key Features

### 🖌️ Smart Generation Modes

* **Text2Image** — Full control over the diffusion process: sampler, scheduler, CFG, steps, and dimensions.
* **Inpainting (Editing)** — Advanced interactive canvas (`QGraphicsView`) for drawing precise binary masks. Features full **Undo/Redo** history (Ctrl+Z, Ctrl+Y) and image centering. Supports dedicated inpainting models and component sharing (saves VRAM).
* **ControlNet (Canny)** — Edge-based generation from a reference image with smart scaling and OpenCV edge detection.
* **Upscaler** — High-quality image upscaling support powered by the `spandrel` library.

### ⚙️ Advanced Settings (`settings.ini`)

* **First Launch Wizard** — A welcoming setup guide to help you configure your initial language and theme preferences.
* **Modular Configuration** — Complete freedom in defining model paths and output directories.
* **Dynamic Themes** — Seamless switching between **Dark** and **Light** modes with customizable accent colors.
* **Performance Tweaks** — Optional VRAM Slicing and VAE Tiling for low-memory cards.
* **i18n System (Multilingual Support)** — The application is fully prepared for multiple languages via JSON files (`locales/`). It officially supports English and Polish out of the box, but **you can easily add your own custom language** by simply dropping a new JSON file into the folder.

### 📦 Asset Management

* **Autonomous Refreshing** — Thanks to `QFileSystemWatcher`, the interface dynamically reacts to new models/LoRAs added to the disk without restarting the app, smartly retaining your current selections.
* **Latent Mixology Station** — A mixer for up to 5 LoRA adapters simultaneously with a visual weight equalizer. It automatically reloads active adapters when switching base models and physically unloads them to prevent memory conflicts.
* **Smart Scanner** — Automatic detection of `.safetensors`, `.pth`, `.onnx`, and other common model formats.

* **Zero-Copy Memory** — Highly efficient image conversion between the AI engine (PIL) and the UI (QImage) via direct memory views, eliminating CPU bottlenecks and ensuring memory stability (prevents SegFaults).

### 🖼️ Gallery & PNG Info

* Browse your creations using the built-in file explorer.
* **Recall Parameters** — Read the prompt, seed, and generation settings directly from PNG metadata and restore them to the pipeline with a single click.
* **Floating Tips** — Interactive HTML documentation and guides available as floating windows within the app.

---

## 📂 Project Structure

```text
SwiftDiffusion/
│   CHANGELOG.md
│   config.py
│   engine.py
│   install.bat
│   LICENSE
│   main.py
│   README.md
│   requirements.txt
│   start.bat
│   test_engine.py
│   utils.py
│   widgets.py
│   worker.py
│
├───docs
│       tips_controlnet.html
│       tips_inpaint.html
│
└───locales
        en.json
        pl.json

```

---

## 🛠️ Installation

### Quick Start (Windows)

Run the `install.bat` file, which will automatically configure a virtual environment, install PyTorch with CUDA 12.8 support, and download all necessary dependencies.

### Launching

After a successful installation, simply double-click `start.bat`.

---

## 📋 Technical Requirements

* **Python:** 3.10+
* **GPU:** CUDA-compatible (e.g., GTX 1060 or similar with min. 6 GB VRAM recommended)
* **OS:** Windows / Linux (must support PyQt6)

---

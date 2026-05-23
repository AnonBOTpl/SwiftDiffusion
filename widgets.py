import os
import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint, QUrl, QTimer, QThread
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtGui import (
    QPixmap, QIcon, QFont, QColor, QPalette, QPainter, QPen, QBrush,
    QImage, QIntValidator, QUndoStack, QUndoCommand, QPainterPath
)
from PIL import Image as PILImage
from utils import qimage_to_pil
from config import logger, settings, get_style, tr

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("welcome_title"))
        self.setMinimumSize(450, 300)

        layout = QVBoxLayout(self)
        lbl_welcome = QLabel(tr("welcome_header"))
        lbl_welcome.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d4ff;")
        lbl_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_welcome)

        layout.addWidget(QLabel(tr("welcome_lang")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Polski", "pl")
        self.lang_combo.addItem("English", "en")
        layout.addWidget(self.lang_combo)

        lbl_restart_w = QLabel(tr("lbl_restart_required"))
        lbl_restart_w.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        layout.addWidget(lbl_restart_w)

        layout.addWidget(QLabel(tr("welcome_theme")))
        self.theme_combo = QComboBox()
        for name in ("Dark", "Amber", "Nord", "Dracula", "Monokai", "Forest", "Ocean"):
            self.theme_combo.addItem(name, name)
        layout.addWidget(self.theme_combo)

        layout.addStretch()
        btn_finish = QPushButton(tr("btn_finish"))
        btn_finish.setObjectName("GenerateBtn")
        btn_finish.clicked.connect(self.save_and_close)
        layout.addWidget(btn_finish)

    def save_and_close(self):
        lang = self.lang_combo.currentData()
        theme = self.theme_combo.currentData()
        settings.set('UI', 'language', lang)
        settings.set('UI', 'theme', theme)
        settings.save()
        self.accept()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, app_version="1.0.0"):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumSize(920, 500)
        self.parent_win = parent
        self.app_version = app_version

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 1. Performance
        perf_tab = QWidget(); self.tabs.addTab(perf_tab, tr("settings_tab_perf")); perf_l = QVBoxLayout(perf_tab)
        self.vram_slice = QCheckBox(tr("settings_vram_slice"))
        self.vram_slice.setChecked(settings.get_bool('Performance', 'vram_slicing'))
        self.cb_attention_slicing = QCheckBox(tr("perf_attention_slicing"))
        self.cb_attention_slicing.setChecked(settings.get_bool('Performance', 'attention_slicing'))
        self.cb_cpu_offload = QCheckBox(tr("perf_cpu_offload"))
        self.cb_cpu_offload.setChecked(settings.get_bool('Performance', 'cpu_offload'))
        self.cb_auto_clear = QCheckBox(tr("perf_auto_clear_vram"))
        self.cb_auto_clear.setChecked(settings.get_bool('Performance', 'auto_clear_vram'))

        perf_l.addWidget(self.vram_slice)
        perf_l.addWidget(self.cb_attention_slicing)
        perf_l.addWidget(self.cb_cpu_offload)
        perf_l.addWidget(self.cb_auto_clear)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("color: #333;"); perf_l.addWidget(sep)
        self.cb_preview = QCheckBox(tr("settings_preview_enable"))
        self.cb_preview.setChecked(settings.get_bool('Preview', 'enabled'))
        perf_l.addWidget(self.cb_preview)

        preview_interval_l = QHBoxLayout()
        preview_interval_l.addWidget(QLabel(tr("settings_preview_interval")))
        self.preview_interval_spin = QSpinBox()
        self.preview_interval_spin.setRange(1, 20)
        self.preview_interval_spin.setValue(int(settings.get('Preview', 'interval', fallback='5')))
        preview_interval_l.addWidget(self.preview_interval_spin)
        perf_l.addLayout(preview_interval_l)
        perf_l.addStretch()

        # 2. Paths
        paths_tab = QWidget(); self.tabs.addTab(paths_tab, tr("settings_tab_paths")); paths_l = QVBoxLayout(paths_tab)
        self.path_edits = {}
        for key, val in settings.config['Paths'].items():
            h = QHBoxLayout()
            h.addWidget(QLabel(key.replace('_', ' ').title() + ":"))
            edit = QLineEdit(val); self.path_edits[key] = edit
            h.addWidget(edit)
            btn = QPushButton("..."); btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked, k=key: self.browse_path(k))
            h.addWidget(btn)
            paths_l.addLayout(h)
        paths_l.addStretch()

        # 3. Preferences
        pref_tab = QWidget(); self.tabs.addTab(pref_tab, tr("settings_tab_pref")); pref_l = QVBoxLayout(pref_tab)
        self.sampler_combo = QComboBox(); self.sampler_combo.addItems(["DPM++ 2M", "Euler", "Euler a", "DDIM"])
        self.sampler_combo.setCurrentText(settings.get('Generation', 'default_sampler'))
        self.sched_combo = QComboBox(); self.sched_combo.addItems(["Normal", "Karras", "Exponential"])
        self.sched_combo.setCurrentText(settings.get('Generation', 'default_scheduler'))
        self.vae_combo = QComboBox()
        self.refresh_vae_list()
        self.vae_combo.setCurrentText(settings.get('Generation', 'default_vae'))

        pref_l.addWidget(QLabel(tr("settings_default_sampler"))); pref_l.addWidget(self.sampler_combo)
        pref_l.addWidget(QLabel(tr("settings_default_scheduler"))); pref_l.addWidget(self.sched_combo)
        pref_l.addWidget(QLabel(tr("settings_default_vae"))); pref_l.addWidget(self.vae_combo)
        pref_l.addStretch()

        # 4. Appearance
        ui_tab = QWidget(); self.tabs.addTab(ui_tab, tr("settings_tab_ui")); ui_l = QVBoxLayout(ui_tab)

        ui_l.addWidget(QLabel(tr("settings_lang")))
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Polski", "pl")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.setCurrentIndex(0 if settings.get('UI', 'language') == 'pl' else 1)
        ui_l.addWidget(self.lang_combo)

        lbl_info = QLabel(tr("lbl_restart_required"))
        lbl_info.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        ui_l.addWidget(lbl_info)

        ui_l.addWidget(QLabel(tr("settings_theme")))
        self.theme_combo = QComboBox()
        for name in ("Dark", "Amber", "Nord", "Dracula", "Monokai", "Forest", "Ocean"):
            self.theme_combo.addItem(name, name)
        current = settings.get('UI', 'theme', fallback='Dark')
        if current not in ("Dark", "Amber", "Nord", "Dracula", "Monokai", "Forest", "Ocean"):
            current = "Dark"
        self.theme_combo.setCurrentText(current)
        ui_l.addWidget(self.theme_combo)

        accent_row = QHBoxLayout()
        self.accent_btn = QPushButton()
        self.accent_btn.setFixedSize(28, 28)
        self.curr_accent = settings.get('UI', 'accent_color', fallback='#00d4ff')
        self.chk_custom_accent = QCheckBox(tr("settings_custom_accent"))
        self.chk_custom_accent.setChecked(settings.get_bool('UI', 'use_custom_accent', fallback=False))
        self.chk_custom_accent.toggled.connect(self._toggle_accent_picker)
        self._update_accent_btn()
        accent_row.addWidget(QLabel(tr("settings_accent")))
        accent_row.addWidget(self.accent_btn)
        accent_row.addWidget(self.chk_custom_accent)
        accent_row.addStretch()
        self.accent_btn.clicked.connect(self.pick_color)
        self._toggle_accent_picker(self.chk_custom_accent.isChecked())
        ui_l.addLayout(accent_row)
        ui_l.addStretch()

        # 5. Integration
        int_tab = QWidget(); self.tabs.addTab(int_tab, tr("settings_tab_integration")); int_l = QVBoxLayout(int_tab)
        int_l.addWidget(QLabel(tr("settings_integration_hf")))
        self.hf_token_edit = QLineEdit()
        self.hf_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_token_edit.setText(settings.get('Integration', 'hf_token'))
        self.hf_token_edit.setPlaceholderText("hf_xxxxxxxx...")
        int_l.addWidget(self.hf_token_edit)
        int_l.addSpacing(10)
        int_l.addWidget(QLabel(tr("settings_integration_civitai")))
        self.civitai_key_edit = QLineEdit()
        self.civitai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.civitai_key_edit.setText(settings.get('Integration', 'civitai_api_key'))
        self.civitai_key_edit.setPlaceholderText(tr("settings_integration_civitai_placeholder"))
        int_l.addWidget(self.civitai_key_edit)
        int_l.addStretch()

        # 6. About
        about_tab = QWidget(); self.tabs.addTab(about_tab, tr("settings_tab_about")); about_l = QVBoxLayout(about_tab)
        accent = settings.get('UI', 'accent_color', fallback='#00d4ff')
        try: from importlib.metadata import version as _ver
        except: _ver = lambda x: "N/A"
        try: import torch; tv = torch.__version__; cv = torch.version.cuda or "N/A"
        except: tv = "N/A"; cv = "N/A"
        try: from PyQt6.QtCore import PYQT_VERSION_STR as pv
        except: pv = "N/A"
        try: dv = _ver("diffusers")
        except: dv = "N/A"
        try: import platform; ps = platform.system(); pr = platform.release()
        except: ps = "N/A"; pr = ""
        gpu_name = "N/A"; gpu_vram = "N/A"
        try:
            import pynvml
            pynvml.nvmlInit()
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = pynvml.nvmlDeviceGetName(h).decode() if isinstance(pynvml.nvmlDeviceGetName(h), bytes) else pynvml.nvmlDeviceGetName(h)
            mi = pynvml.nvmlDeviceGetMemoryInfo(h)
            gpu_vram = f"{mi.total / 1024**3:.1f} GB"
            pynvml.nvmlShutdown()
        except: pass

        license_text = (
            "MIT License\n\nCopyright (c) 2026 AnonBOTpl\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT."
        )

        html = f"""<div style='color: #ccc; font-family: Segoe UI, sans-serif;'>
<div style='border-bottom: 2px solid {accent}; padding-bottom: 12px; margin-bottom: 16px;'>
  <h1 style='color: {accent}; margin: 0; font-size: 22px;'>Swift Diffusion v{self.app_version}</h1>
  <p style='color: #888; margin: 4px 0 0 0; font-size: 13px;'>Stable Diffusion GUI for older GPUs (GTX 1060 6GB)</p>
</div>

<div style='display: flex; gap: 20px;'>
  <div style='flex: 1;'>
    <h3 style='color: {accent}; border-bottom: 1px solid #333; padding-bottom: 4px;'>Environment</h3>
    <table style='font-size: 12px; color: #aaa; line-height: 1.8;'>
      <tr><td style='padding-right: 16px; color: #888;'>Python</td><td>{sys.version.split()[0]}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>System</td><td>{ps} {pr}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>PyQt6</td><td>{pv}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>Torch</td><td>{tv}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>CUDA</td><td>{cv}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>Diffusers</td><td>{dv}</td></tr>
    </table>
  </div>
  <div style='flex: 1;'>
    <h3 style='color: {accent}; border-bottom: 1px solid #333; padding-bottom: 4px;'>GPU</h3>
    <table style='font-size: 12px; color: #aaa; line-height: 1.8;'>
      <tr><td style='padding-right: 16px; color: #888;'>Model</td><td>{gpu_name}</td></tr>
      <tr><td style='padding-right: 16px; color: #888;'>VRAM</td><td>{gpu_vram}</td></tr>
    </table>
  </div>
</div>

<h3 style='color: {accent}; border-bottom: 1px solid #333; padding-bottom: 4px; margin-top: 20px;'>Links</h3>
<p style='font-size: 12px; line-height: 2;'>
  🌐 <a href='https://anonbotpl.github.io/' style='color: {accent}; text-decoration: none;'>Website</a>&nbsp;&nbsp;
  📖 <a href='https://github.com/AnonBOTpl/SwiftDiffusion/blob/main/README.md' style='color: {accent}; text-decoration: none;'>Documentation</a>&nbsp;&nbsp;
  🐙 <a href='https://github.com/AnonBOTpl/SwiftDiffusion' style='color: {accent}; text-decoration: none;'>GitHub</a>
</p>

<h3 style='color: {accent}; border-bottom: 1px solid #333; padding-bottom: 4px;'>License</h3>
<p style='font-size: 11px; color: #666; line-height: 1.6; white-space: pre-wrap;'>{license_text}</p>
</div>"""
        tb = QTextBrowser(); tb.setOpenExternalLinks(True); tb.setHtml(html)
        tb.setStyleSheet("background: transparent; border: none;")
        about_l.addWidget(tb)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_imp = QPushButton(tr("btn_import")); btn_imp.clicked.connect(self.import_settings)
        btn_exp = QPushButton(tr("btn_export")); btn_exp.clicked.connect(self.export_settings)
        btn_save = QPushButton(tr("btn_save_close")); btn_save.setObjectName("GenerateBtn")
        btn_save.clicked.connect(self.save_and_close)
        btn_box.addWidget(btn_imp); btn_box.addWidget(btn_exp); btn_box.addStretch(); btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def refresh_vae_list(self):
        self.vae_combo.clear()
        self.vae_combo.addItem(tr("opt_default_vae"), "Domyślne (z modelu)")
        path = settings.get('Paths', 'models_vae')
        if os.path.exists(path):
            vae_exts = (".safetensors", ".pt", ".ckpt")
            for f in os.listdir(path):
                if f.lower().endswith(vae_exts):
                    self.vae_combo.addItem(f, os.path.join(path, f))

    def browse_path(self, key):
        d = QFileDialog.getExistingDirectory(self, tr("dialog_select_dir"), self.path_edits[key].text())
        if d: self.path_edits[key].setText(d)

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.curr_accent), self)
        if c.isValid():
            self.curr_accent = c.name()
            self._update_accent_btn()

    def _update_accent_btn(self):
        self.accent_btn.setStyleSheet(f"background-color: {self.curr_accent}; border: 2px solid white; border-radius: 4px;")

    def _toggle_accent_picker(self, enabled):
        self.accent_btn.setEnabled(enabled)
        if not enabled:
            self.accent_btn.setStyleSheet("background-color: #444; border: 2px solid #555; border-radius: 4px;")

    def save_and_close(self):
        settings.set('Performance', 'vram_slicing', self.vram_slice.isChecked())
        settings.set('Performance', 'attention_slicing', self.cb_attention_slicing.isChecked())
        settings.set('Performance', 'cpu_offload', self.cb_cpu_offload.isChecked())
        settings.set('Performance', 'auto_clear_vram', self.cb_auto_clear.isChecked())
        for k, edit in self.path_edits.items():
            p = edit.text()
            settings.set('Paths', k, p)
            os.makedirs(p, exist_ok=True)
        settings.set('Generation', 'default_sampler', self.sampler_combo.currentText())
        settings.set('Generation', 'default_scheduler', self.sched_combo.currentText())
        settings.set('Preview', 'enabled', self.cb_preview.isChecked())
        settings.set('Preview', 'interval', str(self.preview_interval_spin.value()))
        settings.set('Integration', 'hf_token', self.hf_token_edit.text())
        settings.set('Integration', 'civitai_api_key', self.civitai_key_edit.text())

        vae_val = self.vae_combo.currentData()
        settings.set('Generation', 'default_vae', vae_val)
        settings.set('UI', 'language', self.lang_combo.currentData())
        settings.set('UI', 'theme', self.theme_combo.currentText())
        settings.set('UI', 'accent_color', self.curr_accent)
        settings.set('UI', 'use_custom_accent', self.chk_custom_accent.isChecked())
        settings.save()


        if self.parent_win:
            self.parent_win.apply_settings_ui()
        self.accept()

    def import_settings(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_import_settings"), "", "INI Files (*.ini)")
        if f: settings.import_settings(f); self.accept()

    def export_settings(self):
        f, _ = QFileDialog.getSaveFileName(self, tr("dialog_export_settings"), "settings_backup.ini", "INI Files (*.ini)")
        if f: settings.export_settings(f)

class FloatingTips(QDialog):
    def __init__(self, title, file_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
        self.setMinimumWidth(400)

        l = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setStyleSheet("background-color: transparent; border: none; color: #e0e0e0;")
        self.browser.setOpenExternalLinks(True)

        content = ""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"Błąd odczytu pliku: {e}"
        else:
            content = f"Brak pliku wskazówek: {file_path}"

        if file_path.endswith(".html"):
            self.browser.setHtml(content)
        else:
            self.browser.setPlainText(content)

        l.addWidget(self.browser)

        btn_close = QPushButton(tr("btn_close"))
        btn_close.clicked.connect(self.close)
        l.addWidget(btn_close)

        # Auto-rozmiar wysokości
        self.browser.document().contentsChanged.connect(self.adjust_height)
        self.adjust_height()

    def adjust_height(self):
        doc_height = self.browser.document().size().height()
        target_height = min(int(doc_height) + 100, 600)
        self.resize(self.width(), target_height)

class GalleryDetailWindow(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("gallery_details_title"))
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setStyleSheet("background-color: #1e1e1e;")
        self.setMinimumSize(900, 600)
        self.path = path
        self.parent_win = parent

        l = QHBoxLayout(self)

        # Lewa strona - podgląd
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(path)
        self.preview.setPixmap(pix.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        l.addWidget(self.preview, 1)

        # Prawa strona - parametry
        r_l = QVBoxLayout()
        self.browser = QTextBrowser()
        self.browser.setStyleSheet("background-color: #121212; border: none; color: #00d4ff; font-family: Consolas, monospace;")

        self.params = {}
        try:
            img = PILImage.open(path)
            raw_params = img.text.get("sd_params")
            if raw_params:
                self.params = json.loads(raw_params)
                text = f"<h3>{tr('gallery_params_header')}</h3><hr>"
                for k, v in self.params.items():
                    text += f"<b>{k.upper()}:</b> {v}<br>"
                self.browser.setHtml(text)
            else:
                self.browser.setPlainText(tr("gallery_no_meta"))
        except Exception as e:
            self.browser.setPlainText(f"{tr('gallery_read_error')}{e}")

        r_l.addWidget(self.browser)

        btn_send = QPushButton(tr("btn_send_to_t2i"))
        btn_send.setObjectName("GenerateBtn")
        btn_send.clicked.connect(self.send_to_t2i)
        r_l.addWidget(btn_send)

        l.addLayout(r_l, 1)

    def send_to_t2i(self):
        if not self.params: return
        w = self.parent_win
        w.t2i_prompt.setPlainText(self.params.get("prompt", ""))
        w.t2i_neg.setPlainText(self.params.get("neg_prompt", ""))
        w.s_steps.spin.setValue(int(self.params.get("steps", 20)))
        w.s_cfg.spin.setValue(float(self.params.get("cfg", 6.0)))
        w.s_w.spin.setValue(int(self.params.get("width", 512)))
        w.s_h.spin.setValue(int(self.params.get("height", 512)))
        w.s_seed.setText(str(self.params.get("seed", -1)))

        sampler = self.params.get("sampler")
        if sampler:
            idx = w.sampler_combo.findText(sampler)
            if idx >= 0: w.sampler_combo.setCurrentIndex(idx)

        scheduler = self.params.get("scheduler")
        if scheduler:
            idx = w.scheduler_combo.findText(scheduler)
            if idx >= 0: w.scheduler_combo.setCurrentIndex(idx)

        w.tabs.setCurrentIndex(0)
        self.close()

class ImageViewer(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog); self.setStyleSheet("background-color: rgba(0, 0, 0, 240);")
        # Centrowanie na ekranie
        screen_geo = self.screen().availableGeometry()
        self.setGeometry(screen_geo)

        l = QVBoxLayout(self); l.setContentsMargins(0,0,0,0); self.label = QLabel(); self.label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.label.setPixmap(pixmap.scaled(self.screen().availableGeometry().size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); l.addWidget(self.label)
        self.show()
    def mousePressEvent(self, e): self.accept()
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape: self.accept()

class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPixmap)
    def __init__(self, text="", parent=None):
        super().__init__(text, parent); self.pixmap_cached = None
    def get_image_pil(self):
        if not self.pixmap_cached: return None
        return qimage_to_pil(self.pixmap_cached.toImage())
    def set_image(self, path_or_pixmap):
        self.pixmap_cached = QPixmap(path_or_pixmap) if isinstance(path_or_pixmap, str) else path_or_pixmap
        if self.pixmap_cached:
            self.setPixmap(self.pixmap_cached.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def update_scaling(self):
        if self.pixmap_cached:
            self.setPixmap(self.pixmap_cached.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def mousePressEvent(self, e):
        if self.pixmap_cached: self.clicked.emit(self.pixmap_cached)

class DrawCommand(QUndoCommand):
    def __init__(self, scene, path_item):
        super().__init__()
        self.scene = scene
        self.path_item = path_item
    def redo(self):
        self.scene.addItem(self.path_item)
    def undo(self):
        self.scene.removeItem(self.path_item)

class InpaintCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(26, 26, 26)))

        self.base_pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.base_pixmap_item)

        self.undo_stack = QUndoStack(self)
        self.brush_size = 20
        self.current_path_item = None
        self.last_point = QPoint()

    def set_base_image(self, pixmap):
        scaled = pixmap.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.base_pixmap_item.setPixmap(scaled)
        self.scene.setSceneRect(0, 0, scaled.width(), scaled.height())
        # Wyczyszczenie historii przy nowym obrazie
        self.undo_stack.clear()
        # Wyczyszczenie poprzednich masek
        for item in self.scene.items():
            if isinstance(item, QGraphicsPathItem):
                self.scene.removeItem(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.last_point = scene_pos
            path = QPainterPath()
            path.moveTo(scene_pos)

            self.current_path_item = QGraphicsPathItem()
            self.current_path_item.setPath(path)
            self.current_path_item.setPen(QPen(Qt.GlobalColor.white, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            self.scene.addItem(self.current_path_item)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.current_path_item:
            scene_pos = self.mapToScene(event.pos())
            path = self.current_path_item.path()
            path.lineTo(scene_pos)
            self.current_path_item.setPath(path)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_path_item:
            item = self.current_path_item
            self.current_path_item = None
            # Usuń tymczasowy i dodaj przez UndoStack
            self.scene.removeItem(item)
            command = DrawCommand(self.scene, item)
            self.undo_stack.push(command)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo_stack.undo()
            elif event.key() == Qt.Key.Key_Y:
                self.undo_stack.redo()
        super().keyPressEvent(event)

    def get_mask_pil(self):
        # Renderowanie samej maski (bez obrazu bazowego)
        size = self.scene.sceneRect().size().toSize()
        if size.isEmpty(): return PILImage.new("L", (512, 512), 0)

        mask_image = QImage(size, QImage.Format.Format_RGBA8888)
        mask_image.fill(Qt.GlobalColor.black)

        painter = QPainter(mask_image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Ukryj obraz bazowy na czas renderowania maski
        self.base_pixmap_item.hide()
        self.scene.render(painter)
        self.base_pixmap_item.show()
        painter.end()

        pil_mask = qimage_to_pil(mask_image).convert("L")
        binary_mask = pil_mask.point(lambda p: 255 if p > 10 else 0)
        binary_mask.save("output/debug_mask.png")
        return binary_mask

    def get_image_pil(self):
        pix = self.base_pixmap_item.pixmap()
        if pix.isNull(): return PILImage.new("RGB", (512, 512), (0,0,0))
        return qimage_to_pil(pix.toImage())

class ParameterSlider(QWidget):
    changed = pyqtSignal()
    def __init__(self, label, min_val, max_val, default, step=1, is_float=False):
        super().__init__(); l = QVBoxLayout(self); l.setContentsMargins(0, 2, 0, 2); l.setSpacing(0)
        h = QHBoxLayout(); lbl = QLabel(label); lbl.setStyleSheet("color: #aaa; font-size: 11px;"); h.addWidget(lbl); h.addStretch()
        self.spin = QDoubleSpinBox() if is_float else QSpinBox()
        self.spin.setRange(min_val, max_val); self.spin.setFixedWidth(65); self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter); self.spin.setValue(default)
        if is_float: self.spin.setSingleStep(step)
        self.spin.valueChanged.connect(lambda: self.changed.emit()); h.addWidget(self.spin); l.addLayout(h)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        if is_float: self.slider.setRange(int(min_val * 100), int(max_val * 100)); self.slider.setValue(int(default * 100))
        else: self.slider.setRange(min_val, max_val); self.slider.setValue(default)
        self.slider.valueChanged.connect(self.on_slider_move); self.spin.valueChanged.connect(self.on_spin_move); l.addWidget(self.slider)
    def on_slider_move(self, v):
        self.spin.blockSignals(True); self.spin.setValue(v / 100.0 if isinstance(self.spin, QDoubleSpinBox) else v); self.spin.blockSignals(False); self.changed.emit()
    def on_spin_move(self, v):
        self.slider.blockSignals(True); self.slider.setValue(int(v * 100) if isinstance(self.spin, QDoubleSpinBox) else v); self.slider.blockSignals(False); self.changed.emit()
    def value(self): return self.spin.value()

class LoRAItem(QWidget):
    removed = pyqtSignal(str); changed = pyqtSignal()
    def __init__(self, name, path):
        super().__init__(); self.name = name; self.path = path
        l = QVBoxLayout(self); l.setContentsMargins(0, 5, 0, 5); l.setSpacing(2)
        h = QHBoxLayout(); lbl = QLabel(name); lbl.setStyleSheet("font-weight: bold; color: #888; font-size: 11px;")
        btn = QPushButton("X"); btn.setObjectName("RemoveBtn"); btn.setFixedSize(16, 16); btn.clicked.connect(lambda: self.removed.emit(self.name))
        h.addWidget(lbl); h.addStretch(); h.addWidget(btn); l.addLayout(h)
        ctrls = QHBoxLayout(); ctrls.setSpacing(10); self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(-100, 200); self.slider.setValue(100); self.slider.setFixedHeight(20)
        self.spin = QDoubleSpinBox(); self.spin.setRange(-1.0, 2.0); self.spin.setValue(1.0); self.spin.setFixedWidth(45); self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider.valueChanged.connect(self.on_changed); self.spin.valueChanged.connect(self.on_spin_changed); ctrls.addWidget(self.slider); ctrls.addWidget(self.spin); l.addLayout(ctrls)
    def on_changed(self, v): self.spin.blockSignals(True); self.spin.setValue(v / 100.0); self.spin.blockSignals(False); self.changed.emit()
    def on_spin_changed(self, v): self.slider.blockSignals(True); self.slider.setValue(int(v * 100)); self.slider.blockSignals(False); self.changed.emit()
    def weight(self): return self.spin.value()

class LoRAVisualizer(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(60); self.weights = []
    def update_weights(self, w): self.weights = w; self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); w, h = self.width(), self.height()
        p.setBrush(QBrush(QColor(25, 25, 25))); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(0, 0, w, h, 5, 5)
        if not self.weights: p.setPen(QColor(80, 80, 80)); p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, tr("opt_no_lora")); return
        m = 15; count = len(self.weights); bw = (w - 2 * m) / max(count, 1)
        for i, (name, weight) in enumerate(self.weights):
            nw = max(0, min(1, (weight + 1) / 3.0)); bh = int(nw * (h - 2 * m)); x = int(m + i * bw)
            p.setBrush(QBrush(QColor(0, 212, 255))); p.drawRoundedRect(QRect(x + 5, h - m - bh, int(bw - 10), bh), 2, 2)

class UrlDownloaderTab(QWidget):
    """URL-based model downloader — paste a link, see info, download."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parsed = None
        self._info = None
        self._selected_file_idx = 0
        self._analyze_timer = QTimer()
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.timeout.connect(self.do_analyze)
        self.placeholder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        self._search_thread = None
        self.init_ui()
        self._show_search_results(False)

    def init_ui(self):
        l = QVBoxLayout(self)

        # ── Search section ──
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("dl_search_models"))
        self.search_input.returnPressed.connect(self.do_search_results)
        search_row.addWidget(self.search_input, 1)
        self.btn_search = QPushButton("🔍 " + tr("dl_search"))
        self.btn_search.setObjectName("SecondaryBtn")
        self.btn_search.setFixedWidth(100)
        self.btn_search.clicked.connect(self.do_search_results)
        search_row.addWidget(self.btn_search)
        l.addLayout(search_row)

        self.search_results = QTreeWidget()
        self.search_results.setHeaderLabels([
            tr("dl_name"), tr("dl_source"), tr("dl_architecture"),
            tr("dl_type"), tr("dl_author")
        ])
        self.search_results.setColumnWidth(0, 180)
        self.search_results.setColumnWidth(1, 60)
        self.search_results.setColumnWidth(2, 70)
        self.search_results.setColumnWidth(3, 70)
        self.search_results.setAlternatingRowColors(True)
        self.search_results.setRootIsDecorated(False)
        self.search_results.itemClicked.connect(self._on_result_clicked)
        self.search_results.setMinimumHeight(100)
        l.addWidget(self.search_results, 1)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        l.addWidget(sep)

        # ── URL input ──
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(tr("dl_url_placeholder"))
        self.url_input.textChanged.connect(self._on_url_changed)
        url_row.addWidget(self.url_input, 1)
        self.btn_analyze = QPushButton(tr("dl_btn_analyze"))
        self.btn_analyze.setObjectName("SecondaryBtn")
        self.btn_analyze.setFixedWidth(100)
        self.btn_analyze.clicked.connect(self.do_analyze)
        url_row.addWidget(self.btn_analyze)
        l.addLayout(url_row)

        # ── Info group ──
        self.info_group = QGroupBox(tr("dl_model_info"))
        info_l = QVBoxLayout(self.info_group)

        info_top = QHBoxLayout()
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(80, 80)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        info_top.addWidget(self.thumb_label)

        info_fields = QVBoxLayout()
        self.lbl_name = QLabel(); self.lbl_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_author = QLabel(); self.lbl_author.setStyleSheet("color: #888;")
        self.lbl_meta = QLabel(); self.lbl_meta.setStyleSheet("color: #aaa;")
        info_fields.addWidget(self.lbl_name)
        info_fields.addWidget(self.lbl_author)
        info_fields.addWidget(self.lbl_meta)
        info_top.addLayout(info_fields, 1)

        self.btn_open_url = QPushButton(tr("dl_open_browser"))
        self.btn_open_url.setFixedWidth(100)
        self.btn_open_url.clicked.connect(self._open_in_browser)
        info_top.addWidget(self.btn_open_url)
        info_l.addLayout(info_top)

        # File/version list
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels([
            tr("dl_name"), tr("dl_file_version"), tr("dl_architecture"), tr("dl_size")
        ])
        self.file_tree.setColumnWidth(0, 200)
        self.file_tree.setColumnWidth(1, 100)
        self.file_tree.setColumnWidth(2, 80)
        self.file_tree.setRootIsDecorated(False)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setMinimumHeight(80)
        self.file_tree.itemClicked.connect(self._on_file_clicked)
        info_l.addWidget(self.file_tree, 1)

        self.info_group.hide()
        l.addWidget(self.info_group, 1)

        # Download
        dl_row = QHBoxLayout()
        self.btn_download = QPushButton(tr("dl_btn_download"))
        self.btn_download.setObjectName("GenerateBtn")
        self.btn_download.setFixedHeight(40)
        self.btn_download.clicked.connect(self.start_download)
        self.btn_download.setEnabled(False)
        dl_row.addWidget(self.btn_download)

        self.dl_progress = QProgressBar()
        self.dl_progress.setFixedHeight(20)
        self.dl_progress.hide()
        dl_row.addWidget(self.dl_progress, 1)
        l.addLayout(dl_row)

        self.dl_status = QLabel(tr("dl_url_hint"))
        self.dl_status.setStyleSheet("color: #888; font-size: 11px;")
        l.addWidget(self.dl_status)

        l.addStretch()

    def _on_url_changed(self, text):
        self.info_group.hide()
        self.btn_download.setEnabled(False)
        self.dl_status.setText(tr("dl_url_hint"))
        self.thumb_label.clear()
        self._analyze_timer.start(600)

    def _show_search_results(self, visible):
        self.search_results.setVisible(visible)

    def do_search_results(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.search_results.clear()
        self.btn_search.setEnabled(False)
        self.search_results.setHeaderLabel(tr("dl_searching"))

        class _SearchThread(QThread):
            finished = pyqtSignal(list)
            def run(self):
                from models_registry import search_source, reset_page
                token = settings.get('Integration', 'hf_token')
                api_key = settings.get('Integration', 'civitai_api_key')
                all_results = []
                for src in ["CivitAI", "HuggingFace"]:
                    reset_page(src)
                    results, _ = search_source(src, query, token, api_key, None)
                    for r in results:
                        r["_source_label"] = src
                    all_results.extend(results)
                self.finished.emit(all_results)

        self._search_thread = _SearchThread()
        self._search_thread.finished.connect(self._on_search_done)
        self._search_thread.start()

    def _on_search_done(self, results):
        self.btn_search.setEnabled(True)
        self.search_results.clear()
        self._show_search_results(True)
        if not results:
            self.search_results.setHeaderLabel(tr("dl_search_no_results"))
            return
        self.search_results.setHeaderLabels([
            tr("dl_name"), tr("dl_source"), tr("dl_architecture"),
            tr("dl_type"), tr("dl_author")
        ])
        for r in results:
            src = r.get("_source_label", r.get("source", "?"))
            arch = r.get("architecture", "?")
            mtype = r.get("model_type", "Checkpoint")
            author = r.get("author", "")
            item = QTreeWidgetItem([r.get("name", "?"), src, arch, mtype, author])
            item.setData(0, Qt.ItemDataRole.UserRole, r)
            self.search_results.addTopLevelItem(item)
        self.search_results.resizeColumnToContents(2)
        self.dl_status.setText(f"Znaleziono {len(results)} modeli — kliknij wynik by wkleić URL")

    def _on_result_clicked(self, item, column):
        r = item.data(0, Qt.ItemDataRole.UserRole)
        if not r:
            return
        src = r.get("source", "")
        repo_id = r.get("repo_id", "")
        if src == "civitai":
            url = f"https://civitai.com/models/{repo_id}"
        else:
            url = f"https://huggingface.co/{repo_id}"
        self.url_input.setText(url)
        self._show_search_results(False)
        self.do_analyze()

    def do_analyze(self):
        url = self.url_input.text().strip()
        if not url:
            return
        from url_downloader import parse_url, fetch_model_info
        parsed = parse_url(url)
        if not parsed:
            self.dl_status.setText(tr("dl_url_invalid"))
            return
        self.dl_status.setText(tr("dl_analyzing"))
        self.btn_analyze.setEnabled(False)
        self._parsed = parsed
        info = fetch_model_info(parsed)
        self.btn_analyze.setEnabled(True)
        if not info:
            self.dl_status.setText(tr("dl_url_fetch_error"))
            return
        self._info = info
        self._show_info(info)

    def _show_info(self, info):
        self.lbl_name.setText(info.get("name", "?"))
        self.lbl_author.setText(f"{info.get('author', '?')}  |  {info.get('source', '?')}")
        arch = info.get("architecture", "?")
        mt = info.get("model_type", "?")
        cat = info.get("category", "").replace("models_", "")
        n_files = len(info.get("files", []))
        self.lbl_meta.setText(f"{mt}  |  {arch}  |  {cat}  |  {n_files} plików")

        # Thumbnail — clear before loading new
        self.thumb_label.clear()
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            self._load_thumb(thumb_url)

        # File list
        self.file_tree.clear()
        for i, f in enumerate(info.get("files", [])):
            fn = f.get("name", "?")
            vn = f.get("version_name", "")
            arch_f = f.get("architecture", "")
            sz = f.get("size", 0)
            size_str = f"{sz//1024} MB" if sz else ""
            item = QTreeWidgetItem([fn, vn, arch_f, size_str])
            item.setData(0, Qt.ItemDataRole.UserRole, i)
            item.setToolTip(0, fn)
            self.file_tree.addTopLevelItem(item)

        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)
        self.file_tree.resizeColumnToContents(3)
        if self.file_tree.topLevelItemCount() > 0:
            self.file_tree.topLevelItem(0).setSelected(True)
        self._selected_file_idx = 0

        self.info_group.show()
        self.btn_download.setEnabled(True)
        self.dl_status.setText(tr("dl_url_ready"))

    def _open_in_browser(self):
        from PyQt6.QtGui import QDesktopServices
        url = self.url_input.text().strip()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _load_thumb(self, url):
        req = QNetworkRequest(QUrl(url))
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        req.setTransferTimeout(5000)
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self._on_thumb_loaded)
        self.nam.get(req)

    def _on_thumb_loaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pix = QPixmap()
            if pix.loadFromData(data):
                self.thumb_label.setPixmap(pix.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        reply.deleteLater()

    def _on_file_clicked(self, item, column):
        idx = item.data(0, Qt.ItemDataRole.UserRole)
        if idx is not None:
            self._selected_file_idx = idx

    def start_download(self):
        if not self._info or not self._info.get("files"):
            return
        files = self._info["files"]
        idx = self._selected_file_idx
        if idx < 0 or idx >= len(files):
            return
        file_info = files[idx]
        category = self._info.get("category", "models_sd")
        dest_dir = settings.get('Paths', category)
        self.btn_download.setEnabled(False)
        self.dl_progress.setValue(0)
        self.dl_progress.show()
        self.dl_status.setText("Pobieranie...")

        from url_downloader import download_model
        self._download_thread(download_model, file_info, dest_dir)

    def _download_thread(self, download_fn, file_info, dest_dir):
        class _DownloadThread(QThread):
            progress = pyqtSignal(float, str)
            finished = pyqtSignal(bool, str)
            def run(self):
                dest = download_fn(file_info, dest_dir, on_progress=lambda p, m: self.progress.emit(p, m))
                if dest:
                    self.finished.emit(True, dest)
                else:
                    self.finished.emit(False, "Błąd pobierania")
        self._worker = _DownloadThread()
        self._worker.progress.connect(self._on_dl_progress)
        self._worker.finished.connect(self._on_dl_finished)
        self._worker.start()

    def _on_dl_progress(self, pct, msg):
        self.dl_progress.setValue(int(pct))
        self.dl_status.setText(msg)

    def _on_dl_finished(self, success, msg):
        self.btn_download.setEnabled(True)
        self.dl_progress.hide()
        if success:
            self.dl_status.setText(tr("dl_done"))
        else:
            self.dl_status.setText(f"{tr('dl_error')}: {msg}")


class ScrapingTab(QWidget):
    """Experimental — search via DDG + API fallback, send URLs to downloader."""
    url_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._last_url = None
        self.init_ui()

    def init_ui(self):
        l = QVBoxLayout(self)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("dl_browse_placeholder"))
        self.search_input.returnPressed.connect(self.do_search)
        search_row.addWidget(self.search_input, 1)
        self.btn_search = QPushButton(tr("dl_browse_btn"))
        self.btn_search.setObjectName("SecondaryBtn")
        self.btn_search.setFixedWidth(120)
        self.btn_search.clicked.connect(self.do_search)
        search_row.addWidget(self.btn_search)
        l.addLayout(search_row)

        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels([
            tr("dl_source"), tr("dl_name"), tr("dl_url")
        ])
        self.result_tree.setColumnWidth(0, 70)
        self.result_tree.setColumnWidth(1, 250)
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemClicked.connect(self._on_item_clicked)
        self.result_tree.itemDoubleClicked.connect(self._send_url)
        l.addWidget(self.result_tree, 1)

        btn_row = QHBoxLayout()
        self.btn_send = QPushButton(tr("dl_browse_send"))
        self.btn_send.setObjectName("GenerateBtn")
        self.btn_send.clicked.connect(self._send_url)
        self.btn_send.setEnabled(False)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_send)
        l.addLayout(btn_row)

        self.status_label = QLabel(tr("dl_url_hint"))
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        l.addWidget(self.status_label)

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.result_tree.clear()
        self.btn_search.setEnabled(False)
        self.btn_send.setEnabled(False)
        self._last_url = None
        self.status_label.setText(tr("dl_searching"))

        class _SearchThread(QThread):
            finished = pyqtSignal(list)
            def run(self):
                from scraper import search_ddg_model
                results = search_ddg_model(query)
                self.finished.emit(results)

        self._worker = _SearchThread()
        self._worker.finished.connect(self._on_search_done)
        self._worker.start()

    def _on_search_done(self, results):
        self.btn_search.setEnabled(True)
        if not results:
            self.status_label.setText(tr("dl_search_no_results"))
            return
        for r in results:
            item = QTreeWidgetItem([r["source"], r["title"], r["url"]])
            item.setToolTip(2, r["url"])
            self.result_tree.addTopLevelItem(item)
        self.status_label.setText(f"Znaleziono {len(results)} wyników")

    def _on_item_clicked(self, item, column):
        self._last_url = item.text(2)
        self.btn_send.setEnabled(True)

    def _send_url(self):
        if self._last_url:
            self.url_selected.emit(self._last_url)


class ModelDownloaderTab(QWidget):
    """Container: URL-based downloader + experimental scraper tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.url_tab = UrlDownloaderTab()
        self.scrape_tab = ScrapingTab()
        self.scrape_tab.url_selected.connect(self._on_scrape_url)
        self.tab_widget.addTab(self.url_tab, "📥 " + tr("dl_tab_download"))
        self.tab_widget.addTab(self.scrape_tab, "🕷️ " + tr("dl_tab_browse"))
        l.addWidget(self.tab_widget)

    def _on_scrape_url(self, url):
        self.tab_widget.setCurrentWidget(self.url_tab)
        self.url_tab.url_input.setText(url)
        self.url_tab.do_analyze()

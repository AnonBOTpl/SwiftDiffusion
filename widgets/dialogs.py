import os
import sys
import json
from PIL import Image as PILImage
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QFont, QTextDocument
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
        self.cb_tiled_vae = QCheckBox(tr("perf_tiled_vae"))
        self.cb_tiled_vae.setChecked(settings.get_bool('Performance', 'tiled_vae'))
        self.cb_tiled_vae.setToolTip(tr("perf_tiled_vae_tip"))

        perf_l.addWidget(self.vram_slice)
        perf_l.addWidget(self.cb_attention_slicing)
        perf_l.addWidget(self.cb_cpu_offload)
        perf_l.addWidget(self.cb_auto_clear)
        perf_l.addWidget(self.cb_tiled_vae)

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

        # 6. Prompt Builder
        pb_tab = QWidget(); self.tabs.addTab(pb_tab, tr("settings_tab_pb")); pb_l = QVBoxLayout(pb_tab)
        pb_l.addWidget(QLabel(tr("pb_random_count")))
        self.random_count_spin = QSpinBox()
        self.random_count_spin.setRange(1, 5)
        self.random_count_spin.setValue(int(settings.get('PromptBuilder', 'random_tags_count', fallback='1')))
        pb_l.addWidget(self.random_count_spin)
        pb_l.addStretch()

        # 7. About
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
        settings.set('Performance', 'tiled_vae', self.cb_tiled_vae.isChecked())
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
        settings.set('PromptBuilder', 'random_tags_count', str(self.random_count_spin.value()))
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
                content = tr("error_reading_file").format(e=e)
        else:
            content = tr("error_tips_missing").format(file_path=file_path)

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

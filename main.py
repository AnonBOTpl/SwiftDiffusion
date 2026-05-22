import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize, QFileSystemWatcher
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator

from engine import DiffusionEngine
from worker import GenerationWorker, UpscaleWorker, InpaintWorker, ControlNetWorker
from config import get_style, settings, FOLDERS, logger, tr, translator
from utils import qimage_to_pil
from widgets import (
    ImageViewer, ClickableLabel, InpaintCanvas, ParameterSlider,
    LoRAItem, LoRAVisualizer, FloatingTips, GalleryDetailWindow,
    SettingsDialog, WelcomeDialog
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = DiffusionEngine()
        self.loras = {}
        self.setup_folders()
        self.setup_watchers()
        self.current_seed = None
        self.last_generated_path = None
        self.last_upscaled_path = None
        self.ref_image_pil = None
        self.tips_window = None

        self.init_ui()

        if settings.is_first_run:
            WelcomeDialog(self).exec()
            self.apply_settings_ui()
    def setup_folders(self):
        for p in FOLDERS:
            if not os.path.exists(p): os.makedirs(p)
    def setup_watchers(self):
        self.model_watcher = QFileSystemWatcher()
        paths = [
            settings.get('Paths', 'models_sd'),
            settings.get('Paths', 'models_lora'),
            settings.get('Paths', 'models_controlnet'),
            settings.get('Paths', 'models_inpaint'),
            settings.get('Paths', 'models_vae'),
            settings.get('Paths', 'models_upscalers')
        ]
        for p in paths:
            if os.path.exists(p):
                self.model_watcher.addPath(p)
        self.model_watcher.directoryChanged.connect(self.refresh_all_comboboxes)
    def scan_models(self, folder, exts=(".safetensors",)):
        if not os.path.exists(folder): return []
        return [f for f in os.listdir(folder) if f.lower().endswith(exts)]

    def init_ui(self):
        self.setWindowTitle("Stable Diffusion UI - Modern Dark")
        central_widget = QWidget(); self.setCentralWidget(central_widget); global_layout = QHBoxLayout(central_widget); global_layout.setContentsMargins(0, 0, 0, 0); global_layout.setSpacing(0)

        # SIDEBAR
        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(15, 10, 15, 10); sidebar_layout.setSpacing(10)

        lbl_model = QLabel(tr("sidebar_model_header")); lbl_model.setObjectName("Header"); sidebar_layout.addWidget(lbl_model)
        model_row = QHBoxLayout(); self.model_combo = QComboBox(); self.refresh_base_models(); btn_br = QPushButton("..."); btn_br.setFixedSize(30, 28); btn_br.clicked.connect(self.browse_model); model_row.addWidget(self.model_combo); model_row.addWidget(btn_br); sidebar_layout.addLayout(model_row)
        btn_load = QPushButton(tr("btn_load_model")); btn_load.clicked.connect(self.load_model); sidebar_layout.addWidget(btn_load)

        sidebar_layout.addWidget(QLabel(tr("lbl_vae")))
        self.vae_combo = QComboBox()
        self.refresh_vae_models()
        sidebar_layout.addWidget(self.vae_combo)

        lbl_mix = QLabel(tr("lbl_latent_mixology")); lbl_mix.setObjectName("Header"); sidebar_layout.addWidget(lbl_mix)
        self.lora_visualizer = LoRAVisualizer(); sidebar_layout.addWidget(self.lora_visualizer)
        self.lora_list_widget = QWidget(); self.lora_list_layout = QVBoxLayout(self.lora_list_widget); self.lora_list_layout.setContentsMargins(0, 0, 0, 0); self.lora_list_layout.setSpacing(2); sidebar_layout.addWidget(self.lora_list_widget)
        btn_add_lora = QPushButton(tr("btn_add_lora")); btn_add_lora.setObjectName("SecondaryBtn"); btn_add_lora.clicked.connect(self.add_lora_dialog); sidebar_layout.addWidget(btn_add_lora)

        lbl_ups = QLabel(tr("lbl_global_upscaler")); lbl_ups.setObjectName("Header"); sidebar_layout.addWidget(lbl_ups)
        self.upscaler_combo = QComboBox(); self.refresh_upscalers(); sidebar_layout.addWidget(self.upscaler_combo)
        self.check_auto = QCheckBox(tr("chk_auto_upscale")); self.check_vram = QCheckBox(tr("chk_keep_vram"))
        sidebar_layout.addWidget(self.check_auto); sidebar_layout.addWidget(self.check_vram)

        lbl_samp = QLabel(tr("lbl_sampling_header")); lbl_samp.setObjectName("Header"); sidebar_layout.addWidget(lbl_samp)
        self.sampler_combo = QComboBox(); self.sampler_combo.addItems(["DPM++ 2M", "Euler", "Euler a", "DDIM"]); sidebar_layout.addWidget(self.sampler_combo)
        self.scheduler_combo = QComboBox(); self.scheduler_combo.addItems(["Normal", "Karras", "Exponential"]); sidebar_layout.addWidget(self.scheduler_combo)

        sidebar_layout.addStretch()
        btn_settings = QPushButton(tr("btn_settings")); btn_settings.setObjectName("ActionBtn"); btn_settings.clicked.connect(self.open_settings); sidebar_layout.addWidget(btn_settings)
        global_layout.addWidget(sidebar)

        self.tabs = QTabWidget(); global_layout.addWidget(self.tabs, 1)

        # 1. TEXT2IMAGE
        self.t2i_tab = QWidget(); self.tabs.addTab(self.t2i_tab, tr("tab_t2i")); t2i_l = QHBoxLayout(self.t2i_tab); t2i_params = QVBoxLayout(); t2i_params.setContentsMargins(15, 10, 15, 10); t2i_params.setSpacing(10); self.lbl_p = QLabel(tr("header_params")); self.lbl_p.setObjectName("Header"); t2i_params.addWidget(self.lbl_p); self.s_steps = ParameterSlider(tr("label_steps"), 1, 100, 20); self.s_cfg = ParameterSlider(tr("label_cfg"), 1.0, 20.0, 6.0, 0.5, True); self.s_w = ParameterSlider(tr("label_width"), 256, 1024, 512, 64); self.s_h = ParameterSlider(tr("label_height"), 256, 1024, 512, 64); self.s_seed = QLineEdit("-1"); self.s_seed.setValidator(QIntValidator(-1, 2147483647))
        for s in [self.s_steps, self.s_cfg, self.s_w, self.s_h]: t2i_params.addWidget(s)
        self.lbl_seed_t2i = QLabel(tr("label_seed")); t2i_params.addWidget(self.lbl_seed_t2i); t2i_params.addWidget(self.s_seed); t2i_params.addStretch()
        self.btn_gen_t2i = QPushButton(tr("btn_generate")); self.btn_gen_t2i.setObjectName("GenerateBtn"); self.btn_gen_t2i.setFixedHeight(45); self.btn_gen_t2i.clicked.connect(self.start_generation); t2i_params.addWidget(self.btn_gen_t2i); t2i_l.addLayout(t2i_params, 0)
        t2i_main = QVBoxLayout(); t2i_main.setContentsMargins(20, 10, 20, 0); self.t2i_prompt = QPlainTextEdit(); self.t2i_prompt.setPlaceholderText(tr("placeholder_prompt")); self.t2i_prompt.setFixedHeight(60); self.t2i_neg = QPlainTextEdit(); self.t2i_neg.setPlaceholderText(tr("placeholder_negative")); self.t2i_neg.setFixedHeight(35); self.lbl_prompt_t2i = QLabel(tr("label_prompt")); t2i_main.addWidget(self.lbl_prompt_t2i); t2i_main.addWidget(self.t2i_prompt); self.lbl_neg_t2i = QLabel(tr("label_negative")); t2i_main.addWidget(self.lbl_neg_t2i); t2i_main.addWidget(self.t2i_neg)
        self.preview_container = QWidget(); self.preview_layout = QHBoxLayout(self.preview_container); self.preview_layout.setContentsMargins(0, 0, 0, 0); self.preview_layout.setSpacing(20); self.c_orig = QWidget(); l_orig = QVBoxLayout(self.c_orig); l_orig.setContentsMargins(0, 0, 0, 0); self.l_orig_lbl = QLabel(tr("label_original")); self.l_orig_lbl.setStyleSheet("color: #00d4ff; font-weight: bold;"); self.l_orig_lbl.hide(); self.v_orig = ClickableLabel(tr("label_waiting")); self.v_orig.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_orig.setObjectName("PreviewArea"); self.v_orig.setStyleSheet("color: #444; font-size: 18px; font-weight: bold;"); self.v_orig.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_orig.setMinimumSize(1, 1); self.v_orig.clicked.connect(self.open_fullscreen); l_orig.addWidget(self.l_orig_lbl); l_orig.addWidget(self.v_orig, 1); self.c_ups = QWidget(); l_ups = QVBoxLayout(self.c_ups); l_ups.setContentsMargins(0, 0, 0, 0); self.l_ups_lbl = QLabel(tr("label_upscaled")); self.l_ups_lbl.setStyleSheet("color: #00d4ff; font-weight: bold;"); self.l_ups_lbl.hide(); self.v_ups = ClickableLabel(); self.v_ups.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_ups.setObjectName("PreviewArea"); self.v_ups.setStyleSheet("color: #444; font-size: 18px; font-weight: bold;"); self.v_ups.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_ups.setMinimumSize(1, 1); self.v_ups.clicked.connect(self.open_fullscreen); l_ups.addWidget(self.l_ups_lbl); l_ups.addWidget(self.v_ups, 1); self.c_ups.hide(); self.preview_layout.addWidget(self.c_orig, 1); self.preview_layout.addWidget(self.c_ups, 1); t2i_main.addWidget(self.preview_container, 1)
        up_box = QHBoxLayout(); self.btn_up = QPushButton(tr("btn_apply_upscaler")); self.btn_up.setObjectName("ActionBtn"); self.btn_up.clicked.connect(self.manual_upscale); self.btn_to_inpaint = QPushButton(tr("btn_send_to_inpaint")); self.btn_to_inpaint.setObjectName("ActionBtn"); self.btn_to_inpaint.clicked.connect(self.send_to_inpaint); up_box.addStretch(); up_box.addWidget(self.btn_up); up_box.addWidget(self.btn_to_inpaint); up_box.addStretch(); t2i_main.addLayout(up_box); s_box = QHBoxLayout(); self.l_status = QLabel(""); self.l_status.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 11px;"); self.btn_copy = QPushButton(tr("btn_copy")); self.btn_copy.setObjectName("CopyBtn"); self.btn_copy.hide(); self.btn_copy.clicked.connect(self.copy_seed_to_clipboard); s_box.addStretch(); s_box.addWidget(self.l_status); s_box.addWidget(self.btn_copy); s_box.addStretch(); t2i_main.addLayout(s_box); self.p_bar = QProgressBar(); t2i_main.addWidget(self.p_bar); t2i_l.addLayout(t2i_main, 1)

        # 2. INPAINTING
        self.inpaint_tab = QWidget()
        self.tabs.addTab(self.inpaint_tab, tr("tab_inpaint"))
        inp_l = QHBoxLayout(self.inpaint_tab)
        inp_params = QVBoxLayout()
        inp_params.setContentsMargins(15, 10, 15, 10)
        inp_params.setSpacing(10)

        self.lbl_it = QLabel(tr("header_inpaint_tools"))
        self.lbl_it.setObjectName("Header")
        inp_params.addWidget(self.lbl_it)

        self.inp_model_combo = QComboBox()
        self.inp_model_combo.addItem(tr("opt_use_main_model"), "original")
        self.refresh_inpaint_models()
        inp_params.addWidget(self.inp_model_combo)

        self.btn_load_inp_model = QPushButton(tr("btn_load_inpaint_model"))
        self.btn_load_inp_model.setObjectName("SecondaryBtn")
        self.btn_load_inp_model.clicked.connect(self.explicit_load_inpaint_model)
        inp_params.addWidget(self.btn_load_inp_model)

        self.i_steps = ParameterSlider(tr("label_steps"), 1, 100, 30)
        self.i_cfg = ParameterSlider(tr("label_cfg"), 1.0, 20.0, 7.5, 0.5, True)
        self.i_denoise = ParameterSlider(tr("label_denoise"), 0.0, 1.0, 0.75, 0.05, True)
        inp_params.addWidget(self.i_steps)
        inp_params.addWidget(self.i_cfg)
        inp_params.addWidget(self.i_denoise)

        self.lbl_brush_inp = QLabel(tr("label_brush"))
        inp_params.addWidget(self.lbl_brush_inp)
        self.brush_sl = QSlider(Qt.Orientation.Horizontal)
        self.brush_sl.setRange(5, 100)
        self.brush_sl.setValue(20)
        inp_params.addWidget(self.brush_sl)

        self.btn_load_i = QPushButton(tr("btn_load_image"))
        self.btn_load_i.setObjectName("SecondaryBtn")
        self.btn_load_i.clicked.connect(self.load_inpaint_image)
        inp_params.addWidget(self.btn_load_i)

        self.btn_tips_inp = QPushButton(tr("btn_tips"))
        self.btn_tips_inp.setObjectName("SecondaryBtn")
        self.btn_tips_inp.clicked.connect(lambda: self.show_tips("Wskazówki Inpainting", "docs/tips_inpaint.html"))
        inp_params.addWidget(self.btn_tips_inp)

        undo_redo_l = QHBoxLayout()
        self.btn_undo = QPushButton(tr("btn_undo"))
        self.btn_undo.setObjectName("SecondaryBtn")
        self.btn_redo = QPushButton(tr("btn_redo"))
        self.btn_redo.setObjectName("SecondaryBtn")
        undo_redo_l.addWidget(self.btn_undo)
        undo_redo_l.addWidget(self.btn_redo)
        inp_params.addLayout(undo_redo_l)

        inp_params.addStretch()

        self.btn_gen_inp = QPushButton(tr("btn_generate_fix"))
        self.btn_gen_inp.setObjectName("GenerateBtn")
        self.btn_gen_inp.clicked.connect(self.start_inpaint)
        inp_params.addWidget(self.btn_gen_inp)

        inp_l.addLayout(inp_params, 0)
        inp_main = QVBoxLayout(); inp_main.setContentsMargins(20, 10, 20, 0); self.i_prompt = QPlainTextEdit(); self.i_prompt.setPlaceholderText(tr("placeholder_prompt")); self.i_prompt.setFixedHeight(50); self.i_neg = QPlainTextEdit(); self.i_neg.setPlaceholderText(tr("placeholder_negative")); self.i_neg.setFixedHeight(30); inp_main.addWidget(QLabel(tr("label_prompt"))); inp_main.addWidget(self.i_prompt); inp_main.addWidget(QLabel(tr("label_negative"))); inp_main.addWidget(self.i_neg); self.canvas_scroll = QScrollArea(); self.canvas_scroll.setWidgetResizable(True); self.canvas = InpaintCanvas(); self.canvas_scroll.setWidget(self.canvas); inp_main.addWidget(self.canvas_scroll, 1); self.brush_sl.valueChanged.connect(lambda v: setattr(self.canvas, 'brush_size', v));
        self.btn_undo.clicked.connect(self.canvas.undo_stack.undo)
        self.btn_redo.clicked.connect(self.canvas.undo_stack.redo)
        self.i_progress = QProgressBar(); inp_main.addWidget(self.i_progress); inp_l.addLayout(inp_main, 1)

        # 3. CONTROLNET
        self.cn_tab = QWidget(); self.tabs.addTab(self.cn_tab, tr("tab_controlnet")); cn_l = QHBoxLayout(self.cn_tab); cn_params = QVBoxLayout(); cn_params.setContentsMargins(15, 10, 15, 10); cn_params.setSpacing(10); lbl_ct = QLabel(tr("header_controlnet_tools")); lbl_ct.setObjectName("Header"); cn_params.addWidget(lbl_ct); self.cn_model_combo = QComboBox(); self.refresh_cn_models(); cn_params.addWidget(self.cn_model_combo); self.cn_steps = ParameterSlider(tr("label_steps"), 1, 100, 25); self.cn_cfg = ParameterSlider(tr("label_cfg"), 1.0, 20.0, 7.5, 0.5, True); self.cn_strength = ParameterSlider(tr("label_weight"), 0.0, 2.0, 1.0, 0.1, True); self.cn_w = ParameterSlider(tr("label_width"), 256, 1024, 512, 64); self.cn_h = ParameterSlider(tr("label_height"), 256, 1024, 512, 64); self.cn_seed = QLineEdit("-1"); self.cn_seed.setValidator(QIntValidator(-1, 2147483647))
        for s in [self.cn_steps, self.cn_cfg, self.cn_strength, self.cn_w, self.cn_h]: cn_params.addWidget(s)
        cn_params.addWidget(QLabel(tr("label_seed"))); cn_params.addWidget(self.cn_seed); self.btn_load_cn = QPushButton(tr("btn_load_ref")); self.btn_load_cn.setObjectName("SecondaryBtn"); self.btn_load_cn.clicked.connect(self.load_cn_image); cn_params.addWidget(self.btn_load_cn); self.btn_tips_cn = QPushButton(tr("btn_tips")); self.btn_tips_cn.setObjectName("SecondaryBtn"); self.btn_tips_cn.clicked.connect(lambda: self.show_tips("Wskazówki ControlNet", "docs/tips_controlnet.html")); cn_params.addWidget(self.btn_tips_cn); cn_params.addStretch(); self.btn_gen_cn = QPushButton(tr("btn_generate_comp")); self.btn_gen_cn.setObjectName("GenerateBtn"); self.btn_gen_cn.clicked.connect(self.start_controlnet); cn_params.addWidget(self.btn_gen_cn); cn_l.addLayout(cn_params, 0)
        cn_main = QVBoxLayout(); cn_main.setContentsMargins(20, 10, 20, 0); self.cn_prompt = QPlainTextEdit(); self.cn_prompt.setPlaceholderText(tr("placeholder_prompt")); self.cn_prompt.setFixedHeight(50); self.cn_neg = QPlainTextEdit(); self.cn_neg.setPlaceholderText(tr("placeholder_negative")); self.cn_neg.setFixedHeight(30); cn_main.addWidget(QLabel(tr("label_prompt"))); cn_main.addWidget(self.cn_prompt); cn_main.addWidget(QLabel(tr("label_negative"))); cn_main.addWidget(self.cn_neg); self.cn_preview = ClickableLabel(tr("placeholder_drop")); self.cn_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cn_preview.setObjectName("PreviewArea"); self.cn_preview.setStyleSheet("border: 2px dashed #333; color: #555;"); cn_main.addWidget(self.cn_preview, 1); self.cn_progress = QProgressBar(); cn_main.addWidget(self.cn_progress); cn_l.addLayout(cn_main, 1)

        self.setAcceptDrops(True)

        # 4. GALLERY
        self.gal_tab = QWidget(); self.tabs.addTab(self.gal_tab, tr("tab_gallery")); gal_l = QVBoxLayout(self.gal_tab)
        h_gal = QHBoxLayout(); btn_ref = QPushButton(tr("btn_refresh_gallery")); btn_ref.setObjectName("ActionBtn"); btn_ref.clicked.connect(self.refresh_gallery); h_gal.addWidget(btn_ref); h_gal.addStretch(); gal_l.addLayout(h_gal)
        self.gal_list = QListWidget(); self.gal_list.setViewMode(QListWidget.ViewMode.IconMode); self.gal_list.setResizeMode(QListWidget.ResizeMode.Adjust); self.gal_list.setIconSize(QSize(200, 200)); self.gal_list.setSpacing(10); self.gal_list.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;"); self.gal_list.itemDoubleClicked.connect(self.open_gallery_detail); gal_l.addWidget(self.gal_list)

        self.apply_settings_ui()
        self.refresh_gallery()
        self.showMaximized()

    def apply_settings_ui(self):
        accent = settings.get('UI', 'accent_color')
        is_dark = settings.get('UI', 'theme') == 'dark'
        self.setStyleSheet(get_style(accent, is_dark))
        self.sampler_combo.setCurrentText(settings.get('Generation', 'default_sampler'))
        self.scheduler_combo.setCurrentText(settings.get('Generation', 'default_scheduler'))

        vae_val = settings.get('Generation', 'default_vae')
        idx = self.vae_combo.findData(vae_val)
        if idx < 0: idx = self.vae_combo.findText(vae_val)
        if idx >= 0: self.vae_combo.setCurrentIndex(idx)

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def refresh_all_comboboxes(self, path=None):
        logger.info(f"[SYSTEM] Wykryto zmiany w folderach modeli, odświeżanie list...")
        self.refresh_base_models()
        self.refresh_vae_models()
        self.refresh_inpaint_models()
        self.refresh_cn_models()
        self.refresh_upscalers()

    def refresh_base_models(self):
        curr = self.model_combo.currentText()
        self.model_combo.clear()
        path = settings.get('Paths', 'models_sd')
        for f in self.scan_models(path): self.model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.model_combo.findText(curr)
            if idx >= 0: self.model_combo.setCurrentIndex(idx)

    def refresh_vae_models(self):
        curr = self.vae_combo.currentText()
        self.vae_combo.clear()
        self.vae_combo.addItem(tr("opt_default_vae"), "Domyślne (z modelu)")
        path = settings.get('Paths', 'models_vae')
        vae_exts = (".safetensors", ".pt", ".ckpt")
        for f in self.scan_models(path, exts=vae_exts):
            self.vae_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.vae_combo.findText(curr)
            if idx >= 0: self.vae_combo.setCurrentIndex(idx)
    def explicit_load_inpaint_model(self):
        m = self.inp_model_combo.currentData()
        if m: self.btn_gen_inp.setEnabled(False); self.i_progress.setFormat(tr("status_loading_inpaint")); self.engine.load_inpaint_model(m); self.btn_gen_inp.setEnabled(True); self.i_progress.setFormat(tr("status_inpaint_ready"))
    def refresh_upscalers(self):
        curr = self.upscaler_combo.currentText()
        self.upscaler_combo.clear(); self.upscaler_combo.addItem(tr("opt_no_upscaler"), "")
        path = settings.get('Paths', 'models_upscalers')
        ups_exts = (".pth", ".pt", ".bin", ".onnx", ".safetensors", ".ckpt")
        for f in self.scan_models(path, exts=ups_exts):
            self.upscaler_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.upscaler_combo.findText(curr)
            if idx >= 0: self.upscaler_combo.setCurrentIndex(idx)

    def refresh_inpaint_models(self):
        curr = self.inp_model_combo.currentText()
        # zachowaj statyczny wpis
        self.inp_model_combo.clear()
        self.inp_model_combo.addItem(tr("opt_use_main_model"), "original")
        path = settings.get('Paths', 'models_inpaint')
        for f in self.scan_models(path): self.inp_model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.inp_model_combo.findText(curr)
            if idx >= 0: self.inp_model_combo.setCurrentIndex(idx)

    def refresh_cn_models(self):
        curr = self.cn_model_combo.currentText()
        self.cn_model_combo.clear()
        path = settings.get('Paths', 'models_controlnet')
        for f in self.scan_models(path): self.cn_model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.cn_model_combo.findText(curr)
            if idx >= 0: self.cn_model_combo.setCurrentIndex(idx)
    def browse_model(self):
        file, _ = QFileDialog.getOpenFileName(self, tr("dialog_model"), "", "Safetensors (*.safetensors);;All Files (*)")
        if file: name = os.path.basename(file); self.model_combo.insertItem(0, name, file); self.model_combo.setCurrentIndex(0)
    def add_lora_dialog(self):
        if len(self.loras) >= 5: return
        file, _ = QFileDialog.getOpenFileName(self, tr("dialog_lora"), "", "Safetensors (*.safetensors)")
        if file:
            name = os.path.basename(file).split('.')[0]
            if name in self.loras: name += f"_{len(self.loras)}"
            self.engine.load_lora(file, name); item = LoRAItem(name, file); item.removed.connect(self.remove_lora); item.changed.connect(self.update_lora_visualizer); self.lora_list_layout.addWidget(item); self.loras[name] = item; self.update_lora_visualizer()
    def remove_lora(self, name):
        if name in self.loras:
            self.engine.unload_lora(name)
            item = self.loras.pop(name); self.lora_list_layout.removeWidget(item); item.deleteLater(); self.update_lora_visualizer()
    def update_lora_visualizer(self): self.lora_visualizer.update_weights([(n, i.weight()) for n, i in self.loras.items()])
    def load_model(self):
        m = self.model_combo.currentData()
        if m:
            self.btn_gen_t2i.setEnabled(False)
            self.p_bar.setFormat(tr("status_loading_model"))
            self.engine.load_model(m)
            # Przeładowanie LoRA do nowego pipeline
            for name, lora_item in self.loras.items():
                self.engine.load_lora(lora_item.path, name)
            self.btn_gen_t2i.setEnabled(True)
            self.p_bar.setFormat(tr("status_model_ready"))
    def start_generation(self):
        if not self.engine.pipe: return QMessageBox.warning(self, tr("status_error"), tr("status_model_error"))
        try: sv = int(self.s_seed.text())
        except: sv = -1
        params = {
            "prompt": self.t2i_prompt.toPlainText(),
            "neg_prompt": self.t2i_neg.toPlainText(),
            "steps": self.s_steps.value(),
            "cfg": self.s_cfg.value(),
            "width": self.s_w.value(),
            "height": self.s_h.value(),
            "seed": sv,
            "auto_upscale": self.check_auto.isChecked(),
            "upscaler_model": self.upscaler_combo.currentData(),
            "keep_upscaler_vram": self.check_vram.isChecked(),
            "loras": [{'name': n, 'weight': i.weight()} for n, i in self.loras.items()],
            "sampler": self.sampler_combo.currentText(),
            "scheduler": self.scheduler_combo.currentText(),
            "vae_path": self.vae_combo.currentData()
        }
        self.btn_gen_t2i.setEnabled(False); self.p_bar.setMaximum(params["steps"]); self.p_bar.setValue(0); self.worker = GenerationWorker(self.engine, params); self.worker.progress.connect(self.p_bar.setValue); self.worker.status.connect(self.l_status.setText); self.worker.part_finished.connect(self.on_base_finished); self.worker.finished.connect(self.on_generation_finished); self.worker.start()
    def manual_upscale(self):
        if not self.last_generated_path or not self.upscaler_combo.currentData(): return QMessageBox.warning(self, tr("status_error"), tr("status_no_data"))
        self.btn_up.setEnabled(False); self.p_bar.setFormat(tr("status_upscaling")); self.up_w = UpscaleWorker(self.engine, self.last_generated_path, self.upscaler_combo.currentData(), self.check_vram.isChecked()); self.up_w.status.connect(self.l_status.setText); self.up_w.finished.connect(self.on_upscale_finished); self.up_w.start()
    def on_base_finished(self, path, seed):
        self.last_generated_path = path; self.last_upscaled_path = None; self.v_orig.set_image(path); self.v_orig.setText(""); self.l_orig_lbl.hide(); self.l_ups_lbl.hide(); self.c_ups.hide()
        if isinstance(seed, int): self.current_seed = seed; self.l_status.setText(f"{tr('status_seed')}{seed}"); self.btn_copy.show()
        else: self.l_status.setText(str(seed)); self.btn_copy.hide()
    def on_generation_finished(self, path, seed):
        self.btn_gen_t2i.setEnabled(True); self.p_bar.setFormat(tr("status_done")); self.p_bar.setMaximum(100); self.p_bar.setValue(100)
        if "_upscaled" in path: self.last_upscaled_path = path; self.v_ups.set_image(path); self.v_ups.setText(""); self.l_orig_lbl.show(); self.l_ups_lbl.show(); self.c_ups.show(); self.l_status.setText(tr("status_finished"))
    def on_upscale_finished(self, path):
        if path: self.on_generation_finished(path, "N/A"); self.btn_up.setEnabled(True)
        else: self.btn_up.setEnabled(True); self.p_bar.setFormat(tr("status_upscale_error"))
    def copy_seed_to_clipboard(self):
        if self.current_seed is not None: QApplication.clipboard().setText(str(self.current_seed))
    def open_fullscreen(self, pixmap): ImageViewer(pixmap, self).exec()
    def send_to_inpaint(self):
        if self.last_generated_path: self.canvas.set_base_image(QPixmap(self.last_generated_path)); self.tabs.setCurrentIndex(1)
    def load_inpaint_image(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg)")
        if f: self.canvas.set_base_image(QPixmap(f))
    def start_inpaint(self):
        if not self.engine.inpaint_pipe and not self.engine.pipe: return QMessageBox.warning(self, tr("status_error"), tr("status_model_error"))
        params = {
            "prompt": self.i_prompt.toPlainText(),
            "neg_prompt": self.i_neg.toPlainText(),
            "image": self.canvas.get_image_pil(),
            "mask": self.canvas.get_mask_pil(),
            "steps": self.i_steps.value(),
            "cfg": self.i_cfg.value(),
            "strength": self.i_denoise.value(),
            "inpaint_model": self.inp_model_combo.currentData(),
            "sampler": self.sampler_combo.currentText(),
            "scheduler": self.scheduler_combo.currentText(),
            "vae_path": self.vae_combo.currentData()
        }
        self.btn_gen_inp.setEnabled(False); self.i_progress.setMaximum(0); self.i_progress.setValue(0); self.in_worker = InpaintWorker(self.engine, params); self.in_worker.status.connect(self.i_progress.setFormat); self.in_worker.finished.connect(self.on_inpaint_finished); self.in_worker.start()
    def on_inpaint_finished(self, path, seed):
        self.btn_gen_inp.setEnabled(True); self.i_progress.setMaximum(100); self.i_progress.setValue(100); self.i_progress.setFormat(f"{tr('status_done')} ({seed})"); ImageViewer(QPixmap(path), self).exec()
    def load_cn_image(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_ref"), "", "Images (*.png *.jpg *.jpeg)")
        if f: self.set_cn_ref_image(f)
    def set_cn_ref_image(self, path):
        pix = QPixmap(path); scaled = pix.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logger.info(f"[SYSTEM] Skalowanie CN: {pix.width()}x{pix.height()} -> {scaled.width()}x{scaled.height()}"); self.cn_preview.set_image(scaled); self.cn_preview.setText("")
        self.ref_image_pil = qimage_to_pil(scaled.toImage())
    def start_controlnet(self):
        if not self.engine.pipe or not self.ref_image_pil: return QMessageBox.warning(self, tr("status_error"), tr("status_no_data"))
        try: sv = int(self.cn_seed.text())
        except: sv = -1
        params = {
            "prompt": self.cn_prompt.toPlainText(),
            "neg_prompt": self.cn_neg.toPlainText(),
            "image": self.ref_image_pil,
            "strength": self.cn_strength.value(),
            "steps": self.cn_steps.value(),
            "cfg": self.cn_cfg.value(),
            "width": self.cn_w.value(),
            "height": self.cn_h.value(),
            "seed": sv,
            "cn_model": self.cn_model_combo.currentData(),
            "sampler": self.sampler_combo.currentText(),
            "scheduler": self.scheduler_combo.currentText(),
            "vae_path": self.vae_combo.currentData()
        }
        self.btn_gen_cn.setEnabled(False); self.cn_progress.setMaximum(0); self.cn_progress.setValue(0); self.cn_wkr = ControlNetWorker(self.engine, params); self.cn_wkr.status.connect(self.cn_progress.setFormat); self.cn_wkr.finished.connect(self.on_cn_finished); self.cn_wkr.start()
    def on_cn_finished(self, path, seed):
        self.btn_gen_cn.setEnabled(True); self.cn_progress.setMaximum(100); self.cn_progress.setValue(100); self.cn_progress.setFormat(f"{tr('status_done')} ({seed})"); ImageViewer(QPixmap(path), self).exec()

    def refresh_gallery(self):
        self.gal_list.clear()
        folder = settings.get('Paths', 'output_txt2img')
        if not os.path.exists(folder): return

        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")]
        # Sortowanie po dacie modyfikacji (najnowsze pierwsze)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        for path in files:
            item = QListWidgetItem(QIcon(path), "")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.gal_list.addItem(item)

    def open_gallery_detail(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path: self.gallery_detail = GalleryDetailWindow(path, self); self.gallery_detail.show()
    def show_tips(self, title, path):
        self.tips_window = FloatingTips(title, path, self); self.tips_window.show()
    def resizeEvent(self, event):
        super().resizeEvent(event); self.v_orig.update_scaling(); self.v_ups.update_scaling()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())

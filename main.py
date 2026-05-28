import sys
import os

import boot

print("[UI] Importing PyQt6...")
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator, QColor

from engine import DiffusionEngine
from model_manager import ModelManager
from generation_controller import GenerationController
from mode_controllers import InpaintController, ControlNetController, ADetailerController
from config import get_style, settings, logger, tr
from widgets import (
    ImageViewer, ClickableLabel, InpaintCanvas, ParameterSlider,
    LoRAVisualizer, FloatingTips, GalleryDetailWindow,
    SettingsDialog, WelcomeDialog, ModelDownloaderTab,
    PromptBuilderPanel, ResourceMonitor, BatchThumbnailBar,
    ClipInterrogatorTab, RestorationTab
)

APP_VERSION = "2.21.0"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("[STARTUP] Initializing MainWindow...")
        self.engine = DiffusionEngine()
        logger.info("[STARTUP] DiffusionEngine created")
        self.model_mgr = ModelManager(self.engine, self)
        self.model_mgr.setup_folders()
        logger.info("[STARTUP] Folders ready")
        self.model_mgr.setup_watchers()
        logger.info("[STARTUP] File watchers active")
        self.last_generated_path = None
        self.img2img_image_pil = None
        self.gen_ctrl = GenerationController(self.engine, self.model_mgr, self)
        self.inp_ctrl = InpaintController(self.engine, self)
        self.cn_ctrl = ControlNetController(self.engine, self)
        self.adet_ctrl = ADetailerController(self.engine, self)
        logger.info("[STARTUP] Generation controllers created")
        self.tips_window = None

        self.init_ui()
        logger.info("[STARTUP] UI initialized")

        if settings.is_first_run:
            logger.info("[STARTUP] First run - showing WelcomeDialog")
            WelcomeDialog(self).exec()
            self.apply_settings_ui()
    def init_ui(self):
        self.setWindowTitle(f"Swift Diffusion v{APP_VERSION}")
        logger.info("[UI] Building interface...")
        central_widget = QWidget(); self.setCentralWidget(central_widget); global_layout = QHBoxLayout(central_widget); global_layout.setContentsMargins(0, 0, 0, 0); global_layout.setSpacing(0)

        # SIDEBAR
        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar_layout = QVBoxLayout(sidebar); sidebar_layout.setContentsMargins(15, 10, 15, 10); sidebar_layout.setSpacing(10)

        lbl_model = QLabel(tr("sidebar_model_header")); lbl_model.setObjectName("Header"); sidebar_layout.addWidget(lbl_model)
        model_row = QHBoxLayout(); self.model_combo = QComboBox(); self.model_mgr.refresh_base_models(); btn_br = QPushButton("..."); btn_br.setFixedSize(30, 28); btn_br.clicked.connect(self.model_mgr.browse_model); model_row.addWidget(self.model_combo); model_row.addWidget(btn_br); sidebar_layout.addLayout(model_row)
        self.btn_load = QPushButton(tr("btn_load_model")); self.btn_load.clicked.connect(self.model_mgr.load_model); sidebar_layout.addWidget(self.btn_load)

        self.load_progress = QProgressBar(); self.load_progress.setFixedHeight(8); self.load_progress.setTextVisible(False); self.load_progress.hide(); sidebar_layout.addWidget(self.load_progress)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.Shape.HLine); sep1.setStyleSheet("color: #333;"); sidebar_layout.addWidget(sep1)

        sidebar_layout.addWidget(QLabel(tr("lbl_vae")))
        self.vae_combo = QComboBox()
        self.model_mgr.refresh_vae_models()
        sidebar_layout.addWidget(self.vae_combo)

        lbl_samp = QLabel(tr("lbl_sampling_header")); lbl_samp.setObjectName("Header"); sidebar_layout.addWidget(lbl_samp)
        self.sampler_combo = QComboBox(); self.sampler_combo.addItems(["DPM++ 2M", "Euler", "Euler a", "DDIM"]); sidebar_layout.addWidget(self.sampler_combo)
        self.scheduler_combo = QComboBox(); self.scheduler_combo.addItems(["Normal", "Karras", "Exponential"]); sidebar_layout.addWidget(self.scheduler_combo)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine); sep2.setStyleSheet("color: #333;"); sidebar_layout.addWidget(sep2)

        lbl_mix = QLabel(tr("lbl_latent_mixology")); lbl_mix.setObjectName("Header"); sidebar_layout.addWidget(lbl_mix)
        self.lora_visualizer = LoRAVisualizer(); sidebar_layout.addWidget(self.lora_visualizer)
        self.lora_list_widget = QWidget(); self.lora_list_layout = QVBoxLayout(self.lora_list_widget); self.lora_list_layout.setContentsMargins(0, 0, 0, 0); self.lora_list_layout.setSpacing(2); sidebar_layout.addWidget(self.lora_list_widget)
        btn_add_lora = QPushButton(tr("btn_add_lora")); btn_add_lora.setObjectName("SecondaryBtn"); btn_add_lora.clicked.connect(self.model_mgr.add_lora_dialog); sidebar_layout.addWidget(btn_add_lora)

        sep3 = QFrame(); sep3.setFrameShape(QFrame.Shape.HLine); sep3.setStyleSheet("color: #333;"); sidebar_layout.addWidget(sep3)

        lbl_ups = QLabel(tr("lbl_global_upscaler")); lbl_ups.setObjectName("Header"); sidebar_layout.addWidget(lbl_ups)
        self.upscaler_combo = QComboBox(); self.model_mgr.refresh_upscalers(); sidebar_layout.addWidget(self.upscaler_combo)

        opt_frame = QFrame(); opt_frame.setStyleSheet("border: 1px solid #333; border-radius: 4px; padding: 4px;"); opt_l = QVBoxLayout(opt_frame); opt_l.setContentsMargins(6, 4, 6, 4); opt_l.setSpacing(2)
        self.check_auto = QCheckBox(tr("chk_auto_upscale")); opt_l.addWidget(self.check_auto)
        self.check_vram = QCheckBox(tr("chk_keep_vram")); opt_l.addWidget(self.check_vram)
        sidebar_layout.addWidget(opt_frame)
        opt_shadow = QGraphicsDropShadowEffect(); opt_shadow.setBlurRadius(12); opt_shadow.setColor(QColor(0, 0, 0, 60)); opt_shadow.setOffset(0, 2); opt_frame.setGraphicsEffect(opt_shadow)

        sidebar_layout.addStretch()

        self.resource_monitor = ResourceMonitor()
        sidebar_layout.addWidget(self.resource_monitor)

        btn_settings = QPushButton(tr("btn_settings")); btn_settings.setObjectName("ActionBtn"); btn_settings.clicked.connect(self.open_settings); sidebar_layout.addWidget(btn_settings)
        global_layout.addWidget(sidebar)

        self.tabs = QTabWidget(); global_layout.addWidget(self.tabs, 1)

        # 1. TEXT2IMAGE
        logger.info("[UI] Building T2I tab...")
        self.t2i_tab = QWidget(); self.tabs.addTab(self.t2i_tab, tr("tab_t2i")); t2i_l = QHBoxLayout(self.t2i_tab); t2i_params = QVBoxLayout(); t2i_params.setContentsMargins(15, 10, 15, 10); t2i_params.setSpacing(10); self.lbl_p = QLabel(tr("header_params")); self.lbl_p.setObjectName("Header"); t2i_params.addWidget(self.lbl_p); self.s_steps = ParameterSlider(tr("label_steps"), 1, 100, 20); self.s_cfg = ParameterSlider(tr("label_cfg"), 1.0, 20.0, 6.0, 0.5, True); self.s_w = ParameterSlider(tr("label_width"), 256, 2048, 512, 64); self.s_h = ParameterSlider(tr("label_height"), 256, 2048, 512, 64); self.s_seed = QLineEdit("-1"); self.s_seed.setValidator(QIntValidator(-1, 2147483647))
        for s in [self.s_steps, self.s_cfg, self.s_w, self.s_h]: t2i_params.addWidget(s)
        self.lbl_seed_t2i = QLabel(tr("label_seed")); t2i_params.addWidget(self.lbl_seed_t2i); t2i_params.addWidget(self.s_seed)

        # Img2Img section
        self.chk_img2img = QCheckBox(tr("chk_img2img"))
        self.chk_img2img.toggled.connect(self.toggle_img2img_ui)
        t2i_params.addWidget(self.chk_img2img)

        self.img2img_strength = ParameterSlider(tr("label_strength"), 0.0, 1.0, 0.75, 0.05, True)
        self.img2img_strength.hide()
        t2i_params.addWidget(self.img2img_strength)

        self.btn_load_img2img = QPushButton(tr("btn_load_img2img"))
        self.btn_load_img2img.setObjectName("SecondaryBtn")
        self.btn_load_img2img.clicked.connect(self.load_img2img_image)
        self.btn_load_img2img.hide()
        t2i_params.addWidget(self.btn_load_img2img)

        self.img2img_preview = ClickableLabel(tr("label_no_image"))
        self.img2img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img2img_preview.setObjectName("PreviewArea")
        self.img2img_preview.setStyleSheet("border: 2px dashed #333; color: #555; font-size: 11px;")
        self.img2img_preview.setFixedHeight(80)
        self.img2img_preview.hide()
        t2i_params.addWidget(self.img2img_preview)

        t2i_params.addStretch()

        self.live_preview = QLabel()
        self.live_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_preview.setFixedHeight(160)
        self.live_preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.live_preview.setStyleSheet("border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; color: #444; font-size: 12px;")
        self.live_preview.hide()
        t2i_params.addWidget(self.live_preview)
        batch_row = QHBoxLayout()
        self.lbl_batch = QLabel(tr("batch_label"))
        self.lbl_batch.setStyleSheet("color: #aaa; font-size: 11px;")
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 10)
        self.batch_spin.setValue(1)
        self.batch_spin.setFixedWidth(50)
        self.batch_spin.setToolTip(tr("batch_tooltip"))
        batch_row.addWidget(self.lbl_batch)
        batch_row.addWidget(self.batch_spin)
        batch_row.addStretch()
        t2i_params.addLayout(batch_row)

        self.btn_gen_t2i = QPushButton(tr("btn_generate")); self.btn_gen_t2i.setObjectName("GenerateBtn"); self.btn_gen_t2i.setFixedHeight(45); self.btn_gen_t2i.setMinimumWidth(180); self.btn_gen_t2i.clicked.connect(self.gen_ctrl.start_generation); t2i_params.addWidget(self.btn_gen_t2i); t2i_l.addLayout(t2i_params, 0)
        t2i_main = QVBoxLayout(); t2i_main.setContentsMargins(20, 10, 20, 0); self.t2i_prompt = QPlainTextEdit(); self.t2i_prompt.setPlaceholderText(tr("placeholder_prompt")); self.t2i_prompt.setFixedHeight(60); self.t2i_neg = QPlainTextEdit(); self.t2i_neg.setPlaceholderText(tr("placeholder_negative")); self.t2i_neg.setFixedHeight(50); self.lbl_prompt_t2i = QLabel(tr("label_prompt")); self.lbl_compel = QLabel(); self.lbl_compel.setStyleSheet("color: #666; font-size: 10px;"); t2i_main.addWidget(self.lbl_prompt_t2i); t2i_main.addWidget(self.lbl_compel); self.lbl_wildcards_t2i = QLabel(tr("wildcards_tooltip")); self.lbl_wildcards_t2i.setStyleSheet("color: #666; font-size: 10px; margin-top: -4px;"); t2i_main.addWidget(self.lbl_wildcards_t2i); t2i_main.addWidget(self.t2i_prompt); self.lbl_neg_t2i = QLabel(tr("label_negative")); t2i_main.addWidget(self.lbl_neg_t2i); t2i_main.addWidget(self.t2i_neg)

        self.preview_container = QWidget(); self.preview_layout = QHBoxLayout(self.preview_container); self.preview_layout.setContentsMargins(0, 0, 0, 0); self.preview_layout.setSpacing(20)

        self.c_orig = QWidget(); l_orig = QVBoxLayout(self.c_orig); l_orig.setContentsMargins(0, 0, 0, 0); self.l_orig_lbl = QLabel(tr("label_original")); self.l_orig_lbl.setStyleSheet("color: #00d4ff; font-weight: bold;"); self.l_orig_lbl.hide(); self.v_orig = ClickableLabel(tr("label_waiting")); self.v_orig.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_orig.setObjectName("PreviewArea"); self.v_orig.setStyleSheet("color: #444; font-size: 18px; font-weight: bold;"); self.v_orig.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_orig.setMinimumSize(1, 1); self.v_orig.clicked.connect(self.open_fullscreen); l_orig.addWidget(self.l_orig_lbl); l_orig.addWidget(self.v_orig, 1)

        self.c_ups = QWidget(); l_ups = QVBoxLayout(self.c_ups); l_ups.setContentsMargins(0, 0, 0, 0); self.l_ups_lbl = QLabel(tr("label_upscaled")); self.l_ups_lbl.setStyleSheet("color: #00d4ff; font-weight: bold;"); self.l_ups_lbl.hide(); self.v_ups = ClickableLabel(); self.v_ups.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_ups.setObjectName("PreviewArea"); self.v_ups.setStyleSheet("color: #444; font-size: 18px; font-weight: bold;"); self.v_ups.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_ups.setMinimumSize(1, 1); self.v_ups.clicked.connect(self.open_fullscreen); l_ups.addWidget(self.l_ups_lbl); l_ups.addWidget(self.v_ups, 1); self.c_ups.hide()

        self.preview_layout.addWidget(self.c_orig, 1); self.preview_layout.addWidget(self.c_ups, 1); t2i_main.addWidget(self.preview_container, 1)

        up_box = QHBoxLayout(); self.btn_up = QPushButton(tr("btn_apply_upscaler")); self.btn_up.setObjectName("ActionBtn"); self.btn_up.clicked.connect(self.gen_ctrl.manual_upscale)
        self.btn_face = QPushButton(tr("btn_apply_adetailer")); self.btn_face.setObjectName("ActionBtn"); self.btn_face.clicked.connect(self.adet_ctrl.send_to_adetailer)
        self.btn_to_inpaint = QPushButton(tr("btn_send_to_inpaint")); self.btn_to_inpaint.setObjectName("ActionBtn"); self.btn_to_inpaint.clicked.connect(self.inp_ctrl.send_to_inpaint)
        up_box.addStretch(); up_box.addWidget(self.btn_up); up_box.addWidget(self.btn_face); up_box.addWidget(self.btn_to_inpaint); up_box.addStretch(); t2i_main.addLayout(up_box)

        s_box = QHBoxLayout(); self.l_status = QLabel(""); self.l_status.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 11px;"); self.btn_copy = QPushButton(tr("btn_copy")); self.btn_copy.setObjectName("CopyBtn"); self.btn_copy.hide(); self.btn_copy.clicked.connect(self.gen_ctrl.copy_seed_to_clipboard); s_box.addStretch(); s_box.addWidget(self.l_status); s_box.addWidget(self.btn_copy); s_box.addStretch(); t2i_main.addLayout(s_box); self.p_bar = QProgressBar(); t2i_main.addWidget(self.p_bar)
        self.batch_thumb_container = QWidget()
        self.batch_thumb_layout = QVBoxLayout(self.batch_thumb_container)
        self.batch_thumb_layout.setContentsMargins(0, 0, 0, 0)
        self.batch_thumb_container.hide()
        t2i_main.addWidget(self.batch_thumb_container)
        t2i_l.addLayout(t2i_main, 1)

        # 2. INPAINTING
        logger.info("[UI] Building Inpaint tab...")
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
        self.model_mgr.refresh_inpaint_models()
        inp_params.addWidget(self.inp_model_combo)

        self.btn_load_inp_model = QPushButton(tr("btn_load_inpaint_model"))
        self.btn_load_inp_model.setObjectName("SecondaryBtn")
        self.btn_load_inp_model.clicked.connect(self.model_mgr.explicit_load_inpaint_model)
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
        self.btn_load_i.clicked.connect(self.inp_ctrl.load_inpaint_image)
        inp_params.addWidget(self.btn_load_i)

        self.btn_tips_inp = QPushButton(tr("btn_tips"))
        self.btn_tips_inp.setObjectName("SecondaryBtn")
        self.btn_tips_inp.clicked.connect(lambda: self.show_tips(tr("tips_title_inpaint"), "docs/tips_inpaint.html"))
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
        self.btn_gen_inp.setMinimumWidth(180)
        self.btn_gen_inp.clicked.connect(self.inp_ctrl.start_inpaint)
        inp_params.addWidget(self.btn_gen_inp)

        inp_l.addLayout(inp_params, 0)
        inp_main = QVBoxLayout(); inp_main.setContentsMargins(20, 10, 16, 0); self.i_prompt = QPlainTextEdit(); self.i_prompt.setPlaceholderText(tr("placeholder_prompt")); self.i_prompt.setFixedHeight(60); self.i_neg = QPlainTextEdit(); self.i_neg.setPlaceholderText(tr("placeholder_negative")); self.i_neg.setFixedHeight(50); inp_main.addWidget(QLabel(tr("label_prompt"))); self.lbl_wildcards_inp = QLabel(tr("wildcards_tooltip")); self.lbl_wildcards_inp.setStyleSheet("color: #666; font-size: 10px; margin-top: -4px;"); inp_main.addWidget(self.lbl_wildcards_inp); inp_main.addWidget(self.i_prompt); inp_main.addWidget(QLabel(tr("label_negative"))); inp_main.addWidget(self.i_neg);
        inp_previews = QHBoxLayout()
        self.canvas_scroll = QScrollArea(); self.canvas_scroll.setWidgetResizable(True); self.canvas = InpaintCanvas(); self.canvas_scroll.setWidget(self.canvas); inp_previews.addWidget(self.canvas_scroll, 1)
        self.v_inpaint_out = ClickableLabel(); self.v_inpaint_out.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_inpaint_out.setObjectName("PreviewArea"); self.v_inpaint_out.setStyleSheet("background-color: #1a1a1a;"); self.v_inpaint_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_inpaint_out.setMinimumSize(1, 1); self.v_inpaint_out.clicked.connect(self.open_fullscreen); inp_previews.addWidget(self.v_inpaint_out, 1)
        inp_main.addLayout(inp_previews, 1)
        self.brush_sl.valueChanged.connect(lambda v: setattr(self.canvas, 'brush_size', v));
        self.btn_undo.clicked.connect(self.canvas.undo_stack.undo)
        self.btn_redo.clicked.connect(self.canvas.undo_stack.redo)
        self.i_progress = QProgressBar(); inp_main.addWidget(self.i_progress); inp_l.addLayout(inp_main, 1)

        # 3. CONTROLNET
        logger.info("[UI] Building ControlNet tab...")
        self.cn_tab = QWidget(); self.tabs.addTab(self.cn_tab, tr("tab_controlnet")); cn_l = QHBoxLayout(self.cn_tab); cn_params = QVBoxLayout(); cn_params.setContentsMargins(15, 10, 15, 10); cn_params.setSpacing(10); lbl_ct = QLabel(tr("header_controlnet_tools")); lbl_ct.setObjectName("Header"); cn_params.addWidget(lbl_ct); self.cn_model_combo = QComboBox(); self.model_mgr.refresh_cn_models(); cn_params.addWidget(self.cn_model_combo); self.cn_steps = ParameterSlider(tr("label_steps"), 1, 100, 25); self.cn_cfg = ParameterSlider(tr("label_cfg"), 1.0, 20.0, 7.5, 0.5, True); self.cn_strength = ParameterSlider(tr("label_weight"), 0.0, 2.0, 1.0, 0.1, True); self.cn_w = ParameterSlider(tr("label_width"), 256, 2048, 512, 64); self.cn_h = ParameterSlider(tr("label_height"), 256, 2048, 512, 64); self.cn_seed = QLineEdit("-1"); self.cn_seed.setValidator(QIntValidator(-1, 2147483647))
        for s in [self.cn_steps, self.cn_cfg, self.cn_strength, self.cn_w, self.cn_h]: cn_params.addWidget(s)
        cn_params.addWidget(QLabel(tr("label_seed"))); cn_params.addWidget(self.cn_seed); self.btn_load_cn = QPushButton(tr("btn_load_ref")); self.btn_load_cn.setObjectName("SecondaryBtn"); self.btn_load_cn.clicked.connect(self.cn_ctrl.load_cn_image); cn_params.addWidget(self.btn_load_cn); self.btn_tips_cn = QPushButton(tr("btn_tips")); self.btn_tips_cn.setObjectName("SecondaryBtn"); self.btn_tips_cn.clicked.connect(lambda: self.show_tips(tr("tips_title_controlnet"), "docs/tips_controlnet.html")); cn_params.addWidget(self.btn_tips_cn); cn_params.addStretch(); self.btn_gen_cn = QPushButton(tr("btn_generate_comp")); self.btn_gen_cn.setObjectName("GenerateBtn"); self.btn_gen_cn.setMinimumWidth(180); self.btn_gen_cn.clicked.connect(self.cn_ctrl.start_controlnet); cn_params.addWidget(self.btn_gen_cn); cn_l.addLayout(cn_params, 0)
        cn_main = QVBoxLayout(); cn_main.setContentsMargins(20, 10, 16, 0); self.cn_prompt = QPlainTextEdit(); self.cn_prompt.setPlaceholderText(tr("placeholder_prompt")); self.cn_prompt.setFixedHeight(60); self.cn_neg = QPlainTextEdit(); self.cn_neg.setPlaceholderText(tr("placeholder_negative")); self.cn_neg.setFixedHeight(50); cn_main.addWidget(QLabel(tr("label_prompt"))); self.lbl_wildcards_cn = QLabel(tr("wildcards_tooltip")); self.lbl_wildcards_cn.setStyleSheet("color: #666; font-size: 10px; margin-top: -4px;"); cn_main.addWidget(self.lbl_wildcards_cn); cn_main.addWidget(self.cn_prompt); cn_main.addWidget(QLabel(tr("label_negative"))); cn_main.addWidget(self.cn_neg);
        cn_prev_layout = QHBoxLayout()
        self.cn_preview = ClickableLabel(tr("placeholder_drop")); self.cn_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cn_preview.setObjectName("PreviewArea"); self.cn_preview.setStyleSheet("border: 2px dashed #333; color: #555;"); self.cn_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.cn_preview.setMinimumSize(1, 1); cn_prev_layout.addWidget(self.cn_preview, 1)
        self.v_cn_out = ClickableLabel(); self.v_cn_out.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_cn_out.setObjectName("PreviewArea"); self.v_cn_out.setStyleSheet("background-color: #1a1a1a;"); self.v_cn_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_cn_out.setMinimumSize(1, 1); self.v_cn_out.clicked.connect(self.open_fullscreen); cn_prev_layout.addWidget(self.v_cn_out, 1)
        cn_main.addLayout(cn_prev_layout, 1); self.cn_progress = QProgressBar(); cn_main.addWidget(self.cn_progress); cn_l.addLayout(cn_main, 1)

        self.setAcceptDrops(True)

        # 4. ADETAILER
        logger.info("[UI] Building ADetailer tab...")
        self.adet_tab = QWidget(); self.tabs.addTab(self.adet_tab, tr("tab_adetailer")); adet_l = QHBoxLayout(self.adet_tab)
        adet_params = QVBoxLayout(); adet_params.setContentsMargins(15, 10, 15, 10); adet_params.setSpacing(10)
        lbl_adet_h = QLabel(tr("tab_adetailer")); lbl_adet_h.setObjectName("Header"); adet_params.addWidget(lbl_adet_h)

        self.adet_model_combo = QComboBox(); self.adet_model_combo.addItems(["face_yolov8n.pt"]); adet_params.addWidget(self.adet_model_combo)
        self.adet_denoise = ParameterSlider(tr("label_denoise_adetailer"), 0.0, 1.0, 0.40, 0.05, True)
        self.adet_dilation = ParameterSlider(tr("label_dilation"), 0, 32, 4)
        self.adet_conf = ParameterSlider(tr("label_confidence"), 0.0, 1.0, 0.30, 0.05, True)
        for s in [self.adet_denoise, self.adet_dilation, self.adet_conf]: adet_params.addWidget(s)

        self.btn_load_adet = QPushButton(tr("btn_load_image")); self.btn_load_adet.setObjectName("SecondaryBtn"); self.btn_load_adet.clicked.connect(self.adet_ctrl.load_adet_image); adet_params.addWidget(self.btn_load_adet)
        self.check_adet_upscale = QCheckBox(tr("chk_auto_upscale_adet")); adet_params.addWidget(self.check_adet_upscale)
        adet_params.addStretch()
        self.btn_gen_adet = QPushButton(tr("btn_generate_adet")); self.btn_gen_adet.setObjectName("GenerateBtn"); self.btn_gen_adet.setFixedHeight(45); self.btn_gen_adet.setMinimumWidth(180); self.btn_gen_adet.clicked.connect(self.adet_ctrl.start_adetailer); adet_params.addWidget(self.btn_gen_adet)

        self.model_mgr.disable_until_model_loaded()
        adet_l.addLayout(adet_params, 0)

        adet_main = QVBoxLayout(); adet_main.setContentsMargins(20, 10, 20, 0)
        self.adet_prompt = QPlainTextEdit(); self.adet_prompt.setPlaceholderText(tr("placeholder_prompt")); self.adet_prompt.setFixedHeight(50)
        self.adet_neg = QPlainTextEdit(); self.adet_neg.setPlaceholderText(tr("placeholder_negative")); self.adet_neg.setFixedHeight(50)
        adet_main.addWidget(QLabel(tr("lbl_adetailer_prompt"))); self.lbl_wildcards_adet = QLabel(tr("wildcards_tooltip")); self.lbl_wildcards_adet.setStyleSheet("color: #666; font-size: 10px; margin-top: -4px;"); adet_main.addWidget(self.lbl_wildcards_adet); adet_main.addWidget(self.adet_prompt)
        adet_main.addWidget(QLabel(tr("lbl_adetailer_neg"))); adet_main.addWidget(self.adet_neg)

        adet_previews = QHBoxLayout()
        self.v_adet_in = ClickableLabel(tr("placeholder_drop")); self.v_adet_in.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_adet_in.setObjectName("PreviewArea"); self.v_adet_in.setStyleSheet("border: 2px dashed #333;"); self.v_adet_in.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_adet_in.setMinimumSize(1, 1); self.v_adet_in.clicked.connect(self.open_fullscreen)
        self.v_adet_out = ClickableLabel(); self.v_adet_out.setAlignment(Qt.AlignmentFlag.AlignCenter); self.v_adet_out.setObjectName("PreviewArea"); self.v_adet_out.setStyleSheet("background-color: #1a1a1a;"); self.v_adet_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.v_adet_out.setMinimumSize(1, 1); self.v_adet_out.clicked.connect(self.open_fullscreen)
        adet_previews.addWidget(self.v_adet_in, 1); adet_previews.addWidget(self.v_adet_out, 1)
        adet_main.addLayout(adet_previews, 1); self.adet_progress = QProgressBar(); adet_main.addWidget(self.adet_progress)
        adet_l.addLayout(adet_main, 1)

        # 5. GALLERY
        logger.info("[UI] Building Gallery tab...")
        self.gal_tab = QWidget(); self.tabs.addTab(self.gal_tab, tr("tab_gallery")); gal_l = QVBoxLayout(self.gal_tab)
        h_gal = QHBoxLayout(); btn_ref = QPushButton(tr("btn_refresh_gallery")); btn_ref.setObjectName("ActionBtn"); btn_ref.clicked.connect(self.refresh_gallery); h_gal.addWidget(btn_ref); h_gal.addStretch(); gal_l.addLayout(h_gal)
        self.gal_list = QListWidget(); self.gal_list.setViewMode(QListWidget.ViewMode.IconMode); self.gal_list.setResizeMode(QListWidget.ResizeMode.Adjust); self.gal_list.setIconSize(QSize(200, 200)); self.gal_list.setSpacing(10); self.gal_list.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;"); self.gal_list.itemDoubleClicked.connect(self.open_gallery_detail); gal_l.addWidget(self.gal_list)

        # 6. PROMPT BUILDER
        logger.info("[UI] Building Prompt Builder tab...")
        self.pb_panel = PromptBuilderPanel(engine=self.engine)
        self.pb_panel.prompt_ready.connect(self._on_prompt_ready)
        self.pb_panel.neg_prompt_ready.connect(self._on_neg_prompt_ready)
        self.tabs.addTab(self.pb_panel, tr("tab_prompt_builder"))

        # 7. CLIP INTERROGATOR
        logger.info("[UI] Building CLIP Interrogator tab...")
        self.clip_tab = ClipInterrogatorTab()
        self.clip_tab.prompt_ready.connect(self._on_prompt_ready)
        self.tabs.addTab(self.clip_tab, tr("tab_clip"))

        # 8. PHOTO RESTORATION
        logger.info("[UI] Building Photo Restoration tab...")
        self.restore_tab = RestorationTab()
        self.tabs.addTab(self.restore_tab, tr("tab_restoration"))

        # 9. DOWNLOADER
        logger.info("[UI] Building Downloader tab...")
        self.dl_tab = ModelDownloaderTab()
        self.tabs.addTab(self.dl_tab, "📥 Downloader")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        logger.info("[UI] Finalizing startup...")

        self.apply_settings_ui()
        self.refresh_gallery()

        self.showMaximized()

    def apply_settings_ui(self):
        theme = settings.get('UI', 'theme', fallback='Dark')
        if theme not in ("Dark", "Amber", "Nord", "Dracula", "Monokai", "Forest", "Ocean"):
            theme = "Dark"
        use_custom = settings.get_bool('UI', 'use_custom_accent', fallback=False)
        if use_custom:
            accent = settings.get('UI', 'accent_color', fallback='#00d4ff')
        else:
            from config import THEMES
            accent = THEMES.get(theme, {}).get('accent', '#00d4ff')
        self.setStyleSheet(get_style(theme, accent))
        self.sampler_combo.setCurrentText(settings.get('Generation', 'default_sampler'))
        self.scheduler_combo.setCurrentText(settings.get('Generation', 'default_scheduler'))

        vae_val = settings.get('Generation', 'default_vae')
        idx = self.vae_combo.findData(vae_val)
        if idx < 0: idx = self.vae_combo.findText(vae_val)
        if idx >= 0: self.vae_combo.setCurrentIndex(idx)

    def open_settings(self):
        dlg = SettingsDialog(self, APP_VERSION)
        dlg.exec()

    def toggle_img2img_ui(self, enabled):
        self.img2img_strength.setVisible(enabled)
        self.btn_load_img2img.setVisible(enabled)
        self.img2img_preview.setVisible(enabled)

    def load_img2img_image(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg)")
        if f:
            from PIL import Image as PILImage
            from utils import prepare_image_for_img2img
            pil = PILImage.open(f).convert("RGB")
            self.img2img_image_pil = prepare_image_for_img2img(pil, self.s_w.value(), self.s_h.value())
            from PyQt6.QtGui import QPixmap
            from utils import pil_to_qimage
            qimg = pil_to_qimage(self.img2img_image_pil)
            pix = QPixmap.fromImage(qimg)
            self.img2img_preview.setPixmap(pix.scaled(self.img2img_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.img2img_preview.setText("")

    def _on_prompt_ready(self, text):
        self.t2i_prompt.setPlainText(text)
        self.tabs.setCurrentWidget(self.t2i_tab)

    def _on_neg_prompt_ready(self, text):
        self.t2i_neg.setPlainText(text)
        self.tabs.setCurrentWidget(self.t2i_tab)

    def open_fullscreen(self, pixmap): ImageViewer(pixmap, self).exec()

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
    def closeEvent(self, event):
        self.engine._clear_vram()
        self.resource_monitor.shutdown()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event); self.v_orig.update_scaling(); self.v_ups.update_scaling(); self.v_adet_in.update_scaling(); self.v_adet_out.update_scaling(); self.v_inpaint_out.update_scaling(); self.v_cn_out.update_scaling()

    def _on_tab_changed(self, index):
        for w in [self.v_orig, self.v_ups, self.v_adet_in, self.v_adet_out, self.cn_preview, self.v_inpaint_out, self.v_cn_out]:
            w.update_scaling()
        if self.canvas.base_pixmap_item.pixmap() and not self.canvas.base_pixmap_item.pixmap().isNull():
            self.canvas.fitInView(self.canvas.base_pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())

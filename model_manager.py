import os
import logging
from PyQt6.QtCore import QFileSystemWatcher
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from config import FOLDERS, settings, tr
from worker import ModelLoaderWorker


class ModelManager:
    def __init__(self, engine, main_window):
        self.engine = engine
        self.mw = main_window
        self.loras = {}
        self.model_watcher = None
        self.emb_watcher = None

    def setup_folders(self):
        for p in FOLDERS:
            if not os.path.exists(p):
                os.makedirs(p)

    def setup_watchers(self):
        self.model_watcher = QFileSystemWatcher()
        paths = [
            settings.get('Paths', 'models_sd'),
            settings.get('Paths', 'models_lora'),
            settings.get('Paths', 'models_controlnet'),
            settings.get('Paths', 'models_inpaint'),
            settings.get('Paths', 'models_vae'),
            settings.get('Paths', 'models_facerestore'),
            settings.get('Paths', 'models_upscalers')
        ]
        for p in paths:
            if os.path.exists(p):
                self.model_watcher.addPath(p)
        self.model_watcher.directoryChanged.connect(self.refresh_all_comboboxes)
        emb_dir = settings.get('Paths', 'models_embeddings')
        if emb_dir and os.path.exists(emb_dir):
            self.emb_watcher = QFileSystemWatcher()
            self.emb_watcher.addPath(emb_dir)
            self.emb_watcher.directoryChanged.connect(self._on_embeddings_changed)

    def _on_embeddings_changed(self, path):
        self.engine.scan_embeddings()
        if hasattr(self.mw, 'pb_panel') and self.mw.pb_panel:
            self.mw.pb_panel.refresh_embeddings()

    def scan_models(self, folder, exts=(".safetensors",)):
        if not os.path.exists(folder):
            return []
        return [f for f in os.listdir(folder) if f.lower().endswith(exts)]

    def refresh_all_comboboxes(self, path=None):
        logging.info("[SYSTEM] Detected changes in model folders, refreshing lists...")
        self.refresh_base_models()
        self.refresh_vae_models()
        self.refresh_inpaint_models()
        self.refresh_cn_models()
        self.refresh_upscalers()

    def refresh_base_models(self):
        curr = self.mw.model_combo.currentText()
        self.mw.model_combo.clear()
        path = settings.get('Paths', 'models_sd')
        for f in self.scan_models(path):
            self.mw.model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.mw.model_combo.findText(curr)
            if idx >= 0:
                self.mw.model_combo.setCurrentIndex(idx)

    def refresh_vae_models(self):
        curr = self.mw.vae_combo.currentText()
        self.mw.vae_combo.clear()
        self.mw.vae_combo.addItem(tr("opt_default_vae"), "Domy\u015blne (z modelu)")
        path = settings.get('Paths', 'models_vae')
        vae_exts = (".safetensors", ".pt", ".ckpt")
        for f in self.scan_models(path, exts=vae_exts):
            self.mw.vae_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.mw.vae_combo.findText(curr)
            if idx >= 0:
                self.mw.vae_combo.setCurrentIndex(idx)

    def explicit_load_inpaint_model(self):
        m = self.mw.inp_model_combo.currentData()
        if m:
            self.mw.btn_gen_inp.setEnabled(False)
            self.mw.i_progress.setFormat(tr("status_loading_inpaint"))
            self.engine.load_inpaint_model(m)
            self.mw.btn_gen_inp.setEnabled(True)
            self.mw.i_progress.setFormat(tr("status_inpaint_ready"))

    def refresh_upscalers(self):
        curr = self.mw.upscaler_combo.currentText()
        self.mw.upscaler_combo.clear()
        self.mw.upscaler_combo.addItem(tr("opt_no_upscaler"), "")
        path = settings.get('Paths', 'models_upscalers')
        ups_exts = (".pth", ".pt", ".bin", ".onnx", ".safetensors", ".ckpt")
        for f in self.scan_models(path, exts=ups_exts):
            self.mw.upscaler_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.mw.upscaler_combo.findText(curr)
            if idx >= 0:
                self.mw.upscaler_combo.setCurrentIndex(idx)

    def refresh_inpaint_models(self):
        curr = self.mw.inp_model_combo.currentText()
        self.mw.inp_model_combo.clear()
        self.mw.inp_model_combo.addItem(tr("opt_use_main_model"), "original")
        path = settings.get('Paths', 'models_inpaint')
        for f in self.scan_models(path):
            self.mw.inp_model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.mw.inp_model_combo.findText(curr)
            if idx >= 0:
                self.mw.inp_model_combo.setCurrentIndex(idx)

    def refresh_cn_models(self):
        curr = self.mw.cn_model_combo.currentText()
        self.mw.cn_model_combo.clear()
        path = settings.get('Paths', 'models_controlnet')
        for f in self.scan_models(path):
            self.mw.cn_model_combo.addItem(f, os.path.join(path, f))
        if curr:
            idx = self.mw.cn_model_combo.findText(curr)
            if idx >= 0:
                self.mw.cn_model_combo.setCurrentIndex(idx)

    def browse_model(self):
        file, _ = QFileDialog.getOpenFileName(
            self.mw, tr("dialog_model"), "",
            "Safetensors (*.safetensors);;All Files (*)"
        )
        if file:
            name = os.path.basename(file)
            self.mw.model_combo.insertItem(0, name, file)
            self.mw.model_combo.setCurrentIndex(0)

    def add_lora_dialog(self):
        if len(self.loras) >= 5:
            return
        file, _ = QFileDialog.getOpenFileName(
            self.mw, tr("dialog_lora"), "",
            "Safetensors (*.safetensors)"
        )
        if file:
            name = os.path.basename(file).split('.')[0]
            if name in self.loras:
                name += f"_{len(self.loras)}"
            self.engine.load_lora(file, name)
            from widgets import LoRAItem
            item = LoRAItem(name, file)
            item.removed.connect(self.remove_lora)
            item.changed.connect(self.update_lora_visualizer)
            self.mw.lora_list_layout.addWidget(item)
            self.loras[name] = item
            self.update_lora_visualizer()

    def remove_lora(self, name):
        if name in self.loras:
            self.engine.unload_lora(name)
            item = self.loras.pop(name)
            self.mw.lora_list_layout.removeWidget(item)
            item.deleteLater()
            self.update_lora_visualizer()

    def update_lora_visualizer(self):
        self.mw.lora_visualizer.update_weights(
            [(n, i.weight()) for n, i in self.loras.items()]
        )

    def disable_until_model_loaded(self):
        self.mw.btn_gen_t2i.setEnabled(False)
        self.mw.btn_gen_inp.setEnabled(False)
        self.mw.btn_gen_cn.setEnabled(False)
        self.mw.btn_gen_adet.setEnabled(False)

    def enable_generate_buttons(self):
        self.mw.btn_gen_t2i.setEnabled(True)
        self.mw.btn_gen_inp.setEnabled(True)
        self.mw.btn_gen_cn.setEnabled(True)
        self.mw.btn_gen_adet.setEnabled(True)

    def load_model(self):
        m = self.mw.model_combo.currentData()
        if m:
            self.mw.btn_load.setEnabled(False)
            self.mw.model_combo.setEnabled(False)
            self.mw.load_progress.setRange(0, 0)
            self.mw.load_progress.show()
            self.mw.p_bar.setFormat(tr("status_loading_model"))

            self.load_worker = ModelLoaderWorker(self.engine, m, self.loras)
            self.load_worker.finished.connect(self.on_model_loaded)
            self.load_worker.start()

    def on_model_loaded(self, success, message):
        self.mw.btn_load.setEnabled(True)
        self.mw.model_combo.setEnabled(True)
        self.mw.load_progress.hide()
        self.mw.load_progress.setRange(0, 100)

        if success:
            self.mw.p_bar.setFormat(tr("status_model_ready"))
            self.enable_generate_buttons()
            logging.info("[SYSTEM] Model loaded asynchronously.")
            try:
                import compel
                self.mw.lbl_compel.setText(tr("compel_available"))
                self.mw.lbl_compel.setStyleSheet("color: #4caf50; font-size: 10px;")
            except ImportError:
                self.mw.lbl_compel.setText(tr("compel_unavailable"))
                self.mw.lbl_compel.setStyleSheet("color: #888; font-size: 10px;")
            self.mw.pb_panel.refresh_embeddings()
        else:
            self.mw.p_bar.setFormat(tr("status_error"))
            QMessageBox.critical(
                self.mw, tr("status_error"),
                tr("error_loading_model").format(message=message)
            )

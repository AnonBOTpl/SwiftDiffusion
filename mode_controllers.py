import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PIL import Image as PILImage
from config import settings, tr, logger
from utils import qimage_to_pil
from worker import InpaintWorker, ControlNetWorker, ADetailerWorker


class InpaintController:
    def __init__(self, engine, main_window):
        self.engine = engine
        self.mw = main_window
        self.in_worker = None

    def load_inpaint_image(self):
        f, _ = QFileDialog.getOpenFileName(self.mw, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.mw.canvas.set_base_image(QPixmap(f))
            self.mw.v_inpaint_out.clear()
            self.mw.v_inpaint_out.setText("")

    def send_to_inpaint(self):
        if self.mw.last_generated_path:
            self.mw.canvas.set_base_image(QPixmap(self.mw.last_generated_path))
            self.mw.tabs.setCurrentIndex(1)

    def start_inpaint(self):
        if self.in_worker and self.in_worker.isRunning():
            self.in_worker.stop()
            self.mw.btn_gen_inp.setText(tr("btn_generate_fix"))
            self.mw.btn_gen_inp.setStyleSheet("")
            return
        if not self.engine.inpaint_pipe and not self.engine.pipe:
            return QMessageBox.warning(self.mw, tr("status_error"), tr("status_model_error"))
        params = {
            "prompt": self.mw.i_prompt.toPlainText(),
            "neg_prompt": self.mw.i_neg.toPlainText(),
            "image": self.mw.canvas.get_image_pil(),
            "mask": self.mw.canvas.get_mask_pil(),
            "steps": self.mw.i_steps.value(),
            "cfg": self.mw.i_cfg.value(),
            "strength": self.mw.i_denoise.value(),
            "inpaint_model": self.mw.inp_model_combo.currentData(),
            "sampler": self.mw.sampler_combo.currentText(),
            "scheduler": self.mw.scheduler_combo.currentText(),
            "vae_path": self.mw.vae_combo.currentData()
        }
        self.mw.btn_gen_inp.setText(tr("btn_stop"))
        self.mw.btn_gen_inp.setStyleSheet("background: #cc3333; color: white; font-weight: bold;")
        self.mw.btn_gen_inp.setEnabled(False)
        self.mw.i_progress.setMaximum(0)
        self.mw.i_progress.setValue(0)
        self.in_worker = InpaintWorker(self.engine, params)
        self.in_worker.status.connect(self.mw.i_progress.setFormat)
        self.in_worker.finished.connect(self.on_inpaint_finished)
        self.in_worker.start()
        self.mw.btn_gen_inp.setEnabled(True)

    def on_inpaint_finished(self, path, seed):
        self.mw.btn_gen_inp.setText(tr("btn_generate_fix"))
        self.mw.btn_gen_inp.setStyleSheet("")
        self.mw.btn_gen_inp.setEnabled(True)
        self.mw.i_progress.setMaximum(100)
        self.mw.i_progress.setValue(100)
        self.mw.i_progress.setFormat(f"{tr('status_done')} ({seed})")
        self.mw.v_inpaint_out.set_image(path)
        self.mw.v_inpaint_out.setText("")
        self.engine._clear_vram()


class ControlNetController:
    def __init__(self, engine, main_window):
        self.engine = engine
        self.mw = main_window
        self.cn_wkr = None
        self.ref_image_pil = None

    def load_cn_image(self):
        f, _ = QFileDialog.getOpenFileName(self.mw, tr("dialog_ref"), "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.set_cn_ref_image(f)
            self.mw.v_cn_out.clear()
            self.mw.v_cn_out.setText("")

    def set_cn_ref_image(self, path):
        pix = QPixmap(path)
        logger.info(f"[SYSTEM] Loading CN image: {pix.width()}x{pix.height()}")
        self.mw.cn_preview.set_image(pix)
        self.mw.cn_preview.setText("")
        self.ref_image_pil = qimage_to_pil(pix.toImage())

    def start_controlnet(self):
        if self.cn_wkr and self.cn_wkr.isRunning():
            self.cn_wkr.stop()
            self.mw.btn_gen_cn.setText(tr("btn_generate_cn"))
            self.mw.btn_gen_cn.setStyleSheet("")
            return
        if not self.engine.pipe or not self.ref_image_pil:
            return QMessageBox.warning(self.mw, tr("status_error"), tr("status_no_data"))
        try:
            sv = int(self.mw.cn_seed.text())
        except Exception:
            sv = -1
        params = {
            "prompt": self.mw.cn_prompt.toPlainText(),
            "neg_prompt": self.mw.cn_neg.toPlainText(),
            "image": self.ref_image_pil,
            "strength": self.mw.cn_strength.value(),
            "steps": self.mw.cn_steps.value(),
            "cfg": self.mw.cn_cfg.value(),
            "width": self.mw.cn_w.value(),
            "height": self.mw.cn_h.value(),
            "seed": sv,
            "cn_model": self.mw.cn_model_combo.currentData(),
            "sampler": self.mw.sampler_combo.currentText(),
            "scheduler": self.mw.scheduler_combo.currentText(),
            "vae_path": self.mw.vae_combo.currentData()
        }
        self.mw.btn_gen_cn.setText(tr("btn_stop"))
        self.mw.btn_gen_cn.setStyleSheet("background: #cc3333; color: white; font-weight: bold;")
        self.mw.btn_gen_cn.setEnabled(False)
        self.mw.cn_progress.setMaximum(0)
        self.mw.cn_progress.setValue(0)
        self.cn_wkr = ControlNetWorker(self.engine, params)
        self.cn_wkr.status.connect(self.mw.cn_progress.setFormat)
        self.cn_wkr.finished.connect(self.on_cn_finished)
        self.cn_wkr.start()
        self.mw.btn_gen_cn.setEnabled(True)

    def on_cn_finished(self, path, seed):
        self.mw.btn_gen_cn.setText(tr("btn_generate_cn"))
        self.mw.btn_gen_cn.setStyleSheet("")
        self.mw.btn_gen_cn.setEnabled(True)
        self.mw.cn_progress.setMaximum(100)
        self.mw.cn_progress.setValue(100)
        self.mw.cn_progress.setFormat(f"{tr('status_done')} ({seed})")
        self.mw.v_cn_out.set_image(path)
        self.mw.v_cn_out.setText("")
        self.engine._clear_vram()


class ADetailerController:
    def __init__(self, engine, main_window):
        self.engine = engine
        self.mw = main_window
        self.adet_worker = None

    def load_adet_image(self):
        f, _ = QFileDialog.getOpenFileName(self.mw, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg)")
        if f:
            self.mw.v_adet_in.set_image(f)
            self.mw.v_adet_in.setText("")

    def send_to_adetailer(self):
        if self.mw.last_generated_path:
            self.mw.v_adet_in.set_image(self.mw.last_generated_path)
            self.mw.v_adet_in.setText("")
            self.mw.tabs.setCurrentIndex(3)

    def start_adetailer(self):
        if self.adet_worker and self.adet_worker.isRunning():
            self.adet_worker.stop()
            self.mw.btn_gen_adet.setText(tr("btn_generate_adet"))
            self.mw.btn_gen_adet.setStyleSheet("")
            return
        input_img = self.mw.v_adet_in.get_image_pil()
        if not input_img or not self.engine.pipe:
            return QMessageBox.warning(self.mw, tr("status_error"), tr("status_no_data"))

        params = {
            "image": input_img,
            "model_path": os.path.join(
                settings.get('Paths', 'models_facedetection'),
                self.mw.adet_model_combo.currentText()
            ),
            "prompt": self.mw.adet_prompt.toPlainText(),
            "neg_prompt": self.mw.adet_neg.toPlainText(),
            "denoise": self.mw.adet_denoise.value(),
            "dilation": self.mw.adet_dilation.value(),
            "conf": self.mw.adet_conf.value(),
            "auto_upscale": self.mw.check_adet_upscale.isChecked(),
            "upscaler_model": self.mw.upscaler_combo.currentData(),
            "keep_upscaler_vram": self.mw.check_vram.isChecked()
        }

        self.mw.btn_gen_adet.setText(tr("btn_stop"))
        self.mw.btn_gen_adet.setStyleSheet("background: #cc3333; color: white; font-weight: bold;")
        self.mw.btn_gen_adet.setEnabled(False)
        self.mw.adet_progress.setMaximum(30)
        self.mw.adet_progress.setValue(0)

        self.adet_worker = ADetailerWorker(self.engine, params)
        self.adet_worker.progress.connect(self.mw.adet_progress.setValue)
        self.adet_worker.status.connect(self.mw.l_status.setText)
        self.adet_worker.finished.connect(self.on_adetailer_finished)
        self.adet_worker.start()
        self.mw.btn_gen_adet.setEnabled(True)

    def on_adetailer_finished(self, path):
        self.mw.btn_gen_adet.setText(tr("btn_generate_adet"))
        self.mw.btn_gen_adet.setStyleSheet("")
        self.mw.btn_gen_adet.setEnabled(True)
        if path:
            self.mw.v_adet_out.set_image(path)
            self.mw.adet_progress.setValue(30)
            self.mw.l_status.setText(tr("status_finished"))
            self.mw.last_generated_path = path
        else:
            self.mw.adet_progress.setFormat(tr("status_error"))
        self.engine._clear_vram()

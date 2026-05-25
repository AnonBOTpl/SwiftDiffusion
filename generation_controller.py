from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image as PILImage
from config import settings, tr
from worker import GenerationWorker, Img2ImgWorker, UpscaleWorker
from widgets import BatchThumbnailBar


class GenerationController:
    def __init__(self, engine, model_mgr, main_window):
        self.engine = engine
        self.model_mgr = model_mgr
        self.mw = main_window
        self.worker = None
        self.up_w = None
        self._prog_anim = None
        self._pulse_state = False
        self._pulse_timer = None
        self.current_seed = None
        self.last_upscaled_path = None
        self._batch_results = []      # (raw_path, final_path, seed)
        self._batch_raw_results = []  # raw paths from part_finished
        self._batch_total = 1
        self._batch_idx = 0
        self._base_params = None

    def _animate_progress(self, target):
        if self._prog_anim is None:
            self._prog_anim = QPropertyAnimation(self.mw.p_bar, b"value")
            self._prog_anim.setDuration(250)
            self._prog_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._prog_anim.stop()
        self._prog_anim.setStartValue(self.mw.p_bar.value())
        self._prog_anim.setEndValue(target)
        self._prog_anim.start()

    def _pulse_border(self):
        accent = settings.get('UI', 'accent_color', fallback='#00d4ff')
        if self._pulse_state:
            self.mw.live_preview.setStyleSheet(
                f"border: 2px solid {accent}; border-radius: 8px; background-color: #1a1a1a; color: #444; font-size: 12px;")
        else:
            self.mw.live_preview.setStyleSheet(
                "border: 2px solid #444; border-radius: 8px; background-color: #1a1a1a; color: #444; font-size: 12px;")
        self._pulse_state = not self._pulse_state

    def start_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._finish_batch()
            return
        if not self.engine.pipe:
            return QMessageBox.warning(self.mw, tr("status_error"), tr("status_model_error"))
        try:
            sv = int(self.mw.s_seed.text())
        except Exception:
            sv = -1
        preview_enabled = settings.get_bool('Preview', 'enabled')
        preview_interval = int(settings.get('Preview', 'interval', fallback='5'))
        params = {
            "preview_enabled": preview_enabled,
            "preview_interval": preview_interval,
            "prompt": self.mw.t2i_prompt.toPlainText(),
            "neg_prompt": self.mw.t2i_neg.toPlainText(),
            "steps": self.mw.s_steps.value(),
            "cfg": self.mw.s_cfg.value(),
            "width": self.mw.s_w.value(),
            "height": self.mw.s_h.value(),
            "seed": sv,
            "auto_upscale": self.mw.check_auto.isChecked(),
            "upscaler_model": self.mw.upscaler_combo.currentData(),
            "keep_upscaler_vram": self.mw.check_vram.isChecked(),
            "loras": [{'name': n, 'weight': i.weight()} for n, i in self.model_mgr.loras.items()],
            "sampler": self.mw.sampler_combo.currentText(),
            "scheduler": self.mw.scheduler_combo.currentText(),
            "vae_path": self.mw.vae_combo.currentData()
        }

        self.mw.batch_thumb_container.hide()
        for i in reversed(range(self.mw.batch_thumb_layout.count())):
            w = self.mw.batch_thumb_layout.itemAt(i).widget()
            if w: w.deleteLater()

        self._batch_total = self.mw.batch_spin.value()
        self._batch_idx = 0
        self._batch_results = []
        self._batch_raw_results = []
        self._base_params = params

        self.mw.btn_gen_t2i.setText(tr("btn_stop"))
        self.mw.btn_gen_t2i.setStyleSheet("background: #cc3333; color: white; font-weight: bold;")
        self.mw.btn_gen_t2i.setEnabled(False)
        self.mw.p_bar.setMaximum(params["steps"])
        self.mw.p_bar.setValue(0)
        self.mw.live_preview.setStyleSheet("border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; color: #555; font-size: 12px;")
        self.mw.live_preview.show()
        self._pulse_state = False
        if self._pulse_timer is None:
            self._pulse_timer = QTimer()
            self._pulse_timer.timeout.connect(self._pulse_border)
        self._pulse_timer.start(500)

        if self.mw.chk_img2img.isChecked() and not self.mw.img2img_image_pil:
            self.mw.live_preview.hide()
            QMessageBox.warning(self.mw, tr("status_error"), tr("error_load_img2img"))
            self._finish_batch()
            return

        self._run_batch_next()

    def _run_batch_next(self):
        if self._batch_idx >= self._batch_total:
            return
        params = dict(self._base_params)
        if params.get('seed') != -1:
            params['seed'] = params['seed'] + self._batch_idx
        self.mw.l_status.setText(f"Batch {self._batch_idx + 1}/{self._batch_total}...")
        self.mw.p_bar.setMaximum(params["steps"])
        self.mw.p_bar.setValue(0)
        if self.mw.chk_img2img.isChecked():
            params["image"] = self.mw.img2img_image_pil
            params["strength"] = self.mw.img2img_strength.value()
            self.worker = Img2ImgWorker(self.engine, params)
        else:
            self.worker = GenerationWorker(self.engine, params)
        self.worker.part_finished.connect(self._on_batch_part_finished)
        self.worker.finished.connect(self._on_batch_item_finished)
        self.worker.progress.connect(self.on_preview_update)
        self.worker.status.connect(self.mw.l_status.setText)
        self.worker.start()
        self.mw.btn_gen_t2i.setEnabled(True)
        self._batch_idx += 1

    def _on_batch_part_finished(self, path, seed):
        self._batch_raw_results.append(path)
        self.mw.last_generated_path = path
        self.last_upscaled_path = None
        self.mw.v_orig.set_image(path)
        self.mw.v_orig.setText("")
        self.mw.l_orig_lbl.hide()
        self.mw.l_ups_lbl.hide()
        self.mw.c_ups.hide()
        if isinstance(seed, int):
            self.current_seed = seed
            self.mw.l_status.setText(f"{tr('status_seed')}{seed}")
            self.mw.btn_copy.show()
        else:
            self.mw.l_status.setText(str(seed))
            self.mw.btn_copy.hide()

    def _on_batch_item_finished(self, path, seed):
        if not path:
            self._finish_batch()
            return
        idx = len(self._batch_results)
        raw_path = self._batch_raw_results[idx] if idx < len(self._batch_raw_results) else path
        self._batch_results.append((raw_path, path, seed))
        self.mw.last_generated_path = path
        if self._batch_idx < self._batch_total:
            self._run_batch_next()
        else:
            self._show_batch_results()

    def _show_batch_results(self):
        self.mw.btn_gen_t2i.setText(tr("btn_generate"))
        self.mw.btn_gen_t2i.setStyleSheet("")
        self.mw.btn_gen_t2i.setEnabled(True)
        self.mw.p_bar.setFormat(tr("status_done"))
        self.mw.p_bar.setMaximum(100)
        self.mw.p_bar.setValue(100)
        self.mw.live_preview.hide()
        if self._pulse_timer and self._pulse_timer.isActive():
            self._pulse_timer.stop()
        self.engine._clear_vram()
        if not self._batch_results:
            return
        last_raw, last_final, last_seed = self._batch_results[-1]
        self.mw.v_orig.set_image(last_raw)
        self.mw.v_orig.setText("")
        self.mw.last_generated_path = last_final
        if "_upscaled" in last_final:
            self.last_upscaled_path = last_final
            self.mw.v_ups.set_image(last_final)
            self.mw.v_ups.setText("")
            self.mw.l_orig_lbl.show()
            self.mw.l_ups_lbl.show()
            self.mw.c_ups.show()
        else:
            self.mw.c_ups.hide()
        if isinstance(last_seed, int):
            self.current_seed = last_seed
            self.mw.l_status.setText(f"{tr('status_seed')}{last_seed}")
            self.mw.btn_copy.show()
        else:
            self.mw.l_status.setText(str(last_seed))
            self.mw.btn_copy.hide()
        if self._batch_total > 1:
            paths = [final for _, final, _ in self._batch_results]
            bar = BatchThumbnailBar()
            bar.set_images(paths)
            bar.imageSelected.connect(self._on_thumb_selected)
            self.mw.batch_thumb_layout.addWidget(bar)
            self.mw.batch_thumb_container.show()

    def _on_thumb_selected(self, path):
        for raw, final, seed in self._batch_results:
            if final == path:
                self.mw.v_orig.set_image(raw)
                self.mw.v_orig.setText("")
                self.mw.last_generated_path = final
                if "_upscaled" in final:
                    self.mw.v_ups.set_image(final)
                    self.mw.v_ups.setText("")
                    self.mw.l_orig_lbl.show()
                    self.mw.l_ups_lbl.show()
                    self.mw.c_ups.show()
                else:
                    self.mw.c_ups.hide()
                break

    def _finish_batch(self):
        self.mw.btn_gen_t2i.setText(tr("btn_generate"))
        self.mw.btn_gen_t2i.setStyleSheet("")
        self.mw.btn_gen_t2i.setEnabled(True)
        self.mw.p_bar.setMaximum(100)
        self.mw.p_bar.setValue(0)
        self.mw.live_preview.hide()
        if self._pulse_timer and self._pulse_timer.isActive():
            self._pulse_timer.stop()
        self.engine._clear_vram()
        self._batch_results = []
        self._batch_raw_results = []

    def on_preview_update(self, step, preview):
        self._animate_progress(step)
        if preview:
            if isinstance(preview, PILImage.Image):
                qimage = QImage(
                    preview.tobytes("raw", "RGB"), preview.width, preview.height,
                    QImage.Format.Format_RGB888
                )
                pix = QPixmap.fromImage(qimage)
                self.mw.live_preview.setPixmap(
                    pix.scaled(self.mw.live_preview.width(), self.mw.live_preview.height(),
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation))
                self.mw.live_preview.setText("")

    def manual_upscale(self):
        if not self.mw.last_generated_path or not self.mw.upscaler_combo.currentData():
            return QMessageBox.warning(self.mw, tr("status_error"), tr("status_no_data"))
        self.mw.btn_up.setEnabled(False)
        self.mw.p_bar.setFormat(tr("status_upscaling"))
        self.up_w = UpscaleWorker(
            self.engine, self.mw.last_generated_path,
            self.mw.upscaler_combo.currentData(), self.mw.check_vram.isChecked()
        )
        self.up_w.status.connect(self.mw.l_status.setText)
        self.up_w.finished.connect(self.on_upscale_finished)
        self.up_w.start()

    def on_base_finished(self, path, seed):
        self.mw.last_generated_path = path
        self.last_upscaled_path = None
        self.mw.v_orig.set_image(path)
        self.mw.v_orig.setText("")
        self.mw.l_orig_lbl.hide()
        self.mw.l_ups_lbl.hide()
        self.mw.c_ups.hide()
        if isinstance(seed, int):
            self.current_seed = seed
            self.mw.l_status.setText(f"{tr('status_seed')}{seed}")
            self.mw.btn_copy.show()
        else:
            self.mw.l_status.setText(str(seed))
            self.mw.btn_copy.hide()

    def on_generation_finished(self, path, seed):
        self.mw.btn_gen_t2i.setText(tr("btn_generate"))
        self.mw.btn_gen_t2i.setStyleSheet("")
        self.mw.btn_gen_t2i.setEnabled(True)
        self.mw.p_bar.setFormat(tr("status_done"))
        self.mw.p_bar.setMaximum(100)
        self.mw.p_bar.setValue(100)
        self.mw.live_preview.hide()
        if self._pulse_timer and self._pulse_timer.isActive():
            self._pulse_timer.stop()
        if "_upscaled" in path:
            self.last_upscaled_path = path
            self.mw.v_ups.set_image(path)
            self.mw.v_ups.setText("")
            self.mw.l_orig_lbl.show()
            self.mw.l_ups_lbl.show()
            self.mw.c_ups.show()
            self.mw.l_status.setText(tr("status_finished"))
        self.engine._clear_vram()

    def on_upscale_finished(self, path):
        if path:
            self.on_generation_finished(path, "N/A")
            self.mw.btn_up.setEnabled(True)
        else:
            self.mw.btn_up.setEnabled(True)
            self.mw.p_bar.setFormat(tr("status_upscale_error"))

    def copy_seed_to_clipboard(self):
        if self.current_seed is not None:
            QApplication.clipboard().setText(str(self.current_seed))

import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from config import settings, tr
from widgets.widgets_common import ClickableLabel
from worker import RestorationWorker, RestorationDownloadWorker

RESTORATION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.get('Paths', 'models_restoration', fallback='models/restoration'))
COLORIZATION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.get('Paths', 'models_colorization', fallback='models/colorization'))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), settings.get('Paths', 'output_restoration', fallback='output/restoration'))


class RestorationTab(QWidget):
    restoration_result = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._dl_worker = None
        self._image_path = None
        self._result_path = None
        self.init_ui()

    def init_ui(self):
        l = QHBoxLayout(self)

        # --- LEFT PANEL ---
        left = QVBoxLayout()
        left.setContentsMargins(15, 10, 10, 10)
        left.setSpacing(10)
        left.addWidget(QLabel(tr("restore_image")))

        self.before_preview = ClickableLabel(tr("placeholder_drop"))
        self.before_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.before_preview.setObjectName("PreviewArea")
        self.before_preview.setStyleSheet("border: 2px dashed #333; color: #555;")
        self.before_preview.setMinimumSize(300, 300)
        self.before_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left.addWidget(self.before_preview, 1)

        self.btn_load = QPushButton(tr("btn_load_image"))
        self.btn_load.setObjectName("SecondaryBtn")
        self.btn_load.clicked.connect(self.load_image)
        left.addWidget(self.btn_load)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        left.addWidget(sep)

        self.chk_colorize = QCheckBox(tr("restore_colorize"))
        self.chk_colorize.setStyleSheet("color: #aaa; font-size: 11px;")
        self.chk_colorize.toggled.connect(self._on_colorize_toggled)
        left.addWidget(self.chk_colorize)

        self.colorize_combo = QComboBox()
        self.colorize_combo.addItem(tr("restore_color_opencv"), "opencv")
        self.colorize_combo.hide()
        left.addWidget(self.colorize_combo)

        self.chk_scratch = QCheckBox(tr("restore_scratch"))
        self.chk_scratch.setChecked(True)
        self.chk_scratch.setStyleSheet("color: #aaa; font-size: 11px;")
        left.addWidget(self.chk_scratch)

        self.chk_upscale = QCheckBox("Upscale")
        self.chk_upscale.setStyleSheet("color: #aaa; font-size: 11px;")
        left.addWidget(self.chk_upscale)

        self.btn_restore = QPushButton(tr("btn_restore"))
        self.btn_restore.setObjectName("GenerateBtn")
        self.btn_restore.setFixedHeight(40)
        self.btn_restore.clicked.connect(self.start_restoration)
        self.btn_restore.setEnabled(False)
        left.addWidget(self.btn_restore)

        self.restore_progress = QProgressBar()
        self.restore_progress.setFixedHeight(8)
        self.restore_progress.setTextVisible(True)
        self.restore_progress.hide()
        left.addWidget(self.restore_progress)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #888; font-size: 10px;")
        left.addWidget(self.lbl_status)

        l.addLayout(left, 1)

        # --- RIGHT PANEL ---
        right = QVBoxLayout()
        right.setContentsMargins(10, 10, 15, 10)
        right.setSpacing(8)

        right.addWidget(QLabel(tr("restore_result")))

        self.after_preview = ClickableLabel(tr("restore_result_empty"))
        self.after_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.after_preview.setObjectName("PreviewArea")
        self.after_preview.setStyleSheet("border: 2px dashed #333; color: #555;")
        self.after_preview.setMinimumSize(300, 300)
        self.after_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right.addWidget(self.after_preview, 1)

        self.btn_open = QPushButton(tr("restore_open"))
        self.btn_open.setObjectName("ActionBtn")
        self.btn_open.clicked.connect(self.open_result)
        self.btn_open.hide()
        right.addWidget(self.btn_open)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #333;")
        right.addWidget(sep2)

        right.addWidget(QLabel(tr("restore_models")))
        dl_row = QHBoxLayout()
        self.btn_dl_restore = QPushButton(tr("btn_dl_restoration"))
        self.btn_dl_restore.setObjectName("SecondaryBtn")
        self.btn_dl_restore.clicked.connect(lambda: self.download_models("restoration"))
        dl_row.addWidget(self.btn_dl_restore)
        self.btn_dl_color = QPushButton(tr("btn_dl_colorization"))
        self.btn_dl_color.setObjectName("SecondaryBtn")
        self.btn_dl_color.clicked.connect(lambda: self.download_models("colorization"))
        dl_row.addWidget(self.btn_dl_color)
        right.addLayout(dl_row)

        self.lbl_dl_status = QLabel("")
        self.lbl_dl_status.setStyleSheet("color: #888; font-size: 10px;")
        right.addWidget(self.lbl_dl_status)

        l.addLayout(right, 1)

        self._check_models()

    def _on_colorize_toggled(self, enabled):
        self.colorize_combo.setVisible(enabled)

    def _check_models(self):
        restore_ok = os.path.isfile(os.path.join(RESTORATION_DIR, "RealESRGAN_x4plus.pth"))
        color_ok = os.path.isfile(os.path.join(RESTORATION_DIR, "GFPGANv1.4.pth"))
        if restore_ok and color_ok:
            self.btn_dl_restore.setText("\u2713 " + tr("btn_dl_restoration"))
            self.btn_dl_restore.setEnabled(False)
        color_files = ["colorization_deploy_v2.prototxt", "colorization_release_v2.caffemodel", "pts_in_hull.npy"]
        if all(os.path.isfile(os.path.join(COLORIZATION_DIR, f)) for f in color_files):
            self.btn_dl_color.setText("\u2713 " + tr("btn_dl_colorization"))
            self.btn_dl_color.setEnabled(False)

    def load_image(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if f:
            self._image_path = f
            pix = QPixmap(f)
            self.before_preview.set_image(pix)
            self.before_preview.setText("")
            self.btn_restore.setEnabled(True)
            self.after_preview.setText(tr("restore_result_empty"))
            self.after_preview.clear()
            self.btn_open.hide()
            self._result_path = None

    def download_models(self, model_type):
        if self._dl_worker and self._dl_worker.isRunning():
            return
        self.lbl_dl_status.setText(tr("clip_downloading"))
        self.restore_progress.setMaximum(0)
        self.restore_progress.show()
        self._dl_worker = RestorationDownloadWorker(model_type)
        self._dl_worker.progress.connect(self._on_dl_progress)
        self._dl_worker.finished.connect(self._on_dl_finished)
        self._dl_worker.start()

    def _on_dl_progress(self, pct, msg):
        if pct == -1:
            self.lbl_dl_status.setText(msg)
            return
        if self.restore_progress.maximum() == 0 and pct > 0:
            self.restore_progress.setMaximum(100)
        if pct >= 0:
            self.restore_progress.setValue(pct)
        if msg:
            self.lbl_dl_status.setText(msg)

    def _on_dl_finished(self, success, msg):
        self.restore_progress.hide()
        self.lbl_dl_status.setText(msg)
        if success:
            self._check_models()

    def start_restoration(self):
        if not self._image_path:
            return
        if self._worker and self._worker.isRunning():
            return

        colorize = None
        if self.chk_colorize.isChecked():
            colorize = self.colorize_combo.currentData()

        self.btn_restore.setEnabled(False)
        self.after_preview.setText(tr("restore_processing"))
        self.after_preview.clear()
        self.restore_progress.setMaximum(100)
        self.restore_progress.setValue(0)
        self.restore_progress.show()
        self.btn_open.hide()

        self._worker = RestorationWorker(
            image_path=self._image_path,
            output_dir=OUTPUT_DIR,
            colorize_method=colorize,
            auto_scratch=self.chk_scratch.isChecked(),
            upscale=self.chk_upscale.isChecked(),
        )
        self._worker.progress.connect(self._on_restore_progress)
        self._worker.status.connect(self.lbl_status.setText)
        self._worker.finished.connect(self._on_restore_finished)
        self._worker.start()

    def _on_restore_progress(self, value):
        self.restore_progress.setValue(value)

    def _on_restore_finished(self, path):
        self.restore_progress.hide()
        self.btn_restore.setEnabled(True)
        if path:
            self._result_path = path
            pix = QPixmap(path)
            self.after_preview.set_image(pix)
            self.after_preview.setText("")
            self.btn_open.show()
            self.lbl_status.setText(tr("restore_done"))
        else:
            self.after_preview.setText(tr("restore_error"))
            self.after_preview.clear()
            self.lbl_status.setText(tr("restore_error"))

    def open_result(self):
        if self._result_path:
            self.restoration_result.emit(self._result_path)

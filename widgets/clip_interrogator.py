import os
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap
from config import settings, tr
from worker import ClipDownloadWorker, CLIPInterrogatorWorker
from widgets.widgets_common import ClickableLabel

CLIP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "clip")
CLIP_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "clip_data")

CLIP_MODELS = [
    ("ViT-B/32 \u2013 fast (570 MB)", "openai/clip-vit-base-patch32"),
    ("ViT-L/14 \u2013 accurate (1.7 GB)", "openai/clip-vit-large-patch14"),
]


class ClipInterrogatorTab(QWidget):
    prompt_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dl_worker = None
        self._clip_worker = None
        self._candidates = {}
        self._model_ready = False
        self.init_ui()
        self.refresh_candidates()

    def init_ui(self):
        l = QHBoxLayout(self)

        # --- LEFT PANEL ---
        left = QVBoxLayout()
        left.setContentsMargins(15, 10, 10, 10)
        left.setSpacing(10)
        left.addWidget(QLabel(tr("clip_image")))
        self.clip_preview = ClickableLabel(tr("placeholder_drop"))
        self.clip_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clip_preview.setObjectName("PreviewArea")
        self.clip_preview.setStyleSheet("border: 2px dashed #333; color: #555;")
        self.clip_preview.setMinimumSize(300, 300)
        self.clip_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left.addWidget(self.clip_preview, 1)

        self.btn_load_clip = QPushButton(tr("btn_load_image"))
        self.btn_load_clip.setObjectName("SecondaryBtn")
        self.btn_load_clip.clicked.connect(self.load_image)
        left.addWidget(self.btn_load_clip)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #333;")
        left.addWidget(sep)

        self.chk_use_gpu = QCheckBox(tr("clip_use_gpu"))
        self.chk_use_gpu.setStyleSheet("color: #aaa; font-size: 11px;")
        left.addWidget(self.chk_use_gpu)

        self.btn_analyze = QPushButton(tr("btn_clip_analyze"))
        self.btn_analyze.setObjectName("GenerateBtn")
        self.btn_analyze.setFixedHeight(40)
        self.btn_analyze.clicked.connect(self.analyze)
        self.btn_analyze.setEnabled(False)
        left.addWidget(self.btn_analyze)

        self.clip_progress = QProgressBar()
        self.clip_progress.setFixedHeight(8)
        self.clip_progress.setTextVisible(True)
        self.clip_progress.hide()
        left.addWidget(self.clip_progress)

        l.addLayout(left, 1)

        # --- RIGHT PANEL ---
        right = QVBoxLayout()
        right.setContentsMargins(10, 10, 15, 10)
        right.setSpacing(8)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel(tr("clip_model")))
        self.model_combo = QComboBox()
        for label, _ in CLIP_MODELS:
            self.model_combo.addItem(label)
        self.model_combo.setMinimumWidth(220)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_row.addWidget(self.model_combo)
        self.btn_dl_model = QPushButton(tr("btn_clip_download"))
        self.btn_dl_model.setObjectName("SecondaryBtn")
        self.btn_dl_model.clicked.connect(self.download_model)
        model_row.addWidget(self.btn_dl_model)
        right.addLayout(model_row)

        self.lbl_dl_status = QLabel("")
        self.lbl_dl_status.setStyleSheet("color: #888; font-size: 10px;")
        right.addWidget(self.lbl_dl_status)

        right.addWidget(QLabel(tr("clip_prompt")))
        self.clip_prompt_edit = QPlainTextEdit()
        self.clip_prompt_edit.setReadOnly(True)
        self.clip_prompt_edit.setFixedHeight(80)
        self.clip_prompt_edit.setPlaceholderText(tr("clip_prompt_placeholder"))
        right.addWidget(self.clip_prompt_edit)

        self.btn_copy_t2i = QPushButton(tr("btn_clip_copy_t2i"))
        self.btn_copy_t2i.setObjectName("ActionBtn")
        self.btn_copy_t2i.clicked.connect(self.copy_to_t2i)
        right.addWidget(self.btn_copy_t2i)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #333;")
        right.addWidget(sep2)

        right.addWidget(QLabel(tr("clip_ranking")))
        self.ranking_list = QTreeWidget()
        self.ranking_list.setHeaderLabels([tr("clip_category"), tr("clip_match"), tr("clip_score")])
        self.ranking_list.setColumnWidth(0, 100)
        self.ranking_list.setColumnWidth(1, 200)
        self.ranking_list.setAlternatingRowColors(True)
        self.ranking_list.setRootIsDecorated(False)
        right.addWidget(self.ranking_list, 1)

        l.addLayout(right, 2)

        self._check_model_state()

    def _model_local_dir(self):
        idx = self.model_combo.currentIndex()
        _, model_id = CLIP_MODELS[idx]
        safe = model_id.replace("/", "_")
        return os.path.join(CLIP_DIR, safe)

    def _model_downloaded(self):
        return os.path.isdir(self._model_local_dir())

    def _on_model_changed(self):
        self._check_model_state()

    def _check_model_state(self):
        if self._model_downloaded():
            self.btn_dl_model.setText(tr("btn_clip_downloaded"))
            self.btn_dl_model.setEnabled(False)
            self.lbl_dl_status.setText(tr("clip_model_ready"))
            self._model_ready = True
            self.btn_analyze.setEnabled(True)
        else:
            self.btn_dl_model.setText(tr("btn_clip_download"))
            self.btn_dl_model.setEnabled(True)
            self.lbl_dl_status.setText(tr("clip_model_need_dl"))
            self._model_ready = False
            self.btn_analyze.setEnabled(False)

    def load_image(self):
        f, _ = QFileDialog.getOpenFileName(self, tr("dialog_image"), "", "Images (*.png *.jpg *.jpeg *.webp)")
        if f:
            pix = QPixmap(f)
            self.clip_preview.set_image(pix)
            self.clip_preview.setText("")
            self._image_path = f

    def download_model(self):
        if self._dl_worker and self._dl_worker.isRunning():
            return
        self.btn_dl_model.setEnabled(False)
        self.btn_dl_model.setText(tr("btn_clip_downloading"))
        self.lbl_dl_status.setText(tr("clip_downloading"))
        self.clip_progress.setMaximum(0)
        self.clip_progress.show()
        _, model_id = CLIP_MODELS[self.model_combo.currentIndex()]
        self._dl_worker = ClipDownloadWorker(model_id, self._model_local_dir())
        self._dl_worker.finished.connect(self._on_dl_finished)
        self._dl_worker.progress.connect(self._on_dl_progress)
        self._dl_worker.start()

    def _on_dl_progress(self, pct, msg):
        if self.clip_progress.maximum() == 0 and pct > 0:
            self.clip_progress.setMaximum(100)
        if pct >= 0:
            self.clip_progress.setValue(pct)
        self.lbl_dl_status.setText(msg)

    def _on_dl_finished(self, success, msg):
        self.clip_progress.hide()
        if success:
            self.lbl_dl_status.setText(tr("clip_dl_done"))
            self._check_model_state()
        else:
            self.lbl_dl_status.setText(msg)
            self.btn_dl_model.setText(tr("btn_clip_download"))
            self.btn_dl_model.setEnabled(True)

    def analyze(self):
        if not hasattr(self, '_image_path') or not self._image_path:
            QMessageBox.warning(self, tr("status_error"), tr("clip_no_image"))
            return
        if not self._model_ready:
            QMessageBox.warning(self, tr("status_error"), tr("clip_model_need_dl"))
            return
        if self._clip_worker and self._clip_worker.isRunning():
            return

        self.btn_analyze.setEnabled(False)
        self.clip_prompt_edit.clear()
        self.ranking_list.clear()
        self.clip_progress.setMaximum(100)
        self.clip_progress.setValue(0)
        self.clip_progress.show()

        _, model_id = CLIP_MODELS[self.model_combo.currentIndex()]
        use_gpu = self.chk_use_gpu.isChecked()

        self._clip_worker = CLIPInterrogatorWorker(
            image_path=self._image_path,
            model_id=model_id,
            local_dir=self._model_local_dir(),
            candidates=self._candidates,
            use_gpu=use_gpu
        )
        self._clip_worker.progress.connect(self._on_clip_progress)
        self._clip_worker.status.connect(self.lbl_dl_status.setText)
        self._clip_worker.finished.connect(self._on_clip_finished)
        self._clip_worker.start()

    def _on_clip_progress(self, value):
        self.clip_progress.setValue(value)

    def _on_clip_finished(self, prompt, rankings):
        self.clip_progress.hide()
        self.btn_analyze.setEnabled(True)
        if prompt:
            self.clip_prompt_edit.setPlainText(prompt)
        self.ranking_list.clear()
        for cat, text, score in rankings:
            item = QTreeWidgetItem([cat, text, f"{score:.3f}"])
            self.ranking_list.addTopLevelItem(item)
        self.lbl_dl_status.setText(tr("clip_done"))

    def copy_to_t2i(self):
        text = self.clip_prompt_edit.toPlainText()
        if text:
            self.prompt_ready.emit(text)

    def refresh_candidates(self):
        self._candidates = {}
        if not os.path.isdir(CLIP_DATA_DIR):
            return
        for fname in sorted(os.listdir(CLIP_DATA_DIR)):
            if fname.endswith(".json"):
                path = os.path.join(CLIP_DATA_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for cat, terms in data.items():
                        if isinstance(terms, list):
                            self._candidates.setdefault(cat, []).extend(terms)
                except Exception as e:
                    print(f"[CLIP] Error loading {fname}: {e}")

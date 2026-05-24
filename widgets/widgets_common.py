from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QSpinBox, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QFont, QDoubleValidator
from utils import qimage_to_pil
from config import tr


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
            self.update_scaling()
    def update_scaling(self):
        if self.pixmap_cached and not self.pixmap_cached.isNull():
            s = self.size()
            if s.isValid() and s.width() > 1 and s.height() > 1:
                self.setPixmap(self.pixmap_cached.scaled(s, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scaling()
    def mousePressEvent(self, e):
        if self.pixmap_cached: self.clicked.emit(self.pixmap_cached)


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
    def setValue(self, v): self.spin.setValue(v)


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

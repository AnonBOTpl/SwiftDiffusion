import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QGraphicsDropShadowEffect
from config import tr


class ResourceMonitor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nvml_active = False
        self._init_nvml()
        self._build_ui()
        self._start_timer()

    def _init_nvml(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nvml_active = True
            logging.info("[ResourceMonitor] NVIDIA management initialized")
        except Exception:
            self.nvml_active = False
            logging.info("[ResourceMonitor] NVIDIA management not available")

    def _build_ui(self):
        mon_frame = QFrame()
        mon_l = QVBoxLayout(mon_frame)
        mon_l.setContentsMargins(0, 5, 0, 0)
        mon_l.setSpacing(4)

        lbl_mon = QLabel(tr("sidebar_monitor"))
        lbl_mon.setObjectName("Header")
        mon_l.addWidget(lbl_mon)

        self.lbl_vram_info = QLabel("VRAM: -")
        self.lbl_vram_info.setStyleSheet("font-size: 10px; color: #aaa;")
        self.vram_bar = QProgressBar()
        self.vram_bar.setFixedHeight(12)
        self.vram_bar.setTextVisible(False)
        mon_l.addWidget(self.lbl_vram_info)
        mon_l.addWidget(self.vram_bar)

        self.lbl_gpu_info = QLabel("GPU: -")
        self.lbl_gpu_info.setStyleSheet("font-size: 10px; color: #aaa;")
        self.gpu_bar = QProgressBar()
        self.gpu_bar.setFixedHeight(12)
        self.gpu_bar.setTextVisible(False)
        mon_l.addWidget(self.lbl_gpu_info)
        mon_l.addWidget(self.gpu_bar)

        self.lbl_ram_info = QLabel("RAM: -")
        self.lbl_ram_info.setStyleSheet("font-size: 10px; color: #aaa;")
        self.ram_bar = QProgressBar()
        self.ram_bar.setFixedHeight(12)
        self.ram_bar.setTextVisible(False)
        mon_l.addWidget(self.lbl_ram_info)
        mon_l.addWidget(self.ram_bar)

        mon_shadow = QGraphicsDropShadowEffect()
        mon_shadow.setBlurRadius(15)
        mon_shadow.setColor(QColor(0, 0, 0, 80))
        mon_shadow.setOffset(0, 3)
        mon_frame.setGraphicsEffect(mon_shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(mon_frame)

    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(1000)

    def _update(self):
        try:
            import psutil
            ram = psutil.virtual_memory()
            self.ram_bar.setValue(int(ram.percent))
            self.lbl_ram_info.setText(tr("monitor_ram").format(used=ram.used/1024**3, total=ram.total/1024**3))
            self._set_mon_color(self.lbl_ram_info, ram.percent)

            if self.nvml_active:
                try:
                    import pynvml
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    vram_used = info.used / 1024**3
                    vram_total = info.total / 1024**3
                    vram_perc = (info.used / info.total) * 100
                    self.vram_bar.setValue(int(vram_perc))
                    self.lbl_vram_info.setText(tr("monitor_vram").format(used=vram_used, total=vram_total))
                    self._set_mon_color(self.lbl_vram_info, vram_perc)

                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    self.gpu_bar.setValue(int(util.gpu))
                    self.lbl_gpu_info.setText(tr("monitor_gpu").format(util=util.gpu, temp=temp))
                    self._set_mon_color(self.lbl_gpu_info, util.gpu)
                except Exception as e:
                    self.nvml_active = False
                    self.lbl_vram_info.setText(tr("monitor_vram_error"))
                    self.lbl_gpu_info.setText(tr("monitor_gpu_error"))
            else:
                self.lbl_vram_info.setText(tr("monitor_vram_na"))
                self.lbl_gpu_info.setText(tr("monitor_gpu_na"))

        except Exception as e:
            logging.debug(f"Monitor error: {e}")

    def _set_mon_color(self, label, percent):
        color = "#00ff00" if percent < 80 else "#ffaa00" if percent < 95 else "#ff4444"
        label.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: bold;")

    def shutdown(self):
        self._timer.stop()
        if self.nvml_active:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass

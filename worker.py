from PyQt6.QtCore import QThread, pyqtSignal

class GenerationWorker(QThread):
    finished = pyqtSignal(str, int) # końcowa ścieżka, ziarno
    part_finished = pyqtSignal(str, int) # ścieżka bazy, ziarno
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def run(self):
        self.status.emit("Generowanie...")
        file_path, used_seed = self.engine.generate(self.params, callback=lambda s: self.progress.emit(s))
        self.part_finished.emit(file_path, used_seed)

        if self.params.get('auto_upscale') and self.params.get('upscaler_model'):
            self.status.emit("Powiększanie (Upscaling)...")
            upscaled_path = self.engine.upscale_image(
                file_path,
                self.params['upscaler_model'],
                self.params.get('keep_upscaler_vram', False)
            )
            if upscaled_path:
                file_path = upscaled_path

        self.finished.emit(file_path, used_seed)

class InpaintWorker(QThread):
    finished = pyqtSignal(str, int)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def run(self):
        self.status.emit("Inpainting...")
        file_path, used_seed = self.engine.inpaint(self.params, callback=lambda s: self.progress.emit(s))
        self.finished.emit(file_path, used_seed)

class ControlNetWorker(QThread):
    finished = pyqtSignal(str, int)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def run(self):
        self.status.emit("ControlNet (Canny)...")
        file_path, used_seed = self.engine.controlnet_generate(self.params, callback=lambda s: self.progress.emit(s))
        self.finished.emit(file_path, used_seed)

class ADetailerWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def run(self):
        self.status.emit("Detekcja YOLO / Inpainting...")
        out_path = self.engine.apply_adetailer(self.params, callback=lambda s: self.progress.emit(s))

        if out_path and self.params.get('auto_upscale') and self.params.get('upscaler_model'):
            self.status.emit("ADetailer -> Upscaling...")
            ups_path = self.engine.upscale_image(
                out_path,
                self.params['upscaler_model'],
                self.params.get('keep_upscaler_vram', False)
            )
            if ups_path: out_path = ups_path

        self.finished.emit(out_path)

class ModelLoaderWorker(QThread):
    finished = pyqtSignal(bool, str) # success, message
    def __init__(self, engine, model_path, loras):
        super().__init__()
        self.engine = engine
        self.model_path = model_path
        self.loras = loras
    def run(self):
        try:
            self.engine.load_model(self.model_path)
            for name, lora_item in self.loras.items():
                self.engine.load_lora(lora_item.path, name)
            self.finished.emit(True, "Model loaded")
        except Exception as e:
            self.finished.emit(False, str(e))

class UpscaleWorker(QThread):
    finished = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, engine, image_path, model_path, keep_vram):
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.model_path = model_path
        self.keep_vram = keep_vram

    def run(self):
        self.status.emit("Powiększanie...")
        upscaled_path = self.engine.upscale_image(self.image_path, self.model_path, self.keep_vram)
        self.finished.emit(upscaled_path)

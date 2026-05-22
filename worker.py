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

        if self.params.get('auto_facerestore') and self.params.get('facerestore_model'):
            self.status.emit("Face Restore...")
            restored_path = self.engine.apply_face_restore(
                file_path,
                self.params['facerestore_model'],
                self.params.get('face_detector', 'retinaface_resnet50')
            )
            if restored_path:
                file_path = restored_path

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

class FaceRestoreWorker(QThread):
    finished = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self, engine, image_path, model_path, detector_model):
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.model_path = model_path
        self.detector_model = detector_model

    def run(self):
        self.status.emit("Face Restore...")
        path = self.engine.apply_face_restore(self.image_path, self.model_path, self.detector_model)
        self.finished.emit(path)

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

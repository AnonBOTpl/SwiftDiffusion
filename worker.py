from PyQt6.QtCore import QThread, pyqtSignal
import os, time, random, re
import requests
from config import settings, tr

WILDCARDS_DIR = os.path.join(os.path.dirname(__file__), "wildcards")

def resolve_wildcards(text):
    if not text:
        return text
    def _replace(m):
        token = m.group(1)
        path = os.path.join(WILDCARDS_DIR, f"{token}.txt")
        if not os.path.isfile(path):
            return m.group(0)
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return m.group(0)
        return random.choice(lines)
    result = re.sub(r"__(\w+)__", _replace, text)
    print(f"[Wildcards] resolved: {result}")
    return result

def log(msg):
    """Print to console for debugging."""
    print(f"[SwiftDiffusion] {msg}")

class GenerationWorker(QThread):
    finished = pyqtSignal(str, int)
    part_finished = pyqtSignal(str, int)
    progress = pyqtSignal(int, object)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def stop(self):
        self.engine.stop_generation()

    def run(self):
        self.status.emit(tr("worker_generating"))
        self.params['prompt'] = resolve_wildcards(self.params.get('prompt', ''))
        self.params['neg_prompt'] = resolve_wildcards(self.params.get('neg_prompt', ''))
        try:
            file_path, used_seed = self.engine.generate(self.params, callback=lambda s, p: self.progress.emit(s, p))
        except Exception as e:
            if "STOPPED" in str(e):
                self.finished.emit("", 0)
                return
            log(f"GenerationWorker error: {e}")
            self.finished.emit("", 0)
            return
        self.part_finished.emit(file_path, used_seed)

        if self.params.get('auto_upscale') and self.params.get('upscaler_model'):
            self.status.emit(tr("status_upscaling"))
            upscaled_path = self.engine.upscale_image(
                file_path,
                self.params['upscaler_model'],
                self.params.get('keep_upscaler_vram', False)
            )
            if upscaled_path:
                file_path = upscaled_path

        self.finished.emit(file_path, used_seed)

class Img2ImgWorker(QThread):
    finished = pyqtSignal(str, int)
    part_finished = pyqtSignal(str, int)
    progress = pyqtSignal(int, object)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def stop(self):
        self.engine.stop_generation()

    def run(self):
        self.status.emit(tr("worker_img2img"))
        self.params['prompt'] = resolve_wildcards(self.params.get('prompt', ''))
        self.params['neg_prompt'] = resolve_wildcards(self.params.get('neg_prompt', ''))
        try:
            file_path, used_seed = self.engine.img2img(self.params, callback=lambda s, p: self.progress.emit(s, p))
        except Exception as e:
            if "STOPPED" in str(e):
                self.finished.emit("", 0)
                return
            log(f"Img2ImgWorker error: {e}")
            self.finished.emit("", 0)
            return
        self.part_finished.emit(file_path, used_seed)

        if self.params.get('auto_upscale') and self.params.get('upscaler_model'):
            self.status.emit(tr("status_upscaling"))
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

    def stop(self):
        self.engine.stop_generation()

    def run(self):
        self.status.emit(tr("worker_inpainting"))
        self.params['prompt'] = resolve_wildcards(self.params.get('prompt', ''))
        self.params['neg_prompt'] = resolve_wildcards(self.params.get('neg_prompt', ''))
        try:
            file_path, used_seed = self.engine.inpaint(self.params, callback=lambda s: self.progress.emit(s))
        except Exception as e:
            if "STOPPED" in str(e):
                self.finished.emit("", 0)
                return
            log(f"InpaintWorker error: {e}")
            self.finished.emit("", 0)
            return
        self.finished.emit(file_path, used_seed)

class ControlNetWorker(QThread):
    finished = pyqtSignal(str, int)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def stop(self):
        self.engine.stop_generation()

    def run(self):
        self.status.emit(tr("worker_controlnet"))
        self.params['prompt'] = resolve_wildcards(self.params.get('prompt', ''))
        self.params['neg_prompt'] = resolve_wildcards(self.params.get('neg_prompt', ''))
        try:
            file_path, used_seed = self.engine.controlnet_generate(self.params, callback=lambda s: self.progress.emit(s))
        except Exception as e:
            if "STOPPED" in str(e):
                self.finished.emit("", 0)
                return
            log(f"ControlNetWorker error: {e}")
            self.finished.emit("", 0)
            return
        self.finished.emit(file_path, used_seed)

class ADetailerWorker(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, engine, params):
        super().__init__()
        self.engine = engine
        self.params = params

    def stop(self):
        self.engine.stop_generation()

    def run(self):
        try:
            self.status.emit(tr("worker_yolo_detection"))
            self.params['prompt'] = resolve_wildcards(self.params.get('prompt', ''))
            self.params['neg_prompt'] = resolve_wildcards(self.params.get('neg_prompt', ''))
            out_path = self.engine.apply_adetailer(self.params, callback=lambda s: self.progress.emit(s))

            if out_path and self.params.get('auto_upscale') and self.params.get('upscaler_model'):
                self.status.emit(tr("worker_adetailer_upscale"))
                ups_path = self.engine.upscale_image(
                    out_path,
                    self.params['upscaler_model'],
                    self.params.get('keep_upscaler_vram', False)
                )
                if ups_path: out_path = ups_path

            self.finished.emit(out_path)
        except Exception as e:
            log(f"ADetailerWorker error: {e}")
            self.finished.emit("")

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

class SearchWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, source_name, query, token=None, api_key=None, model_type=None):
        super().__init__()
        self.source_name = source_name
        self.query = query
        self.token = token
        self.api_key = api_key
        self.model_type = model_type

    def run(self):
        log(f"SearchWorker: source={self.source_name}, query='{self.query}', type='{self.model_type}'")
        try:
            from models_registry import search_source, reset_page, SOURCE_PAGES
            reset_page(self.source_name)
            results, cursor = search_source(self.source_name, self.query, self.token, self.api_key, self.model_type)
            SOURCE_PAGES[self.source_name]["cursor"] = cursor
            SOURCE_PAGES[self.source_name]["has_more"] = cursor is not None
            log(f"SearchWorker: {len(results)} results, has_more={cursor is not None}")
            self.finished.emit(results)
        except Exception as e:
            log(f"SearchWorker ERROR: {e}")
            self.finished.emit([])

class SearchMoreWorker(QThread):
    finished = pyqtSignal(list, str)

    def __init__(self, query, source_name, token=None, api_key=None, model_type=None):
        super().__init__()
        self.query = query
        self.source_name = source_name
        self.token = token
        self.api_key = api_key
        self.model_type = model_type

    def run(self):
        log(f"SearchMoreWorker: source={self.source_name}, query='{self.query}'")
        try:
            from models_registry import search_more
            results, has_more = search_more(self.query, self.source_name, self.token, self.api_key, self.model_type)
            log(f"SearchMoreWorker: {len(results)} results, has_more={has_more}")
            self.finished.emit(results, self.source_name)
        except Exception as e:
            log(f"SearchMoreWorker ERROR: {e}")
            self.finished.emit([], self.source_name)

def _hf_list_files(repo_id, token=None):
    """Fetch list of .safetensors files from a HF model repo."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(
            f"https://huggingface.co/api/models/{repo_id}",
            headers=headers, timeout=10
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        siblings = data.get("siblings", [])
        safetensors = [s["rfilename"] for s in siblings if s["rfilename"].endswith(".safetensors")]
        return safetensors
    except Exception:
        return []

class DownloadWorker(QThread):
    progress = pyqtSignal(float, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, destination, repo_id, filename, token=None, source="huggingface", version_id=None):
        super().__init__()
        self.destination = destination
        self.repo_id = repo_id
        self.filename = filename
        self.token = token
        self.source = source
        self.version_id = version_id

    def run(self):
        log(f"DownloadWorker: source={self.source}, repo={self.repo_id}, dest={self.destination}")
        try:
            if self.source == "civitai":
                self._download_civitai()
            else:
                self._download_hf()
        except Exception as e:
            log(f"DownloadWorker EXCEPTION: {e}")
            self.finished.emit(False, str(e))

    def _download_hf(self):
        from huggingface_hub import hf_hub_download
        log(f"HF download: repo_id={self.repo_id}, filename='{self.filename}'")
        self.progress.emit(0, tr("dl_connecting_hf"))

        fn = self.filename
        if not fn:
            self.progress.emit(0, tr("dl_searching_repo"))
            log(f"HF auto-detect files for {self.repo_id}")
            files = _hf_list_files(self.repo_id, self.token)
            log(f"HF files found: {files}")
            if not files:
                log(f"HF ERROR: no .safetensors in {self.repo_id}")
                self.finished.emit(False, tr("dl_error_no_files"))
                return
            fn = files[0]
            if len(files) > 1:
                for f in files:
                    if "ema" not in f.lower() and "pruned" in f.lower():
                        fn = f
                        break
            log(f"HF selected file: {fn}")

        out = hf_hub_download(
            repo_id=self.repo_id,
            filename=fn,
            token=self.token if self.token else None,
            local_dir=os.path.dirname(self.destination)
        )
        log(f"HF download complete: {out}")
        self.progress.emit(100, tr("dl_download_done"))
        self.finished.emit(True, out)

    def _download_civitai(self):
        self.progress.emit(0, tr("dl_downloading_civitai"))
        log(f"CivitAI download: version_id={self.version_id}, dest={self.destination}")

        vid = self.version_id
        if not vid:
            log("CivitAI ERROR: no version_id")
            self.finished.emit(False, tr("dl_error_no_version"))
            return

        api_key = settings.get('Integration', 'civitai_api_key')
        log(f"CivitAI API key set: {bool(api_key)}")
        headers = {"User-Agent": "SwiftDiffusion/1.0"}
        dl_url = f"https://civitai.com/api/download/models/{vid}?type=Model&format=SafeTensor"
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            dl_url += f"&token={api_key}"
        log(f"CivitAI URL: {dl_url}")
        try:
            resp = requests.get(dl_url, headers=headers, stream=True, timeout=30)
        except Exception as e:
            log(f"CivitAI connection error: {e}")
            self.finished.emit(False, tr("dl_error_connection").format(e=e))
            return

        log(f"CivitAI response: {resp.status_code}")
        if resp.status_code != 200:
            log(f"CivitAI error body: {resp.text[:500]}")
            self.finished.emit(False, tr("dl_error_server").format(code=resp.status_code))
            return

        total = int(resp.headers.get("content-length", 0))
        log(f"CivitAI file size: {total} bytes")
        downloaded = 0
        last_emit = 0
        with open(self.destination, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if total and now - last_emit > 0.15:
                        pct = int(downloaded / total * 100)
                        self.progress.emit(pct, tr("dl_downloading_progress").format(pct=pct, downloaded=downloaded//1048576, total=total//1048576))
                        log(f"CivitAI progress: {pct}% ({downloaded}/{total})")
                        last_emit = now

        log(f"CivitAI download complete: {self.destination}")
        self.progress.emit(100, tr("dl_download_done"))
        self.finished.emit(True, self.destination)

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
        try:
            self.status.emit(tr("status_upscaling"))
            upscaled_path = self.engine.upscale_image(self.image_path, self.model_path, self.keep_vram)
            self.finished.emit(upscaled_path)
        except Exception as e:
            log(f"UpscaleWorker error: {e}")
            self.finished.emit("")


class ClipDownloadWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, model_id, local_dir):
        super().__init__()
        self.model_id = model_id
        self.local_dir = local_dir

    def run(self):
        try:
            from huggingface_hub import snapshot_download, HfApi
            os.makedirs(os.path.dirname(self.local_dir), exist_ok=True)
            self.progress.emit(-1, f"Downloading {self.model_id}...")

            api = HfApi()
            files = api.list_repo_files(self.model_id)
            has_safetensors = any(f.endswith(".safetensors") for f in files)

            ignore = ["flax_model.msgpack", "tf_model.h5"]
            if has_safetensors:
                ignore.append("pytorch_model.bin")

            snapshot_download(
                repo_id=self.model_id,
                local_dir=self.local_dir,
                local_dir_use_symlinks=False,
                resume_download=True,
                ignore_patterns=ignore
            )
            self.finished.emit(True, "Model downloaded")
        except Exception as e:
            log(f"ClipDownloadWorker error: {e}")
            self.finished.emit(False, str(e))


class CLIPInterrogatorWorker(QThread):
    finished = pyqtSignal(str, list)
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def __init__(self, image_path, clip_model_name, candidates, use_gpu=False):
        super().__init__()
        self.image_path = image_path
        self.clip_model_name = clip_model_name
        self.candidates = candidates
        self.use_gpu = use_gpu

    def run(self):
        try:
            from PIL import Image
            from clip_interrogator import Config, Interrogator
            import torch

            config = Config()
            config.clip_model_name = self.clip_model_name
            if self.use_gpu and torch.cuda.is_available():
                config.device = "cuda"

            interrogator = Interrogator(config)
            self.progress.emit(50)

            image = Image.open(self.image_path).convert("RGB")
            results = interrogator.interrogate(image)
            self.progress.emit(100)

            items = [(cat, term, f"{score:.3f}") for cat, terms in results if cat != "rating" for term, score in terms]
            self.finished.emit(results[0][1][0][0] if results else "", items)
        except Exception as e:
            log(f"CLIPInterrogatorWorker error: {e}")
            self.finished.emit("", [])

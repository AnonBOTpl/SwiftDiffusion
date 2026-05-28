import torchvision.transforms.functional as TF
import sys
import types

if 'torchvision.transforms.functional_tensor' not in sys.modules:
    fake_module = types.ModuleType('torchvision.transforms.functional_tensor')
    fake_module.rgb_to_grayscale = TF.rgb_to_grayscale
    sys.modules['torchvision.transforms.functional_tensor'] = fake_module

import torch
import gc
import cv2
import numpy as np
import os
import requests
import logging
from huggingface_hub import hf_hub_download
from config import settings

logger = logging.getLogger("SwiftDiffusion")

RESTORATION_DIR = os.path.join(os.path.dirname(__file__), settings.get('Paths', 'models_restoration'))
COLORIZATION_DIR = os.path.join(os.path.dirname(__file__), settings.get('Paths', 'models_colorization'))

RESTORATION_FILES = [
    ("RealESRGAN_x4plus.pth", "LS110824/upscale", "model"),
    ("GFPGANv1.4.pth", "nlightcho/gfpgan_v14", "model"),
]

COLORIZATION_FILES = [
    ("colorization_deploy_v2.prototxt", None, "https://raw.githubusercontent.com/richzhang/colorization/caffe/models/colorization_deploy_v2.prototxt"),
    ("colorization_release_v2.caffemodel", "viveknarayan/Image_Colorization", "space"),
    ("pts_in_hull.npy", "viveknarayan/Image_Colorization", "space"),
]


class RestorationEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def _clear_vram(self):
        torch.cuda.empty_cache()
        gc.collect()

    def _remove_scratches(self, img):
        logger.info(f"[Restoration] Scratch removal input: shape={img.shape}, dtype={img.dtype}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
        _, mask = cv2.threshold(tophat, 15, 255, cv2.THRESH_BINARY)
        mask = cv2.dilate(mask, kernel, iterations=1)
        n_pixels = int(mask.sum() / 255)
        logger.info(f"[Restoration] Scratch mask: {n_pixels} pixels detected out of {mask.size}")
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
        logger.info(f"[Restoration] Scratch removal done: range=[{result.min()},{result.max()}]")
        return result

    def _upscale(self, img):
        logger.info(f"[Restoration] Upscale input: shape={img.shape}, range=[{img.min()},{img.max()}]")
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet

        model_path = os.path.join(RESTORATION_DIR, "RealESRGAN_x4plus.pth")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Real-ESRGAN model not found: {model_path}")

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        upscaler = RealESRGANer(
            scale=4, model_path=model_path, model=model,
            tile=400, tile_pad=10, half=True, device=self.device
        )
        img, _ = upscaler.enhance(img, outscale=2)
        del upscaler
        self._clear_vram()
        logger.info(f"[Restoration] Upscale output: shape={img.shape}, range=[{img.min()},{img.max()}]")
        return img

    def _enhance_faces(self, img):
        logger.info(f"[Restoration] Face enhance input: shape={img.shape}, range=[{img.min()},{img.max()}]")
        from gfpgan import GFPGANer

        model_path = os.path.join(RESTORATION_DIR, "GFPGANv1.4.pth")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"GFPGAN model not found: {model_path}")

        enhancer = GFPGANer(
            model_path=model_path, upscale=2, arch='clean',
            channel_multiplier=2, bg_upsampler=None, device=self.device
        )
        _, _, img = enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
        del enhancer
        self._clear_vram()
        logger.info(f"[Restoration] Face enhance output: shape={img.shape}, range=[{img.min()},{img.max()}]")
        return img

    def _colorize_opencv(self, img):
        h, w = img.shape[:2]
        logger.info(f"[Restoration] Colorization input: shape={img.shape}, dtype={img.dtype}")
        prototxt = os.path.join(COLORIZATION_DIR, "colorization_deploy_v2.prototxt")
        caffemodel = os.path.join(COLORIZATION_DIR, "colorization_release_v2.caffemodel")
        pts_path = os.path.join(COLORIZATION_DIR, "pts_in_hull.npy")
        for p in [prototxt, caffemodel, pts_path]:
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Colorization file not found: {p}")

        net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        pts_in_hull = np.load(pts_path)
        logger.info(f"[Restoration] Hull points: shape={pts_in_hull.shape}, range=[{pts_in_hull.min():.3f},{pts_in_hull.max():.3f}]")
        pts_in_hull = pts_in_hull.transpose().reshape(2, 313, 1, 1)
        net.getLayer(net.getLayerId("class8_ab")).blobs = [pts_in_hull.astype(np.float32)]
        net.getLayer(net.getLayerId("conv8_313_rh")).blobs = [np.full([1, 313], 2.606, np.float32)]

        img_rgb = (img[:, :, [2, 1, 0]].astype(np.float32)) / 255.0
        img_lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2Lab)
        L = img_lab[:, :, 0]
        logger.info(f"[Restoration] L channel: range=[{L.min():.2f},{L.max():.2f}]")
        L_in = cv2.resize(L, (224, 224)) - 50.0
        logger.info(f"[Restoration] L input to net: range=[{L_in.min():.2f},{L_in.max():.2f}]")
        net.setInput(L_in.reshape(1, 1, 224, 224).astype(np.float32))

        ab = net.forward()[0, :, :, :].transpose((1, 2, 0))
        logger.info(f"[Restoration] ab output from net: shape={ab.shape}, range=[{ab.min():.4f},{ab.max():.4f}]")
        ab = cv2.resize(ab, (w, h), interpolation=cv2.INTER_LINEAR)
        logger.info(f"[Restoration] ab resized to ({w},{h}): range=[{ab.min():.4f},{ab.max():.4f}]")
        del net
        self._clear_vram()
        lab = np.concatenate([L[:, :, np.newaxis], ab], axis=2)
        out = np.clip(cv2.cvtColor(lab, cv2.COLOR_Lab2BGR), 0, 1)
        logger.info(f"[Restoration] Colorization output: range=[{out.min():.4f},{out.max():.4f}]")
        return (out * 255).astype(np.uint8)

    def _pass1_colorize(self, img, colorize_method, status_cb):
        status_cb("Colorizing (OpenCV DNN)...")
        logger.info("[Restoration] Pass1: OpenCV DNN colorization")
        return self._colorize_opencv(img)

    def _pass2_scratch_upscale_face(self, img, status_cb):
        status_cb("Removing scratches...")
        img = self._remove_scratches(img)
        if self._stop_flag:
            return None
        status_cb("Upscaling (Real-ESRGAN)...")
        img = self._upscale(img)
        if self._stop_flag:
            return None
        status_cb("Enhancing faces (GFPGAN)...")
        img = self._enhance_faces(img)
        if self._stop_flag:
            return None
        return img

    def run_pipeline(self, image_path, progress_cb, status_cb, auto_scratch=True, colorize_method=None, extra_upscale=False):
        self._stop_flag = False
        logger.info(f"[Restoration] Pipeline start: image={image_path}, auto_scratch={auto_scratch}, colorize={colorize_method}")

        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"[Restoration] Failed to load image: {image_path}")
            raise ValueError("Could not load image")
        logger.info(f"[Restoration] Image loaded: shape={img.shape}, dtype={img.dtype}, range=[{img.min()},{img.max()}]")

        needs_colorize = colorize_method is not None

        if needs_colorize:
            # ---- PASS 1: colorize -> upscale -> face enhance (always) ----
            status_cb("Pass 1/2: Colorizing...")
            progress_cb(0)
            img = self._pass1_colorize(img, colorize_method, status_cb)
            if self._stop_flag:
                return None
            progress_cb(15)

            status_cb("Pass 1/2: Upscaling...")
            img = self._upscale(img)
            if self._stop_flag:
                return None
            progress_cb(35)

            status_cb("Pass 1/2: Enhancing faces...")
            img = self._enhance_faces(img)
            if self._stop_flag:
                return None
            progress_cb(50)

            # ---- PASS 2: only if scratch removal is also checked ----
            if auto_scratch:
                status_cb("Pass 2/2: Removing scratches...")
                progress_cb(55)
                img = self._remove_scratches(img)
                if self._stop_flag:
                    return None
                progress_cb(70)

                if extra_upscale:
                    status_cb("Pass 2/2: Upscaling...")
                    img = self._upscale(img)
                    if self._stop_flag:
                        return None
                    progress_cb(85)

                status_cb("Pass 2/2: Enhancing faces...")
                img = self._enhance_faces(img)
                if self._stop_flag:
                    return None
                progress_cb(100)

        else:
            # No colorization: single pass scratch -> upscale -> face
            if auto_scratch:
                status_cb("Removing scratches...")
                img = self._remove_scratches(img)
                if self._stop_flag:
                    return None
                progress_cb(30)

            status_cb("Upscaling (Real-ESRGAN)...")
            img = self._upscale(img)
            if self._stop_flag:
                return None
            progress_cb(65)

            status_cb("Enhancing faces (GFPGAN)...")
            img = self._enhance_faces(img)
            if self._stop_flag:
                return None
            progress_cb(100)

        logger.info(f"[Restoration] Pipeline complete: shape={img.shape}, range=[{img.min()},{img.max()}]")
        status_cb("Done")
        return img


class RestorationDownloader:
    def __init__(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def _download_file(self, url, dest, progress_cb, start_pct, end_pct):
        r = requests.get(url, stream=True, timeout=(10, 120))
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if self._stop or chunk is None:
                    return False
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    file_pct = downloaded / total_size
                    progress_cb(int(start_pct + (end_pct - start_pct) * file_pct))
        return True

    def _download_hf(self, fname, repo_id, repo_type, dest_dir, progress_cb, status_cb, start_pct, end_pct):
        dest = os.path.join(dest_dir, fname)
        if os.path.isfile(dest):
            return dest
        status_cb(f"Downloading {fname}...")
        progress_cb(int(start_pct))
        rt = "space" if repo_type == "space" else "model"
        path = hf_hub_download(
            repo_id=repo_id, filename=fname, repo_type=rt,
            local_dir=dest_dir, local_dir_use_symlinks=False,
            resume_download=True,
        )
        progress_cb(int(end_pct))
        return path

    def download_restoration(self, progress_cb, status_cb):
        self._stop = False
        os.makedirs(RESTORATION_DIR, exist_ok=True)
        total = len(RESTORATION_FILES)
        file_pct = 100.0 / total
        for idx, (fname, repo_id, repo_type) in enumerate(RESTORATION_FILES):
            if self._stop:
                return False
            dest = os.path.join(RESTORATION_DIR, fname)
            if os.path.isfile(dest):
                status_cb(f"{fname} already exists")
                progress_cb(int((idx + 1) * file_pct))
                continue
            start_pct = idx * file_pct
            end_pct = (idx + 1) * file_pct
            try:
                self._download_hf(fname, repo_id, repo_type, RESTORATION_DIR,
                                  progress_cb, status_cb, start_pct, end_pct)
            except Exception as e:
                status_cb(f"Failed to download {fname}: {e}")
                return False
        status_cb("Restoration models ready")
        return True

    def download_colorization(self, progress_cb, status_cb):
        self._stop = False
        os.makedirs(COLORIZATION_DIR, exist_ok=True)
        total = len(COLORIZATION_FILES)
        file_pct = 100.0 / total
        for idx, (fname, repo_id, repo_type_or_url) in enumerate(COLORIZATION_FILES):
            if self._stop:
                return False
            dest = os.path.join(COLORIZATION_DIR, fname)
            if os.path.isfile(dest):
                status_cb(f"{fname} already exists")
                progress_cb(int((idx + 1) * file_pct))
                continue
            start_pct = idx * file_pct
            end_pct = (idx + 1) * file_pct
            try:
                if repo_id is not None:
                    self._download_hf(fname, repo_id, repo_type_or_url,
                                      COLORIZATION_DIR, progress_cb, status_cb, start_pct, end_pct)
                else:
                    self._download_file(repo_type_or_url, dest,
                                        progress_cb, start_pct, end_pct)
            except Exception as e:
                status_cb(f"Failed to download {fname}: {e}")
                return False
        status_cb("Colorization models ready")
        return True

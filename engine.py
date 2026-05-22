import torch
import gc
import uuid
import random
import os
import logging
import json
import numpy as np
import cv2
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from config import settings
from diffusers import (
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
    StableDiffusionInpaintPipeline,
    ControlNetModel,
    StableDiffusionControlNetPipeline,
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler,
    DDIMScheduler
)
try:
    from spandrel import ModelLoader, ImageModelDescriptor
except ImportError:
    ModelLoader = None

# --- LOGGING CONFIG ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("SD-Controller")

class DiffusionEngine:
    def __init__(self):
        self.pipe = None
        self.inpaint_pipe = None
        self.controlnet_pipe = None
        self.current_model_path = None
        self.current_inpaint_model_path = None
        self.current_cn_model_path = None
        self.upscaler_model = None
        self.upscaler_path = None

    def _clear_vram(self):
        torch.cuda.empty_cache()
        logger.info("[VRAM] Wyczyszczono pamięć GPU (torch.cuda.empty_cache())")

    def load_model(self, model_path):
        if self.current_model_path == model_path and self.pipe:
            return

        if self.pipe: del self.pipe
        if self.inpaint_pipe: del self.inpaint_pipe
        if self.controlnet_pipe: del self.controlnet_pipe

        self._clear_vram()

        logger.info(f"[SYSTEM] Ładowanie modelu bazowego: {model_path}")
        if model_path.endswith('.safetensors'):
            self.pipe = StableDiffusionPipeline.from_single_file(
                model_path, torch_dtype=torch.float16, use_safetensors=True
            )
        else:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_path, torch_dtype=torch.float16, use_safetensors=True
            )

        self.pipe.safety_checker = None
        self.pipe.feature_extractor = None
        self.pipe.enable_xformers_memory_efficient_attention()
        self._apply_performance_settings(self.pipe)
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.current_model_path = model_path
        self.current_inpaint_model_path = None
        self.current_cn_model_path = None
        self.inpaint_pipe = None
        self.controlnet_pipe = None

    def load_inpaint_model(self, model_path):
        if model_path == "original":
            if self.inpaint_pipe and self.current_inpaint_model_path == "original": return
            logger.info("[SYSTEM] Inicjalizacja Inpaint Pipeline z komponentów modelu głównego")
            self.inpaint_pipe = StableDiffusionInpaintPipeline(**self.pipe.components)
            self.current_inpaint_model_path = "original"
        else:
            if self.current_inpaint_model_path == model_path: return
            if self.pipe:
                del self.pipe
                self.pipe = None
            if self.inpaint_pipe: del self.inpaint_pipe
            self._clear_vram()

            logger.info(f"[SYSTEM] Ładowanie dedykowanego modelu Inpaint: {model_path}")
            self.inpaint_pipe = StableDiffusionInpaintPipeline.from_single_file(
                model_path, torch_dtype=torch.float16, use_safetensors=True
            )
            self.current_inpaint_model_path = model_path
            self.current_model_path = None

        self.inpaint_pipe.enable_xformers_memory_efficient_attention()
        self._apply_performance_settings(self.inpaint_pipe)

    def load_controlnet_model(self, cn_model_path):
        if not self.pipe:
            raise RuntimeError("Najpierw załaduj model główny!")

        if self.current_cn_model_path == cn_model_path and self.controlnet_pipe:
            return

        self._clear_vram()
        logger.info(f"[SYSTEM] Ładowanie modelu ControlNet (współdzielenie komponentów): {cn_model_path}")

        if cn_model_path.endswith('.safetensors'):
            controlnet = ControlNetModel.from_single_file(cn_model_path, torch_dtype=torch.float16)
        else:
            controlnet = ControlNetModel.from_pretrained(cn_model_path, torch_dtype=torch.float16)

        self.controlnet_pipe = StableDiffusionControlNetPipeline(**self.pipe.components, controlnet=controlnet)
        self.controlnet_pipe.enable_xformers_memory_efficient_attention()
        self._apply_performance_settings(self.controlnet_pipe)
        self.current_cn_model_path = cn_model_path

    def load_lora(self, lora_path, adapter_name):
        if self.pipe and lora_path:
            self.pipe.load_lora_weights(lora_path, adapter_name=adapter_name)
            logger.info(f"[SYSTEM] LoRA {lora_path} załadowana jako {adapter_name}")

    def unload_lora(self, adapter_name):
        if hasattr(self, 'pipe') and self.pipe is not None:
            try:
                self.pipe.delete_adapters(adapter_name)
                logger.info(f"[SYSTEM] LoRA {adapter_name} usunięta z pamięci modelu")
            except Exception as e:
                logger.warning(f"[SYSTEM] Błąd przy usuwaniu LoRA {adapter_name}: {e}")

    def apply_loras(self, lora_configs):
        if self.pipe and lora_configs:
            names = [cfg['name'] for cfg in lora_configs]
            weights = [cfg['weight'] for cfg in lora_configs]
            self.pipe.set_adapters(names, adapter_weights=weights)
            logger.info(f"[SYSTEM] Zastosowano wagi LoRA: {dict(zip(names, weights))}")
        elif self.pipe:
            self.pipe.disable_lora()

    def _apply_performance_settings(self, pipe):
        if settings.get_bool('Performance', 'attention_slicing'):
            pipe.enable_attention_slicing()
        else:
            pipe.disable_attention_slicing()

        if settings.get_bool('Performance', 'cpu_offload'):
            pipe.enable_model_cpu_offload()
        else:
            pipe.to("cuda")

        if hasattr(pipe, "vae") and pipe.vae is not None:
            if settings.get_bool('Performance', 'vram_slicing'):
                pipe.vae.enable_slicing()
                pipe.vae.enable_tiling()
            else:
                pipe.vae.disable_slicing()
                pipe.vae.disable_tiling()

    def _set_scheduler(self, pipe, sampler_name, scheduler_name):
        config = pipe.scheduler.config
        use_karras = (scheduler_name == "Karras")
        use_exp = (scheduler_name == "Exponential")

        logger.info(f"[SYSTEM] Ustawianie Schedulera: {sampler_name} ({scheduler_name})")

        if sampler_name == "DPM++ 2M":
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(config, use_karras_sigmas=use_karras, use_exponential_sigmas=use_exp)
        elif sampler_name == "Euler":
            pipe.scheduler = EulerDiscreteScheduler.from_config(config, use_karras_sigmas=use_karras, use_exponential_sigmas=use_exp)
        elif sampler_name == "Euler a":
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(config)
        elif sampler_name == "DDIM":
            pipe.scheduler = DDIMScheduler.from_config(config)

        self._apply_performance_settings(pipe)

    def _maybe_auto_clear(self):
        if settings.get_bool('Performance', 'auto_clear_vram'):
            gc.collect()
            torch.cuda.empty_cache()
            logger.info("[VRAM] Automatyczne czyszczenie pamięci (auto_clear_vram)")

    def generate(self, params, callback=None):
        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.pipe, params['sampler'], params['scheduler'])
        if 'loras' in params: self.apply_loras(params['loras'])
        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if callback: callback(step + 1)
            return callback_kwargs

        logger.info(f"[SYSTEM] Generowanie obrazu (txt2img), seed: {seed}")
        image = self.pipe(
            prompt=params['prompt'],
            negative_prompt=params['neg_prompt'],
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            width=params['width'],
            height=params['height'],
            generator=generator,
            callback_on_step_end=progress_callback
        ).images[0]

        filename = f"gen_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_txt2img'), filename)

        # Zapis metadanych
        metadata = PngInfo()
        metadata_dict = {
            "prompt": params['prompt'],
            "neg_prompt": params['neg_prompt'],
            "steps": params['steps'],
            "cfg": params['cfg'],
            "width": params['width'],
            "height": params['height'],
            "seed": seed,
            "sampler": params.get('sampler', 'DPM++ 2M'),
            "scheduler": params.get('scheduler', 'Normal')
        }
        metadata.add_text("sd_params", json.dumps(metadata_dict))

        image.save(file_path, pnginfo=metadata)
        self._maybe_auto_clear()
        return file_path, seed

    def inpaint(self, params, callback=None):
        self._clear_vram()
        if params.get('inpaint_model') == "original":
            self.load_inpaint_model("original")

        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.inpaint_pipe, params['sampler'], params['scheduler'])

        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if callback: callback(step + 1)
            return callback_kwargs

        mask_img = params['mask']
        orig_img = params['image']
        logger.info(f"[DEBUG INPAINT] Mode: {orig_img.mode}/{mask_img.mode}, Size: {orig_img.size}, Strength: {params.get('strength')}, Steps: {params.get('steps')}, Seed: {seed}")

        image = self.inpaint_pipe(
            prompt=params['prompt'],
            negative_prompt=params['neg_prompt'],
            image=orig_img,
            mask_image=mask_img,
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            strength=params.get('strength', 0.75),
            generator=generator,
            callback_on_step_end=progress_callback
        ).images[0]

        filename = f"inpaint_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_inpaint'), filename)
        image.save(file_path)
        self._maybe_auto_clear()
        return file_path, seed

    def controlnet_generate(self, params, callback=None):
        self._clear_vram()
        self.load_controlnet_model(params['cn_model'])

        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.controlnet_pipe, params['sampler'], params['scheduler'])

        image_np = np.array(params['image'])
        image_canny = cv2.Canny(image_np, 100, 200)
        image_canny = image_canny[:, :, None]
        image_canny = np.concatenate([image_canny, image_canny, image_canny], axis=2)
        canny_image = Image.fromarray(image_canny)

        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if callback: callback(step + 1)
            return callback_kwargs

        logger.info(f"[SYSTEM] Rozpoczęcie generacji ControlNet, seed: {seed}")
        image = self.controlnet_pipe(
            prompt=params['prompt'],
            negative_prompt=params['neg_prompt'],
            image=canny_image,
            num_inference_steps=params.get('steps', 25),
            guidance_scale=params.get('cfg', 7.5),
            controlnet_conditioning_scale=params.get('strength', 1.0),
            generator=generator,
            callback_on_step_end=progress_callback
        ).images[0]

        filename = f"cn_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_controlnet'), filename)
        image.save(file_path)
        self._maybe_auto_clear()
        return file_path, seed

    def upscale_image(self, image_path, upscaler_model_path, keep_in_vram=False):
        if not upscaler_model_path or not os.path.exists(upscaler_model_path) or ModelLoader is None:
            return None

        if self.upscaler_path != upscaler_model_path:
            if self.upscaler_model: del self.upscaler_model; self._clear_vram()
            logger.info(f"[SYSTEM] Ładowanie upscalera: {upscaler_model_path}")
            loader = ModelLoader()
            model = loader.load_from_file(upscaler_model_path)
            self.upscaler_model = model.to("cuda").eval()
            self.upscaler_path = upscaler_model_path

        img = Image.open(image_path).convert("RGB")
        img_np = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to("cuda")

        logger.info(f"[SYSTEM] Powiększanie obrazu: {image_path}")
        with torch.no_grad():
            out_tensor = self.upscaler_model(img_tensor)
            out_np = out_tensor.squeeze(0).permute(1, 2, 0).cpu().clamp(0, 1).numpy()
            out_img = Image.fromarray((out_np * 255).astype(np.uint8))

        filename = os.path.basename(image_path).replace(".png", "_upscaled.png")
        upscaled_path = os.path.join(settings.get('Paths', 'output_upscaled'), filename)
        out_img.save(upscaled_path)

        if not keep_in_vram:
            del self.upscaler_model; self.upscaler_model = None; self.upscaler_path = None; self._clear_vram()

        return upscaled_path

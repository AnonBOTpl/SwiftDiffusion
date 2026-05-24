import torch
import gc
import uuid
import random
import os
import json
import logging
import numpy as np
import cv2
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from config import settings
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    StableDiffusionInpaintPipeline,
    StableDiffusionControlNetPipeline,
    AutoencoderKL,
    DPMSolverMultistepScheduler,
    ControlNetModel,
    EulerDiscreteScheduler,
    EulerAncestralDiscreteScheduler,
    DDIMScheduler
)

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("SD-Controller")

try:
    from spandrel import ModelLoader
except ImportError:
    ModelLoader = None
    logger.error("[SYSTEM] Missing spandrel library")

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    logger.error("[SYSTEM] Missing ultralytics (YOLO) library")


def get_vram_gb():
    try:
        return torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except Exception:
        return 0


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
        self._stop_flag = False
        self.embeddings = []

    def stop_generation(self):
        self._stop_flag = True
        logger.info("[SYSTEM] Generation stop requested")

    def _clear_vram(self):
        gc.collect()
        torch.cuda.empty_cache()
        logger.info("[VRAM] GPU memory cleared (torch.cuda.empty_cache())")

    def load_model(self, model_path):
        if self.current_model_path == model_path and self.pipe:
            return

        if self.pipe: del self.pipe
        if self.inpaint_pipe: del self.inpaint_pipe
        if self.controlnet_pipe: del self.controlnet_pipe
        self._clear_vram()

        logger.info(f"[SYSTEM] Loading model: {model_path}")

        try:
            if model_path.endswith('.safetensors'):
                self.pipe = StableDiffusionPipeline.from_single_file(
                    model_path, torch_dtype=torch.float16, use_safetensors=True
                )
            else:
                self.pipe = StableDiffusionPipeline.from_pretrained(
                    model_path, torch_dtype=torch.float16, use_safetensors=True
                )
        except torch.cuda.OutOfMemoryError:
            logger.error("[SYSTEM] CUDA OOM while loading model - not enough VRAM")
            self._clear_vram()
            raise
        except Exception as e:
            logger.error(f"[SYSTEM] Failed to load model: {e}")
            self._clear_vram()
            raise

        if hasattr(self.pipe, "safety_checker"):
            self.pipe.safety_checker = None
        if hasattr(self.pipe, "feature_extractor"):
            self.pipe.feature_extractor = None
        self.pipe.enable_xformers_memory_efficient_attention()
        self._apply_performance_settings(self.pipe)
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.current_model_path = model_path
        self.current_inpaint_model_path = None
        self.current_cn_model_path = None
        self.inpaint_pipe = None
        self.controlnet_pipe = None
        self._load_embeddings()

    def load_inpaint_model(self, model_path):
        if model_path == "original":
            if self.inpaint_pipe and self.current_inpaint_model_path == "original": return
            logger.info("[SYSTEM] Initializing Inpaint Pipeline from main model components")
            self.inpaint_pipe = StableDiffusionInpaintPipeline(**self.pipe.components)
            self.current_inpaint_model_path = "original"
        else:
            if self.current_inpaint_model_path == model_path: return
            if self.pipe:
                del self.pipe
                self.pipe = None
            if self.inpaint_pipe: del self.inpaint_pipe
            self._clear_vram()

            logger.info(f"[SYSTEM] Loading dedicated Inpaint model: {model_path}")
            self.inpaint_pipe = StableDiffusionInpaintPipeline.from_single_file(
                model_path, torch_dtype=torch.float16, use_safetensors=True
            )
            self.current_inpaint_model_path = model_path
            self.current_model_path = None

        self.inpaint_pipe.enable_xformers_memory_efficient_attention()
        self._apply_performance_settings(self.inpaint_pipe)

    def load_controlnet_model(self, cn_model_path):
        if not self.pipe:
            raise RuntimeError("Load the main model first!")

        if self.current_cn_model_path == cn_model_path and self.controlnet_pipe:
            return

        self._clear_vram()
        logger.info(f"[SYSTEM] Loading ControlNet model (component sharing): {cn_model_path}")

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
            logger.info(f"[SYSTEM] LoRA {lora_path} loaded as {adapter_name}")

    def unload_lora(self, adapter_name):
        if hasattr(self, 'pipe') and self.pipe is not None:
            try:
                self.pipe.delete_adapters(adapter_name)
                logger.info(f"[SYSTEM] LoRA {adapter_name} removed from model memory")
            except Exception as e:
                logger.warning(f"[SYSTEM] Error removing LoRA {adapter_name}: {e}")

    def apply_loras(self, lora_configs):
        if self.pipe and lora_configs:
            names = [cfg['name'] for cfg in lora_configs]
            weights = [cfg['weight'] for cfg in lora_configs]
            self.pipe.set_adapters(names, adapter_weights=weights)
            logger.info(f"[SYSTEM] Applied LoRA weights: {dict(zip(names, weights))}")
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
            else:
                pipe.vae.disable_slicing()

            if settings.get_bool('Performance', 'tiled_vae'):
                pipe.vae.enable_tiling()
            else:
                pipe.vae.disable_tiling()

    def _set_scheduler(self, pipe, sampler_name, scheduler_name):
        config = pipe.scheduler.config
        use_karras = (scheduler_name == "Karras")
        use_exp = (scheduler_name == "Exponential")

        logger.info(f"[SYSTEM] Setting scheduler: {sampler_name} ({scheduler_name})")

        if sampler_name == "DPM++ 2M":
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(config, use_karras_sigmas=use_karras, use_exponential_sigmas=use_exp)
        elif sampler_name == "Euler":
            pipe.scheduler = EulerDiscreteScheduler.from_config(config, use_karras_sigmas=use_karras, use_exponential_sigmas=use_exp)
        elif sampler_name == "Euler a":
            pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(config)
        elif sampler_name == "DDIM":
            pipe.scheduler = DDIMScheduler.from_config(config)

        self._apply_performance_settings(pipe)

    def _apply_custom_vae(self, pipe, vae_path):
        if not vae_path or vae_path == "Domy\u015blne (z modelu)":
            return

        logger.info(f"[SYSTEM] Loading custom VAE: {vae_path}")
        if vae_path.endswith((".safetensors", ".pt", ".ckpt")):
            custom_vae = AutoencoderKL.from_single_file(vae_path, torch_dtype=torch.float16, use_safetensors=vae_path.endswith(".safetensors"))
        else:
            custom_vae = AutoencoderKL.from_pretrained(vae_path, torch_dtype=torch.float16)

        pipe.vae = custom_vae.to(pipe.device)
        self._apply_performance_settings(pipe)

    def _maybe_auto_clear(self):
        if settings.get_bool('Performance', 'auto_clear_vram'):
            gc.collect()
            torch.cuda.empty_cache()
            logger.info("[VRAM] Auto-clearing memory (auto_clear_vram)")

    def _load_embeddings(self):
        self.embeddings = []
        if self.pipe is None:
            return
        emb_dir = settings.get('Paths', 'models_embeddings')
        if not emb_dir or not os.path.isdir(emb_dir):
            return
        exts = (".pt", ".bin", ".safetensors")
        for fname in sorted(os.listdir(emb_dir)):
            if not fname.lower().endswith(exts):
                continue
            path = os.path.join(emb_dir, fname)
            token = os.path.splitext(fname)[0].lower().replace(" ", "_")
            try:
                self.pipe.load_textual_inversion(path, token=token)
                self.embeddings.append(token)
                logger.info(f"[EMBED] Loaded: {fname} as '{token}'")
            except Exception as e:
                logger.warning(f"[EMBED] Failed to load {fname}: {e}")

    def scan_embeddings(self):
        if self.pipe is None:
            return []
        emb_dir = settings.get('Paths', 'models_embeddings')
        if not emb_dir or not os.path.isdir(emb_dir):
            return []
        exts = (".pt", ".bin", ".safetensors")
        existing = set(self.embeddings)
        new_ones = []
        for fname in sorted(os.listdir(emb_dir)):
            if not fname.lower().endswith(exts):
                continue
            token = os.path.splitext(fname)[0].lower().replace(" ", "_")
            if token in existing:
                continue
            path = os.path.join(emb_dir, fname)
            try:
                self.pipe.load_textual_inversion(path, token=token)
                self.embeddings.append(token)
                new_ones.append(token)
                logger.info(f"[EMBED] Loaded new: {fname} as '{token}'")
            except Exception as e:
                logger.warning(f"[EMBED] Failed to load {fname}: {e}")
        return self.embeddings[:]

    def get_embeddings(self):
        return self.embeddings[:]

    def _encode_prompt(self, prompt, neg_prompt):
        try:
            from compel import Compel
            if not prompt and not neg_prompt:
                return False, prompt, neg_prompt
            pipe = self.pipe
            if pipe is None or not hasattr(pipe, 'tokenizer') or not hasattr(pipe, 'text_encoder'):
                return False, prompt, neg_prompt
            compel = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)
            p_emb = compel(prompt) if prompt else None
            n_emb = compel(neg_prompt) if neg_prompt else None
            if p_emb is None and n_emb is None:
                return False, prompt, neg_prompt
            if p_emb is None:
                p_emb = compel("")
            if n_emb is None:
                n_emb = compel("")
            logger.info(f"[COMPEL] Active - prompt embeddings shape: {p_emb.shape}")
            return True, p_emb, n_emb
        except Exception as e:
            logger.info(f"[COMPEL] Not available (using plain text): {e}")
            return False, prompt, neg_prompt

    def generate(self, params, callback=None):
        self._stop_flag = False
        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.pipe, params['sampler'], params['scheduler'])

        if 'vae_path' in params:
            self._apply_custom_vae(self.pipe, params['vae_path'])

        if 'loras' in params: self.apply_loras(params['loras'])
        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        preview_enabled = params.get('preview_enabled', False)
        preview_interval = params.get('preview_interval', 5)
        total_steps = params['steps']

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if self._stop_flag:
                raise RuntimeError("STOPPED")
            if callback:
                preview = None
                if preview_enabled and (step % preview_interval == 0 or step == total_steps - 1):
                    latents = callback_kwargs.get("latents")
                    if latents is not None:
                        with torch.no_grad():
                            image = pipe.vae.decode(latents / pipe.vae.config.scaling_factor, return_dict=False)[0]
                            image = (image / 2 + 0.5).clamp(0, 1)
                            image = image.cpu().permute(0, 2, 3, 1).float().numpy()
                        from PIL import Image as PILImage
                        preview = PILImage.fromarray((image[0] * 255).astype('uint8'))
                callback(step + 1, preview)
            return callback_kwargs

        logger.info(f"[SYSTEM] Generating image (txt2img), seed: {seed}")
        use_emb, p_data, n_data = self._encode_prompt(params['prompt'], params['neg_prompt'])
        gen_kwargs = dict(
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            width=params['width'],
            height=params['height'],
            generator=generator,
            callback_on_step_end=progress_callback
        )
        if use_emb:
            gen_kwargs['prompt_embeds'] = p_data
            gen_kwargs['negative_prompt_embeds'] = n_data
        else:
            gen_kwargs['prompt'] = params['prompt']
            gen_kwargs['negative_prompt'] = params['neg_prompt']
        try:
            image = self.pipe(**gen_kwargs).images[0]
        except RuntimeError as e:
            if "STOPPED" in str(e):
                self._clear_vram()
                raise
            raise

        filename = f"gen_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_txt2img'), filename)

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

    def img2img(self, params, callback=None):
        self._stop_flag = False
        pipe = StableDiffusionImg2ImgPipeline(**self.pipe.components)
        self._apply_performance_settings(pipe)

        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(pipe, params['sampler'], params['scheduler'])

        if 'vae_path' in params:
            self._apply_custom_vae(pipe, params['vae_path'])

        seed = params.get('seed', -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        preview_enabled = params.get('preview_enabled', False)
        preview_interval = params.get('preview_interval', 5)
        total_steps = params['steps']

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if self._stop_flag:
                raise RuntimeError("STOPPED")
            if callback:
                preview = None
                if preview_enabled and (step % preview_interval == 0 or step == total_steps - 1):
                    latents = callback_kwargs.get("latents")
                    if latents is not None:
                        with torch.no_grad():
                            image = pipe.vae.decode(latents / pipe.vae.config.scaling_factor, return_dict=False)[0]
                            image = (image / 2 + 0.5).clamp(0, 1)
                            image = image.cpu().permute(0, 2, 3, 1).float().numpy()
                        from PIL import Image as PILImage
                        preview = PILImage.fromarray((image[0] * 255).astype('uint8'))
                callback(step + 1, preview)
            return callback_kwargs

        logger.info(f"[SYSTEM] Generating image (img2img), seed: {seed}")
        use_emb, p_data, n_data = self._encode_prompt(params['prompt'], params['neg_prompt'])
        pipe_kwargs = dict(
            image=params['image'],
            strength=params.get('strength', 0.75),
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            generator=generator,
            callback_on_step_end=progress_callback
        )
        if use_emb:
            pipe_kwargs['prompt_embeds'] = p_data
            pipe_kwargs['negative_prompt_embeds'] = n_data
        else:
            pipe_kwargs['prompt'] = params['prompt']
            pipe_kwargs['negative_prompt'] = params['neg_prompt']
        try:
            result = pipe(**pipe_kwargs).images[0]
        except RuntimeError as e:
            if "STOPPED" in str(e):
                self._clear_vram()
                raise
            raise

        filename = f"img2img_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_txt2img'), filename)

        metadata = PngInfo()
        metadata_dict = {
            "prompt": params['prompt'],
            "neg_prompt": params['neg_prompt'],
            "steps": params['steps'],
            "cfg": params['cfg'],
            "strength": params.get('strength', 0.75),
            "seed": seed,
            "sampler": params.get('sampler', 'DPM++ 2M'),
            "scheduler": params.get('scheduler', 'Normal')
        }
        metadata.add_text("sd_params", json.dumps(metadata_dict))
        result.save(file_path, pnginfo=metadata)
        self._maybe_auto_clear()
        return file_path, seed

    def inpaint(self, params, callback=None):
        self._stop_flag = False
        self._clear_vram()
        if params.get('inpaint_model') == "original":
            self.load_inpaint_model("original")

        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.inpaint_pipe, params['sampler'], params['scheduler'])

        if 'vae_path' in params:
            self._apply_custom_vae(self.inpaint_pipe, params['vae_path'])

        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if self._stop_flag:
                raise RuntimeError("STOPPED")
            if callback: callback(step + 1)
            return callback_kwargs

        mask_img = params['mask']
        orig_img = params['image']
        logger.info(f"[DEBUG INPAINT] Mode: {orig_img.mode}/{mask_img.mode}, Size: {orig_img.size}, Strength: {params.get('strength')}, Steps: {params.get('steps')}, Seed: {seed}")
        w = orig_img.width - orig_img.width % 8
        h = orig_img.height - orig_img.height % 8

        use_emb, p_data, n_data = self._encode_prompt(params['prompt'], params['neg_prompt'])
        pipe_kwargs = dict(
            image=orig_img,
            mask_image=mask_img,
            width=w,
            height=h,
            num_inference_steps=params['steps'],
            guidance_scale=params['cfg'],
            strength=params.get('strength', 0.75),
            generator=generator,
            callback_on_step_end=progress_callback
        )
        if use_emb:
            pipe_kwargs['prompt_embeds'] = p_data
            pipe_kwargs['negative_prompt_embeds'] = n_data
        else:
            pipe_kwargs['prompt'] = params['prompt']
            pipe_kwargs['negative_prompt'] = params['neg_prompt']
        try:
            image = self.inpaint_pipe(**pipe_kwargs).images[0]
        except RuntimeError as e:
            if "STOPPED" in str(e):
                self._clear_vram()
                raise
            raise

        filename = f"inpaint_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_inpaint'), filename)
        image.save(file_path)
        self._maybe_auto_clear()
        return file_path, seed

    def controlnet_generate(self, params, callback=None):
        self._stop_flag = False
        self._clear_vram()
        self.load_controlnet_model(params['cn_model'])

        if 'sampler' in params and 'scheduler' in params:
            self._set_scheduler(self.controlnet_pipe, params['sampler'], params['scheduler'])

        if 'vae_path' in params:
            self._apply_custom_vae(self.controlnet_pipe, params['vae_path'])

        image_np = np.array(params['image'])
        image_canny = cv2.Canny(image_np, 100, 200)
        image_canny = image_canny[:, :, None]
        image_canny = np.concatenate([image_canny, image_canny, image_canny], axis=2)
        canny_image = Image.fromarray(image_canny)

        seed = params.get('seed', -1)
        if seed == -1: seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)

        def progress_callback(pipe, step, timestep, callback_kwargs):
            if self._stop_flag:
                raise RuntimeError("STOPPED")
            if callback: callback(step + 1)
            return callback_kwargs

        logger.info(f"[SYSTEM] Starting ControlNet generation, seed: {seed}")
        use_emb, p_data, n_data = self._encode_prompt(params['prompt'], params['neg_prompt'])
        cn_kwargs = dict(
            image=canny_image,
            num_inference_steps=params.get('steps', 25),
            guidance_scale=params.get('cfg', 7.5),
            controlnet_conditioning_scale=params.get('strength', 1.0),
            generator=generator,
            callback_on_step_end=progress_callback
        )
        if use_emb:
            cn_kwargs['prompt_embeds'] = p_data
            cn_kwargs['negative_prompt_embeds'] = n_data
        else:
            cn_kwargs['prompt'] = params['prompt']
            cn_kwargs['negative_prompt'] = params['neg_prompt']
        try:
            image = self.controlnet_pipe(**cn_kwargs).images[0]
        except RuntimeError as e:
            if "STOPPED" in str(e):
                self._clear_vram()
                raise
            raise

        filename = f"cn_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(settings.get('Paths', 'output_controlnet'), filename)
        image.save(file_path)
        self._maybe_auto_clear()
        return file_path, seed


    def apply_adetailer(self, params, callback=None):
        image = params['image']
        model_path = params['model_path']
        prompt = params['prompt']
        neg_prompt = params['neg_prompt']
        strength = params['denoise']
        dilation = params['dilation']
        threshold = params['conf']

        if YOLO is None or not self.pipe:
            logger.error("[ADETAILER] YOLO or SD pipeline not initialized")
            return None

        self._stop_flag = False
        logger.info(f"[ADETAILER] Starting detection: {model_path}")
        try:
            yolo_model = YOLO(model_path)
            results = yolo_model(image, conf=threshold)

            img_np = np.array(image)
            mask_np = np.zeros(img_np.shape[:2], dtype=np.uint8)

            faces_found = 0
            for result in results:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(mask_np, (x1, y1), (x2, y2), 255, -1)
                    faces_found += 1

            del yolo_model

            if faces_found == 0:
                logger.info("[ADETAILER] No face detected. Skipping.")
                return image

            if dilation > 0:
                kernel = np.ones((dilation, dilation), np.uint8)
                mask_np = cv2.dilate(mask_np, kernel, iterations=1)

            mask_pil = Image.fromarray(mask_np).convert("L")

            logger.info(f"[ADETAILER] Starting Inpainting ({faces_found} faces)")
            inpaint_pipe = StableDiffusionInpaintPipeline(**self.pipe.components)
            self._apply_performance_settings(inpaint_pipe)

            def progress_wrap(pipe, step, timestep, callback_kwargs):
                if self._stop_flag:
                    raise RuntimeError("STOPPED")
                if callback: callback(step + 1)
                return callback_kwargs

            w = image.width - image.width % 8
            h = image.height - image.height % 8
            use_emb, p_data, n_data = self._encode_prompt(prompt, neg_prompt)
            ad_kwargs = dict(
                image=image,
                mask_image=mask_pil,
                width=w,
                height=h,
                num_inference_steps=30,
                guidance_scale=7.5,
                strength=strength,
                generator=torch.Generator(device="cuda").manual_seed(random.randint(0, 2**32-1)),
                callback_on_step_end=progress_wrap
            )
            if use_emb:
                ad_kwargs['prompt_embeds'] = p_data
                ad_kwargs['negative_prompt_embeds'] = n_data
            else:
                ad_kwargs['prompt'] = prompt
                ad_kwargs['negative_prompt'] = neg_prompt
            try:
                result_img = inpaint_pipe(**ad_kwargs).images[0]
            except RuntimeError as e:
                if "STOPPED" in str(e):
                    raise
                raise

            filename = f"adet_{uuid.uuid4().hex[:8]}.png"
            out_path = os.path.join(settings.get('Paths', 'output_txt2img'), filename)
            result_img.save(out_path)

            return out_path

        except Exception as e:
            if "STOPPED" in str(e):
                logger.info("[ADETAILER] Generation stopped by user")
                return None
            logger.error(f"[ADETAILER] Critical error: {e}")
            return None
        finally:
            if 'inpaint_pipe' in locals(): del inpaint_pipe
            self._clear_vram()

    def upscale_image(self, image_path, upscaler_model_path, keep_in_vram=False):
        if not upscaler_model_path or not os.path.exists(upscaler_model_path) or ModelLoader is None:
            return None

        if self.upscaler_path != upscaler_model_path:
            if self.upscaler_model: del self.upscaler_model; self._clear_vram()
            logger.info(f"[SYSTEM] Loading upscaler: {upscaler_model_path}")
            loader = ModelLoader()
            model = loader.load_from_file(upscaler_model_path)
            self.upscaler_model = model.to("cuda").eval()
            self.upscaler_path = upscaler_model_path

        img = Image.open(image_path).convert("RGB")
        img_np = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0).to("cuda")

        logger.info(f"[SYSTEM] Upscaling image: {image_path}")
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

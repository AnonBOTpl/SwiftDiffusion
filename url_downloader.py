import re
import os
import time
import requests
from config import settings

def log(msg):
    print(f"[SwiftDiffusion] {msg}")

# ── URL parsing ─────────────────────────────────────────────
def parse_url(url):
    """Parse URL and return info dict or None."""
    url = url.strip()

    # CivitAI download URL (direct)
    m = re.search(r'civitai\.com/api/download/models/(\d+)', url)
    if m:
        return {"source": "civitai", "type": "direct_download", "version_id": m.group(1)}

    # CivitAI model page (with optional versionId)
    m = re.search(r'civitai\.com/models/(\d+)', url)
    if m:
        result = {"source": "civitai", "type": "model_page", "model_id": m.group(1)}
        vm = re.search(r'[?&]modelVersionId=(\d+)', url)
        if vm:
            result["version_id"] = vm.group(1)
        return result

    # HuggingFace direct file
    m = re.search(r'huggingface\.co/([^/]+/[^/]+)/resolve/([^/]+)/(.+)', url)
    if m:
        return {"source": "huggingface", "type": "direct_file",
                "repo_id": m.group(1), "revision": m.group(2), "filename": m.group(3)}

    # HuggingFace repo
    m = re.search(r'huggingface\.co/([^/]+/[^/?#]+)', url)
    if m:
        return {"source": "huggingface", "type": "repo", "repo_id": m.group(1)}

    # Direct .safetensors URL
    if url.lower().endswith('.safetensors') and url.startswith('http'):
        return {"source": "direct", "type": "direct_url", "url": url}

    return None

# ── Fetch metadata ──────────────────────────────────────────
def _api_headers(source, token=None, api_key=None):
    h = {"User-Agent": "SwiftDiffusion/1.0", "Accept": "application/json"}
    if source == "civitai" and api_key:
        h["Authorization"] = f"Bearer {api_key}"
    if source == "huggingface" and token:
        h["Authorization"] = f"Bearer {token}"
    return h

def fetch_model_info(parsed):
    """Fetch metadata for a parsed URL. Returns dict or None."""
    try:
        if parsed["source"] == "civitai":
            return _fetch_civitai(parsed)
        elif parsed["source"] == "huggingface":
            return _fetch_hf(parsed)
        elif parsed["source"] == "direct":
            return _fetch_direct(parsed)
    except Exception as e:
        log(f"fetch_model_info error: {e}")
    return None

def _fetch_civitai(parsed):
    api_key = settings.get('Integration', 'civitai_api_key')
    h = _api_headers("civitai", api_key=api_key)

    if parsed["type"] == "direct_download":
        vid = parsed["version_id"]
        # Check version info via API
        resp = requests.get(f"https://civitai.com/api/v1/model-versions/{vid}", headers=h, timeout=15)
        if resp.status_code == 200:
            v = resp.json()
            model_name = v.get("model", {}).get("name", "") if v.get("model") else ""
            return {
                "name": model_name or f"Model #{parsed.get('model_id', vid)}",
                "author": v.get("model", {}).get("creator", {}).get("username", "") if v.get("model") else "",
                "source": "civitai",
                "model_type": v.get("model", {}).get("type", "Checkpoint"),
                "architecture": v.get("baseModel", "Unknown"),
                "description": "",
                "thumbnail": (v.get("images") or [{}])[0].get("url", "") if v.get("images") else "",
                "files": [{"name": f.get("name", f"model.safetensors"), "size": f.get("sizeKB", 0),
                           "url": f.get("downloadUrl", f"https://civitai.com/api/download/models/{vid}"),
                           "version_name": v.get("name", "")} for f in (v.get("files") or [])],
                "category": _auto_category(v.get("model", {}).get("type", "")),
            }
        return None

    model_id = parsed["model_id"]
    resp = requests.get(f"https://civitai.com/api/v1/models/{model_id}", headers=h, timeout=15)
    if resp.status_code != 200:
        log(f"CivitAI API error: {resp.status_code}")
        return None
    data = resp.json()

    model_type = data.get("type", "Checkpoint")
    versions = data.get("modelVersions", [])
    all_files = []
    for v in versions:
        # Filter to only the version if specified
        if "version_id" in parsed and str(v.get("id")) != parsed["version_id"]:
            continue
        for f in v.get("files", []):
            all_files.append({
                "name": f.get("name", "model.safetensors"),
                "size": f.get("sizeKB", 0),
                "url": f.get("downloadUrl", ""),
                "version_id": str(v.get("id", "")),
                "version_name": v.get("name", ""),
                "architecture": v.get("baseModel", "Unknown"),
            })

    if not all_files:
        return None

    # Architecture from first version
    arch = (versions[0] if versions else {}).get("baseModel", "Unknown")

    return {
        "name": data.get("name", f"Model #{model_id}"),
        "author": data.get("creator", {}).get("username", ""),
        "source": "civitai",
        "model_type": model_type,
        "architecture": arch,
        "description": (data.get("description") or "")[:300],
        "thumbnail": (versions[0].get("images") or [{}])[0].get("url", "") if versions else "",
        "files": all_files,
        "category": _auto_category(model_type),
    }

def _fetch_hf(parsed):
    token = settings.get('Integration', 'hf_token')
    h = _api_headers("huggingface", token=token)
    api_url = "https://huggingface.co/api/models"

    if parsed["type"] == "direct_file":
        repo_id = parsed["repo_id"]
        filename = parsed["filename"]
        resp = requests.get(f"{api_url}/{repo_id}", headers=h, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        tags = data.get("tags", [])
        return {
            "name": repo_id.split("/")[-1],
            "author": repo_id.split("/")[0],
            "source": "huggingface",
            "model_type": data.get("pipeline_tag", "Checkpoint"),
            "architecture": _detect_arch_hf(tags, data.get("pipeline_tag", "")),
            "description": "",
            "thumbnail": f"https://huggingface.co/{repo_id}/resolve/main/preview.png",
            "files": [{"name": filename, "size": 0, "url": f"https://huggingface.co/{repo_id}/resolve/main/{filename}",
                       "version_id": "", "version_name": "", "architecture": ""}],
            "category": _auto_category(data.get("pipeline_tag", ""), filename),
        }

    # Repo
    repo_id = parsed["repo_id"]
    resp = requests.get(f"{api_url}/{repo_id}", headers=h, timeout=15)
    if resp.status_code != 200:
        log(f"HF API error: {resp.status_code}")
        return None
    data = resp.json()
    siblings = data.get("siblings", [])
    safetensors = [s["rfilename"] for s in siblings if s["rfilename"].endswith(".safetensors")]
    if not safetensors:
        return None

    tags = data.get("tags", [])
    pt = data.get("pipeline_tag", "")
    arch = _detect_arch_hf(tags, pt)

    files = [{
        "name": fn,
        "size": 0,
        "url": f"https://huggingface.co/{repo_id}/resolve/main/{fn}",
        "version_id": "", "version_name": "", "architecture": arch,
    } for fn in safetensors]

    return {
        "name": repo_id.split("/")[-1],
        "author": repo_id.split("/")[0],
        "source": "huggingface",
        "model_type": pt or "Checkpoint",
        "architecture": arch,
        "description": data.get("pipeline_tag", ""),
        "thumbnail": f"https://huggingface.co/{repo_id}/resolve/main/preview.png",
        "files": files,
        "category": _auto_category(pt, ""),
    }

def _fetch_direct(parsed):
    return {
        "name": parsed["url"].split("/")[-1],
        "author": "",
        "source": "direct",
        "model_type": "Checkpoint",
        "architecture": "Unknown",
        "description": "",
        "thumbnail": "",
        "files": [{"name": parsed["url"].split("/")[-1], "size": 0, "url": parsed["url"],
                   "version_id": "", "version_name": "", "architecture": "Unknown"}],
        "category": _auto_category("", parsed["url"]),
    }

# ── Helpers ─────────────────────────────────────────────────
def _detect_arch_hf(tags, pipeline_tag):
    tags_lower = set(t.lower() for t in (tags or []) if isinstance(t, str))
    pt = (pipeline_tag or "").lower()
    if "flux" in tags_lower or "flux" in pt: return "Flux"
    if "sdxl" in tags_lower or "sdxl" in pt: return "SDXL"
    if "pony" in tags_lower or "pony" in pt: return "Pony"
    if "illustrious" in tags_lower: return "Illustrious"
    if "playground" in tags_lower: return "Playground"
    if "sd3" in tags_lower or "stable-diffusion-3" in pt: return "SD3"
    if "qwen" in tags_lower or "qwen" in pt: return "SDXL"  # treat as non-SD1.5
    if "pixart" in tags_lower or "pixart" in pt: return "PixArt"
    return "SD 1.5"

def _auto_category(model_type_or_tags, filename=""):
    mt = model_type_or_tags.upper()
    fn = filename.lower()
    if "LORA" in mt: return "models_lora"
    if "CONTROLNET" in mt: return "models_controlnet"
    if "VAE" in mt: return "models_vae"
    if "UPSCAL" in mt: return "models_upscalers"
    if "lora" in fn: return "models_lora"
    if "control" in fn or "_cn_" in fn: return "models_controlnet"
    if "vae" in fn: return "models_vae"
    if "upscal" in fn: return "models_upscalers"
    return "models_sd"

# ── Download ────────────────────────────────────────────────
def download_model(file_info, dest_dir, on_progress=None):
    """Download a single file. file_info has: name, url, version_id, source.
    on_progress(pct, msg) called during download."""
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, file_info["name"])

    token = settings.get('Integration', 'hf_token')
    api_key = settings.get('Integration', 'civitai_api_key')

    url = file_info["url"]
    if not url:
        return None

    h = {"User-Agent": "SwiftDiffusion/1.0"}
    if api_key and "civitai" in url:
        h["Authorization"] = f"Bearer {api_key}"
        if "?" in url: url += "&"
        else: url += "?"
        url += f"type=Model&format=SafeTensor&token={api_key}"
    if token and "huggingface" in url:
        h["Authorization"] = f"Bearer {token}"

    log(f"Download: {url}")
    if on_progress:
        on_progress(0, "Łączenie...")

    try:
        resp = requests.get(url, headers=h, stream=True, timeout=60)
    except Exception as e:
        log(f"Download connection error: {e}")
        if on_progress:
            on_progress(0, f"Błąd: {e}")
        return None

    if resp.status_code != 200:
        log(f"Download HTTP {resp.status_code}: {resp.text[:200]}")
        if on_progress:
            on_progress(0, f"Błąd HTTP {resp.status_code}")
        return None

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    last_emit = 0
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if total and now - last_emit > 0.15 and on_progress:
                    pct = int(downloaded / total * 100)
                    on_progress(pct, f"Pobieranie... {pct}% ({downloaded//1048576}MB / {total//1048576}MB)")
                    last_emit = now

    log(f"Download complete: {dest}")
    if on_progress:
        on_progress(100, "Gotowe!")
    return dest

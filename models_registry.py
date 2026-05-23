import requests
from config import settings

SEARCH_SOURCES = {}
SOURCE_PAGES = {}

def register_source(name, func):
    SEARCH_SOURCES[name] = func
    SOURCE_PAGES[name] = {"cursor": None, "has_more": True}

def search_source(src_name, query, token=None, api_key=None, model_type=None, cursor=None):
    """Search a single source. Returns (results, next_cursor_or_none)."""
    search_fn = SEARCH_SOURCES.get(src_name)
    if not search_fn:
        return [], None
    try:
        if src_name == "CivitAI":
            results, next_cursor = search_fn(query, api_key=api_key, limit=20, cursor=cursor, model_type=model_type)
        else:
            results = search_fn(query, token=token, limit=20, model_type=model_type)
            next_cursor = None
        for r in results:
            r["_source_label"] = src_name
        return results, next_cursor
    except Exception as e:
        print(f"[SwiftDiffusion] Search error in {src_name}: {e}")
        return [], None

def search_more(src_name, query, token=None, api_key=None, model_type=None):
    """Fetch next page for a source using stored cursor."""
    cursor = SOURCE_PAGES[src_name].get("cursor")
    results, next_cursor = search_source(src_name, query, token, api_key, model_type, cursor)
    has_more = next_cursor is not None
    SOURCE_PAGES[src_name]["cursor"] = next_cursor
    SOURCE_PAGES[src_name]["has_more"] = has_more
    return results, has_more

def reset_page(src_name):
    if src_name in SOURCE_PAGES:
        SOURCE_PAGES[src_name] = {"cursor": None, "has_more": True}

def reset_pages():
    for name in SOURCE_PAGES:
        reset_page(name)

def _detect_architecture_hf(tags_list, pipeline_tag):
    tags_lower = set(t.lower() for t in (tags_list or []) if isinstance(t, str))
    pt = (pipeline_tag or "").lower()
    if "flux" in tags_lower or "flux" in pt:
        return "Flux"
    if "sdxl" in tags_lower or "sdxl" in pt or "text-to-image-sdxl" in pt:
        return "SDXL"
    if "pony" in tags_lower or "pony" in pt:
        return "Pony"
    if "illustrious" in tags_lower:
        return "Illustrious"
    if "playground" in tags_lower:
        return "Playground"
    if "sd3" in tags_lower or "stable-diffusion-3" in pt:
        return "SD3"
    return "SD 1.5"

TYPE_MAP_HF = {
    "Checkpoint": "text-to-image",
    "LoRA": "lora",
    "ControlNet": "controlnet",
    "VAE": "vae",
    "Upscaler": "image-upscaling",
}

# ── HuggingFace search ──────────────────────────────────────
def search_hf(query, token=None, limit=20, model_type=None):
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        kwargs = dict(search=query, sort="downloads", direction=-1, limit=limit)
        if model_type and model_type != "All":
            kwargs["filter"] = TYPE_MAP_HF.get(model_type, "text-to-image")
        models = list(api.list_models(**kwargs))
        results = []
        for m in models:
            tags = getattr(m, "tags", []) or []
            arch = _detect_architecture_hf(tags, getattr(m, "pipeline_tag", ""))
            siblings = getattr(m, "siblings", []) or []
            safetensors = [s.rfilename for s in siblings if s.rfilename.endswith(".safetensors")]
            results.append({
                "name": m.modelId.split("/")[-1],
                "repo_id": m.modelId,
                "filename": safetensors[0] if safetensors else "",
                "thumb": f"https://huggingface.co/{m.modelId}/resolve/main/preview.png",
                "desc": getattr(m, "pipeline_tag", ""),
                "author": m.modelId.split("/")[0] if "/" in m.modelId else "",
                "stars": str(getattr(m, "likes", 0)),
                "downloads": str(getattr(m, "downloads", 0)),
                "last_updated": str(getattr(m, "lastModified", ""))[:10],
                "model_type": getattr(m, "pipeline_tag", "text-to-image"),
                "tags": ", ".join(tags[:5]),
                "architecture": arch,
                "category": "models_sd",
                "source": "huggingface"
            })
        return results
    except Exception as e:
        print(f"[SwiftDiffusion] HfApi error: {e}")
        return _search_hf_fallback(query, token, limit, model_type)

def _search_hf_fallback(query, token=None, limit=20, model_type=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        params = {"search": query, "sort": "downloads", "direction": -1, "limit": limit}
        if model_type and model_type != "All":
            params["task"] = TYPE_MAP_HF.get(model_type, "text-to-image")
        resp = requests.get("https://huggingface.co/api/models", params=params, headers=headers, timeout=30)
        if resp.status_code != 200:
            return []
        results = []
        for m in resp.json():
            raw_tags = m.get("tags", m.get("pipeline_tags", [])) or []
            tags_list = raw_tags if isinstance(raw_tags, list) else [str(raw_tags)]
            tags_str = ", ".join(tags_list[:5])
            modelId = m.get("modelId", "")
            arch = _detect_architecture_hf(tags_list, m.get("pipeline_tag", ""))
            results.append({
                "name": modelId.split("/")[-1], "repo_id": modelId, "filename": "",
                "thumb": f"https://huggingface.co/{modelId}/resolve/main/preview.png",
                "desc": m.get("pipeline_tag", ""),
                "author": modelId.split("/")[0] if "/" in modelId else "",
                "stars": str(m.get("likes", 0)), "downloads": str(m.get("downloads", 0)),
                "last_updated": (m.get("lastModified") or "")[:10],
                "model_type": m.get("pipeline_tag", "text-to-image"),
                "tags": tags_str, "architecture": arch, "category": "models_sd", "source": "huggingface"
            })
        return results
    except Exception:
        return []

# ── CivitAI search (cursor-based pagination) ────────────────
CIVITAI_TYPE_MAP = {
    "Checkpoint": "Checkpoint", "LoRA": "LORA",
    "ControlNet": "Controlnet", "VAE": "VAE", "Upscaler": "Upscaler",
}

def search_civitai(query, api_key=None, limit=20, cursor=None, model_type=None):
    headers = {"User-Agent": "SwiftDiffusion/1.0", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        params = {"query": query, "limit": limit, "sort": "Highest Rated"}
        if cursor:
            params["cursor"] = cursor
        if model_type and model_type != "All":
            params["types"] = CIVITAI_TYPE_MAP.get(model_type, model_type)
        resp = requests.get("https://civitai.com/api/v1/models", params=params, headers=headers, timeout=30)
        print(f"[SwiftDiffusion] CivitAI search: status={resp.status_code}, cursor={'yes' if cursor else 'no'}")
        if resp.status_code != 200:
            print(f"[SwiftDiffusion] CivitAI error: {resp.text[:200]}")
            return [], None
        data = resp.json()
        next_cursor = data.get("metadata", {}).get("nextCursor")
        results = []
        for m in data.get("items", []):
            mv = m.get("modelVersions", [{}])[0]
            img_url = (mv.get("images", []) or [{}])[0].get("url", "") if mv.get("images") else ""
            model_type_val = m.get("type", "Checkpoint")
            mt = model_type_val.upper()
            cat = "models_sd"
            if "LORA" in mt: cat = "models_lora"
            elif "CONTROLNET" in mt: cat = "models_controlnet"
            elif "VAE" in mt: cat = "models_vae"
            elif "UPSCAL" in mt: cat = "models_upscalers"
            stats = m.get("stats", {})
            results.append({
                "name": m.get("name", ""), "repo_id": str(m.get("id", "")),
                "version_id": str(mv.get("id", "")), "filename": "", "thumb": img_url,
                "desc": (m.get("description") or "")[:120],
                "author": m.get("creator", {}).get("username", ""),
                "stars": str(stats.get("ratingCount", 0)),
                "downloads": str(stats.get("downloadCount", 0)),
                "last_updated": (m.get("lastUpdatedAt") or "")[:10],
                "model_type": model_type_val, "tags": "",
                "architecture": mv.get("baseModel", "Unknown"),
                "category": cat, "source": "civitai"
            })
        print(f"[SwiftDiffusion] CivitAI returned {len(results)} items, next_cursor={'yes' if next_cursor else 'no'}")
        return results, next_cursor
    except Exception as e:
        print(f"[SwiftDiffusion] CivitAI search exception: {e}")
        return [], None

register_source("HuggingFace", search_hf)
register_source("CivitAI", search_civitai)

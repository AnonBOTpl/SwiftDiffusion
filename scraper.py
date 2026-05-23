import re
import requests
from config import settings

def log(msg):
    print(f"[SwiftDiffusion] {msg}")

def search_ddg_model(query, limit=20):
    """Search for model links (DDG, fallback to APIs). Experimental."""
    results = []
    seen_urls = set()

    # Method 1: DuckDuckGo (Bing) — may find obscure models
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(f"{query} model", max_results=limit * 5):
                url = r.get("href", "") if isinstance(r, dict) else getattr(r, "href", "")
                title = r.get("title", "") if isinstance(r, dict) else getattr(r, "title", "")
                if not url or not title:
                    continue
                if "civitai.com/models/" in url:
                    mid = re.search(r"civitai\.com/models/(\d+)", url)
                    clean_url = f"https://civitai.com/models/{mid.group(1)}" if mid else url
                elif re.match(r"https?://huggingface\.co/[^/]+/[^/]+/?$", url):
                    clean_url = url.split("?")[0].rstrip("/")
                else:
                    continue
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    source = "civitai" if "civitai" in clean_url else "huggingface"
                    results.append({"title": title, "url": clean_url, "source": source})
        log(f"DDGS: {len(results)} results")
    except ImportError:
        log("duckduckgo_search not installed, skipping DDG")

    # Method 2: Fallback to API search (always works)
    if len(results) < limit:
        try:
            from models_registry import search_source
            token = settings.get('Integration', 'hf_token')
            api_key = settings.get('Integration', 'civitai_api_key')
            for src in ["CivitAI", "HuggingFace"]:
                api_results, _ = search_source(src, query, token, api_key, None)
                for r in api_results:
                    if src == "CivitAI":
                        url = f"https://civitai.com/models/{r['repo_id']}"
                        title = r.get("name", "")
                    else:
                        url = f"https://huggingface.co/{r['repo_id']}"
                        title = r.get("name", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        results.append({"title": title, "url": url, "source": src.lower()})
            log(f"API fallback: added {len(results)} total results")
        except Exception as e:
            log(f"API fallback error: {e}")

    return results[:limit]

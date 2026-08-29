"""Resolve image-block prompts to real URLs (Unsplash, with picsum fallback)."""

from __future__ import annotations

import hashlib
from urllib.parse import quote_plus

import httpx

from app.config import Settings, get_settings
from app.course_schemas import ContentBlock, ImageBlock


async def resolve_image_url(prompt: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    query = prompt.strip() or "education"
    key = settings.unsplash_access_key
    if key is not None and key.get_secret_value().strip():
        url = await _unsplash_search(query, access_key=key.get_secret_value())
        if url:
            return url
    seed = hashlib.sha256(query.encode()).hexdigest()[:16]
    return f"https://picsum.photos/seed/{seed}/960/540"


async def _unsplash_search(query: str, *, access_key: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {access_key}"},
            )
            if response.status_code != 200:
                return None
            results = response.json().get("results") or []
            if not results:
                return None
            urls = results[0].get("urls") or {}
            return urls.get("regular") or urls.get("small")
    except Exception:
        return None


async def resolve_image_blocks(
    blocks: list[ContentBlock],
    *,
    settings: Settings | None = None,
) -> list[ContentBlock]:
    settings = settings or get_settings()
    resolved: list[ContentBlock] = []
    for block in blocks:
        if isinstance(block, ImageBlock):
            url = block.url.strip() if block.url else ""
            if not url:
                url = await resolve_image_url(block.prompt, settings=settings)
            resolved.append(block.model_copy(update={"url": url}))
        else:
            resolved.append(block)
    return resolved


def unsplash_source_url(prompt: str) -> str:
    # ponytail: unused helper kept for demos without API key docs
    return f"https://source.unsplash.com/960x540/?{quote_plus(prompt.strip() or 'learning')}"

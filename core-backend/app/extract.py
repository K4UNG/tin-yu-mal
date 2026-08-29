"""Best-effort text extraction so uploads can be fed into LLM prompts."""

from __future__ import annotations

import io


def extract_text(data: bytes, *, filename: str, content_type: str) -> str | None:
    name = filename.lower()
    ctype = (content_type or "").lower()

    if ctype.startswith("text/") or name.endswith((".txt", ".md", ".markdown", ".csv", ".json")):
        return _decode_text(data)

    if ctype == "application/json" or name.endswith(".json"):
        return _decode_text(data)

    if ctype == "application/pdf" or name.endswith(".pdf"):
        return _extract_pdf(data)

    # images / binaries: no OCR in MVP
    return None


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts) if parts else None


def build_llm_context(
    files: list[tuple[str, str | None]],
    *,
    max_chars: int,
) -> str:
    """files: list of (filename, extracted_text)."""
    if not files:
        return ""
    chunks: list[str] = []
    used = 0
    for filename, text in files:
        if not text or not text.strip():
            chunks.append(f"[File: {filename} — no extractable text]")
            continue
        header = f"[File: {filename}]\n"
        body = text.strip()
        remaining = max_chars - used - len(header)
        if remaining <= 0:
            chunks.append(f"[File: {filename} — truncated, context budget exhausted]")
            break
        if len(body) > remaining:
            body = body[:remaining] + "\n…[truncated]"
        chunks.append(header + body)
        used += len(header) + len(body)
    return "\n\n".join(chunks)

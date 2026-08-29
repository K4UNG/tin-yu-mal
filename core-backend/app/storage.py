from __future__ import annotations

import io
from functools import lru_cache
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from app.config import Settings, get_settings


@lru_cache
def get_minio_client() -> Minio:
    # ponytail: no Settings arg — pydantic models aren't hashable for lru_cache
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key.get_secret_value(),
        secure=settings.minio_secure,
    )


def ensure_bucket(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def put_bytes(
    *,
    data: bytes,
    filename: str,
    content_type: str,
    settings: Settings | None = None,
) -> str:
    """Upload bytes to MinIO; returns object key."""
    settings = settings or get_settings()
    client = get_minio_client()
    ensure_bucket(settings)
    key = f"uploads/{uuid4()}/{filename}"
    client.put_object(
        settings.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type or "application/octet-stream",
    )
    return key


def get_bytes(object_key: str, settings: Settings | None = None) -> bytes:
    settings = settings or get_settings()
    client = get_minio_client()
    try:
        response = client.get_object(settings.minio_bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        raise FileNotFoundError(object_key) from exc

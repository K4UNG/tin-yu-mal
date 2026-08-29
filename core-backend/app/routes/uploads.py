from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Body
from litestar.status_codes import HTTP_201_CREATED
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.course_schemas import UploadedFileRead
from app.extract import extract_text
from app.models import UploadedFile
from app.storage import put_bytes


class UploadsController(Controller):
    path = "/uploads"
    tags = ["Uploads"]

    @post("/", status_code=HTTP_201_CREATED)
    async def upload_file(
        self,
        file: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        db_session: AsyncSession,
    ) -> UploadedFileRead:
        settings = get_settings()
        raw = await file.read()
        if not raw:
            raise ClientException(detail="Empty file")
        if len(raw) > settings.upload_max_bytes:
            raise ClientException(
                detail=f"File exceeds max size of {settings.upload_max_bytes} bytes"
            )

        filename = file.filename or "upload.bin"
        content_type = file.content_type or "application/octet-stream"
        object_key = await asyncio.to_thread(
            put_bytes,
            data=raw,
            filename=filename,
            content_type=content_type,
            settings=settings,
        )
        text = await asyncio.to_thread(
            extract_text,
            raw,
            filename=filename,
            content_type=content_type,
        )

        row = UploadedFile(
            object_key=object_key,
            filename=filename,
            content_type=content_type,
            size_bytes=len(raw),
            extracted_text=text,
        )
        db_session.add(row)
        await db_session.flush()
        await db_session.refresh(row)
        return UploadedFileRead(
            id=row.id,
            filename=row.filename,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
            has_text=bool(row.extracted_text and row.extracted_text.strip()),
            created_at=row.created_at,
        )

    @get("/{file_id:uuid}")
    async def get_upload(self, file_id: UUID, db_session: AsyncSession) -> UploadedFileRead:
        result = await db_session.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundException(detail="Upload not found")
        return UploadedFileRead(
            id=row.id,
            filename=row.filename,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
            has_text=bool(row.extracted_text and row.extracted_text.strip()),
            created_at=row.created_at,
        )

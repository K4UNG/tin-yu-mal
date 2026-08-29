from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ComplexityLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PrimaryLanguage(str, enum.Enum):
    ENGLISH = "en"
    BURMESE = "my"


class ChapterStatus(str, enum.Enum):
    NOT_GENERATED = "not_generated"
    GENERATING = "generating"
    READY = "ready"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(500))
    level: Mapped[ComplexityLevel] = mapped_column(Enum(ComplexityLevel, name="complexity_level", native_enum=False))
    language: Mapped[PrimaryLanguage] = mapped_column(
        Enum(PrimaryLanguage, name="primary_language", native_enum=False)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Chapter.index",
        lazy="selectin",
    )
    files: Mapped[list[UploadedFile]] = relationship(
        back_populates="course",
        lazy="selectin",
    )


class Chapter(Base):
    """ChapterSummary + optional full content (blocks filled on generate)."""

    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"))
    index: Mapped[int] = mapped_column(Integer)  # 0-based per SPECS
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[ChapterStatus] = mapped_column(
        Enum(ChapterStatus, name="chapter_status", native_enum=False),
        default=ChapterStatus.NOT_GENERATED,
    )
    # Full chapter body — null until POST .../generate
    blocks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    edit_history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    course: Mapped[Course] = relationship(back_populates="chapters")


class UploadedFile(Base):
    """User-uploaded material stored in MinIO and optionally linked to a course."""

    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(255), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
    )

    course: Mapped[Course | None] = relationship(back_populates="files")

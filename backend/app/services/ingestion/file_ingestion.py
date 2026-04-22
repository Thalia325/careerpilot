from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ocr.providers import BaseOCRProvider, OCRError, is_reusable_ocr_result
from app.integrations.storage.providers import BaseStorageProvider
from app.models import Certificate, Resume, Student, Transcript, UploadedFile

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class FileIngestionService:
    def __init__(self, storage_provider: BaseStorageProvider, ocr_provider: BaseOCRProvider) -> None:
        self.storage_provider = storage_provider
        self.ocr_provider = ocr_provider

    def _cached_ocr_result(self, uploaded: UploadedFile, document_type: str) -> dict | None:
        meta = uploaded.meta_json or {}
        ocr = meta.get("ocr")
        ocr_meta = meta.get("ocr_meta")
        if not isinstance(ocr, dict) or not isinstance(ocr_meta, dict):
            return None
        provider_name = getattr(self.ocr_provider, "provider_name", self.ocr_provider.__class__.__name__.lower())
        if ocr_meta.get("provider") != provider_name:
            return None
        if ocr_meta.get("document_type") != document_type:
            return None
        return ocr if is_reusable_ocr_result(ocr) else None

    def _cached_ocr_is_recent(self, uploaded: UploadedFile, ttl_seconds: int | None) -> bool:
        if not ttl_seconds or ttl_seconds <= 0:
            return False
        meta = uploaded.meta_json or {}
        ocr_meta = meta.get("ocr_meta")
        if not isinstance(ocr_meta, dict):
            return False
        parsed_at = _parse_datetime(ocr_meta.get("parsed_at"))
        if not parsed_at:
            return False
        return datetime.now(timezone.utc) - parsed_at <= timedelta(seconds=ttl_seconds)

    async def upload_file(
        self,
        db: Session,
        owner_id: int,
        file_type: str,
        file_name: str,
        content: bytes,
        content_type: str,
    ) -> UploadedFile:
        stored = await self.storage_provider.save_file(file_name, content, content_type)
        uploaded = UploadedFile(
            owner_id=owner_id,
            file_type=file_type,
            file_name=file_name,
            content_type=stored["content_type"],
            storage_key=stored["storage_key"],
            url=stored["url"],
            meta_json={},
        )
        db.add(uploaded)
        db.flush()
        student = db.scalar(select(Student).where(Student.user_id == owner_id))
        sid = student.id if student else None
        if sid and file_type == "resume":
            db.add(Resume(student_id=sid, file_id=uploaded.id, parsed_json={}))
        elif sid and file_type == "transcript":
            db.add(Transcript(student_id=sid, file_id=uploaded.id, parsed_json={}, gpa=None))
        elif sid and file_type == "certificate":
            db.add(Certificate(student_id=sid, file_id=uploaded.id, name=file_name, issuer="", level="", parsed_json={}))
        db.commit()
        db.refresh(uploaded)
        return uploaded

    async def parse_uploaded_file(
        self,
        db: Session,
        uploaded_file_id: int,
        document_type: str,
        *,
        force_refresh: bool = False,
        recent_cache_ttl_seconds: int | None = None,
    ) -> dict:
        uploaded = db.get(UploadedFile, uploaded_file_id)
        if not uploaded:
            raise ValueError("上传文件不存在")
        cached_result = self._cached_ocr_result(uploaded, document_type)
        if cached_result and not force_refresh:
            logger.info("Reusing cached OCR result: file_id=%s document_type=%s", uploaded_file_id, document_type)
            return cached_result
        if cached_result and force_refresh and self._cached_ocr_is_recent(uploaded, recent_cache_ttl_seconds):
            logger.info(
                "Skipping OCR refresh for recent cached result: file_id=%s document_type=%s ttl=%ss",
                uploaded_file_id,
                document_type,
                recent_cache_ttl_seconds,
            )
            return cached_result
        try:
            content = await self.storage_provider.read_file(uploaded.storage_key)
            result = await self.ocr_provider.parse_document(uploaded.file_name, content, document_type=document_type)
            meta = dict(uploaded.meta_json or {})
            meta["ocr"] = result
            meta["ocr_meta"] = {
                "provider": getattr(self.ocr_provider, "provider_name", self.ocr_provider.__class__.__name__.lower()),
                "document_type": document_type,
                "parsed_at": _utc_now_iso(),
                "storage_key": uploaded.storage_key,
            }
            uploaded.meta_json = meta
            if document_type == "resume":
                resume = db.scalar(select(Resume).where(Resume.file_id == uploaded.id))
                if resume:
                    resume.parsed_json = result["structured_json"]
            elif document_type == "transcript":
                transcript = db.scalar(select(Transcript).where(Transcript.file_id == uploaded.id))
                if transcript:
                    transcript.parsed_json = result["structured_json"]
                    transcript.gpa = result["structured_json"].get("gpa")
            elif document_type == "certificate":
                certificate = db.scalar(select(Certificate).where(Certificate.file_id == uploaded.id))
                if certificate:
                    certificate.parsed_json = result["structured_json"]
                    certificate.name = result["structured_json"].get("certificates", [uploaded.file_name])[0]
            db.commit()
            return result
        except OCRError as e:
            if cached_result and e.retryable:
                logger.warning(
                    "OCR refresh failed, falling back to cached OCR: file_id=%s document_type=%s err=%s",
                    uploaded_file_id,
                    document_type,
                    e,
                )
                return cached_result
            raise
        except ValueError as e:
            logger.error(f"ValueError while parsing file {uploaded_file_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse uploaded file {uploaded_file_id} with type {document_type}: {str(e)}")
            raise ValueError(f"Failed to parse document: {str(e)}") from e

    def list_files(self, db: Session, owner_id: int) -> list[UploadedFile]:
        rows = db.scalars(
            select(UploadedFile)
            .where(UploadedFile.owner_id == owner_id)
            .order_by(UploadedFile.created_at.desc())
        ).all()
        return list(rows)

    async def clear_files(self, db: Session, owner_id: int) -> int:
        files = self.list_files(db, owner_id)
        count = 0
        for f in files:
            try:
                await self.delete_file(db, file_id=f.id, owner_id=owner_id)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete file {f.id}: {e}")
        return count

    async def delete_file(self, db: Session, file_id: int, owner_id: int) -> None:
        uploaded = db.get(UploadedFile, file_id)
        if not uploaded:
            raise ValueError("文件不存在")
        if uploaded.owner_id != owner_id:
            raise ValueError("无权删除此文件")
        resume = db.scalar(select(Resume).where(Resume.file_id == file_id))
        if resume:
            db.delete(resume)
        transcript = db.scalar(select(Transcript).where(Transcript.file_id == file_id))
        if transcript:
            db.delete(transcript)
        certificate = db.scalar(select(Certificate).where(Certificate.file_id == file_id))
        if certificate:
            db.delete(certificate)
        try:
            await self.storage_provider.delete_file(uploaded.storage_key)
        except Exception as e:
            logger.warning(f"Failed to delete physical file {uploaded.storage_key}: {e}")
        db.delete(uploaded)
        db.commit()

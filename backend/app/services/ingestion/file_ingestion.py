from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ocr.providers import BaseOCRProvider
from app.integrations.storage.providers import BaseStorageProvider
from app.models import Certificate, Resume, Student, Transcript, UploadedFile

logger = logging.getLogger(__name__)


class FileIngestionService:
    def __init__(self, storage_provider: BaseStorageProvider, ocr_provider: BaseOCRProvider) -> None:
        self.storage_provider = storage_provider
        self.ocr_provider = ocr_provider

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
        student = db.get(Student, owner_id)
        if student and file_type == "resume":
            db.add(Resume(student_id=owner_id, file_id=uploaded.id, parsed_json={}))
        elif student and file_type == "transcript":
            db.add(Transcript(student_id=owner_id, file_id=uploaded.id, parsed_json={}, gpa=None))
        elif student and file_type == "certificate":
            db.add(Certificate(student_id=owner_id, file_id=uploaded.id, name=file_name, issuer="", level="", parsed_json={}))
        db.commit()
        db.refresh(uploaded)
        return uploaded

    async def parse_uploaded_file(self, db: Session, uploaded_file_id: int, document_type: str) -> dict:
        uploaded = db.get(UploadedFile, uploaded_file_id)
        if not uploaded:
            raise ValueError("上传文件不存在")
        try:
            content = await self.storage_provider.read_file(uploaded.storage_key)
            result = await self.ocr_provider.parse_document(uploaded.file_name, content, document_type=document_type)
            uploaded.meta_json = {"ocr": result}
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
        except ValueError as e:
            logger.error(f"ValueError while parsing file {uploaded_file_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse uploaded file {uploaded_file_id} with type {document_type}: {str(e)}")
            raise ValueError(f"Failed to parse document: {str(e)}") from e


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.profile import OCRParseRequest, OCRParseResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/parse", response_model=OCRParseResponse)
async def parse_document(
    payload: OCRParseRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> OCRParseResponse:
    if payload.uploaded_file_id:
        result = await container.file_service.parse_uploaded_file(db, payload.uploaded_file_id, payload.document_type)
    elif payload.raw_text:
        result = await container.file_service.ocr_provider.parse_document(
            file_name="manual_input.txt",
            content_bytes=payload.raw_text.encode("utf-8"),
            document_type=payload.document_type,
            raw_text=payload.raw_text,
        )
    else:
        raise HTTPException(status_code=400, detail="请提供 uploaded_file_id 或 raw_text")
    return OCRParseResponse(**result)


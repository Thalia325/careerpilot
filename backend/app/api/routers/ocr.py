from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.integrations.ocr.providers import OCRParseError, OCRServiceError, OCRNetworkError
from app.models import Resume, UploadedFile, User
from app.schemas.common import APIResponse
from app.schemas.profile import OCRParseRequest, OCRParseResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()

# Map OCR error types to HTTP status codes
_OCR_ERROR_STATUS: dict[type, int] = {
    OCRParseError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    OCRServiceError: status.HTTP_502_BAD_GATEWAY,
    OCRNetworkError: status.HTTP_504_GATEWAY_TIMEOUT,
}


@router.post("/parse", response_model=OCRParseResponse)
async def parse_document(
    payload: OCRParseRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> OCRParseResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    try:
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请提供 uploaded_file_id 或 raw_text")
        return OCRParseResponse(**result)
    except (OCRParseError, OCRServiceError, OCRNetworkError) as e:
        http_status = _OCR_ERROR_STATUS.get(type(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=http_status,
            detail=e.to_dict(),
        ) from e


@router.get("/result/{file_id}", response_model=APIResponse)
async def get_parse_result(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Get the persisted parse result for a specific uploaded file."""
    uploaded = db.get(UploadedFile, file_id)
    if not uploaded:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    if uploaded.owner_id != current_user.id and current_user.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此文件")
    if uploaded.file_type != "resume":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该文件不是简历类型")

    resume = db.scalar(select(Resume).where(Resume.file_id == file_id))
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到简历解析结果")
    if not resume.parsed_json:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该简历尚未解析")

    return APIResponse(data={
        "file_id": file_id,
        "resume_id": resume.id,
        "parsed_json": resume.parsed_json,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
    })


@router.get("/results", response_model=APIResponse)
async def list_parse_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """List all parse results for the current user's resume files."""
    file_rows = db.scalars(
        select(UploadedFile)
        .where(UploadedFile.owner_id == current_user.id, UploadedFile.file_type == "resume")
        .order_by(UploadedFile.created_at.desc())
    ).all()

    results = []
    for f in file_rows:
        resume = db.scalar(select(Resume).where(Resume.file_id == f.id))
        results.append({
            "file_id": f.id,
            "file_name": f.file_name,
            "resume_id": resume.id if resume else None,
            "parsed_json": resume.parsed_json if resume else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })
    return APIResponse(data=results)


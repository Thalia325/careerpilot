import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import User
from app.schemas.common import APIResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()

# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png"}


def get_safe_filename(filename: str) -> str:
    """Generate a safe filename using UUID to prevent path traversal attacks."""
    if not filename:
        raise ValueError("Filename cannot be empty")
    # Extract extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension {ext} not allowed")
    # Generate safe filename with UUID
    safe_name = f"{uuid.uuid4()}{ext}"
    return safe_name


@router.post("/upload", response_model=APIResponse)
async def upload_file(
    owner_id: int = Form(...),
    file_type: str = Form(...),
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """Upload a file with validation."""
    # Verify user owns the resource
    if current_user.id != owner_id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权上传文件")

    # Validate filename
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")

    try:
        safe_filename = get_safe_filename(upload.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Read and validate file size
    content = await upload.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小不能超过 {MAX_FILE_SIZE / (1024*1024):.0f}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件不能为空")

    # Validate content type matches extension
    ext = Path(upload.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}. 支持的类型: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    uploaded = await container.file_service.upload_file(
        db,
        owner_id=owner_id,
        file_type=file_type,
        file_name=safe_filename,
        content=content,
        content_type=upload.content_type or "application/octet-stream",
    )
    return APIResponse(data={"id": uploaded.id, "file_name": uploaded.file_name, "url": uploaded.url})


import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.core.errors import raise_resource_forbidden
from app.models import User
from app.schemas.common import APIResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
VALID_FILE_TYPES = {"resume", "certificate", "transcript", "other"}


def get_safe_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Filename cannot be empty")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension {ext} not allowed")
    safe_name = f"{uuid.uuid4()}{ext}"
    return safe_name


@router.get("/", response_model=APIResponse)
async def list_files(
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    files = container.file_service.list_files(db, owner_id=current_user.id)
    return APIResponse(data=[
        {
            "id": f.id,
            "file_name": f.file_name,
            "file_type": f.file_type,
            "content_type": f.content_type,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ])


@router.post("/upload", response_model=APIResponse)
async def upload_file(
    owner_id: int = Form(...),
    file_type: str = Form(...),
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.id != owner_id and current_user.role != "admin":
        raise_resource_forbidden()

    if file_type not in VALID_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型标签: {file_type}. 支持的类型: {', '.join(sorted(VALID_FILE_TYPES))}",
        )

    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件名不能为空")

    try:
        safe_filename = get_safe_filename(upload.filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    content = await upload.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小不能超过 {MAX_FILE_SIZE / (1024*1024):.0f}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件不能为空")

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
    return APIResponse(data={
        "id": uploaded.id,
        "file_name": uploaded.file_name,
        "file_type": uploaded.file_type,
        "created_at": uploaded.created_at.isoformat() if uploaded.created_at else None,
        "url": uploaded.url,
    })


@router.delete("/clear", response_model=APIResponse)
async def clear_files(
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    count = await container.file_service.clear_files(db, owner_id=current_user.id)
    return APIResponse(message=f"已删除 {count} 个文件")


@router.delete("/{file_id}", response_model=APIResponse)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    try:
        await container.file_service.delete_file(db, file_id=file_id, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return APIResponse(message="文件已删除")


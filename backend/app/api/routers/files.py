from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.common import APIResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/upload", response_model=APIResponse)
async def upload_file(
    owner_id: int = Form(...),
    file_type: str = Form(...),
    upload: UploadFile = File(...),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    uploaded = await container.file_service.upload_file(
        db,
        owner_id=owner_id,
        file_type=file_type,
        file_name=upload.filename,
        content=await upload.read(),
        content_type=upload.content_type or "application/octet-stream",
    )
    return APIResponse(data={"id": uploaded.id, "file_name": uploaded.file_name, "url": uploaded.url})


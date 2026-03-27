from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_db_session
from app.schemas.profile import StudentProfileGenerateRequest, StudentProfileOut
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/generate", response_model=StudentProfileOut)
async def generate_student_profile(
    payload: StudentProfileGenerateRequest,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    result = await container.student_profile_service.generate_profile(
        db,
        student_id=payload.student_id,
        uploaded_file_ids=payload.uploaded_file_ids,
        manual_input=payload.manual_input,
    )
    return StudentProfileOut(**result)


@router.get("/{student_id}", response_model=StudentProfileOut)
def get_student_profile(
    student_id: int,
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    result = container.student_profile_service.get_profile(db, student_id)
    if not result:
        raise HTTPException(status_code=404, detail="学生画像不存在")
    return StudentProfileOut(**result)


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import ProfileVersion, User
from app.schemas.profile import StudentProfileGenerateRequest, StudentProfileOut
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/generate", response_model=StudentProfileOut)
async def generate_student_profile(
    payload: StudentProfileGenerateRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

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
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    result = container.student_profile_service.get_profile(db, student_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生画像不存在")
    return StudentProfileOut(**result)


@router.get("/{student_id}/versions")
def get_profile_versions(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    versions = list(db.scalars(
        select(ProfileVersion)
        .where(ProfileVersion.student_id == student_id)
        .order_by(ProfileVersion.version_no.desc())
        .limit(20)
    ).all())

    return {
        "items": [
            {
                "id": v.id,
                "version_no": v.version_no,
                "source_files": v.source_files,
                "snapshot": v.snapshot_json,
                "created_at": v.created_at.isoformat() if v.created_at else "",
            }
            for v in versions
        ]
    }


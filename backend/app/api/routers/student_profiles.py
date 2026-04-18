from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ensure_student_owns_resource, get_container, get_current_user, get_db_session
from app.core.errors import require_role
from app.models import ProfileVersion, User
from app.schemas.profile import StudentProfileGenerateRequest, StudentProfileOut, ProfileVersionOut
from app.services.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/generate", response_model=StudentProfileOut)
async def generate_student_profile(
    payload: StudentProfileGenerateRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    require_role(current_user.role, "student", "admin", "teacher")

    ensure_student_owns_resource(current_user, db, payload.student_id)

    try:
        result = await container.student_profile_service.generate_profile(
            db,
            student_id=payload.student_id,
            uploaded_file_ids=payload.uploaded_file_ids,
            manual_input=payload.manual_input,
            mode=payload.mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return StudentProfileOut(**result)


@router.get("/{student_id}", response_model=StudentProfileOut)
def get_student_profile(
    student_id: int,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> StudentProfileOut:
    require_role(current_user.role, "student", "admin", "teacher")

    ensure_student_owns_resource(current_user, db, student_id)

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
    require_role(current_user.role, "student", "admin", "teacher")

    ensure_student_owns_resource(current_user, db, student_id)

    versions = list(db.scalars(
        select(ProfileVersion)
        .where(ProfileVersion.student_id == student_id)
        .order_by(ProfileVersion.version_no.desc())
        .limit(20)
    ).all())

    return {
        "items": [
            _version_to_dict(v)
            for v in versions
        ]
    }


@router.get("/{student_id}/versions/{version_id}", response_model=ProfileVersionOut)
def get_profile_version_detail(
    student_id: int,
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> ProfileVersionOut:
    require_role(current_user.role, "student", "admin", "teacher")

    ensure_student_owns_resource(current_user, db, student_id)

    v = db.scalar(
        select(ProfileVersion)
        .where(ProfileVersion.id == version_id, ProfileVersion.student_id == student_id)
    )
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="画像版本不存在")
    return _version_to_out(v)


def _version_to_dict(v: ProfileVersion) -> dict:
    return {
        "id": v.id,
        "version_no": v.version_no,
        "uploaded_file_ids": v.uploaded_file_ids or [],
        "file_summaries": v.file_summaries_json or [],
        "source_files": v.source_files,
        "snapshot": v.snapshot_json,
        "evidence_snapshot": v.evidence_snapshot_json or [],
        "created_at": v.created_at.isoformat() if v.created_at else "",
    }


def _version_to_out(v: ProfileVersion) -> ProfileVersionOut:
    return ProfileVersionOut(**_version_to_dict(v))


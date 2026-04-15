from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.models import JobPosting, JobProfile, User
from app.schemas.common import APIResponse, Pagination
from app.schemas.job import JobImportRequest, JobProfileGenerationRequest
from app.services.bootstrap import ServiceContainer
from app.services.reference import find_best_template, load_sample_job_postings

router = APIRouter()


def _list_value(value: object) -> list:
    return value if isinstance(value, list) else []


def _job_explore_item(row: dict) -> dict:
    template = find_best_template(row.get("title", ""))
    title = row.get("title") or template.get("title") or "未命名岗位"
    description = row.get("description") or template.get("summary") or "暂无岗位说明。"
    skills = _list_value(template.get("skills"))
    certificates = _list_value(template.get("certificates"))
    capabilities = template.get("capabilities") if isinstance(template.get("capabilities"), dict) else {}
    explanations = template.get("explanations") if isinstance(template.get("explanations"), dict) else {}
    dimension_weights = template.get("dimension_weights") if isinstance(template.get("dimension_weights"), dict) else {}

    return {
        "job_code": row.get("job_code") or template.get("job_code") or title,
        "title": title,
        "category": row.get("industry") or "其他",
        "industry": row.get("industry") or "",
        "location": row.get("location") or "",
        "salary_range": row.get("salary_range") or "暂无参考薪资",
        "company_name": row.get("company_name") or "",
        "company_size": row.get("company_size") or "",
        "ownership_type": row.get("ownership_type") or "",
        "description": description,
        "summary": template.get("summary") or description,
        "company_intro": row.get("company_intro") or "",
        "skill_requirements": skills,
        "skills": skills,
        "certificate_requirements": certificates,
        "certificates": certificates,
        "capabilities": capabilities,
        "dimension_weights": dimension_weights,
        "explanations": explanations,
        "source": "sample_jobs.csv",
    }


def _db_job_explore_rows(db: Session) -> list[dict]:
    return [
        {
            "job_code": item.job_code,
            "title": item.title,
            "location": item.location,
            "salary_range": item.salary_range,
            "company_name": item.company_name,
            "industry": item.industry,
            "company_size": item.company_size,
            "ownership_type": item.ownership_type,
            "description": item.description,
            "company_intro": item.company_intro,
        }
        for item in db.scalars(select(JobPosting).order_by(JobPosting.industry, JobPosting.title)).all()
    ]


def _balanced_rows(rows: list[dict], limit: int) -> list[dict]:
    if not rows:
        return []
    categories = [category for category in dict.fromkeys(row.get("industry") or "其他" for row in rows)]
    per_category = max(1, limit // max(len(categories), 1))
    selected: list[dict] = []
    selected_codes: set[str] = set()

    for category in categories:
        taken = 0
        for row in rows:
            if (row.get("industry") or "其他") != category:
                continue
            code = row.get("job_code") or f"{row.get('title')}:{len(selected)}"
            if code in selected_codes:
                continue
            selected.append(row)
            selected_codes.add(code)
            taken += 1
            if taken >= per_category or len(selected) >= limit:
                break
        if len(selected) >= limit:
            return selected

    if len(selected) < limit:
        for row in rows:
            code = row.get("job_code") or f"{row.get('title')}:{len(selected)}"
            if code in selected_codes:
                continue
            selected.append(row)
            selected_codes.add(code)
            if len(selected) >= limit:
                break
    return selected


@router.post("/import", response_model=APIResponse)
async def import_jobs(
    payload: JobImportRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Only admin can import jobs
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以导入职位")

    imported = await container.job_import_service.import_rows(db, [row.model_dump() for row in payload.rows])
    return APIResponse(data={"count": len(imported), "job_codes": [item.job_code for item in imported]})


@router.get("", response_model=APIResponse)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    query = select(JobProfile).order_by(JobProfile.title)
    total = db.query(JobProfile).count()
    items = list(db.scalars(query.offset(skip).limit(limit)).all())
    return APIResponse(
        data={
            "items": [
                {
                    "job_code": item.job_code,
                    "title": item.title,
                    "skills": item.skill_requirements,
                    "weights": item.dimension_weights,
                }
                for item in items
            ],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total,
            },
        }
    )


@router.get("/explore", response_model=APIResponse)
def explore_jobs(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = Query(120, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    rows = load_sample_job_postings() or _db_job_explore_rows(db)
    if keyword:
        lowered_keyword = keyword.lower()
        rows = [
            row for row in rows
            if lowered_keyword in f"{row.get('title', '')} {row.get('industry', '')} {row.get('company_name', '')}".lower()
        ]
    if category and category != "全部":
        rows = [row for row in rows if (row.get("industry") or "其他") == category]
        rows = rows[:limit]
    else:
        rows = _balanced_rows(rows, limit)

    return APIResponse(data=[_job_explore_item(row) for row in rows])


@router.post("/profiles/generate", response_model=APIResponse)
async def generate_job_profiles(
    payload: JobProfileGenerationRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Only admin can generate profiles
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有管理员可以生成职位画像")

    job_codes = payload.job_codes or []
    profiles = await container.job_import_service.generate_profiles(db, job_codes or None)
    return APIResponse(data={"count": len(profiles), "job_codes": [item.job_code for item in profiles]})


@router.get("/profiles/templates", response_model=APIResponse)
def list_templates(
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
) -> APIResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    return APIResponse(data=container.job_import_service.search_templates(keyword))

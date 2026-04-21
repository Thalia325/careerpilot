from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.core.errors import require_role
from app.models import JobPosting, JobProfile, User
from app.schemas.common import APIResponse, Pagination
from app.schemas.job import JobImportRequest, JobProfileGenerationRequest
from app.services.bootstrap import ServiceContainer
from app.services.reference import find_best_template, load_job_postings_dataset

router = APIRouter()


def _list_value(value: object) -> list:
    return value if isinstance(value, list) else []


EXPLORE_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "前端开发",
        (
            "前端", "web前端", "web 前端", "react", "vue", "javascript", "typescript",
        ),
    ),
    (
        "Java开发",
        (
            "java", "spring",
        ),
    ),
    (
        "C/C++开发",
        (
            "c/c++", "c++", "c语言", "嵌入式软件",
        ),
    ),
    (
        "软件测试",
        (
            "软件测试", "测试工程师", "质量管理/测试", "质量保证", "功能测试", "自动化测试",
            "qa",
        ),
    ),
    (
        "硬件测试",
        (
            "硬件测试", "板卡测试", "电子测试",
        ),
    ),
    (
        "实施工程师",
        (
            "实施工程师", "实施顾问", "erp实施", "系统实施", "软件实施", "项目实施",
        ),
    ),
    (
        "技术支持",
        (
            "技术支持", "售后工程师", "客户支持", "服务工程师",
        ),
    ),
    (
        "运维工程师",
        (
            "运维", "devops", "sre", "系统运维",
        ),
    ),
    (
        "产品经理",
        (
            "产品经理", "产品专员", "产品助理", "需求分析", "业务分析",
        ),
    ),
    (
        "项目管理",
        (
            "项目经理", "项目主管", "项目专员", "项目助理", "项目管理", "项目招投标",
            "招投标专员",
        ),
    ),
    (
        "算法工程师",
        (
            "算法", "机器学习", "深度学习", "计算机视觉", "自然语言", "nlp", "cv",
        ),
    ),
    (
        "数据分析",
        (
            "数据分析", "数据挖掘", "bi", "数据统计", "数据运营",
        ),
    ),
    (
        "网络安全",
        (
            "网络安全", "信息安全", "安全工程师", "渗透", "安全运维",
        ),
    ),
    (
        "网络工程师",
        (
            "网络工程师", "网络维护", "传输网络", "通信工程师",
        ),
    ),
    (
        "硬件工程师",
        (
            "硬件工程师", "计算机硬件维护", "硬件维护", "嵌入式硬件",
        ),
    ),
    (
        "售前工程师",
        (
            "售前", "解决方案工程师", "方案工程师",
        ),
    ),
]


EXPLORE_CONTEXT_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    *EXPLORE_CATEGORY_RULES,
]


def _match_explore_category(blob: str, rules: list[tuple[str, tuple[str, ...]]]) -> str:
    lowered_blob = blob.lower()
    for category, keywords in rules:
        if any(keyword.lower() in lowered_blob for keyword in keywords):
            return category
    return ""


def _explore_category(row: dict, template: dict | None = None) -> str:
    title_category = _match_explore_category(str(row.get("title", "")), EXPLORE_CATEGORY_RULES)
    if title_category:
        return title_category

    text_parts = [
        row.get("industry", ""),
        row.get("description", ""),
    ]
    blob = " ".join(str(part) for part in text_parts if part).lower()
    return _match_explore_category(blob, EXPLORE_CONTEXT_CATEGORY_RULES) or "其他岗位"


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
        "category": _explore_category(row, template),
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
        "source": "job_dataset",
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
    categories = [category for category in dict.fromkeys(_explore_category(row) for row in rows)]
    per_category = max(1, limit // max(len(categories), 1))
    selected: list[dict] = []
    selected_codes: set[str] = set()

    for category in categories:
        taken = 0
        for row in rows:
            if _explore_category(row) != category:
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
    require_role(current_user.role, "admin")

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
    require_role(current_user.role, "student", "admin", "teacher")

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
    require_role(current_user.role, "student", "admin", "teacher")

    rows = load_job_postings_dataset() or _db_job_explore_rows(db)
    if keyword:
        lowered_keyword = keyword.lower()
        rows = [
            row for row in rows
            if lowered_keyword in f"{row.get('title', '')} {row.get('industry', '')} {row.get('company_name', '')}".lower()
        ]
    if category and category != "全部":
        rows = [row for row in rows if _explore_category(row) == category]
        rows = rows[:limit]
    else:
        rows = _balanced_rows(rows, limit)

    return APIResponse(data=[_job_explore_item(row) for row in rows])


@router.post("/knowledge-base/export", response_model=APIResponse)
def export_knowledge_base(
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    require_role(current_user.role, "admin")
    result = container.job_import_service.export_local_knowledge_base(db)
    return APIResponse(data=result)


@router.post("/profiles/generate", response_model=APIResponse)
async def generate_job_profiles(
    payload: JobProfileGenerationRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Only admin can generate profiles
    require_role(current_user.role, "admin")

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
    require_role(current_user.role, "student", "admin", "teacher")

    return APIResponse(data=container.job_import_service.search_templates(keyword))

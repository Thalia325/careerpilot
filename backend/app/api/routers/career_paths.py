from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.api.routers.students import resolve_target_job
from app.models import AnalysisRun, PathRecommendation, Student, User
from app.schemas.common import APIResponse
from app.services.bootstrap import ServiceContainer

router = APIRouter()


class PathPlanningRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field(default="", max_length=100)
    profile_version_id: int | None = None
    match_result_id: int | None = None
    analysis_run_id: int | None = None


@router.post("/plan", response_model=APIResponse)
async def plan_career_path(
    payload: PathPlanningRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    # Verify user has access
    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    job_code = payload.job_code
    if not job_code:
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
        if student:
            job_code, _ = resolve_target_job(db, student)
    if not job_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法确定目标岗位，请先选择或确认一个目标岗位")

    try:
        result = await container.career_path_service.plan_path(
            db,
            payload.student_id,
            job_code,
            profile_version_id=payload.profile_version_id,
            match_result_id=payload.match_result_id,
            analysis_run_id=payload.analysis_run_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Bidirectional binding: update AnalysisRun.path_recommendation_id
    path_id = result.get("path_recommendation_id")
    if payload.analysis_run_id and path_id:
        run = db.get(AnalysisRun, payload.analysis_run_id)
        if run and run.path_recommendation_id is None:
            run.path_recommendation_id = path_id
            db.commit()

    return APIResponse(data=result)


def _path_to_dict(path_result: PathRecommendation) -> dict[str, Any]:
    """Convert a PathRecommendation ORM object to a response dict."""
    vertical_graph = path_result.vertical_graph_json or {}
    transition_graph = path_result.transition_graph_json or {}

    # Backward compatibility: build minimal graph from text paths for old records
    if not vertical_graph and path_result.primary_path_json:
        vertical_graph = {
            "title": path_result.primary_path_json[0] if path_result.primary_path_json else "",
            "description": "历史记录（仅保留文本路径，重新生成可查看完整图谱）。",
            "nodes": [
                {"title": t, "level": i + 1, "description": "", "skills": []}
                for i, t in enumerate(path_result.primary_path_json)
            ],
            "edges": [],
            "promotion_paths": [path_result.primary_path_json],
            "vertical_paths": [],
        }
    if not transition_graph and path_result.alternate_paths_json:
        transition_graph = {
            "target": path_result.primary_path_json[0] if path_result.primary_path_json else "",
            "nodes": [],
            "edges": [],
            "role_paths": [
                {
                    "title": path[0] if path else "",
                    "description": "",
                    "skills": [],
                    "paths": [
                        {"steps": path, "relation": "换岗", "description": "", "skill_bridge": []}
                    ],
                }
                for path in (path_result.alternate_paths_json or [])[:5]
            ],
            "clusters": [],
        }

    return {
        "path_recommendation_id": path_result.id,
        "student_id": path_result.student_id,
        "target_job_code": path_result.target_job_code,
        "primary_path": path_result.primary_path_json or [],
        "alternate_paths": path_result.alternate_paths_json or [],
        "vertical_graph": vertical_graph,
        "transition_graph": transition_graph,
        "gaps": path_result.gaps_json or [],
        "recommendations": path_result.recommendations_json or [],
        "rationale": "基于岗位图谱的晋升链路和转岗链路，结合学生当前技能覆盖情况生成主路径与备选路径。",
        "current_ability": path_result.current_ability_json or {},
        "certificate_recommendations": path_result.certificate_recommendations_json or [],
        "learning_resources": path_result.learning_resources_json or [],
        "evaluation_metrics": path_result.evaluation_metrics_json or [],
        "profile_version_id": path_result.profile_version_id,
        "match_result_id": path_result.match_result_id,
        "analysis_run_id": path_result.analysis_run_id,
    }


@router.get("/{path_id}", response_model=APIResponse)
def get_path_result(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> APIResponse:
    """获取指定的路径规划历史记录"""
    path_result = db.scalar(
        select(PathRecommendation).where(PathRecommendation.id == path_id)
    )
    if not path_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="路径规划记录不存在")

    # 检查权限：只有学生本人、教师和管理员可以查看
    student = db.scalar(select(Student).where(Student.id == path_result.student_id))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="学生信息不存在")

    if current_user.role == "student" and student.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此记录")

    if current_user.role not in ["student", "admin", "teacher"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问")

    return APIResponse(data=_path_to_dict(path_result))

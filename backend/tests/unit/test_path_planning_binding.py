"""Tests for US-012: 持久化职业路径规划结果与上下文绑定."""
import pytest
from sqlalchemy import select

from app.models import AnalysisRun, MatchResult, PathRecommendation, ProfileVersion
from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


async def _setup(db_session):
    """Set up a student profile and return container."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="专注前端工程，有丰富的项目经验",
            skills=["JavaScript", "TypeScript", "React", "Next.js", "HTML", "CSS"],
            certificates=["英语四级", "计算机二级"],
            projects=["职业规划平台", "电商管理系统"],
            internships=["前端开发实习"],
        ),
    )
    return container


# --- AC1: Content fields ---


@pytest.mark.asyncio
async def test_result_contains_current_ability(db_session):
    """AC1: 路径规划结果包含当前能力起点"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "current_ability" in result
    ability = result["current_ability"]
    assert isinstance(ability, dict)
    assert "skills" in ability
    assert "certificates" in ability
    assert "projects" in ability
    assert "internships" in ability
    assert "matched_skills" in ability
    assert "missing_skills" in ability


@pytest.mark.asyncio
async def test_result_contains_primary_path(db_session):
    """AC1: 路径规划结果包含主路径"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "primary_path" in result
    assert isinstance(result["primary_path"], list)
    assert len(result["primary_path"]) > 0


@pytest.mark.asyncio
async def test_result_contains_alternate_paths(db_session):
    """AC1: 路径规划结果包含备选路径"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "alternate_paths" in result
    assert isinstance(result["alternate_paths"], list)


@pytest.mark.asyncio
async def test_result_contains_vertical_graph(db_session):
    """AC1: 路径规划结果包含晋升路径（vertical_graph）"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "vertical_graph" in result
    vg = result["vertical_graph"]
    assert isinstance(vg, dict)
    assert "nodes" in vg
    assert "edges" in vg
    assert "promotion_paths" in vg


@pytest.mark.asyncio
async def test_result_contains_transition_graph(db_session):
    """AC1: 路径规划结果包含转岗路径（transition_graph）"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "transition_graph" in result
    tg = result["transition_graph"]
    assert isinstance(tg, dict)
    assert "role_paths" in tg


@pytest.mark.asyncio
async def test_result_contains_gaps(db_session):
    """AC1: 路径规划结果包含技能差距"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "gaps" in result
    assert isinstance(result["gaps"], list)


@pytest.mark.asyncio
async def test_result_contains_certificate_recommendations(db_session):
    """AC1: 路径规划结果包含证书建议"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "certificate_recommendations" in result
    assert isinstance(result["certificate_recommendations"], list)
    for rec in result["certificate_recommendations"]:
        assert "name" in rec
        assert "priority" in rec
        assert "reason" in rec


@pytest.mark.asyncio
async def test_result_contains_learning_resources(db_session):
    """AC1: 路径规划结果包含学习资源建议"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "learning_resources" in result
    assert isinstance(result["learning_resources"], list)
    for resource in result["learning_resources"]:
        assert "type" in resource
        assert "name" in resource
        assert "suggestion" in resource
        assert "phase" in resource


@pytest.mark.asyncio
async def test_result_contains_recommendations(db_session):
    """AC1: 路径规划结果包含短中期计划"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "recommendations" in result
    assert isinstance(result["recommendations"], list)
    phases = [r["phase"] for r in result["recommendations"]]
    assert "短期" in phases
    assert "中期" in phases


@pytest.mark.asyncio
async def test_result_contains_evaluation_metrics(db_session):
    """AC1: 路径规划结果包含评估指标"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "evaluation_metrics" in result
    assert isinstance(result["evaluation_metrics"], list)
    for metric in result["evaluation_metrics"]:
        assert "phase" in metric
        assert "metric" in metric
        assert "target" in metric
        assert "evaluation_method" in metric


# --- AC2: Context binding ---


@pytest.mark.asyncio
async def test_path_bound_to_student(db_session):
    """AC2: 路径规划结果与学生绑定"""
    container = await _setup(db_session)
    await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec is not None
    assert path_rec.student_id == 1


@pytest.mark.asyncio
async def test_path_bound_to_target_job(db_session):
    """AC2: 路径规划结果与目标岗位绑定"""
    container = await _setup(db_session)
    await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec is not None
    assert path_rec.target_job_code == "J-FE-001"


@pytest.mark.asyncio
async def test_path_bound_to_profile_version(db_session):
    """AC2: 路径规划结果与画像版本绑定"""
    container = await _setup(db_session)

    pv = ProfileVersion(student_id=1, version_no=1, snapshot_json={"skills": ["React"]})
    db_session.add(pv)
    db_session.flush()

    result = await container.career_path_service.plan_path(
        db_session, 1, "J-FE-001",
        profile_version_id=pv.id,
    )

    assert result["profile_version_id"] == pv.id
    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.profile_version_id == pv.id


@pytest.mark.asyncio
async def test_path_bound_to_match_result(db_session):
    """AC2: 路径规划结果与匹配结果绑定"""
    container = await _setup(db_session)

    # Run matching first to create a match result
    match_result_data = container.matching_service.analyze_match(db_session, 1, "J-FE-001")
    match_id = match_result_data["match_result_id"]

    result = await container.career_path_service.plan_path(
        db_session, 1, "J-FE-001",
        match_result_id=match_id,
    )

    assert result["match_result_id"] == match_id
    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.match_result_id == match_id


@pytest.mark.asyncio
async def test_path_bound_to_analysis_run(db_session):
    """AC2: 路径规划结果与分析任务绑定"""
    container = await _setup(db_session)

    run = AnalysisRun(student_id=1, status="running", current_step="matched")
    db_session.add(run)
    db_session.flush()

    result = await container.career_path_service.plan_path(
        db_session, 1, "J-FE-001",
        analysis_run_id=run.id,
    )

    assert result["analysis_run_id"] == run.id
    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.analysis_run_id == run.id


# --- AC3: Direct usability for display and history ---


@pytest.mark.asyncio
async def test_result_has_path_recommendation_id(db_session):
    """AC3: 路径规划结果包含 path_recommendation_id，可供历史回放使用"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert "path_recommendation_id" in result
    assert isinstance(result["path_recommendation_id"], int)
    assert result["path_recommendation_id"] > 0


@pytest.mark.asyncio
async def test_result_directly_usable_for_display(db_session):
    """AC3: 返回结果包含完整字段，可直接供页面展示"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    required_keys = [
        "path_recommendation_id", "student_id", "target_job_code",
        "primary_path", "alternate_paths", "vertical_graph", "transition_graph",
        "gaps", "recommendations", "rationale",
        "current_ability", "certificate_recommendations",
        "learning_resources", "evaluation_metrics",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


# --- Persistence tests ---


@pytest.mark.asyncio
async def test_current_ability_persisted(db_session):
    """Verify current_ability is persisted in PathRecommendation"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.current_ability_json == result["current_ability"]


@pytest.mark.asyncio
async def test_certificate_recommendations_persisted(db_session):
    """Verify certificate_recommendations are persisted"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.certificate_recommendations_json == result["certificate_recommendations"]


@pytest.mark.asyncio
async def test_learning_resources_persisted(db_session):
    """Verify learning_resources are persisted"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.learning_resources_json == result["learning_resources"]


@pytest.mark.asyncio
async def test_evaluation_metrics_persisted(db_session):
    """Verify evaluation_metrics are persisted"""
    container = await _setup(db_session)
    result = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    path_rec = db_session.scalar(select(PathRecommendation).limit(1))
    assert path_rec.evaluation_metrics_json == result["evaluation_metrics"]


@pytest.mark.asyncio
async def test_upsert_updates_existing_record(db_session):
    """Verify upsert: second plan_path updates the same record"""
    container = await _setup(db_session)

    result1 = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")
    result2 = await container.career_path_service.plan_path(db_session, 1, "J-FE-001")

    assert result1["path_recommendation_id"] == result2["path_recommendation_id"]

    all_paths = db_session.scalars(
        select(PathRecommendation).where(PathRecommendation.student_id == 1)
    ).all()
    assert len(all_paths) == 1


# --- API integration tests ---


@pytest.mark.asyncio
async def test_api_plan_returns_all_fields(client):
    """POST /career-paths/plan returns all enriched and binding fields"""
    from app.db.session import SessionLocal
    from app.services.bootstrap import create_service_container, initialize_demo_data

    db = SessionLocal()
    try:
        container = create_service_container()
        await initialize_demo_data(db, container)
        await container.student_profile_service.generate_profile(
            db, student_id=1, uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="专注前端工程",
                skills=["JavaScript", "React"],
                certificates=["英语四级"],
                projects=["职业规划平台"],
                internships=["前端实习"],
            ),
        )
    finally:
        db.close()

    resp = client.post("/api/v1/career-paths/plan", json={
        "student_id": 1,
        "job_code": "J-FE-001",
    }, headers={"Authorization": "Bearer dev-bypass"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "current_ability" in data
    assert "certificate_recommendations" in data
    assert "learning_resources" in data
    assert "evaluation_metrics" in data
    assert "path_recommendation_id" in data
    assert "profile_version_id" in data
    assert "match_result_id" in data
    assert "analysis_run_id" in data


@pytest.mark.asyncio
async def test_api_get_returns_all_fields(client):
    """GET /career-paths/{path_id} returns all enriched and binding fields"""
    from app.db.session import SessionLocal
    from app.services.bootstrap import create_service_container, initialize_demo_data

    db = SessionLocal()
    try:
        container = create_service_container()
        await initialize_demo_data(db, container)
        await container.student_profile_service.generate_profile(
            db, student_id=1, uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="专注前端工程",
                skills=["JavaScript", "React"],
                certificates=["英语四级"],
                projects=["职业规划平台"],
                internships=["前端实习"],
            ),
        )
        # Plan to create a PathRecommendation
        await container.career_path_service.plan_path(db, 1, "J-FE-001")
        path_rec = db.scalar(select(PathRecommendation).limit(1))
        path_id = path_rec.id
    finally:
        db.close()

    resp = client.get(f"/api/v1/career-paths/{path_id}", headers={"Authorization": "Bearer dev-bypass"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "current_ability" in data
    assert "certificate_recommendations" in data
    assert "learning_resources" in data
    assert "evaluation_metrics" in data
    assert "path_recommendation_id" in data
    assert data["path_recommendation_id"] == path_id

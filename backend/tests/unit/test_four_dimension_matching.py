"""Tests for US-010: Four-dimension matching result data structure and binding."""
import pytest

from app.models import (
    AnalysisRun,
    MatchDimensionScore,
    MatchResult,
    ProfileVersion,
)
from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data
from sqlalchemy import select


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


@pytest.mark.asyncio
async def test_exactly_four_dimensions(db_session):
    """AC1: 匹配结果固定输出基础要求、职业技能、职业素养、发展潜力四个维度"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    assert len(result["dimensions"]) == 4
    dim_names = [d["dimension"] for d in result["dimensions"]]
    assert "基础要求" in dim_names
    assert "职业技能" in dim_names
    assert "职业素养" in dim_names
    assert "发展潜力" in dim_names


@pytest.mark.asyncio
async def test_dimension_has_score_weight_reasoning_evidence(db_session):
    """AC2: 每个维度包含得分、权重、解释和证据"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    for dim in result["dimensions"]:
        assert "dimension" in dim
        assert "score" in dim
        assert isinstance(dim["score"], (int, float))
        assert dim["score"] >= 0
        assert "weight" in dim
        assert isinstance(dim["weight"], (int, float))
        assert dim["weight"] >= 0
        assert "reasoning" in dim
        assert isinstance(dim["reasoning"], str)
        assert len(dim["reasoning"]) > 0
        assert "evidence" in dim
        assert isinstance(dim["evidence"], dict)


@pytest.mark.asyncio
async def test_result_has_total_score(db_session):
    """AC2: 匹配结果包含总分"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    assert "total_score" in result
    assert isinstance(result["total_score"], (int, float))
    assert result["total_score"] > 0


@pytest.mark.asyncio
async def test_result_has_strengths(db_session):
    """AC2: 匹配结果包含契合点"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    assert "strengths" in result
    assert isinstance(result["strengths"], list)
    # With matching skills provided, strengths should not be empty
    assert len(result["strengths"]) > 0


@pytest.mark.asyncio
async def test_result_has_gap_items(db_session):
    """AC2: 匹配结果包含差距项"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    assert "gap_items" in result
    assert isinstance(result["gap_items"], list)
    for gap in result["gap_items"]:
        assert "type" in gap
        assert "name" in gap
        assert "suggestion" in gap


@pytest.mark.asyncio
async def test_result_has_suggestions(db_session):
    """AC2: 匹配结果包含提升建议"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    assert "suggestions" in result
    assert isinstance(result["suggestions"], list)
    assert len(result["suggestions"]) > 0
    for suggestion in result["suggestions"]:
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0


@pytest.mark.asyncio
async def test_match_result_bound_to_student(db_session):
    """AC3: 匹配结果与学生绑定"""
    container = await _setup(db_session)
    container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.student_id == 1


@pytest.mark.asyncio
async def test_match_result_bound_to_target_job(db_session):
    """AC3: 匹配结果与目标岗位绑定"""
    container = await _setup(db_session)
    container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.target_job_code == "J-FE-001"


@pytest.mark.asyncio
async def test_match_result_bound_to_profile_version(db_session):
    """AC3: 匹配结果与画像版本绑定"""
    container = await _setup(db_session)

    # Create a profile version manually to bind
    pv = ProfileVersion(student_id=1, version_no=1, snapshot_json={"skills": ["React"]})
    db_session.add(pv)
    db_session.flush()

    container.matching_service.analyze_match(
        db_session, 1, "J-FE-001",
        profile_version_id=pv.id,
    )

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.profile_version_id == pv.id


@pytest.mark.asyncio
async def test_match_result_bound_to_analysis_run(db_session):
    """AC3: 匹配结果与分析任务绑定"""
    container = await _setup(db_session)

    # Create an analysis run
    run = AnalysisRun(student_id=1, status="running", current_step="matched")
    db_session.add(run)
    db_session.flush()

    container.matching_service.analyze_match(
        db_session, 1, "J-FE-001",
        analysis_run_id=run.id,
    )

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.analysis_run_id == run.id

    # Verify AnalysisRun.match_result_id is also updated
    db_session.refresh(run)
    assert run.match_result_id == match_result.id


@pytest.mark.asyncio
async def test_dimension_scores_persisted(db_session):
    """Verify dimension scores are stored in MatchDimensionScore table"""
    container = await _setup(db_session)
    container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None

    dim_scores = db_session.scalars(
        select(MatchDimensionScore).where(MatchDimensionScore.match_result_id == match_result.id)
    ).all()
    assert len(dim_scores) == 4

    dim_names = {d.dimension for d in dim_scores}
    assert dim_names == {"基础要求", "职业技能", "职业素养", "发展潜力"}


@pytest.mark.asyncio
async def test_match_result_stores_strengths(db_session):
    """Verify strengths/契合点 are persisted on MatchResult"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.strengths_json == result["strengths"]


@pytest.mark.asyncio
async def test_match_result_stores_gaps_and_suggestions(db_session):
    """Verify gap_items and suggestions are persisted on MatchResult"""
    container = await _setup(db_session)
    result = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    match_result = db_session.scalar(select(MatchResult).limit(1))
    assert match_result is not None
    assert match_result.gaps_json == result["gap_items"]
    assert match_result.suggestions_json == result["suggestions"]


@pytest.mark.asyncio
async def test_multiple_matches_isolated(db_session):
    """Verify matching results are isolated per student-profile + job-profile combination"""
    container = await _setup(db_session)

    result1 = container.matching_service.analyze_match(db_session, 1, "J-FE-001")

    all_matches = db_session.scalars(
        select(MatchResult).where(MatchResult.student_id == 1)
    ).all()
    assert len(all_matches) == 1
    assert all_matches[0].target_job_code == "J-FE-001"

    assert result1["student_id"] == 1
    assert result1["job_code"] == "J-FE-001"
    assert len(result1["dimensions"]) == 4

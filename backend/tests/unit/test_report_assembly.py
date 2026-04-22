"""Tests for US-014: Assemble complete career planning report."""
import pytest
from sqlalchemy import select

from app.models import AnalysisRun, CareerReport, MatchResult, ProfileVersion
from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


@pytest.mark.asyncio
async def test_report_contains_all_required_sections(db_session):
    """Report content must include all 11 required sections."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="希望成为前端工程师",
            skills=["JavaScript", "TypeScript", "React", "Next.js"],
            certificates=["英语四级"],
            projects=["CareerPilot"],
            internships=["前端开发实习"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    content = result["content"]

    required_sections = [
        "student_summary", "resume_summary", "capability_profile", "target_job_analysis",
        "matching_analysis", "gap_analysis", "career_path", "short_term_plan",
        "mid_term_plan", "evaluation_cycle", "teacher_comments",
    ]
    for section in required_sections:
        assert section in content, f"Missing section: {section}"


@pytest.mark.asyncio
async def test_report_student_summary_fields(db_session):
    """student_summary must contain name, major, grade, intent_job."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    summary = result["content"]["student_summary"]

    assert "name" in summary
    assert "major" in summary
    assert "grade" in summary
    assert "intent_job" in summary


@pytest.mark.asyncio
async def test_report_matching_analysis_has_score(db_session):
    """matching_analysis must contain total_score and dimensions."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    ma = result["content"]["matching_analysis"]

    assert "total_score" in ma
    assert isinstance(ma["total_score"], (int, float))
    assert "dimensions" in ma
    assert isinstance(ma["dimensions"], list)


@pytest.mark.asyncio
async def test_report_gap_analysis_fields(db_session):
    """gap_analysis must contain skill_gaps, certificate_gaps, suggestions."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    ga = result["content"]["gap_analysis"]

    assert "skill_gaps" in ga
    assert "certificate_gaps" in ga
    assert "suggestions" in ga


@pytest.mark.asyncio
async def test_report_career_path_fields(db_session):
    """career_path must contain primary_path, alternate_paths, rationale."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    cp = result["content"]["career_path"]

    assert "primary_path" in cp
    assert "alternate_paths" in cp
    assert "rationale" in cp


@pytest.mark.asyncio
async def test_report_evaluation_cycle_fields(db_session):
    """evaluation_cycle must contain cycle and metrics."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    ec = result["content"]["evaluation_cycle"]

    assert "cycle" in ec
    assert "metrics" in ec


@pytest.mark.asyncio
async def test_report_teacher_comments_section(db_session):
    """teacher_comments must exist with status field."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    tc = result["content"]["teacher_comments"]

    assert "status" in tc
    assert "comments" in tc


@pytest.mark.asyncio
async def test_report_markdown_contains_all_sections(db_session):
    """Markdown must contain all 11 section headers."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    md = result["markdown_content"]

    expected_headers = [
        "学生基本情况", "简历解析摘要", "能力画像", "目标岗位分析",
        "人岗匹配分析", "差距分析", "职业路径规划",
        "短期行动计划", "中期行动计划", "评估周期", "教师建议",
    ]
    for header in expected_headers:
        assert header in md, f"Missing markdown section: {header}"


@pytest.mark.asyncio
async def test_report_bound_to_context_ids(db_session):
    """Report must be bound to profile_version_id, match_result_id, analysis_run_id."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )

    # Create an analysis run
    run = AnalysisRun(student_id=1, status="running")
    db_session.add(run)
    db_session.flush()
    run_id = run.id

    result = await container.report_service.generate_report(
        db_session, 1, "J-FE-001", analysis_run_id=run_id,
    )

    assert result["analysis_run_id"] == run_id
    assert result["match_result_id"] is not None

    # Verify binding in DB
    report = db_session.get(CareerReport, result["report_id"])
    assert report.analysis_run_id == run_id
    assert report.match_result_id is not None


@pytest.mark.asyncio
async def test_report_auto_binds_latest_profile_version_and_generation_meta(db_session):
    """Report generation should bind the latest profile version even when not provided explicitly."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    profile = await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )

    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")

    assert result["profile_version_id"] == profile["profile_version_id"]
    report = db_session.get(CareerReport, result["report_id"])
    generation_meta = report.content_json["generation_meta"]
    assert generation_meta["llm_provider"] == "mock"
    assert generation_meta["ocr_provider"] == "mock"
    assert generation_meta["profile_version_id"] == profile["profile_version_id"]
    assert report.profile_version_id == profile["profile_version_id"]


@pytest.mark.asyncio
async def test_report_reads_snapshot_not_latest(db_session):
    """Report viewing should return the snapshot content, not re-assemble."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="原始画像",
            skills=["React"],
        ),
    )
    result1 = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    original_content = result1["content"]
    original_markdown = result1["markdown_content"]

    # Update the student profile — report should NOT change
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="更新后的画像",
            skills=["React", "Vue", "Angular"],
            certificates=["英语六级", "计算机二级"],
        ),
    )

    # Get report directly (snapshot read)
    report = container.report_service.get_report(db_session, result1["report_id"])
    assert report.content_json == original_content
    assert report.markdown_content == original_markdown


@pytest.mark.asyncio
async def test_report_analysis_run_backfill(db_session):
    """When only analysis_run_id is given, profile_version_id and match_result_id should be resolved from the run."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )

    # Create analysis run with profile_version_id
    pv = db_session.scalar(select(ProfileVersion).where(ProfileVersion.student_id == 1))
    run = AnalysisRun(student_id=1, status="running", profile_version_id=pv.id if pv else None)
    db_session.add(run)
    db_session.flush()
    run_id = run.id

    result = await container.report_service.generate_report(
        db_session, 1, "J-FE-001", analysis_run_id=run_id,
    )

    report = db_session.get(CareerReport, result["report_id"])
    assert report.analysis_run_id == run_id
    assert report.match_result_id is not None
    # Verify AnalysisRun.report_id is backfilled
    updated_run = db_session.get(AnalysisRun, run_id)
    assert updated_run.report_id == result["report_id"]


@pytest.mark.asyncio
async def test_report_completeness_with_new_sections(db_session):
    """Completeness check should verify all 11 new sections."""
    container = create_service_container()
    await initialize_demo_data(db_session, container)
    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="测试",
            skills=["React"],
        ),
    )
    result = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    completeness = container.report_service.check_completeness(db_session, result["report_id"])

    assert completeness["is_complete"] is True
    assert completeness["missing_sections"] == []

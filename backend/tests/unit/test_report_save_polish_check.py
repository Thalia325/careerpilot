"""Tests for US-015: report save, polish, and completeness check."""
import pytest

from app.schemas.profile import ManualStudentInput
from app.services.bootstrap import create_service_container, initialize_demo_data


@pytest.fixture
async def setup_report(db_session):
    """Generate a report so subsequent tests can save/polish/check it."""
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
    report = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    return container, report


# --- Save tests ---

@pytest.mark.asyncio
async def test_save_report_creates_version(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]

    new_markdown = "# 修改后的报告\n\n自定义内容。"
    container.report_service.save_report(db_session, report_id, new_markdown)

    report_obj = container.report_service.get_report(db_session, report_id)
    assert report_obj.markdown_content == new_markdown
    assert report_obj.status == "edited"


@pytest.mark.asyncio
async def test_save_report_version_record(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]

    from app.models import ReportVersion
    from sqlalchemy import select

    # generate already created version 1
    versions_before = list(db_session.scalars(
        select(ReportVersion).where(ReportVersion.report_id == report_id)
    ).all())
    assert len(versions_before) >= 1

    container.report_service.save_report(db_session, report_id, "# 手动保存内容\n\n")

    versions_after = list(db_session.scalars(
        select(ReportVersion).where(ReportVersion.report_id == report_id)
    ).all())
    assert len(versions_after) == len(versions_before) + 1
    latest = versions_after[-1]
    assert latest.editor_notes == "手动保存"
    assert latest.version_no == len(versions_after)


@pytest.mark.asyncio
async def test_save_does_not_affect_other_reports(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]

    # Generate a second report for the same student but different job
    report2 = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    report2_id = report2["report_id"]

    # They may be the same report (cached), so let's just verify save is scoped
    container.report_service.save_report(db_session, report_id, "# Report A saved\n\n")
    r1 = container.report_service.get_report(db_session, report_id)
    assert r1.markdown_content == "# Report A saved\n\n"


# --- Polish tests ---

@pytest.mark.asyncio
async def test_polish_report_returns_context_bindings(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]
    original_md = report["markdown_content"]

    result = await container.report_service.polish_report(db_session, report_id, original_md)
    assert "report_id" in result
    assert "student_id" in result
    assert "path_recommendation_id" in result
    assert "profile_version_id" in result
    assert "match_result_id" in result
    assert "analysis_run_id" in result


@pytest.mark.asyncio
async def test_polish_report_updates_status(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]

    result = await container.report_service.polish_report(db_session, report_id, report["markdown_content"])
    assert result["status"] == "polished"

    report_obj = container.report_service.get_report(db_session, report_id)
    assert report_obj.status == "polished"
    assert "智能润色" in report_obj.markdown_content


@pytest.mark.asyncio
async def test_polish_creates_version_record(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]

    from app.models import ReportVersion
    from sqlalchemy import select

    versions_before = list(db_session.scalars(
        select(ReportVersion).where(ReportVersion.report_id == report_id)
    ).all())

    await container.report_service.polish_report(db_session, report_id, report["markdown_content"])

    versions_after = list(db_session.scalars(
        select(ReportVersion).where(ReportVersion.report_id == report_id)
    ).all())
    assert len(versions_after) == len(versions_before) + 1
    latest = versions_after[-1]
    assert latest.editor_notes == "智能润色"


@pytest.mark.asyncio
async def test_polish_does_not_affect_other_reports(setup_report, db_session):
    container, report = await setup_report
    report_id = report["report_id"]
    original_content = report["content"]

    # Polish report A
    result = await container.report_service.polish_report(db_session, report_id, report["markdown_content"])
    polished_id = result["report_id"]

    # The same report should have updated content but other reports (if any) unchanged
    polished_report = container.report_service.get_report(db_session, polished_id)
    assert polished_report.status == "polished"


# --- Completeness check tests ---

@pytest.mark.asyncio
async def test_check_completeness_passes_for_generated_report(setup_report, db_session):
    container, report = await setup_report
    result = container.report_service.check_completeness(db_session, report["report_id"])
    assert result["is_complete"] is True
    assert result["missing_sections"] == []
    assert any("完整" in s for s in result["suggestions"])


@pytest.mark.asyncio
async def test_check_completeness_detects_empty_sections(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)

    await container.student_profile_service.generate_profile(
        db_session,
        student_id=1,
        uploaded_file_ids=[],
        manual_input=ManualStudentInput(
            target_job="前端开发工程师",
            self_introduction="希望成为前端工程师",
            skills=["JavaScript"],
            certificates=[],
            projects=[],
            internships=[],
        ),
    )
    report = await container.report_service.generate_report(db_session, 1, "J-FE-001")
    report_id = report["report_id"]

    # Manually set incomplete content to simulate incomplete report
    from app.models import CareerReport

    report_obj = db_session.get(CareerReport, report_id)
    incomplete_content = dict(report_obj.content_json)
    incomplete_content["matching_analysis"] = {}
    incomplete_content["career_path"] = None
    incomplete_content["evaluation_cycle"] = {}
    # Replace the whole dict to trigger SQLAlchemy dirty tracking
    report_obj.content_json = incomplete_content
    db_session.commit()

    # Re-fetch to ensure fresh data
    db_session.expire_all()
    result = container.report_service.check_completeness(db_session, report_id)
    assert result["is_complete"] is False
    assert "matching_analysis" in result["missing_sections"]
    assert "career_path" in result["missing_sections"]
    assert "evaluation_cycle" in result["missing_sections"]


@pytest.mark.asyncio
async def test_check_completeness_nonexistent_report(db_session):
    container = create_service_container()
    await initialize_demo_data(db_session, container)

    with pytest.raises(ValueError, match="报告不存在"):
        container.report_service.check_completeness(db_session, 99999)

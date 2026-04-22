from app.services.ingestion.job_import_service import JobImportService
from app.services.reference import (
    filter_student_facing_job_templates,
    is_student_facing_computer_job,
    load_job_profile_templates,
)


def test_student_job_template_filter_keeps_computer_roles():
    templates = load_job_profile_templates()
    template_by_title = {item["title"]: item for item in templates}

    assert is_student_facing_computer_job(template_by_title["前端开发工程师"])
    assert is_student_facing_computer_job(template_by_title["后端开发工程师"])
    assert is_student_facing_computer_job(template_by_title["数据分析师"])
    assert is_student_facing_computer_job(template_by_title["数据工程师"])
    assert is_student_facing_computer_job(template_by_title["AI 算法工程师"])


def test_student_job_template_filter_excludes_non_computer_roles():
    templates = load_job_profile_templates()
    template_by_title = {item["title"]: item for item in templates}

    assert not is_student_facing_computer_job(template_by_title["产品经理"])
    assert not is_student_facing_computer_job(template_by_title["UI/UX 设计师"])
    assert not is_student_facing_computer_job(template_by_title["市场营销专员"])
    assert not is_student_facing_computer_job(template_by_title["数据咨询顾问"])
    assert not is_student_facing_computer_job(template_by_title["电气工程师"])


def test_search_templates_returns_only_student_facing_computer_roles():
    service = JobImportService(None, None, None)

    templates = service.search_templates()
    titles = {item["title"] for item in templates}

    assert "前端开发工程师" in titles
    assert "后端开发工程师" in titles
    assert "产品经理" not in titles
    assert "UI/UX 设计师" not in titles
    assert templates == filter_student_facing_job_templates(load_job_profile_templates())

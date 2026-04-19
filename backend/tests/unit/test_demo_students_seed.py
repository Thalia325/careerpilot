"""Tests for US-018: Simulated student dataset for teacher dashboard.

Uses the conftest.py client fixture which triggers create_app() lifespan,
thereby seeding demo users and 35 simulated students via initialize_demo_data().
"""
import pytest
from sqlalchemy import func, select

from app.models import (
    AnalysisRun,
    CareerReport,
    GrowthTask,
    MatchDimensionScore,
    MatchResult,
    Student,
    StudentProfile,
    UploadedFile,
    User,
)
from app.services.seed_demo_students import _STUDENT_TEMPLATES


@pytest.fixture()
def teacher_client(client):
    """Provide a client with teacher auth headers."""
    # Login as teacher to get a valid JWT token
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher_demo",
        "password": "demo123",
    })
    assert resp.status_code == 200, f"Login failed: {resp.json()}"
    token = resp.json()["access_token"]
    client.teacher_headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture()
def seeded_db(client):
    """Provide a DB session after app lifespan has seeded data.

    Depends on client (which triggers create_app lifespan) to ensure
    demo data exists before querying.
    """
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestSeedDemoStudents:
    """Tests for the seed_demo_students function (DB-based)."""

    def test_creates_35_demo_students(self, seeded_db):
        total = seeded_db.scalar(select(func.count(Student.id)))
        assert total >= 60

    def test_covers_multiple_majors(self, seeded_db):
        rows = seeded_db.execute(
            select(Student.major, func.count(Student.id))
            .where(Student.major != "")
            .group_by(Student.major)
        ).all()
        assert len(rows) >= 5

    def test_covers_multiple_target_jobs(self, seeded_db):
        rows = seeded_db.execute(
            select(Student.target_job_code, func.count(Student.id))
            .where(Student.target_job_code != "")
            .group_by(Student.target_job_code)
        ).all()
        assert len(rows) >= 5

    def test_covers_multiple_grades(self, seeded_db):
        rows = seeded_db.execute(
            select(Student.grade, func.count(Student.id))
            .where(Student.grade != "")
            .group_by(Student.grade)
        ).all()
        assert len(rows) >= 3

    def test_covers_all_match_score_ranges(self, seeded_db):
        scores = seeded_db.scalars(select(MatchResult.total_score)).all()
        ranges = {"90+": 0, "80-89": 0, "70-79": 0, "60-69": 0, "<60": 0}
        for s in scores:
            if s >= 90:
                ranges["90+"] += 1
            elif s >= 80:
                ranges["80-89"] += 1
            elif s >= 70:
                ranges["70-79"] += 1
            elif s >= 60:
                ranges["60-69"] += 1
            else:
                ranges["<60"] += 1
        non_zero = sum(1 for v in ranges.values() if v > 0)
        assert non_zero >= 4, f"Match score ranges too narrow: {ranges}"

    def test_has_different_report_statuses(self, seeded_db):
        rows = seeded_db.execute(
            select(CareerReport.status, func.count(CareerReport.id))
            .group_by(CareerReport.status)
        ).all()
        assert len(rows) >= 2

    def test_has_different_growth_task_statuses(self, seeded_db):
        rows = seeded_db.execute(
            select(GrowthTask.status, func.count(GrowthTask.id))
            .group_by(GrowthTask.status)
        ).all()
        assert len(rows) >= 2

    def test_students_have_uploaded_files(self, seeded_db):
        count = seeded_db.scalar(
            select(func.count(UploadedFile.id)).where(
                UploadedFile.file_type == "resume"
            )
        )
        assert count >= 50

    def test_students_have_profiles(self, seeded_db):
        count = seeded_db.scalar(select(func.count(StudentProfile.id)))
        assert count >= 25

    def test_match_results_have_dimension_scores(self, seeded_db):
        # Only check match results from seeded demo students
        demo_student_ids = seeded_db.scalars(
            select(Student.id).join(User).where(User.username.like("demo_student_%"))
        ).all()
        match_ids = seeded_db.scalars(
            select(MatchResult.id).where(MatchResult.student_id.in_(demo_student_ids))
        ).all()
        assert len(match_ids) >= 25, f"Expected >= 25 seeded match results, got {len(match_ids)}"
        for mid in match_ids[:5]:
            dc = seeded_db.scalar(
                select(func.count(MatchDimensionScore.id)).where(
                    MatchDimensionScore.match_result_id == mid
                )
            )
            assert dc == 4, f"MatchResult {mid} has {dc} dimensions, expected 4"

    def test_analysis_runs_created(self, seeded_db):
        count = seeded_db.scalar(
            select(func.count(AnalysisRun.id)).where(
                AnalysisRun.status == "completed"
            )
        )
        assert count >= 25

    def test_reports_have_markdown_content(self, seeded_db):
        demo_student_ids = seeded_db.scalars(
            select(Student.id).join(User).where(User.username.like("demo_student_%"))
        ).all()
        reports = seeded_db.scalars(
            select(CareerReport).where(
                CareerReport.student_id.in_(demo_student_ids),
                CareerReport.markdown_content != "",
            )
        ).all()
        assert len(reports) >= 20, f"Expected >= 20 seeded reports, got {len(reports)}"
        for r in reports:
            assert len(r.markdown_content) > 100

    def test_growth_tasks_have_deadlines(self, seeded_db):
        tasks = seeded_db.scalars(
            select(GrowthTask).where(GrowthTask.deadline.isnot(None))
        ).all()
        assert len(tasks) >= 50


class TestTeacherAPIWithSeedData:
    """Tests that teacher API endpoints return realistic data after seeding."""

    def test_teacher_students_reports_returns_data(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/students/reports",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 60
        student = data[0]
        for key in ["student_id", "name", "major", "grade", "target_job", "match_score", "report_status"]:
            assert key in student

    def test_teacher_match_distribution_has_all_ranges(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/stats/match-distribution",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 5
        non_zero = sum(1 for d in data if d["count"] > 0)
        assert non_zero >= 3

    def test_teacher_major_distribution_returns_data(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/stats/major-distribution",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 5
        names = [d["name"] for d in data]
        assert "暂无数据" not in names

    def test_teacher_advice_returns_data(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/advice",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 50
        summary = data[-1]
        assert summary["name"] == "全班汇总"
        assert summary["student_id"] == 0

    def test_teacher_students_have_varied_match_scores(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/students/reports",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        scores = [s["match_score"] for s in data if s["match_score"] > 0]
        assert len(scores) >= 20
        assert max(scores) >= 85
        assert min(scores) < 70

    def test_teacher_students_have_varied_report_statuses(self, teacher_client):
        resp = teacher_client.get(
            "/api/v1/teacher/students/reports",
            headers=teacher_client.teacher_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        statuses = set(s["report_status"] for s in data)
        assert len(statuses) >= 3


class TestTemplateCoverage:
    """Tests for _STUDENT_TEMPLATES data quality — no DB needed."""

    def test_template_count(self):
        assert len(_STUDENT_TEMPLATES) == 63

    def test_covers_7_majors(self):
        majors = set(t[1] for t in _STUDENT_TEMPLATES)
        assert len(majors) >= 5

    def test_covers_8_target_jobs(self):
        jobs = set(t[4] for t in _STUDENT_TEMPLATES)
        assert len(jobs) >= 5

    def test_covers_4_grades(self):
        grades = set(t[2] for t in _STUDENT_TEMPLATES)
        assert len(grades) >= 3

    def test_covers_all_match_ranges(self):
        scores = [t[6] for t in _STUDENT_TEMPLATES]
        assert any(s >= 90 for s in scores), "No 90+ scores"
        assert any(80 <= s < 90 for s in scores), "No 80-89 scores"
        assert any(70 <= s < 80 for s in scores), "No 70-79 scores"
        assert any(60 <= s < 70 for s in scores), "No 60-69 scores"
        assert any(s < 60 for s in scores), "No <60 scores"

    def test_has_varied_completeness(self):
        completeness_values = [t[11] for t in _STUDENT_TEMPLATES]
        assert min(completeness_values) < 40
        assert max(completeness_values) >= 90

    def test_all_names_are_unique(self):
        names = [t[0] for t in _STUDENT_TEMPLATES]
        assert len(names) == len(set(names))

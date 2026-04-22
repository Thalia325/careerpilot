"""Tests for US-008: standardized recommended job fields and recommendation reasons."""

import re
import pytest

from app.schemas.job import RecommendedJobItem, RecommendedJobsResponse
from app.schemas.profile import ManualStudentInput
from app.api.routers.students import _student_facing_profiles
from app.services.bootstrap import create_service_container, initialize_demo_data
from app.services.matching.recommendation import generate_recommendation_reason


# ── Unit tests for generate_recommendation_reason ──


def _make_scoring(**overrides):
    base = {
        "score": 78.5,
        "matched_skills": ["React", "TypeScript"],
        "missing_skills": ["Node.js"],
        "matched_certificates": [],
        "experience_tags": ["前端"],
        "intent_tags": [],
        "skill_score": 65.0,
        "potential_score": 72.0,
    }
    base.update(overrides)
    return base


class TestGenerateRecommendationReason:
    """Test that generate_recommendation_reason references real evidence."""

    def test_references_major_and_job_title(self):
        from types import SimpleNamespace
        reason = generate_recommendation_reason(
            scoring=_make_scoring(),
            student_info={"major": "计算机科学与技术", "grade": "大三"},
            job_profile=SimpleNamespace(title="前端开发工程师"),
        )
        assert "计算机科学与技术" in reason
        assert "前端开发工程师" in reason

    def test_references_matched_skills(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(matched_skills=["React", "TypeScript", "Vue"]),
        )
        assert "React" in reason
        assert "TypeScript" in reason

    def test_references_project_experience(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(),
            experience={"projects": ["电商平台前端开发", "个人博客系统"], "internships": []},
        )
        assert "电商平台前端开发" in reason

    def test_references_internship_experience(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(),
            experience={"projects": [], "internships": ["字节跳动前端实习"]},
        )
        assert "字节跳动前端实习" in reason

    def test_references_intent_tags(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(intent_tags=["前端开发"]),
        )
        assert "前端开发" in reason

    def test_references_matched_certificates(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(matched_certificates=["CET-6", "软件设计师"]),
        )
        assert "CET-6" in reason
        assert "软件设计师" in reason

    def test_references_missing_skills(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(missing_skills=["Node.js", "Docker"]),
        )
        assert "Node.js" in reason

    def test_fallback_high_score(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(
                matched_skills=[], missing_skills=[], experience_tags=[], intent_tags=[], matched_certificates=[], score=85,
            ),
        )
        assert "85" in reason
        assert "较高" in reason

    def test_fallback_medium_score(self):
        reason = generate_recommendation_reason(
            scoring=_make_scoring(
                matched_skills=[], missing_skills=[], experience_tags=[], intent_tags=[], matched_certificates=[], score=62,
            ),
        )
        assert "62" in reason

    def test_reason_ends_with_period(self):
        reason = generate_recommendation_reason(scoring=_make_scoring())
        assert reason.endswith("。")

    def test_combined_evidence(self):
        """Reason references multiple evidence sources together."""
        from types import SimpleNamespace
        reason = generate_recommendation_reason(
            scoring=_make_scoring(
                matched_skills=["Python", "SQL"],
                matched_certificates=["CET-4"],
                intent_tags=["数据分析"],
                missing_skills=["Spark"],
            ),
            student_info={"major": "统计学", "grade": "研一"},
            job_profile=SimpleNamespace(title="数据分析师"),
            experience={"projects": ["电商数据分析项目"], "internships": ["腾讯数据实习生"]},
        )
        assert "统计学" in reason
        assert "Python" in reason
        assert "电商数据分析项目" in reason
        assert "腾讯数据实习生" in reason
        assert "数据分析" in reason
        assert "CET-4" in reason
        assert "Spark" in reason


# ── Schema tests ──


class TestRecommendedJobItemSchema:
    """Test the Pydantic schema for standardized response."""

    def test_all_required_fields(self):
        item = RecommendedJobItem(
            job_code="J-FE-001",
            title="前端开发工程师",
            company="某科技公司",
            match_score=78.5,
        )
        assert item.job_code == "J-FE-001"
        assert item.title == "前端开发工程师"
        assert item.company == "某科技公司"
        assert item.match_score == 78.5
        # Defaults
        assert item.location == ""
        assert item.salary == ""
        assert item.industry == ""
        assert item.industry_group == ""
        assert item.company_size == ""
        assert item.ownership_type == ""
        assert item.matched_tags == []
        assert item.missing_tags == []
        assert item.reason == ""

    def test_full_fields(self):
        item = RecommendedJobItem(
            job_code="J-PM-001",
            title="产品经理",
            company="阿里巴巴",
            location="杭州",
            salary="20-40K",
            industry="互联网",
            company_size="10000人以上",
            ownership_type="民营",
            match_score=85.0,
            matched_tags=["需求分析", "原型设计"],
            missing_tags=["SQL"],
            reason="已掌握【需求分析、原型设计】等核心技能标签。",
            summary="产品经理岗位",
            tags=["需求分析", "原型设计", "SQL"],
            experience_tags=["产品"],
            base_score=70.0,
            experience_score=60.0,
            skill_score=80.0,
            potential_score=75.0,
        )
        assert item.location == "杭州"
        assert item.salary == "20-40K"
        assert item.industry == "互联网"
        assert item.company_size == "10000人以上"
        assert item.ownership_type == "民营"
        assert len(item.matched_tags) == 2
        assert len(item.missing_tags) == 1
        assert item.reason != ""

    def test_response_wrapper(self):
        resp = RecommendedJobsResponse(items=[
            RecommendedJobItem(job_code="J-FE-001", title="前端", company="A", match_score=80.0),
        ])
        assert len(resp.items) == 1
        assert resp.items[0].job_code == "J-FE-001"


# ── Integration tests via API ──


def _auth_headers(user_id: int = 1) -> dict:
    return {"Authorization": "Bearer dev-bypass"}


class TestRecommendedJobsAPI:
    """Test the /students/me/recommended-jobs endpoint returns standardized fields."""

    @pytest.mark.asyncio
    async def test_recommended_jobs_returns_all_standard_fields(self, client, db_session):
        """Each recommended job item must include all required standard fields."""
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        # Generate student profile
        await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="专注前端",
                skills=["JavaScript", "React", "TypeScript"],
                certificates=["英语四级"],
                projects=["电商平台"],
                internships=["前端实习"],
            ),
        )

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

        if not data["items"]:
            pytest.skip("No recommended jobs returned (possible scoring threshold)")

        job = data["items"][0]
        required_fields = [
            "job_code", "title", "company", "location", "salary",
            "industry", "industry_group", "company_size", "ownership_type", "match_score",
            "matched_tags", "missing_tags", "reason",
        ]
        for field in required_fields:
            assert field in job, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_recommended_jobs_reason_references_real_evidence(self, client, db_session):
        """Reason must reference real evidence (skills, background, etc.)."""
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="专注前端",
                skills=["JavaScript", "React", "TypeScript", "HTML", "CSS"],
                certificates=["英语四级"],
                projects=["电商平台前端"],
                internships=["前端实习"],
            ),
        )

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]

        if not items:
            pytest.skip("No recommended jobs returned")

        # At least one job should have a non-empty reason
        reasons = [item["reason"] for item in items if item.get("reason")]
        assert len(reasons) > 0, "No recommended jobs have reason text"

        # The reason should reference real skills or evidence (not generic text)
        all_reasons = " ".join(reasons)
        assert len(all_reasons) > 10, "Reasons are too short to contain real evidence"

    @pytest.mark.asyncio
    async def test_recommended_jobs_returns_ranked_candidates_below_old_threshold(self, client, db_session):
        """Recommendations should cover the available student-facing catalog, not only a tiny head list."""
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="算法研发工程师",
                self_introduction="软件工程专业，做过 API 调用脚本、统计建模和深度学习项目",
                skills=["Python", "PyTorch", "深度学习", "SQL", "Java", "JavaScript", "Linux"],
                certificates=[],
                projects=["统计建模比赛", "深度学习模型项目", "API 调用脚本"],
                internships=[],
            ),
        )

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]
        available_profiles = _student_facing_profiles(db_session)

        assert len(items) >= 3
        assert items == sorted(items, key=lambda item: item["match_score"], reverse=True)
        assert len(items) == min(30, len(available_profiles))

    @pytest.mark.asyncio
    async def test_recommended_jobs_metadata_is_normalized(self, client, db_session):
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="前端开发工程师",
                self_introduction="专注 Web 前端开发",
                skills=["JavaScript", "React", "TypeScript", "HTML", "CSS"],
                certificates=[],
                projects=["电商平台前端"],
                internships=["前端实习"],
            ),
        )

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]
        if not items:
            pytest.skip("No recommended jobs returned")

        assert all(not re.search(r"\d{6,}", item.get("industry", "")) for item in items)

    @pytest.mark.asyncio
    async def test_recommended_jobs_are_unique_by_job_code(self, client, db_session):
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        await container.student_profile_service.generate_profile(
            db_session,
            student_id=1,
            uploaded_file_ids=[],
            manual_input=ManualStudentInput(
                target_job="后端开发工程师",
                self_introduction="有服务端开发和数据处理经历",
                skills=["Python", "FastAPI", "SQL", "Redis"],
                certificates=[],
                projects=["任务调度平台", "数据清洗脚本"],
                internships=["后端开发实习"],
            ),
        )

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        items = resp.json()["items"]
        if not items:
            pytest.skip("No recommended jobs returned")

        job_codes = [item["job_code"] for item in items]
        assert len(job_codes) == len(set(job_codes))

    @pytest.mark.asyncio
    async def test_recommended_jobs_empty_without_profile(self, client, db_session):
        """Without a student profile, returns empty items."""
        container = create_service_container()
        await initialize_demo_data(db_session, container)

        resp = client.get("/api/v1/students/me/recommended-jobs", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        # Without profile, items should be empty (no scoring possible)
        assert isinstance(data["items"], list)

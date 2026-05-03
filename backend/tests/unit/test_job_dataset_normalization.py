from types import SimpleNamespace

from app.services.reference import (
    derive_industry_group,
    filter_campus_relevant_rows,
    filter_student_facing_job_profiles,
    normalize_industry_value,
    normalize_posting_snapshot,
)


def test_normalize_industry_value_deduplicates_and_strips_codes():
    industry = "计算机软件,互联网,IT服务,计算机软件,100040000,100030000"
    assert normalize_industry_value(industry) == "计算机软件 / 互联网 / IT服务"


def test_normalize_posting_snapshot_standardizes_display_fields():
    snapshot = normalize_posting_snapshot(
        {
            "title": "前端开发（双休）",
            "location": " 上海 - 浦东新区 ",
            "salary_range": "15-20K",
            "company_name": "某科技公司",
            "industry": "云计算,大数据,人工智能,100080000",
            "company_size": "1000-9999人,1000-9999人",
            "ownership_type": "已上市,已上市",
            "description": "负责 React 前端开发",
            "company_intro": "技术团队",
            "job_code": "J-FE-001",
        }
    )
    assert snapshot["title"] == "前端开发"
    assert snapshot["location"] == "上海-浦东新区"
    assert snapshot["industry"] == "云计算 / 大数据 / 人工智能"
    assert snapshot["industry_group"] == "AI/大数据"
    assert snapshot["company_size"] == "1000-9999人"
    assert snapshot["ownership_type"] == "上市公司"


def test_derive_industry_group_prefers_student_facing_groups():
    assert derive_industry_group("计算机软件 / 互联网 / IT服务") == "软件/互联网"
    assert derive_industry_group("电子 / 半导体 / 集成电路") == "硬件/半导体"
    assert derive_industry_group("银行 / 计算机软件") == "金融科技/数据"


def test_filter_student_facing_job_profiles_excludes_non_technical_roles():
    profiles = [
        SimpleNamespace(
            job_code="J-FE-001",
            title="前端开发工程师",
            summary="React",
            skill_requirements=["React", "TypeScript", "JavaScript"],
        ),
        SimpleNamespace(
            job_code="J-PM-001",
            title="产品经理",
            summary="需求分析",
            skill_requirements=["原型", "需求分析", "项目管理"],
        ),
    ]
    filtered = filter_student_facing_job_profiles(profiles)
    assert [profile.job_code for profile in filtered] == ["J-FE-001"]


def test_filter_campus_relevant_rows_keeps_broader_graduate_roles():
    rows = [
        {
            "title": "财务会计管培生",
            "industry": "金融服务,会计/审计",
            "description": "参与财务核算、预算分析和经营报表整理",
            "job_code": "CP-J-ACC-001-03",
        },
        {
            "title": "分拣员",
            "industry": "物流运输",
            "description": "仓库分拣搬运",
            "job_code": "X-001",
        },
    ]
    filtered = filter_campus_relevant_rows(rows)
    assert [row["job_code"] for row in filtered] == ["CP-J-ACC-001-03"]

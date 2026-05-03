from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


HEADERS = [
    "title",
    "location",
    "salary_range",
    "company_name",
    "industry",
    "company_size",
    "ownership_type",
    "job_code",
    "description",
    "company_intro",
    "source_url",
    "updated_at",
]


CITY_ROTATION = [
    "北京-海淀区",
    "上海-浦东新区",
    "广州-天河区",
    "深圳-南山区",
    "杭州-西湖区",
    "成都-高新区",
    "武汉-光谷",
    "西安-高新区",
    "南京-江宁区",
    "苏州-工业园区",
    "天津-滨海新区",
    "重庆-渝北区",
]


COMPANY_SUFFIXES = [
    "创新科技有限公司",
    "产业发展集团",
    "咨询服务有限公司",
    "智能制造有限公司",
    "现代服务有限公司",
]


CATEGORY_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("互联网/软件/数据", ("前端", "后端", "全栈", "软件", "开发", "测试", "数据", "AI", "算法", "运维", "网络安全", "硬件", "嵌入式", "通信", "产品经理", "IT咨询", "Scrum"), "互联网,计算机软件,人工智能,大数据"),
    ("金融/财会/风控", ("金融", "财务", "会计", "审计", "投资", "风险", "银行", "保险", "税务", "成本"), "金融服务,银行,证券,保险,会计/审计"),
    ("法务/合规/知识产权", ("法务", "合规", "知识产权"), "法律服务,企业服务,知识产权"),
    ("教育/培训/科研", ("培训", "教学", "教育", "留学", "职业规划"), "教育培训,科研服务,在线教育"),
    ("市场/品牌/传媒", ("市场", "新媒体", "广告", "品牌", "公关", "活动", "内容", "视频", "文案", "记者", "编辑"), "传媒,广告营销,品牌服务,内容平台"),
    ("销售/商务/客户", ("销售", "客户", "商务", "BD", "外贸"), "企业服务,贸易/进出口,客户服务"),
    ("人力/行政/组织", ("人力", "招聘", "薪酬", "行政", "前台", "文秘"), "人力资源服务,企业管理服务"),
    ("智能制造/工程技术", ("机械", "电气", "土木", "建筑", "质量", "工业", "结构", "航空", "工程项目", "自动化"), "智能制造,机械设备,建筑工程,航空航天"),
    ("医药/健康/生命科学", ("医药", "临床", "生物", "医学", "营养", "心理", "康复"), "医药制造,医疗健康,生命科学"),
    ("供应链/物流/采购", ("供应链", "物流", "采购", "仓储", "冷链"), "物流运输,供应链服务,仓储配送"),
    ("文旅/酒店/餐饮/体育", ("旅游", "导游", "酒店", "餐饮", "体育", "健身", "体能"), "文旅服务,酒店餐饮,体育产业"),
    ("农业/食品/环境", ("农业", "园艺", "畜牧", "食品", "环境", "化工"), "现代农业,食品制造,环保服务,化工"),
    ("能源/绿色低碳", ("新能源", "储能", "能源", "石油"), "新能源,电力能源,绿色低碳"),
    ("设计/创意/数字内容", ("设计", "插画", "动画", "游戏美术", "展览"), "设计服务,数字内容,文化创意"),
    ("公共服务/社区治理", ("社会工作", "社区管理", "网格员", "物业"), "公共服务,社区治理,物业服务"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a broader campus-facing job dataset.")
    parser.add_argument(
        "--base",
        default=str(DATA_DIR / "a13_jobs_augmented.csv"),
        help="Existing cleaned job CSV to merge with the curated campus rows.",
    )
    parser.add_argument(
        "--templates",
        default=str(DATA_DIR / "job_profile_templates.json"),
        help="CareerPilot job profile templates used as the occupation taxonomy seed.",
    )
    parser.add_argument(
        "--curated-output",
        default=str(DATA_DIR / "campus_jobs_curated.csv"),
        help="Output path for newly generated campus job rows.",
    )
    parser.add_argument(
        "--merged-output",
        default=str(DATA_DIR / "campus_jobs_augmented.csv"),
        help="Output path for base rows plus curated campus rows.",
    )
    return parser.parse_args()


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                return [dict(row) for row in csv.DictReader(file)]
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Unable to decode CSV: {path}")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in HEADERS})


def _load_templates(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _classify_template(template: dict[str, Any]) -> tuple[str, str]:
    title = str(template.get("title", ""))
    for category, keywords, industry in CATEGORY_RULES:
        if any(keyword in title for keyword in keywords):
            return category, industry
    skill_blob = " ".join(str(item) for item in template.get("skills", []) if item)
    if any(keyword in skill_blob for keyword in ("Python", "SQL", "Java", "React", "Vue", "Linux", "Docker", "算法", "数据建模")):
        return "互联网/软件/数据", "互联网,计算机软件,人工智能,大数据"
    return "综合管理/专业服务", "专业服务,企业服务,综合管理"


def _salary_for(index: int, variant_index: int) -> str:
    base = 6 + (index % 9) + variant_index
    high = base + 4 + (index % 4)
    if variant_index == 0:
        return f"{base}-{high}K"
    if variant_index == 1:
        return f"{max(4, base - 2)}-{max(7, high - 2)}K"
    return f"{base + 1}-{high + 3}K"


def _title_variants(title: str) -> list[str]:
    compact = title.replace(" ", "")
    if "/" in compact:
        first = compact.split("/", 1)[0]
        return [compact, f"助理{first}", f"{first}管培生"]
    if compact.endswith("工程师"):
        return [compact, f"助理{compact}", compact.replace("工程师", "实习工程师")]
    if compact.endswith("专员"):
        return [compact, f"助理{compact}", compact.replace("专员", "实习专员")]
    if compact.endswith("师"):
        return [compact, f"助理{compact}", f"{compact}实习生"]
    if compact.endswith("经理"):
        return [compact, f"助理{compact}", compact.replace("经理", "管培生")]
    return [compact, f"助理{compact}", f"{compact}管培生"]


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_codes: set[str] = set()
    seen_fallback: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        code = str(row.get("job_code") or "").strip()
        fallback = (
            str(row.get("title") or "").strip().lower(),
            str(row.get("company_name") or "").strip().lower(),
            str(row.get("source_url") or "").strip().lower(),
        )
        if code and code in seen_codes:
            continue
        if fallback in seen_fallback:
            continue
        if code:
            seen_codes.add(code)
        seen_fallback.add(fallback)
        result.append({header: row.get(header, "") for header in HEADERS})
    return result


def build_curated_rows(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, template in enumerate(templates, start=1):
        category, industry = _classify_template(template)
        skills = [str(item) for item in template.get("skills", []) if item]
        certificates = [str(item) for item in template.get("certificates", []) if item]
        summary = str(template.get("summary") or "")
        skill_text = "、".join(skills[:6]) if skills else "岗位通用技能"
        certificate_text = "、".join(certificates[:3]) if certificates else "相关课程、项目或实习经历"
        title_variants = _title_variants(str(template.get("title") or "校园岗位"))
        for variant_index, title in enumerate(title_variants):
            city = CITY_ROTATION[(index + variant_index) % len(CITY_ROTATION)]
            company = f"{city.split('-', 1)[0]}{category.split('/', 1)[0]}{COMPANY_SUFFIXES[(index + variant_index) % len(COMPANY_SUFFIXES)]}"
            job_code = f"CP-{template.get('job_code', f'TPL-{index:03d}')}-{variant_index + 1:02d}"
            description = (
                f"岗位方向：{category}。{summary}\n"
                f"工作内容：参与真实业务项目，完成需求理解、方案执行、数据或文档沉淀、跨团队协作与阶段复盘。\n"
                f"能力要求：掌握{skill_text}，具备学习能力、沟通协作意识和结果交付意识。\n"
                f"加分项：{certificate_text}，或有校内项目、竞赛、实习、社会实践经历。"
            )
            rows.append(
                {
                    "title": title,
                    "location": city,
                    "salary_range": _salary_for(index, variant_index),
                    "company_name": company,
                    "industry": industry,
                    "company_size": ["20-99人", "100-299人", "500-999人", "1000-9999人"][index % 4],
                    "ownership_type": ["民营", "国企", "上市公司", "合资"][variant_index % 4],
                    "job_code": job_code,
                    "description": description,
                    "company_intro": (
                        f"{company}面向应届生和初级人才提供{category}方向的项目实践、导师辅导和轮岗培养。"
                    ),
                    "source_url": f"careerpilot://curated-campus/{job_code}",
                    "updated_at": "2026-05-02",
                }
            )
    return _dedupe(rows)


def main() -> None:
    args = parse_args()
    templates = _load_templates(Path(args.templates))
    curated_rows = build_curated_rows(templates)
    base_rows = _read_csv(Path(args.base))
    merged_rows = _dedupe(base_rows + curated_rows)

    _write_csv(Path(args.curated_output), curated_rows)
    _write_csv(Path(args.merged_output), merged_rows)

    print(f"Templates used: {len(templates)}")
    print(f"Curated campus rows: {len(curated_rows)}")
    print(f"Base rows: {len(base_rows)}")
    print(f"Merged rows: {len(merged_rows)}")
    print(f"Curated output: {Path(args.curated_output)}")
    print(f"Merged output: {Path(args.merged_output)}")


if __name__ == "__main__":
    main()

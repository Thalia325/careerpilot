from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.reference import load_job_profile_templates


def generate_rows(total: int) -> list[dict]:
    templates = load_job_profile_templates()
    cities = ["西安", "深圳", "北京", "上海", "杭州", "成都"]
    industries = ["信息化服务", "智能制造", "教育科技", "互联网", "金融科技"]
    ownership_types = ["民营", "国企", "上市公司"]
    sizes = ["100-499人", "500-999人", "1000-9999人"]
    rows = []
    for index in range(total):
        template = templates[index % len(templates)]
        rows.append(
            {
                "title": template["title"],
                "location": random.choice(cities),
                "salary_range": f"{8 + index % 6}-{13 + index % 6}K",
                "company_name": f"样例企业{index + 1}",
                "industry": random.choice(industries),
                "company_size": random.choice(sizes),
                "ownership_type": random.choice(ownership_types),
                "job_code": f"{template['job_code']}-{index + 1:05d}",
                "description": f"{template['summary']} 重点技能：{', '.join(template['skills'])}",
                "company_intro": "用于演示 CareerPilot 岗位导入能力的样例数据。",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 CareerPilot 样例岗位 CSV")
    parser.add_argument("--output", default="../data/sample_jobs.csv")
    parser.add_argument("--rows", type=int, default=10000)
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    ]
    rows = generate_rows(args.rows)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"已生成 {len(rows)} 条岗位数据 -> {output_path}")


if __name__ == "__main__":
    main()

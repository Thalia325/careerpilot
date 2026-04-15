from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import JobPosting, JobProfile
from app.services.reference import find_best_template


def main() -> None:
    with SessionLocal() as db:
        # 获取所有没有画像的岗位
        postings = db.scalars(
            select(JobPosting).where(
                ~JobPosting.job_code.in_(
                    select(JobProfile.job_code)
                )
            )
        ).all()

        print(f"找到 {len(postings)} 个未生成画像的岗位")

        # 使用模板快速生成画像
        success_count = 0
        for posting in postings:
            try:
                template = find_best_template(posting.title)
                profile = db.scalar(
                    select(JobProfile).where(JobProfile.job_code == posting.job_code)
                )
                if not profile:
                    profile = JobProfile(
                        job_code=posting.job_code,
                        job_posting_id=posting.id,
                        title=posting.title
                    )
                    db.add(profile)
                    db.flush()

                # 使用模板数据填充
                profile.summary = template["summary"]
                profile.skill_requirements = template["skills"]
                profile.certificate_requirements = template.get("certificates", [])
                profile.innovation_requirements = template["explanations"]["创新能力"]
                profile.learning_requirements = template["explanations"]["学习能力"]
                profile.resilience_requirements = template["explanations"]["抗压能力"]
                profile.communication_requirements = template["explanations"]["沟通能力"]
                profile.internship_requirements = template["explanations"]["实习能力"]
                profile.capability_scores = template["capabilities"]
                profile.dimension_weights = template["dimension_weights"]
                profile.explanation_json = template["explanations"]

                success_count += 1
                if success_count % 100 == 0:
                    print(f"已处理 {success_count} 个岗位...")
                    db.commit()
            except Exception as e:
                print(f"处理岗位 {posting.job_code} 失败: {e}")
                continue

        db.commit()
        print(f"成功生成 {success_count} 个岗位画像")


if __name__ == "__main__":
    main()

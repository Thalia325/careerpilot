import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models import StudentProfile, JobProfile
from app.api.routers.students import _score_recommended_job
from sqlalchemy import select


def main():
    db = SessionLocal()

    # 获取学生画像
    student_profile = db.scalar(select(StudentProfile).limit(1))
    if not student_profile:
        print("没有学生画像数据")
        return

    # 获取所有岗位，查看有多少不同的岗位类型
    all_profiles = list(db.scalars(select(JobProfile)).all())
    unique_titles = sorted(set(jp.title for jp in all_profiles))
    print(f"总岗位数: {len(all_profiles)}")
    print(f"不同岗位类型数: {len(unique_titles)}")
    print(f"岗位类型: {unique_titles}")

    # 获取前500个岗位用于计算
    all_profiles = list(db.scalars(select(JobProfile).order_by(JobProfile.title)).all())[:500]

    # 模拟新的推荐逻辑
    scored_profiles = []
    seen_titles = set()
    MAX_RECOMMENDED = 30

    for jp in all_profiles:
        if jp.title in seen_titles:
            continue

        scoring = _score_recommended_job(student_profile, jp)
        seen_titles.add(jp.title)

        skill_weight = 0.6
        weighted_score = (
            scoring["skill_score"] * skill_weight +
            scoring["potential_score"] * (1 - skill_weight)
        )
        scored_profiles.append((weighted_score, scoring, jp))

        if len(seen_titles) >= MAX_RECOMMENDED:
            break

    # 排序
    scored_profiles.sort(key=lambda item: item[0], reverse=True)

    print(f"\n推荐岗位 (前{len(scored_profiles)}个不同的岗位):")
    print(f"{'排名':<5} {'岗位':<20} {'加权分':<10} {'总匹配分':<10} {'技能分':<10} {'匹配技能'}")
    print("-" * 100)

    for i, (weighted_score, scoring, jp) in enumerate(scored_profiles[:30], 1):
        matched = scoring["matched_skills"][:3]
        matched_str = ', '.join(matched) if matched else "无"
        print(f"{i:<5} {jp.title:<20} {weighted_score:<10.1f} {scoring['score']:<10.1f} {scoring['skill_score']:<10.1f} {matched_str}")

    print(f"\n总共找到 {len(seen_titles)} 个不同的岗位类型")


if __name__ == "__main__":
    main()

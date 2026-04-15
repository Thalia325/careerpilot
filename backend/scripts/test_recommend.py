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

    # 获取所有岗位
    all_profiles = list(db.scalars(select(JobProfile)).all())
    print(f"总岗位数: {len(all_profiles)}")

    # 计算加权分数
    scored_profiles = []
    for jp in all_profiles:
        scoring = _score_recommended_job(student_profile, jp)
        skill_weight = 0.6
        weighted_score = (
            scoring["skill_score"] * skill_weight +
            scoring["potential_score"] * (1 - skill_weight)
        )
        scored_profiles.append((weighted_score, scoring, jp))

    # 排序
    scored_profiles.sort(key=lambda item: item[0], reverse=True)

    print(f"\n推荐岗位 (前30个):")
    print(f"{'排名':<5} {'岗位':<20} {'总匹配分':<10} {'技能分':<10} {'潜力分':<10} {'匹配技能'}")
    print("-" * 100)

    for i, (weighted_score, scoring, jp) in enumerate(scored_profiles[:30], 1):
        matched = scoring["matched_skills"][:3]
        matched_str = ', '.join(matched) if matched else "无"
        print(f"{i:<5} {jp.title:<20} {scoring['score']:<10.1f} {scoring['skill_score']:<10.1f} {scoring['potential_score']:<10.1f} {matched_str}")

    print(f"\n按加权分数排序的第30名分数: {scored_profiles[29][0]:.1f}")
    print(f"按加权分数排序的第100名分数: {scored_profiles[99][0]:.1f}")


if __name__ == "__main__":
    main()

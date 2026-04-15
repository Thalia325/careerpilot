import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models import Student, StudentProfile
from sqlalchemy import select

db = SessionLocal()
student = db.scalar(select(Student).limit(1))
if student:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.student_id == student.id))
    if profile:
        print(f'学生ID: {student.id}')
        print(f'专业: {student.major}')
        print(f'年级: {student.grade}')
        print(f'职业目标: {student.career_goal}')
        print(f'技能数量: {len(profile.skills_json) if profile.skills_json else 0}')
        print(f'技能: {profile.skills_json}')
        print(f'证书: {profile.certificates_json}')
        print(f'能力评分: {profile.capability_scores}')
        print(f'完整性评分: {profile.completeness_score}')
        print(f'竞争力评分: {profile.competitiveness_score}')
    else:
        print('没有学生画像')
else:
    print('没有学生数据')

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.bootstrap import create_service_container
from app.db.session import SessionLocal


async def main() -> None:
    print("=== 测试岗位图谱数据 ===\n")

    # 检查数据库中的岗位数量
    from app.models import JobProfile
    from sqlalchemy import select

    with SessionLocal() as db:
        profiles = db.scalars(select(JobProfile)).all()
        print(f"数据库中的岗位画像数量: {len(profiles)}")

    # 测试图谱查询
    container = create_service_container()
    # 初始化图谱数据
    from app.services.reference import load_job_graph_seed
    await container.job_import_service.graph_provider.load_seed(load_job_graph_seed())

    test_jobs = [
        ("J-FE-001", "前端开发工程师"),
        ("J-BE-001", "后端开发工程师"),
        ("J-PM-001", "产品经理"),
    ]

    for job_code, job_name in test_jobs:
        print(f"\n--- {job_name} ({job_code}) ---")
        result = await container.job_import_service.graph_provider.query_job(job_code)

        print(f"描述: {result.get('description', 'N/A')}")
        print(f"技能要求: {result.get('required_skills', [])}")
        print(f"晋升路径数量: {len(result.get('promotion_paths', []))}")
        for path in result.get('promotion_paths', [])[:2]:
            print(f"  - {' -> '.join(path)}")
        print(f"换岗路径数量: {len(result.get('transition_paths', []))}")
        for path in result.get('transition_paths', [])[:3]:
            print(f"  - {' -> '.join(path)}")
        print(f"垂直路径: {len(result.get('vertical_paths', []))} 条")
        for vp in result.get('vertical_paths', []):
            print(f"  - {vp['name']}: {vp['description']}")
        print(f"换岗集群: {len(result.get('transition_clusters', []))} 个")
        for tc in result.get('transition_clusters', []):
            print(f"  - {tc['name']}: {tc['description']}")

    print("\n=== 数据验证完成 ===")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

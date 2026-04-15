import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.bootstrap import create_service_container
from app.services.reference import load_job_graph_seed
from app.db.session import SessionLocal


async def main() -> None:
    container = create_service_container()

    # 加载新的图谱数据
    print("正在加载岗位图谱数据...")
    seed_data = load_job_graph_seed()
    await container.job_import_service.graph_provider.load_seed(seed_data)
    print(f"已加载 {len(seed_data.get('jobs', {}))} 个岗位的图谱数据")

    # 验证加载结果
    test_codes = ["J-FE-001", "J-BE-001", "J-PM-001"]
    for code in test_codes:
        result = await container.job_import_service.graph_provider.query_job(code)
        print(f"\n岗位: {result.get('title', 'N/A')}")
        print(f"  晋升路径: {len(result.get('promotion_paths', []))} 条")
        print(f"  换岗路径: {len(result.get('transition_paths', []))} 条")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

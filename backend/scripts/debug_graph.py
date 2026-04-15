import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.bootstrap import create_service_container
from app.services.reference import load_job_graph_seed


async def main() -> None:
    # 加载原始数据
    seed_data = load_job_graph_seed()
    print(f"原始数据:")
    print(f"  Jobs: {len(seed_data.get('jobs', {}))}")
    print(f"  Vertical paths: {len(seed_data.get('vertical_paths', {}))}")
    print(f"  Transition clusters: {len(seed_data.get('transition_clusters', {}))}")

    # 测试加载到 MockGraphProvider
    container = create_service_container()
    await container.job_import_service.graph_provider.load_seed(seed_data)

    # 查询一个岗位
    result = await container.job_import_service.graph_provider.query_job("J-FE-001")
    print(f"\n加载后的数据:")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Description: {result.get('description', 'N/A')[:50]}...")
    print(f"  Skills: {len(result.get('required_skills', []))}")
    print(f"  Promotions: {len(result.get('promotion_paths', []))}")
    print(f"  Transitions: {len(result.get('transition_paths', []))}")
    print(f"  Vertical paths: {len(result.get('vertical_paths', []))}")
    print(f"  Transition clusters: {len(result.get('transition_clusters', []))}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

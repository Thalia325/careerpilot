from __future__ import annotations

import argparse
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.bootstrap import create_service_container


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export local knowledge base JSON for A13 submission.")
    parser.add_argument(
        "--output",
        help="Output path for exported JSON. Defaults to exports/knowledge_base/a13_local_knowledge_base.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    container = create_service_container()
    with SessionLocal() as db:
        result = container.job_import_service.export_local_knowledge_base(db, args.output)

    print("CareerPilot 本地知识库导出完成")
    print(f"- 输出文件: {result['path']}")
    print(f"- 筛选后岗位数据: {result['posting_count']}")
    print(f"- 岗位画像数: {result['profile_count']}")
    print(f"- 知识文档数: {result['document_count']}")


if __name__ == "__main__":
    main()

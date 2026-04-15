from __future__ import annotations

import asyncio
import csv
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.bootstrap import create_service_container


async def main() -> None:
    csv_path = BACKEND_DIR.parent / "data" / "sample_jobs.csv"
    if not csv_path.exists():
        print(f"CSV文件不存在: {csv_path}")
        return

    print(f"正在读取CSV文件: {csv_path}")
    rows = []
    with csv_path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)

    print(f"读取到 {len(rows)} 条岗位数据")

    container = create_service_container()
    with SessionLocal() as db:
        print("正在导入岗位数据...")
        imported = await container.job_import_service.import_rows(db, rows, generate_profiles=False)
        print(f"成功导入 {len(imported)} 条岗位数据")

        # 为所有导入的岗位生成画像
        print("正在为岗位生成画像...")
        job_codes = [item.job_code for item in imported]
        profiles = await container.job_import_service.generate_profiles(db, job_codes)
        print(f"成功生成 {len(profiles)} 个岗位画像")

    print("岗位数据导入完成！")


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import *  # noqa: F401,F403
from app.services.bootstrap import create_service_container, initialize_demo_data


async def main() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
    container = create_service_container()
    with SessionLocal() as db:
        await initialize_demo_data(db, container)
    print("CareerPilot 演示数据初始化完成")


if __name__ == "__main__":
    asyncio.run(main())

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.bootstrap import create_service_container


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh aggregated job profiles from current postings.")
    parser.add_argument(
        "--profile-provider",
        choices=("mock", "ernie"),
        default="ernie",
        help="LLM provider used for this refresh run.",
    )
    parser.add_argument(
        "--titles",
        nargs="*",
        help="Optional specific normalized titles to refresh. Defaults to all current titles.",
    )
    parser.add_argument(
        "--titles-file",
        help="Optional UTF-8 text file with one normalized title per line.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    os.environ["LLM_PROVIDER"] = args.profile_provider
    if args.profile_provider == "ernie":
        os.environ["JOB_PROFILE_MOCK_FALLBACK_ENABLED"] = "false"

    titles = list(args.titles or [])
    if args.titles_file:
        titles.extend(
            [
                line.strip()
                for line in Path(args.titles_file).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        )
    if titles:
        titles = list(dict.fromkeys(titles))

    container = create_service_container()

    with SessionLocal() as db:
        profiles = await container.job_import_service.generate_aggregated_profiles(db, titles=titles or None)

    print(f"Profile refresh provider: {args.profile_provider}")
    print(f"Generated profiles: {len(profiles)}")
    if titles:
        print(f"Requested titles: {len(titles)}")


if __name__ == "__main__":
    asyncio.run(main())

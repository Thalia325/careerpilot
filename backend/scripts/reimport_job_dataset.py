from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.bootstrap import create_service_container
from app.services.reference import (
    get_job_dataset_metadata,
    load_job_graph_seed,
    load_job_postings_dataset,
    resolve_job_dataset_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reimport CareerPilot job dataset.")
    parser.add_argument(
        "--dataset",
        help="Path to the official A13 job dataset (.xls/.xlsx/.csv). Defaults to JOB_DATASET_PATH.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear existing job postings, profiles, and derived match/report data before import.",
    )
    parser.add_argument(
        "--profile-provider",
        choices=("mock", "ernie"),
        help="Temporarily override LLM provider for profile generation during this import only.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.profile_provider:
        os.environ["LLM_PROVIDER"] = args.profile_provider
    dataset_path = resolve_job_dataset_path(args.dataset)
    metadata = get_job_dataset_metadata(str(dataset_path))
    rows = load_job_postings_dataset(str(dataset_path))

    print(f"Using dataset: {metadata['path']}")
    print(f"Detected source: {metadata['source']}")
    print(f"Raw rows loaded: {metadata['raw_row_count']}")
    print(f"Filtered rows loaded: {metadata['filtered_row_count']}")
    print(f"Excluded rows: {metadata['excluded_row_count']}")
    if args.profile_provider:
        print(f"Profile generation provider override: {args.profile_provider}")

    Base.metadata.create_all(bind=engine)
    container = create_service_container()
    await container.job_import_service.graph_provider.load_seed(load_job_graph_seed())

    with SessionLocal() as db:
        result = await container.job_import_service.reimport_dataset(
            db,
            rows,
            clear_existing=not args.keep_existing,
        )

    print(f"Imported rows: {result['row_count']}")
    print(f"Imported unique postings: {result['posting_count']}")
    print(f"Generated profiles: {result['profile_count']}")


if __name__ == "__main__":
    asyncio.run(main())

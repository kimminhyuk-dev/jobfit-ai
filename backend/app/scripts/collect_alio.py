"""
Run ALIO recruitment collection from the command line.

Example:
    python -m app.scripts.collect_alio --display 100
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.database import SessionLocal
from app.services.alio_collection_service import (
    AlioCollectionError,
    AlioCollectionService,
)


def main() -> int:
    args = _parse_args()
    params = {
        "keyword": args.keyword,
        "start_page": args.start_page,
        "max_pages": args.max_pages,
        "display": args.display,
        "idempotency_key": args.idempotency_key or _make_idempotency_key(),
    }

    try:
        with SessionLocal() as db:
            run = AlioCollectionService(db).collect_jobs(
                params=params,
                triggered_by=args.triggered_by,
                idempotency_key=params["idempotency_key"],
            )
    except AlioCollectionError as exc:
        print(f"ALIO collection failed: {exc}", file=sys.stderr)
        return 1

    _print_run(run)
    return 0 if run.status in {"SUCCESS", "PARTIAL_SUCCESS"} else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect ALIO recruitment postings without logging in to /docs.",
    )
    parser.add_argument("--keyword", default=None, help="Optional title keyword.")
    parser.add_argument("--start-page", type=int, default=1, help="First page number.")
    parser.add_argument("--max-pages", type=int, default=1, help="Number of pages.")
    parser.add_argument("--display", type=int, default=10, help="Rows per page.")
    parser.add_argument(
        "--idempotency-key",
        default=None,
        help="Optional idempotency key. Defaults to a unique CLI key.",
    )
    parser.add_argument(
        "--triggered-by",
        default="CLI",
        help="Value stored in batch_job_runs.triggered_by.",
    )
    args = parser.parse_args()

    if args.start_page < 1:
        parser.error("--start-page must be at least 1")
    if not 1 <= args.max_pages <= 10:
        parser.error("--max-pages must be between 1 and 10")
    if not 1 <= args.display <= 100:
        parser.error("--display must be between 1 and 100")
    return args


def _make_idempotency_key() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    return f"alio-cli-{timestamp}"


def _print_run(run: Any) -> None:
    print(f"run_id={run.run_id}")
    print(f"job_code={run.job_code}")
    print(f"status={run.status}")
    print(f"collected_count={run.collected_count}")
    print(f"inserted_count={run.inserted_count}")
    print(f"updated_count={run.updated_count}")
    print(f"skipped_count={run.skipped_count}")
    print(f"failed_count={run.failed_count}")
    if run.error_code:
        print(f"error_code={run.error_code}")
    if run.error_message:
        print(f"error_message={run.error_message}")


if __name__ == "__main__":
    raise SystemExit(main())

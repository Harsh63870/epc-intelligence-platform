#!/usr/bin/env python3
"""Batch ingest all files from data/ into Postgres + ChromaDB."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal, init_db  # noqa: E402
from app.services.seed_service import run_full_seed  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        result = run_full_seed(db)
        print("Seed complete:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

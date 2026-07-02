#!/usr/bin/env python3
"""Run golden compliance test cases against seeded specifications."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Golden tests always use isolated SQLite — no Docker required
os.environ["DATABASE_URL"] = "sqlite:///./golden_test.db"

from app.agents.spec_compliance_agent import check_submittal_compliance  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.services.seed_service import get_or_create_project, seed_structured_data  # noqa: E402


def main() -> int:
    print("Using database:", os.environ.get("DATABASE_URL", "default"))
    init_db()
    db = SessionLocal()
    golden_path = PROJECT_ROOT / "data" / "test_cases" / "compliance_golden.json"
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    project = get_or_create_project(db)
    seed_structured_data(db, project.id)

    passed = 0
    for case in cases:
        file_path = PROJECT_ROOT / "data" / "submittals" / case["submittal_file"]
        text = file_path.read_text(encoding="utf-8")
        result = check_submittal_compliance(
            db,
            project_id=project.id,
            vendor="Test Vendor",
            text=text,
            filename=case["submittal_file"],
        )
        nc_keys = {
            c["requirement_key"]
            for c in result["checks"]
            if c["status"] == "fail"
        }
        expected = set(case["expected_nc_keys"])
        ok = expected.issubset(nc_keys)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {case['submittal_file']}: expected {expected}, got {nc_keys}")
        if ok:
            passed += 1

    db.close()
    print(f"\n{passed}/{len(cases)} golden tests passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

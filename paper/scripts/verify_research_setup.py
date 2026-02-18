#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required_files = [
        root / "paper" / "scripts" / "generate_audit_runs.py",
        root / "paper" / "scripts" / "make_all_figures.py",
    ]

    errors = []
    for path in required_files:
        if not path.exists():
            errors.append(f"Missing required script: {path}")

    data_dir = root / "paper" / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        errors.append(f"Unable to create logging directory {data_dir}: {exc}")

    if errors:
        print("Research setup verification failed:")
        for msg in errors:
            print(f"- {msg}")
        return 1

    print("Research setup verification passed.")
    print(f"Scripts checked: {len(required_files)}")
    print(f"Logging directory ready: {data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

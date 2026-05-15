from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.storage import get_runtime_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Read Finahunt web-facing data from the configured repository.")
    parser.add_argument("kind", choices=["daily-snapshot", "low-position-workbench"])
    parser.add_argument("--date")
    args = parser.parse_args()

    repository = get_runtime_repository()
    if args.kind == "daily-snapshot":
        payload = repository.load_daily_snapshot(args.date or None)
    else:
        payload = repository.load_low_position_workbench(args.date or None)

    if payload is None:
        payload = {"dataMode": "seed", "date": args.date}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

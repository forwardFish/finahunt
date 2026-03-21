from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.runtime_schedule import run_low_position_workbench_cycle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-items-per-source", type=int, default=8)
    args = parser.parse_args()

    result = run_low_position_workbench_cycle(max_items_per_source=args.max_items_per_source)
    warehouse = result["results"]["result_warehouse"]["content"]
    orchestrator = result["results"]["low_position_orchestrator"]["content"]
    output = {
        "run_id": result["run_id"],
        "artifact_batch_dir": warehouse.get("artifact_batch_dir", ""),
        "frontend_url": "http://127.0.0.1:3021/low-position",
        "message_count": orchestrator.get("daily_message_workbench", {}).get("message_count", 0),
        "theme_count": orchestrator.get("daily_theme_workbench", {}).get("theme_count", 0),
        "status": orchestrator.get("daily_message_workbench", {}).get("status", "empty"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

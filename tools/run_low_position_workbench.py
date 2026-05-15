from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.runtime_schedule import run_low_position_workbench_cycle, run_runtime_cycle


WATCHLIST = {
    "watchlist_symbols": [],
    "watchlist_themes": ["人工智能", "机器人", "算力", "低空经济", "新能源", "医药"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance-smoke", action="store_true", help="Use built-in seed documents; do not perform live source fetch.")
    parser.add_argument("--max-items-per-source", type=int, default=8)
    args = parser.parse_args()

    if args.acceptance_smoke:
        result = run_runtime_cycle(
            schedule_name="low-position-workbench-acceptance-smoke",
            rule_version="v3",
            requested_sources=["cls-telegraph", "jiuyangongshe-live", "xueqiu-hot-spot"],
            live_fetch=False,
            user_profile=WATCHLIST,
            max_items_per_source=1,
        )
    else:
        result = run_low_position_workbench_cycle(max_items_per_source=args.max_items_per_source)

    warehouse = result["results"]["result_warehouse"]["content"]
    orchestrator = result["results"]["low_position_orchestrator"]["content"]
    db_write_status = warehouse.get("db_write_status", {"backend": "unknown", "status": "DOCUMENTED_BLOCKER"})
    output = {
        "run_id": result["run_id"],
        "artifact_batch_dir": warehouse.get("artifact_batch_dir", ""),
        "frontend_url": "http://127.0.0.1:3021/low-position",
        "latestDate": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
        "message_count": orchestrator.get("daily_message_workbench", {}).get("message_count", 0),
        "theme_count": orchestrator.get("daily_theme_workbench", {}).get("theme_count", 0),
        "status": orchestrator.get("daily_message_workbench", {}).get("status", "empty"),
        "db_write_status": db_write_status,
        "acceptance_smoke": bool(args.acceptance_smoke),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if db_write_status.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

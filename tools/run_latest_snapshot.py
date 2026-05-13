from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.runtime_schedule import run_live_event_cognition_cycle, run_runtime_cycle


WATCHLIST = {
    "watchlist_symbols": [],
    "watchlist_themes": ["????", "???", "??", "????"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance-smoke", action="store_true", help="Use built-in seed documents; do not perform live source fetch.")
    parser.add_argument("--max-items-per-source", type=int, default=8)
    args = parser.parse_args()

    if args.acceptance_smoke:
        result = run_runtime_cycle(
            schedule_name="live-event-cognition-acceptance-smoke",
            rule_version="v2",
            requested_sources=["cls-telegraph", "jiuyangongshe-live", "xueqiu-hot-spot"],
            live_fetch=False,
            user_profile=WATCHLIST,
            max_items_per_source=1,
        )
    else:
        result = run_live_event_cognition_cycle(
            user_profile=WATCHLIST,
            max_items_per_source=args.max_items_per_source,
        )

    warehouse = result["results"]["result_warehouse"]["content"]
    run_id = result["run_id"]
    output = {
        "run_id": run_id,
        "artifact_batch_dir": warehouse.get("artifact_batch_dir", ""),
        "frontend_url": "http://127.0.0.1:3021/",
        "low_position_count": len(
            result["results"]["low_position_discovery"]["content"].get("low_position_opportunities", [])
        ),
        "fermenting_theme_count": len(
            result["results"]["fermenting_theme_feed"]["content"].get("fermenting_theme_feed", [])
        ),
        "acceptance_smoke": bool(args.acceptance_smoke),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

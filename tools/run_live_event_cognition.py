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
    "watchlist_themes": ["人工智能", "机器人", "算力", "低空经济"],
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

    output = {
        "low_position_opportunities": result["results"]["low_position_discovery"]["content"].get("low_position_opportunities", []),
        "fermenting_theme_feed": result["results"]["fermenting_theme_feed"]["content"].get("fermenting_theme_feed", []),
        "daily_review": result["results"]["daily_review"]["content"],
        "artifact_batch_dir": result["results"]["result_warehouse"]["content"].get("artifact_batch_dir", ""),
        "acceptance_smoke": bool(args.acceptance_smoke),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

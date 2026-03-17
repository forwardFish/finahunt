from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflows.runtime_schedule import run_live_event_cognition_cycle


def main() -> int:
    result = run_live_event_cognition_cycle(
        user_profile={
            "watchlist_symbols": [],
            "watchlist_themes": ["人工智能", "机器人", "算力", "低空经济"],
        },
        max_items_per_source=8,
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
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

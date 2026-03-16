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
        }
    )
    output = {
        "fermenting_theme_feed": result["results"]["fermenting_theme_feed"]["content"].get("fermenting_theme_feed", []),
        "daily_review": result["results"]["daily_review"]["content"],
        "artifact_batch_dir": result["results"]["result_warehouse"]["content"].get("artifact_batch_dir", ""),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

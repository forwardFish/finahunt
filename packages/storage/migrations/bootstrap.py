from __future__ import annotations

import json

from packages.storage import get_runtime_repository


def main() -> int:
    status = get_runtime_repository().bootstrap()
    print(json.dumps(status.to_dict(), ensure_ascii=False, indent=2))
    return 0 if status.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

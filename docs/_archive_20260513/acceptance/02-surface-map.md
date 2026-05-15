# 02 Surface Map - expanded acceptance pass

## Route surfaces

| Surface ID | Type | Path/name | User purpose | Related req | UI ref | Data source | States | Acceptance | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WEB-001 | route | `/` | Home/news/topic entry | R-AF-001 | contact sheet + home.html | daily snapshot data lib | loading/empty/error/success via safe state summaries | default + date query route smoke + screenshot | `home.png`, `route-smoke.json` |
| WEB-002 | route | `/fermentation` | Topic fermentation board | R-AF-001 | topics/topic-detail refs | daily snapshot data lib | loading/empty/error/success | route smoke + screenshot | `fermentation.png` |
| WEB-003 | route | `/research` | Low-position sample/research library | R-AF-001 | samples/search refs | low-position workbench lib | loading/empty/error/success | route smoke + screenshot | `research.png` |
| WEB-004 | route | `/workbench` | Cross-sectional workbench | R-AF-001/R-AF-003 | search/home refs | daily snapshot + low-position libs | loading/empty/error/success | route smoke + form target smoke | `workbench.png` |
| WEB-005 | route | `/low-position` | Preserved low-position entry | R-AF-001 | board/workbench refs | low-position workbench lib | loading/empty/error/success | route smoke + screenshot | `low-position.png` |
| WEB-006 | route | `/sprint-2` | Backward-compatible acceptance entry | R-AF-001 | dashboard contract | both data libs | loading/empty/error/success | route smoke + screenshot | `sprint-2.png` |

## API and integration surfaces

| Surface ID | Type | Path/name | Purpose | Related req | Data/workflow | Acceptance | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| API-001 | endpoint | `GET /api/daily-snapshot` | Read current or dated daily snapshot | R-AF-002 | `loadDailySnapshot` | 4 contract cases | `api-smoke.json` |
| API-002 | endpoint | `POST /api/refresh-latest` | Trigger latest snapshot Python run | R-AF-002/R-AF-003 | `tools/run_latest_snapshot.py` | POST + method guard | `api-smoke.json`, `python-command-smoke.json` |
| API-003 | endpoint | `POST /api/run-low-position` | Trigger low-position workflow | R-AF-002/R-AF-003 | `tools/run_low_position_workbench.py` | POST + method guard | `api-smoke.json`, `python-command-smoke.json` |
| INT-001 | frontend fetch | `/api/refresh-latest` | Refresh button integration | R-AF-003 | client fetch -> API route | fetch target match | `integration-smoke.json` |
| INT-002 | frontend fetch | `/api/run-low-position` | Low-position button integration | R-AF-003 | client fetch -> API route | fetch target match | `integration-smoke.json` |
| INT-003 | command | `tools/run_live_event_cognition.py` | runtime cognition command surface | R-AF-003 | Python runtime | command JSON smoke | `python-command-smoke.json` |

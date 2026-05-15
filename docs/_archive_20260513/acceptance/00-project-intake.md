# 00 Project Intake - expanded acceptance pass

Generated: 2026-05-13 11:18:56

## Safety baseline

- `git status` was captured before this pass; existing previous-round task YAML and untracked acceptance/UI/workspace material were preserved.
- No `git reset`, `git clean`, force push, deployment, production config change, or reference material deletion was performed.
- The second pass was opened because the previous 6 route / 3 API wording under-described actual integration coverage.

## Detected web routes

- `/`
- `/fermentation`
- `/low-position`
- `/research`
- `/sprint-2`
- `/workbench`

## Detected Next API route files

- `/api/daily-snapshot` methods=['GET'] file=`apps\web\src\app\api\daily-snapshot\route.ts`
- `/api/refresh-latest` methods=['POST'] file=`apps\web\src\app\api\refresh-latest\route.ts`
- `/api/run-low-position` methods=['POST'] file=`apps\web\src\app\api\run-low-position\route.ts`

Important finding: the codebase currently has exactly 3 Next API route files. The acceptance suite now tests 8 API contract cases against those 3 route files instead of reporting only a raw route count.

## Frontend/backend integration surfaces

Client fetch targets:
- `/api/refresh-latest`
- `/api/run-low-position`

GET form targets:
- `/`
- `/fermentation`
- `/low-position`
- `/research`
- `/workbench`

Python workflow command surfaces:
- `C:\Python313\python.exe tools/run_latest_snapshot.py`
- `C:\Python313\python.exe tools/run_low_position_workbench.py`
- `C:\Python313\python.exe tools/run_live_event_cognition.py`

## Newly found unfinished item fixed in this pass

Hard-coded mojibake survived in UI helper/component text. It affected status labels, source labels, date controls, pager labels, and action-button state messages. This pass fixed those strings and expanded smoke detection to catch them.

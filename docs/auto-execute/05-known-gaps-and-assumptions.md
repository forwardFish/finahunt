# Known Gaps and Assumptions

Generated: 2026-05-13 19:31:42 +0800

| Item | Classification | Details | Evidence |
|---|---|---|---|
| `/sprint-2` redirect-only wording conflict | PRODUCT_DECISION_REQUIRED | Docs request redirect to `/workbench`; implementation keeps independent compatibility page. | `redirect-final-url.json` |
| `/low-position` redirect-only wording conflict | PRODUCT_DECISION_REQUIRED | Docs request redirect to `/research`; implementation keeps independent compatibility page. | `redirect-final-url.json` |
| Editorial/pixel-level UI match | MANUAL_REVIEW_REQUIRED | Objective smoke passes; exact financial-publication taste requires human review. | `visual-smoke.md`, screenshots |
| Production/live source acceptance | DEFERRED | Safety forbids production DB/secrets/external production access; local seed smoke used. | `python-command-smoke.json` |

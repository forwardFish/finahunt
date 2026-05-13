# Visual Acceptance Checklist

Generated: 2026-05-13 19:31:42 +0800

| Check | Route / Surface | Automatic status | Manual status | Evidence |
|---|---|---|---|---|
| Desktop screenshots | four main pages plus compatibility routes | PASS | N/A | `screenshots/desktop-*.png` |
| Mobile screenshots | four main pages plus compatibility routes | PASS | N/A | `screenshots/mobile-*.png` |
| Stable H1/page identity | 6 routes | PASS | N/A | `screenshot-capture.json` |
| No mojibake / no Next error | 6 routes | PASS | manual copy sample recommended | `route-smoke.json`, `screenshot-capture.json` |
| No horizontal overflow | desktop/mobile | PASS | N/A | `screenshot-capture.json` |
| ????????? | `/` | PASS via forbidden text | MANUAL_REVIEW_REQUIRED for density/taste | screenshots |
| `/fermentation` ?????? | `/fermentation` | PASS objective | MANUAL_REVIEW_REQUIRED | screenshots vs topic refs |
| `/research` dossier ?? | `/research` | PASS objective | MANUAL_REVIEW_REQUIRED | screenshots vs sample refs |
| `/workbench` ??????? | `/workbench` | PASS objective | MANUAL_REVIEW_REQUIRED | screenshots vs search/home refs |

Manual review remains required for exact financial-publication feel, spacing, hierarchy, and pixel-level match to `docs/UI/contact-sheet.png`; these are not honestly automatable.

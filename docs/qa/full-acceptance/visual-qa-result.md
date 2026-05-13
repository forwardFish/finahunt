# Visual QA Result - Ralph continuation

Generated: 2026-05-13 16:27:40 +0800

## Result

PASS with manual taste-review remaining.

## Screenshot evidence

| Route | Desktop | Mobile | Automated result |
| --- | --- | --- | --- |
| `/` | `docs/qa/full-acceptance/screenshots/desktop-home.png` | `docs/qa/full-acceptance/screenshots/mobile-home.png` | PASS |
| `/fermentation` | `docs/qa/full-acceptance/screenshots/desktop-fermentation.png` | `docs/qa/full-acceptance/screenshots/mobile-fermentation.png` | PASS |
| `/research` | `docs/qa/full-acceptance/screenshots/desktop-research.png` | `docs/qa/full-acceptance/screenshots/mobile-research.png` | PASS |
| `/workbench` | `docs/qa/full-acceptance/screenshots/desktop-workbench.png` | `docs/qa/full-acceptance/screenshots/mobile-workbench.png` | PASS |
| `/low-position` | `docs/qa/full-acceptance/screenshots/desktop-low-position.png` | `docs/qa/full-acceptance/screenshots/mobile-low-position.png` | PASS |
| `/sprint-2` | `docs/qa/full-acceptance/screenshots/desktop-sprint-2.png` | `docs/qa/full-acceptance/screenshots/mobile-sprint-2.png` | PASS |

## Automated visual checks completed

- Opened all 6 actual routes on local Next server.
- Captured desktop and mobile full-page screenshots.
- Checked final URL, H1 presence, route identity text, visible action buttons, internal links, mojibake markers, Next error markers, and horizontal overflow.
- Final screenshot gate reported 12/12 PASS.

## Known visual limitations

- The UI reference set contains multiple HTML reference pages and a contact sheet; pixel-perfect diff is intentionally not used.
- Manual product taste review remains outside the automated pass/fail gate.

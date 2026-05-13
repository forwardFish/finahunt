# Visual Smoke
Generated: 2026-05-13T16:26:28+0800

Automated checks cover final URL, H1, required identity text, mojibake, Next error markers, and horizontal overflow. Editorial tone remains MANUAL_REVIEW_REQUIRED.

- desktop / -> PASS | final=http://127.0.0.1:3021/?date=2026-05-13 | h1=把公开资讯、题材热度和研究入口放回同一张金融信息首页。 | screenshot=docs\qa\full-acceptance\screenshots\desktop-home.png
- desktop /fermentation -> PASS | final=http://127.0.0.1:3021/fermentation?date=2026-05-13 | h1=像题材栏目页一样追踪主线热度、阶段和证据。 | screenshot=docs\qa\full-acceptance\screenshots\desktop-fermentation.png
- desktop /research -> PASS | final=http://127.0.0.1:3021/research?date=2026-05-13 | h1=把低位机会做成可浏览的研究样例库。 | screenshot=docs\qa\full-acceptance\screenshots\desktop-research.png
- desktop /workbench -> PASS | final=http://127.0.0.1:3021/workbench?date=2026-05-13 | h1=总编辑台：主线、低位、消息、证据放在一个可检索页面。 | screenshot=docs\qa\full-acceptance\screenshots\desktop-workbench.png
- mobile / -> PASS | final=http://127.0.0.1:3021/?date=2026-05-13 | h1=把公开资讯、题材热度和研究入口放回同一张金融信息首页。 | screenshot=docs\qa\full-acceptance\screenshots\mobile-home.png
- mobile /fermentation -> PASS | final=http://127.0.0.1:3021/fermentation?date=2026-05-13 | h1=像题材栏目页一样追踪主线热度、阶段和证据。 | screenshot=docs\qa\full-acceptance\screenshots\mobile-fermentation.png
- mobile /research -> PASS | final=http://127.0.0.1:3021/research?date=2026-05-13 | h1=把低位机会做成可浏览的研究样例库。 | screenshot=docs\qa\full-acceptance\screenshots\mobile-research.png
- mobile /workbench -> PASS | final=http://127.0.0.1:3021/workbench?date=2026-05-13 | h1=总编辑台：主线、低位、消息、证据放在一个可检索页面。 | screenshot=docs\qa\full-acceptance\screenshots\mobile-workbench.png

## Classification
- Automated screenshot capture: PASS if all rows above are PASS.
- Editorial visual tone and subtle overlap/aesthetic judgment: MANUAL_REVIEW_REQUIRED.
- This manual review flag is not treated as an automated PASS claim.

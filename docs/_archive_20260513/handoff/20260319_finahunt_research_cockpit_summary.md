# Finahunt Research Cockpit Summary

## Summary

- Date: 2026-03-19
- Scope: `finahunt` 首页 `/` 与工作台 `/sprint-2`
- Goal: 把页面升级为“产品化研究入口 + 深色研究工作台”，并用 `browse -> plan-design-review -> browse -> design-review` 跑完整验收链

## Frontend Outcome

- 首页 `/` 已重构为产品化研究入口：
  - 今日主线
  - 研究优先级
  - 运行来源与批次
  - 主题入口
  - 事件入口
  - 通往 Sprint 2 的桥接 CTA
- `/sprint-2` 已重构为深色研究工作台：
  - hero / view controls
  - decision strip
  - stage strip
  - fermentation board
  - low-position research board
  - matrix view
  - evidence tape
  - risk & method boundary
- 公共样式已统一为深海军蓝 + 青色 + 薄荷 + 琥珀的研究产品视觉系统
- 布局、首页、工作台与刷新按钮文案已统一为稳定的中文界面

## Agentsystem Outcome

- `design_review_framework.py`
  - 新增 `finahunt_research_cockpit` benchmark profile
  - 支持 `finahunt` 路由默认 scope: `/`, `/sprint-2`
  - 将 `/sprint-*` 识别为 `dashboard`
  - 为研究工作台增加 `views / matrix / risk / evidence / refresh` 信号评分
- `playwright_browser_runtime.py`
  - 结构化观测已覆盖：
    - `view_controls`
    - `matrix_headers`
    - `risk_labels`
    - `evidence_labels`
    - `refresh_state`
    - `refresh_message`
- 回归测试通过：
  - `python -m unittest tests.test_browser_runtime -v`
  - `python -m unittest tests.test_design_review_framework -v`

## Validation

- 前端构建：
  - `npm run build` 通过
- 真实刷新：
  - `POST http://127.0.0.1:3004/api/refresh-latest`
  - result:
    - `ok = true`
    - `run_id = run-60726130f6e9`
    - `artifact_batch_dir = workspace/artifacts/runtime/run-60726130f6e9`
    - `latestDate = 2026-03-19`
- 刷新失败态：
  - 使用 `PYTHON_BIN=python_not_found` 启动隔离预览 `http://127.0.0.1:3005`
  - 真实点击首页刷新按钮后，页面进入 `data-refresh-state = error`
  - 错误文案为：
    - `抓取失败：spawn python_not_found ENOENT。请稍后重试，或检查本地运行脚本与公开源连接状态。`
- Browse:
  - `browser_qa_passed = true`
  - `browser_qa_health_score = 100`
- Design Review:
  - `design_review_passed = true`
  - no blocking findings

## Final Scores

- `information_architecture = 9`
- `interaction_state_coverage = 9`
- `user_journey_emotional_arc = 8`
- `ai_slop_risk = 8`
- `design_system_alignment = 9`
- `responsive_accessibility = 9`
- `unresolved_design_decisions = 10`

## Evidence

- Preview:
  - `http://127.0.0.1:3004`
  - `http://127.0.0.1:3004/sprint-2`
  - failure-state preview:
    - `http://127.0.0.1:3005`
- Browser QA report:
  - `.meta/finahunt/browser_qa/browser_qa_report.md`
- Plan design review report:
  - `.meta/finahunt/plan_design_review/design_review_report.md`
- Design review report:
  - `.meta/finahunt/qa_design_review/qa_design_review_report.md`
- Before/after report:
  - `.meta/finahunt/qa_design_review/before_after_report.md`
- Screenshots:
  - `.meta/finahunt/browser_runtime/screenshots/current-1-home-desktop.png`
  - `.meta/finahunt/browser_runtime/screenshots/current-1-home-mobile.png`
  - `.meta/finahunt/browser_runtime/screenshots/current-2-sprint-2-desktop.png`
  - `.meta/finahunt/browser_runtime/screenshots/current-2-sprint-2-mobile.png`
  - `.meta/finahunt/browser_runtime/screenshots/refresh-failure-home-desktop.png`

## Non-blocking Notes

- 首页不是目录站，因此 benchmark 不再要求 `search / categories` 成为硬性通过项；但评分里仍把它们当作“可选增强项”，所以首页最终停在 `information_architecture = 9`、`ai_slop_risk = 8`
- 当前结果已经满足 `finahunt` 研究产品口径下的通过门槛，无 blocking findings

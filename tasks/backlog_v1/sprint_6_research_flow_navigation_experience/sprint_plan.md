# Sprint 6 规划

## Sprint 名称

页面分类重构与完整 UI/browser 验收

## Sprint 目标

把 `finahunt` 前端按研究流程拆成独立页面，建立清晰的导航契约和兼容路由，同时为后续 `browse -> plan-design-review -> design-consultation -> build -> design-review -> qa -> acceptance_gate` 提供正式 story 入口。

## 顶层页面

- `/` 今日入口
- `/fermentation` 主线发酵
- `/research` 低位研究
- `/workbench` 工作台总览

## 兼容路由

- `/sprint-2 -> /workbench`
- `/low-position -> /research`

## Epic 总览

| Epic | Story 数 | 核心职责 |
| :--- | :--- | :--- |
| Epic 6.1 Information Architecture | 1 | 信息架构、线框、导航契约、browse 基线 |
| Epic 6.2 Separated Research Pages | 3 | 今日入口、主线发酵、低位研究拆页实现 |
| Epic 6.3 Workbench Compatibility and Acceptance | 1 | 工作台总览、兼容路由、完整浏览验收 |

## 推荐执行顺序

1. S6-001
2. S6-002
3. S6-003
4. S6-004
5. S6-005

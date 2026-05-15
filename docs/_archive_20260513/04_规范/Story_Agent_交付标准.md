# Finahunt Story Agent 流程接入说明

最后更新：2026-03-20

## 1. 唯一标准来源

`finahunt` 不再单独维护一套 Story / Sprint Agent 正式流程标准。

唯一正式标准以 `agentsystem` 为准：

- `D:/lyh/agent/agent-frame/agentsystem/docs/standards/gstack_platform_migration_spec.md`
- `D:/lyh/agent/agent-frame/agentsystem/docs/standards/story_sprint_agent_workflow_standard.md`

本文件只负责说明 `finahunt` 的接入方式、默认映射和 repo-specific 例外。

## 2. 默认接入规则

`finahunt` 后续 Story 默认按 `agentsystem` 强制矩阵执行：

- 新需求 / 新 Epic / 新 Sprint：
  - `office-hours -> plan-ceo-review -> plan-eng-review`
- 普通后端 / runtime Story：
  - `Requirement -> plan-eng-review -> Builder -> Code Style Reviewer -> Reviewer -> qa 或 qa-only -> Code Acceptance -> Acceptance Gate -> Doc Writer`
- 前端 / 页面 Story：
  - `Requirement -> browse -> design-consultation -> plan-design-review -> Builder -> Reviewer -> browse(local evidence via qa chain) -> design-review -> qa -> Acceptance -> Doc Writer`
- Bug / 回归修复：
  - `investigate -> Builder/Fixer -> Reviewer -> qa -> Acceptance -> Doc Writer`
- Sprint 收尾：
  - `ship -> document-release -> retro`

## 3. Finahunt Repo-Specific 例外

- `finahunt` 以 runtime / data / ranking / artifact warehouse 为主，默认多数 Story 归类为后端或 runtime Story。
- 只有当 Story 明确涉及可视页面、浏览器交互、登录态验证时，才强制进入前端专项链。
- `workspace/artifacts/runtime/` 属于运行结果仓，不得因流程迁移被批量删除或重写。
- `tasks/story_status_registry.json` 仍视为人工验证证据的一部分，流程接入不得覆盖已有手工证据。

## 4. 任务字段映射建议

在 `finahunt` 接入 `agentsystem` 时，任务载荷至少补齐这些字段：

- `story_kind`
- `risk_level`
- `has_browser_surface`
- `bug_scope`
- `investigation_context`
- `release_scope`
- `doc_targets`
- `workflow_enforcement_policy`

推荐默认值：

- 数据链路 / 图谱 / 排名类 Story：
  - `story_kind=backend`
  - `has_browser_surface=false`
- 回归修复：
  - `bug_scope=regression`
  - `workflow_enforcement_policy=gstack_strict`
- Sprint close：
  - `doc_targets=["docs", "tasks", "workspace/artifacts/runtime"]`

## 5. 完成记账口径

`finahunt` 后续必须把“结果完成”和“流程完成”分开记账：

- `implemented`
- `verified`
- `agentized`
- `accepted`

如果只有代码落地但没有跑完要求的 Agent 链，状态只能算：

- 已实现
- 但未完全 Agent 化

## 6. 迁移要求

后续如果 `finahunt` 要新增自己的流程说明：

- 只能写 repo-specific exception
- 不能重新定义一套独立标准
- 必须显式回链到 `agentsystem` 正式标准

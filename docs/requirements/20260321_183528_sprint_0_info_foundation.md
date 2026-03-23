# sprint_0_info_foundation

## Context
- Project: finahunt
- Delivery mode: auto
- CEO review mode: hold_scope
- Source requirement file: inline input

## User Problem
# Sprint 0 规划

## Target Audience
The primary product operators and analysts who depend on this sprint outcome.

## Requirement Summary
# Sprint 0 规划

## Sprint 名称
信息底座与治理基础

## Sprint 目标
把 Finahunt 的资讯接入规则、统一数据契约、合规治理和运行追踪底座打稳，保证后续“潜在题材催化结构化挖掘”有稳定输入和可审计输出。

## 业务边界

### 做什么
- 固化资讯源注册表与接入规范
- 固化原始资讯、标准化资讯、事件对象的统一结构
- 固化合规输出规则、风险提示和事件状态
- 建立 traceability 与 gate registry
- 打通最小 runtime graph 与 runtime schedule 输入输出
- 补齐人工校正记录和 final gate 交付产物

### 不做什么
- 不在 Sprint 0 做完整题材识别和排序逻辑
- 不在 Sprint 0 做用户页面
- 不在 Sprint 0 做通知与研究归档自动化

## Epic 总览

| Epic | Story 数 | 核心职责 |
| :--- | :--- | :--- |
| Epic 0.1 Source Contract | 3 | 定义资讯源、统一 schema 与合规输出契约 |
| Epic 0.2 Runtime Governance | 3 | 建立 trace、gate、runtime 基线和人工介入底座 |

## 推荐执行顺序

1. S0-001
2. S0-002
3. S0-003
4. S0-004
5. S0-005
6. S0-006

Sprint sprint_0_info_foundation should deliver the following story goals in one coordinated cycle:
- 梳理并固化 Finahunt MVP 允许接入的合规资讯源、刷新策略和字段约束，建立统一 source registry 基线。
- 定义 RawNewsItem、NormalizedNewsItem 和基础证据片段的统一结构，给后续清洗和事件抽取提供稳定输入。
- 定义事件对象、状态字段和合规输出要求，让后续催化结果有明确边界。
- 把需求、规则、运行节点和 final gate 的追踪关系定义清楚，保证后续流程可审计。
- 让 runtime_graph 与 runtime_schedule 使用统一输入输出结构，形成最小可运行骨架。
- 为 Finahunt 的运行链路补齐人工校正记录和 final gate 交付物，让后续业务闭环可以人工介入。

## Product Constraints
- Follow the formal story execution matrix.
- Do not skip review, QA, or sprint close evidence.

## Success Signals
- Every story in the sprint completes with formal evidence.
- Sprint-level framing, closeout, and acceptance artifacts are recorded.

## CEO Mode Decision
- Selected mode: hold_scope
- No scope expansion was auto-accepted.

## System Audit Snapshot
- No major UI scope detected from this requirement.
- Office-hours framing is available and should be treated as upstream context.
- Constraint count: 2 | Success signals: 2.

# 合规资讯源接入 Agent 体系完整规范手册

## 1. 目的

本手册把 [Agent体系 - 需求追踪矩阵&落地规范.md](./Agent%E4%BD%93%E7%B3%BB%20-%20%E9%9C%80%E6%B1%82%E8%BF%BD%E8%B8%AA%E7%9F%A9%E9%98%B5%26%E8%90%BD%E5%9C%B0%E8%A7%84%E8%8C%83.md) 中的规划，收敛为一套仓库内可执行、可追溯、可校验的规范体系。规范分为两层：

1. 人类可读规范：本手册及配套附录文档。
2. 机器可读规范：`config/spec/` 下的追踪、门禁、契约、影响分析文件。

## 2. 规范源优先级

1. [远景目标.md](../01_%E6%88%98%E7%95%A5/%E8%BF%9C%E6%99%AF%E7%9B%AE%E6%A0%87.md)
2. [mvp.md](../02_MVP/mvp.md)
3. [mvp功能.md](../02_MVP/mvp%E5%8A%9F%E8%83%BD.md)
4. [Agent 体系设计文档 v1.0 正式落地版.md](../03_%E6%9E%B6%E6%9E%84/Agent%20%E4%BD%93%E7%B3%BB%E8%AE%BE%E8%AE%A1%E6%96%87%E6%A1%A3%20v1.0%20%E6%AD%A3%E5%BC%8F%E8%90%BD%E5%9C%B0%E7%89%88.md)
5. [Agent体系 - 需求追踪矩阵&落地规范.md](./Agent%E4%BD%93%E7%B3%BB%20-%20%E9%9C%80%E6%B1%82%E8%BF%BD%E8%B8%AA%E7%9F%A9%E9%98%B5%26%E8%90%BD%E5%9C%B0%E8%A7%84%E8%8C%83.md)
6. `config/spec/traceability.yaml`
7. `config/spec/agent_contract_registry.json`
8. `config/spec/gate_registry.yaml`

当文档与代码冲突时，先修正 `config/spec/` 的机器规范，再修正文档说明，最后调整代码。

## 3. 系统目标

### 3.1 总目标

实现“合规资讯源接入”全流程 Agent 自主执行，用户只负责：

- 规则定义
- 关键审批
- 结果检查

### 3.2 三平面目标

- Build Plane：完成需求解析、规则落地、架构设计、契约定义、开发、评审、测试、部署和发布闭环。
- Runtime Plane：完成资讯抓取、运行时合规守门、标准化和审计闭环。
- Governance Plane：完成标准统一、策略执行、全链路审计、量化评估和最终决策支撑。

### 3.3 最终决策目标

Final Gate 必须输出唯一明确结论：`PASS`、`PASS_WITH_NOTES`、`BLOCKED`、`RETURN_FOR_REWORK`。

## 4. 边界

### 4.1 人类边界

用户仅承担 `Rule Owner`、`Approval Owner`、`Result Checker` 三个角色，不参与任务拆解、代码实现、测试执行、部署、排障和中间结果修改。

### 4.2 Agent 边界

- 一个 Agent 只负责一个职责。
- 所有输入输出必须结构化。
- 不允许跨 Agent 越权写入非本阶段结果。
- 不允许未经审批跳过 Human Approval Checkpoint。

### 4.3 平面边界

- Build Plane 不承担日常抓取。
- Runtime Plane 不承担从 0 到 1 的开发交付。
- Governance Plane 不直接替代业务执行，只做标准、合规、审计、评估和放行支撑。

## 5. 机器规范落地

### 5.1 追踪

`config/spec/traceability.yaml` 是目标、边界、设计、配置、测试之间的总索引。

### 5.2 契约

`config/spec/agent_contract_registry.json` 是所有 Agent 的结构化注册表，包含：

- plane
- module
- class_name
- stage
- input_contract
- output_contract
- acceptance
- config_refs
- test_refs

### 5.3 门禁

`config/spec/gate_registry.yaml` 定义四级强制门禁：

1. `vision_to_mvp`
2. `mvp_to_orchestration`
3. `orchestration_to_code`
4. `code_to_acceptance`

### 5.4 影响分析

`config/spec/impact_analysis_template.json` 是新增功能时必须填写的模板。任何新增功能如果：

- 超出 MVP 边界
- 改变合规假设
- 影响未知 Agent
- 无法定位设计依据

则禁止推进。

## 6. 执行要求

### 6.1 开发前

- 先更新 `config/spec/traceability.yaml`
- 再更新 `config/spec/agent_contract_registry.json`
- 再更新影响分析记录

### 6.2 开发中

- 代码必须映射到明确阶段和 Agent
- 配置必须可追溯到规则版本
- 所有结果必须可回溯到 `trace_id`

### 6.3 开发后

必须通过以下命令才算完成：

```bash
python tools/gate_check/validate_norms.py
python -m compileall agents packages graphs workflows tests tools
python -m pytest
python -c "from workflows.build_workflow import run_build_workflow; print(run_build_workflow('validation')['results']['final_gate']['content']['final_gate_decision'])"
```

## 7. 当前仓库执行状态

当前仓库已经具备：

- 三平面 Agent 骨架
- LangGraph 图定义
- Build 到 Final Gate 的 happy path 闭环
- Runtime 执行闭环
- 基础测试与执行校验

本轮新增的是“规范层执行能力”：追踪、门禁、影响分析和规范校验。

## 8. 配套文件

- [设计切片与边界附录.md](./%E8%AE%BE%E8%AE%A1%E5%88%87%E7%89%87%E4%B8%8E%E8%BE%B9%E7%95%8C%E9%99%84%E5%BD%95.md)

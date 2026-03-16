# Finahunt MVP 正式 Backlog v1.0

## Backlog 目标

这个 backlog 面向 Finahunt 的第一阶段产品落地，重点验证两件事：

1. 能否把合规金融资讯稳定转换成结构化事件流。
2. 能否把事件、题材、个股、观察池和日终复盘串成一个用户愿意使用的认知闭环。

## 优先级说明

在这个 backlog 里，底座类 sprint 仍然先做，但第一优先的业务功能是：

**潜在题材催化的结构化挖掘结果**

所以我们把它单独拆成一个更细的核心 sprint，而不是混在通用事件处理里。

## Sprint 总览

| Sprint | 名称 | Epic 数 | Story 数 | 核心目标 |
| :--- | :--- | :--- | :--- | :--- |
| Sprint 0 | 信息底座与治理基础 | 2 | 6 | 先把资讯源、数据契约、合规规则、追踪与运行基础打稳 |
| Sprint 1 | 资讯接入与信号准备 | 3 | 9 | 跑通抓取、去重、证据片段提取与候选信号准备 |
| Sprint 2 | 潜在题材催化结构化挖掘核心 | 2 | 6 | 产出真正有业务价值的潜在题材催化结构化结果 |
| Sprint 3 | 关联关系与用户排序 | 2 | 4 | 把题材结果和个股、板块、观察池用户连接起来 |
| Sprint 4 | 输出、复盘与研究闭环 | 2 | 4 | 让结构化结果真正变成用户可消费的输出和复盘资产 |

## 目录结构

```text
tasks/
  backlog_v1/
    sprint_overview.md
    sprint_0_info_foundation/
      sprint_plan.md
      execution_order.txt
      epic_0_1_source_contract.md
      epic_0_2_runtime_governance.md
      epic_0_1_source_contract/
      epic_0_2_runtime_governance/
    sprint_1_event_cognition_loop/
      sprint_plan.md
      execution_order.txt
      ...
    sprint_2_catalyst_mining_core/
      sprint_plan.md
      execution_order.txt
      ...
    sprint_3_linkage_and_ranking/
      sprint_plan.md
      execution_order.txt
      ...
    sprint_4_output_and_research_loop/
      sprint_plan.md
      execution_order.txt
      ...
```

## 当前版本结论

- Sprint 0 用来打底座，不追求页面。
- Sprint 2 是第一优先的业务价值 sprint。
- P1 和 P2 功能暂不进入当前 backlog。

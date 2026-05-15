# 合规资讯源接入Agent体系 - 需求追踪矩阵&落地规范

> 说明：原先拆成多个短文件的设计切片与边界说明，现已统一合并到 `04_规范/设计切片与边界附录.md`，本文件继续保留为需求追踪源文档。

## 一、核心目标（映射到设计/配置/测试文件）

|目标层级|具体目标内容|关联设计文件|关联配置文件|关联测试文件|
|---|---|---|---|---|
|系统总目标|实现「合规资讯源接入」全流程Agent自主执行，用户仅负责规则定义、关键节点审批、最终结果检查|`system_design.md`（设计总纲章节）|`system_config.yaml`（全局目标配置）|`goal_verification_test.py`（目标达成度验证测试）|
|Build Plane目标|把「合规资讯源接入」功能从0到1落地为可在生产稳定运行的交付物|`build_plane_design.md`（4.1章节）|`build_graph_config.json`（Build图配置）|`build_goal_test_suite.py`（开发平面目标测试套件）|
|Runtime Plane目标|保障已交付功能7×24小时稳定运行，完成定时抓取、合规校验、标准化、审计|`runtime_plane_design.md`（4.2章节）|`runtime_schedule_config.yaml`（定时调度配置）|`runtime_stability_test.py`（运行稳定性测试）|
|Governance Plane目标|贯穿全流程执行标准统一、合规管控、全链路审计、效果评估|`governance_plane_design.md`（4.3章节）|`compliance_policy_config.json`（合规策略配置）|`governance_coverage_test.py`（治理覆盖度测试）|
|Final Gate目标|输出唯一、明确的放行决策，作为用户检查结果的核心入口|`final_gate_design.md`（4.4章节）|`final_gate_rule_config.json`（决策规则配置）|`final_decision_test.py`（最终决策准确性测试）|
## 二、核心边界（映射到设计/配置/测试文件）

|边界类型|具体边界内容|关联设计文件|关联配置文件|关联测试文件|
|---|---|---|---|---|
|人类职责边界|仅承担Rule Owner/Approval Owner/Result Checker角色，不做任务拆分、代码实现等执行环节|`human_role_design.md`（1.2章节）|`human_permission_config.yaml`（人类权限配置）|`human_role_boundary_test.py`（人类职责越界校验）|
|Agent职责边界|遵循职责单一原则，一个Agent只负责一件事，无跨职责执行|`agent_boundary_design.md`（1.3章节）|`agent_role_config.json`（Agent职责配置）|`agent_responsibility_test.py`（Agent职责越界测试）|
|三平面边界|Build负责0-1建设、Runtime负责日常运行、Governance负责规则约束，职责解耦|`three_plane_design.md`（1.1章节）|`plane_isolation_config.yaml`（平面隔离配置）|`plane_boundary_test.py`（平面职责交叉校验）|
|人工审批边界|仅在生产发布前触发Human Approval Checkpoint，其余环节无人工干预|`approval_design.md`（4.5章节）|`approval_trigger_config.json`（审批触发配置）|`approval_boundary_test.py`（审批触发时机测试）|
## 三、各Agent核心信息（职责+输入输出契约+验收标准+文件映射）

### 3.1 Build Plane Agents

|Agent名称|核心职责|输入契约（结构化定义）|输出契约（结构化定义）|验收标准|关联文件映射|
|---|---|---|---|---|---|
|Feature Orchestrator Agent|全流程任务编排、子任务拆解、状态跟踪、异常回退管控|`json {"user_demand":"string","UserRuleSet":"object","system_context":"object"} `|`json {"build_plan":"object","subtask_list":"array","execution_status":"object","build_summary":"object"} `|1.需求拆解为可执行子任务；2.子Agent输入输出闭环；3.形成完整交付链路|设计：`build_plane_design.md#4.1`<br>配置：`orchestrator_config.json`<br>测试：`orchestrator_task_test.py`|
|Requirement Parsing Agent|需求语义解析、模糊点澄清、生成标准化需求规格|`json {"user_demand":"string","UserRuleSet":"object"} `|`json {"requirement_spec":"object","ambiguity_list":"array","subtask_candidates":"array","must_not_do_list":"array"} `|1.需求边界清晰；2.输出可被下游直接消费；3.无歧义表述|设计：`build_plane_design.md#4.1`<br>配置：`req_parse_rule_config.json`<br>测试：`req_parse_ambiguity_test.py`|
|Compliance Rules Agent|将合规要求转化为机器可执行规则集，版本管理|`json {"requirement_spec":"object","UserRuleSet":"object","financial_baseline":"object"} `|`json {"compliance_policy":"object","source_whitelist_policy":"object","blocking_rules":"object","rule_version":"string"} `|1.规则可直接执行；2.覆盖全流程合规校验点；3.规则可追溯版本化|设计：`build_plane_design.md#4.1`<br>配置：`compliance_rules_config.json`<br>测试：`compliance_rule_exec_test.py`|
|Source Registry Agent|维护资讯源注册表，留存合法性证明、接入配置等|`json {"compliance_policy":"object","source_official_info":"object","source_scope":"string"} `|`json {"source_registry":"object","source_legality_evidence":"string","source_access_profile":"object","source_risk_level":"string"} `|1.源分类明确；2.注册表信息完整；3.合法性证明可追溯|设计：`build_plane_design.md#4.1`<br>配置：`source_registry_config.yaml`<br>测试：`source_registry_complete_test.py`|
|Architecture Agent|设计系统架构、模块边界、数据流转、异常策略|`json {"requirement_spec":"object","compliance_policy":"object","source_registry":"object"} `|`json {"architecture_spec":"object","module_boundary":"object","data_flow_design":"object","failure_strategy":"object"} `|1.模块边界清晰；2.数据契约可落地；3.异常策略覆盖核心场景|设计：`build_plane_design.md#4.1`<br>配置：`architecture_config.json`<br>测试：`architecture_module_test.py`|
|Contract Agent|定义全系统数据/接口契约，版本管理|`json {"architecture_spec":"object","source_registry":"object","compliance_policy":"object"} `|`json {"raw_document_schema":"object","connector_contract":"object","runtime_output_contract":"object","contract_version":"string"} `|1.覆盖全流程输入输出契约；2.下游可直接对照执行；3.版本管理清晰|设计：`build_plane_design.md#4.1`<br>配置：`contract_schema.json`<br>测试：`contract_coverage_test.py`|
|Development Agent|实现连接器、抓取/标准化/合规校验逻辑，编写单元测试|`json {"architecture_spec":"object","connector_contract":"object","source_registry":"object","compliance_policy":"object"} `|`json {"build_artifacts":"string","code_package":"string","dependency_manifest":"object","unit_test_report":"object"} `|1.代码可编译运行；2.100%符合契约；3.包含错误处理/日志|设计：`build_plane_design.md#4.1`<br>配置：`dev_code_template.yaml`<br>测试：`dev_contract_compliance_test.py`|
|Review Agent|代码全维度评审，阻断不合规/不符合设计的代码|`json {"code_package":"string","architecture_spec":"object","connector_contract":"object","compliance_policy":"object"} `|`json {"review_report":"object","blocking_issues":"array","review_pass":"boolean"} `|1.阻断性问题清零后流转；2.评审覆盖全维度；3.问题定位精准|设计：`build_plane_design.md#4.1`<br>配置：`review_checklist.json`<br>测试：`review_blocking_test.py`|
|Test Agent|功能/契约/合规/可靠性测试，验证达标|`json {"code_package":"string","connector_contract":"object","UserRuleSet":"object","source_registry":"object"} `|`json {"functional_test_report":"object","compliance_test_report":"object","test_pass":"boolean"} `|1.四类测试报告完整；2.核心指标达验收阈值；3.用例可复现|设计：`build_plane_design.md#4.1`<br>配置：`test_case_config.yaml`<br>测试：`test_indicator_test.py`|
|Deploy Staging Agent|预发部署、环境验证、冒烟测试|`json {"test_reports":"object","UserRuleSet":"object","code_package":"string"} `|`json {"staging_deploy_report":"object","smoke_test_result":"object","deploy_pass":"boolean"} `|1.预发服务可用；2.监控配置正常；3.冒烟测试100%通过|设计：`build_plane_design.md#4.1`<br>配置：`staging_deploy_config.yaml`<br>测试：`staging_smoke_test.py`|
|Release Agent|生产灰度发布、监控、异常回滚|`json {"staging_deploy_report":"object","human_approval_result":"object","UserRuleSet":"object"} `|`json {"release_report":"object","rollout_log":"object","release_pass":"boolean"} `|1.灰度发布无异常；2.生产服务稳定；3.回滚策略可用|设计：`build_plane_design.md#4.1`<br>配置：`release_strategy_config.json`<br>测试：`release_rollback_test.py`|
|Build Summary Agent|汇总开发平面全流程交付物与结果|`json {"all_build_agent_outputs":"object"} `|`json {"build_summary_report":"object","full_artifact_list":"array","key_milestone_result":"object"} `|1.交付物无遗漏；2.关键节点结果清晰；3.输出可被Final Gate消费|设计：`build_plane_design.md#4.1`<br>配置：`summary_config.json`<br>测试：`build_summary_complete_test.py`|
### 3.2 Runtime Plane Agents

|Agent名称|核心职责|输入契约（结构化定义）|输出契约（结构化定义）|验收标准|关联文件映射|
|---|---|---|---|---|---|
|Source Runtime Agent|按规则定时抓取资讯源，处理基础异常|`json {"source_registry":"object","runtime_schedule":"object","raw_document_schema":"object"} `|`json {"raw_documents":"string","fetch_status_report":"object","fetch_execution_log":"object"} `|1.抓取成功率达阈值；2.输出符合RawDocument Schema；3.遵循频率限制|设计：`runtime_plane_design.md#4.2`<br>配置：`fetch_schedule_config.yaml`<br>测试：`fetch_success_rate_test.py`|
|Source Compliance Guard Agent|运行时合规校验，阻断不合规内容|`json {"raw_documents":"string","compliance_policy":"object","source_registry":"object"} `|`json {"allowed_documents":"string","blocked_documents":"object","compliance_runtime_log":"object"} `|1.非法内容100%阻断；2.校验全留痕；3.合法内容无遗漏|设计：`runtime_plane_design.md#4.2`<br>配置：`runtime_compliance_rule.json`<br>测试：`runtime_blocking_test.py`|
|Normalize Agent|原始文档标准化，校验契约|`json {"allowed_documents":"string","runtime_output_contract":"object"} `|`json {"normalized_documents":"string","format_validation_report":"object","normalize_failure_record":"object"} `|1.输出100%符合契约；2.失败记录可追溯；3.核心字段无丢失|设计：`runtime_plane_design.md#4.2`<br>配置：`normalize_rule_config.json`<br>测试：`normalize_contract_test.py`|
|Source Audit Agent|记录运行全链路审计日志，生成追溯报告|`json {"all_runtime_agent_outputs":"object"} `|`json {"runtime_audit_log":"object","trace_report":"object","runtime_exception_summary":"object"} `|1.数据可全链路追溯；2.日志符合合规留存要求；3.异常信息完整|设计：`runtime_plane_design.md#4.2`<br>配置：`audit_log_config.yaml`<br>测试：`runtime_trace_test.py`|
### 3.3 Governance Plane Agents

|Agent名称|核心职责|输入契约（结构化定义）|输出契约（结构化定义）|验收标准|关联文件映射|
|---|---|---|---|---|---|
|Standards Agent|定义并维护全系统统一标准，版本管理|`json {"UserRuleSet":"object","industry_standard":"object","compliance_requirement":"object"} `|`json {"standards_manual":"object","standard_version":"string","standard_violation_rules":"object"} `|1.标准统一可执行；2.覆盖全流程；3.更新可同步至所有Agent|设计：`governance_plane_design.md#4.3`<br>配置：`system_standards_config.json`<br>测试：`standards_coverage_test.py`|
|Compliance Policy Agent|全平面合规策略执行，违规阻断|`json {"compliance_policy":"object","all_agent_exec_logs":"object","node_status_events":"object"} `|`json {"policy_enforcement_log":"object","violation_record":"object","block_action":"object"} `|1.违规及时识别阻断；2.执行全留痕；3.规则更新实时同步|设计：`governance_plane_design.md#4.3`<br>配置：`policy_enforce_config.json`<br>测试：`policy_blocking_test.py`|
|Audit Agent|全流程合规审计，输出风险发现|`json {"build_summary_report":"object","runtime_audit_log":"object","policy_enforcement_log":"object"} `|`json {"full_audit_report":"object","risk_findings":"array","rectification_suggestions":"array"} `|1.全流程可审计；2.问题定位精准；3.报告符合金融合规要求|设计：`governance_plane_design.md#4.3`<br>配置：`audit_checklist.yaml`<br>测试：`audit_coverage_test.py`|
|Evaluation Agent|量化评估功能/运行/规则有效性|`json {"test_reports":"object","runtime_status_reports":"object","full_audit_report":"object"} `|`json {"evaluation_report":"object","score_card":"object","improvement_suggestions":"array"} `|1.输出明确达标结论；2.覆盖所有核心指标；3.建议具体可落地|设计：`governance_plane_design.md#4.3`<br>配置：`evaluation_rule_config.json`<br>测试：`evaluation_indicator_test.py`|
### 3.4 Final Gate Agent

|Agent名称|核心职责|输入契约（结构化定义）|输出契约（结构化定义）|验收标准|关联文件映射|
|---|---|---|---|---|---|
|Final Gate Agent|汇总三平面结果，输出唯一放行决策|`json {"build_summary_report":"object","runtime_status_report":"object","full_audit_report":"object","UserRuleSet":"object"} `|`json {"final_gate_decision":"string","rule_check_matrix":"array","risk_notes":"array","action_recommendation":"string"} `|1.结论明确；2.规则校验矩阵可追溯；3.风险点/建议清晰|设计：`final_gate_design.md#4.4`<br>配置：`final_decision_rule.json`<br>测试：`final_decision_accuracy_test.py`|
### 3.5 Human Approval Checkpoint

|节点名称|核心职责|输入契约（结构化定义）|输出契约（结构化定义）|验收标准|关联文件映射|
|---|---|---|---|---|---|
|Human Approval Checkpoint|生产发布前人工审批，留痕审计|`json {"staging_deploy_report":"object","test_reports":"object","release_plan":"object"} `|`json {"approval_result":"string","approval_opinion":"string","approval_audit_log":"object"} `|1.仅在指定时机触发；2.审批操作仅支持3类；3.审计记录完整|设计：`approval_design.md#4.5`<br>配置：`approval_config.yaml`<br>测试：`approval_trigger_test.py`|
## 四、反向复述（机器可读配置）

```JSON

{
  "solve_problem": "实现金融合规资讯源接入全流程的Agent自主执行，减少人工执行环节，确保全流程合规、可追溯、7×24小时稳定运行，仅保留用户规则定义、关键审批、结果检查的核心职责",
  "not_do_list": [
    "不允许用户参与任务拆分、代码实现、测试执行、部署操作、日常排障、Agent间协调、中间结果修改",
    "不允许Agent跨职责执行任务，禁止无意义重试、盲修瞎改",
    "不允许非生产发布环节触发人工审批，禁止审批操作超出Approve/Reject/Request More Info三类",
    "不允许合规校验不通过的内容流入下游环节，禁止规则冲突、无版本管理的规则执行"
  ],
  "current_stage_delivery": {
    "MVP阶段": [
      "Build Plane核心Agent（需求解析→合规规则→源注册→架构→契约→开发→评审→测试→预发部署）的编排落地",
      "Runtime Plane基础抓取+合规守门+标准化能力",
      "Governance Plane核心合规策略执行+审计能力",
      "Final Gate Agent基础决策能力",
      "Human Approval Checkpoint核心审批能力"
    ]
  },
  "completion_standard": {
    "MVP阶段": [
      "Build Plane流程可闭环执行，需求可拆解为可执行子任务，代码通过评审/测试/预发验证",
      "Runtime Plane抓取成功率≥95%，合规阻断率100%，标准化输出符合契约",
      "Governance Plane合规规则覆盖核心场景，审计日志完整可追溯",
      "Final Gate Agent可输出明确的PASS/BLOCKED决策，规则校验矩阵完整",
      "Human Approval Checkpoint可触发/暂停/恢复流程，审批记录全留痕"
    ]
  }
}
```

## 五、阶段门禁（强制校验规则）

|门禁层级|校验内容|阻断条件|校验方式|关联测试文件|
|---|---|---|---|---|
|远景→MVP实现|系统总目标与远景一致性|远景目标未对齐、核心合规要求未纳入|文档评审+配置校验|`vision_mvp_align_test.py`|
|MVP→Agent编排|MVP边界是否清晰、核心Agent职责是否明确|MVP边界模糊、Agent职责交叉、无结构化输入输出定义|配置校验+边界测试|`mvp_orchestration_validate.py`|
|Agent编排→代码实现|Agent输入输出契约是否清晰、版本管理是否落地|契约缺失核心字段、无版本号、Schema不标准化|契约校验+Schema测试|`agent_contract_validate.py`|
|代码实现→完成验收|测试覆盖度、验收标准达成度|单元/集成/规则/验收测试未通过、核心指标未达阈值|全量测试套件执行|`completion_standard_test_suite.py`|
## 六、测试体系（验证理解正确而非仅代码可跑）

|测试类型|测试目标|核心测试用例|关联文件|
|---|---|---|---|
|单元测试|验证Agent职责无越界|1.调用Agent执行超职责范围任务，校验是否阻断；2.输入越界参数，校验是否识别|`agent_responsibility_unit_test.py`|
|集成测试|验证流程顺序无跑偏|1.打乱Build Plane流程节点顺序，校验是否无法执行；2.Runtime Plane异常分支流转校验|`plane_flow_integration_test.py`|
|规则测试|验证合规边界无破|1.输入违规内容，校验是否100%阻断；2.修改合规规则版本，校验执行结果是否同步|`compliance_rule_test.py`|
|验收测试|验证符合文档成功标准|直接对照文档中各Agent成功验收标准，逐条校验指标达成度|`acceptance_standard_test.py`|
## 七、影响分析模板（新增功能必用）

```JSON

{
  "new_feature_name": "",
  "impacted_document_items": [],
  "impacted_agents": [],
  "break_mvp_boundary": false,
  "change_compliance_assumption": false,
  "clarification_required": false,
  "clarification_content": ""
}
```

## 八、从文档到代码的可追溯表

|代码/配置文件路径|对应设计文档章节|核心设计依据|验收标准映射|测试覆盖情况|
|---|---|---|---|---|
|`langgraph/build_graph.py`|5.1 Build Plane - Feature Build Graph|Build Plane流程图、Agent编排规则|Build Plane Agent验收标准|集成测试100%覆盖|
|`langgraph/runtime_graph.py`|5.2 Runtime Plane - Source Runtime Graph|Runtime Plane流程图、异常处理规则|Runtime Plane Agent验收标准|集成测试100%覆盖|
|`config/compliance_policy.json`|4.1 Compliance Rules Agent、4.3 Compliance Policy Agent|合规规则结构化定义、阻断条件|合规策略执行验收标准|规则测试100%覆盖|
|`agent/build/development_agent.py`|4.1 Development Agent|开发Agent职责、输入输出契约|开发Agent验收标准|单元测试100%覆盖|
|`agent/final_gate/final_gate_agent.py`|4.4 Final Gate Agent|最终决策输出规范、决策类型定义|Final Gate验收标准|验收测试100%覆盖|
## 九、下一步需补充的核心内容

### 1. 各Agent的结构化输入输出Schema落地文件

- 为每个Agent的输入输出契约生成可直接引用的JSON Schema文件（如`schema/req_parse_input.schema.json`、`schema/final_gate_output.schema.json`），确保所有Agent执行时严格遵循结构化定义，避免自然语言输出。

### 2. 阶段门禁校验工具

- 开发阶段门禁的自动化校验脚本（如`gate_check/vision_mvp_check.py`、`gate_check/contract_clear_check.py`），在每个阶段执行前自动校验门禁条件，不满足则阻断流程。

### 3. 影响分析自动化校验模板

- 基于影响分析模板开发自动化校验工具（`impact_analysis/analysis_tool.py`），新增功能时自动识别影响的文档条目、Agent，校验是否突破MVP边界/合规假设，未澄清则禁止代码提交。

## 核心原则落地保障

所有落地动作均围绕「不追求主观理解正确，而是通过机制发现并阻断偏差」展开：

1. 结构化契约+Schema校验：阻断Agent输入输出的理解偏差；

2. 阶段门禁+自动化校验：阻断流程推进中的理解偏差；

3. 全维度测试（职责/流程/规则/验收）：阻断实现与设计的理解偏差；

4. 可追溯表+版本管理：阻断变更带来的理解偏差；

5. 影响分析+澄清机制：阻断新增功能的理解偏差。
> （注：文档部分内容可能由 AI 生成）

# Story Agent 交付标准

## 目标

从 Finahunt 当前阶段开始，每个 Story 不只要求“代码实现完成”，还要求有一套完整的 Agent 一条龙交付包，确保：

- 需求清楚
- 实现范围清楚
- 测试与审查有证据
- 最终验收可以回放

## 一条龙交付链

每个 Story 完成时，至少要补齐以下 8 个环节：

1. `Requirement Agent`
   - 说明这个 Story 到底要解决什么问题
   - 说明边界、依赖和禁止事项

2. `Builder Agent`
   - 说明实际改了哪些代码/配置/规则
   - 说明核心交付文件

3. `Code Style Reviewer`
   - 检查风格、一致性、命名和格式
   - 说明是否有 blocking 风格问题

4. `Tester Agent`
   - 说明跑了哪些测试
   - 说明核心验证结果

5. `Reviewer Agent`
   - 检查业务符合度、结构合理性和风险
   - 说明是否存在重要设计问题

6. `Code Acceptance Agent`
   - 检查文件 hygiene、交付物完整性、输出结构稳定性

7. `Acceptance Gate`
   - 对照 Story 的 acceptance criteria 做最终放行
   - 给出 PASS / BLOCKED 结论

8. `Doc Writer`
   - 产出最终交付报告
   - 记录证据、结论、回放入口

## 最低交付物要求

每个 Story 至少要有：

- 一份 `story_delivery_report.md`
- 对应代码/规则/配置的实际落地文件
- 对应测试或 live 验证证据
- 最终验收结论

## 当前执行口径

对于已经完成但尚未走完整 `agentsystem run-task` 链路的 Finahunt Story：

- 允许先补“回填式交付报告”
- 但报告里必须明确说明：
  - 哪些结论来自自动化测试
  - 哪些结论来自 live 验证
  - 哪些结论来自人工补充说明

后续新 Story 优先按实时交付包生成，不再只做事后回填。

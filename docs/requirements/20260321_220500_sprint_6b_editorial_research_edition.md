# Sprint 6B 需求文档

## 名称

Finahunt 编辑型情报台重做与完整 UI/browser 验收

## 背景

Sprint 6 已经把页面拆成了独立 URL，但仍有三个明显问题：

- 顶部导航、头部动作和首页正文 CTA 同时导流，形成重复入口
- 四个页面视觉语言几乎一致，像“同一块玻璃卡换不同标题”
- 展示层存在中文乱码风险，影响页面可信度和专业感

## 目标

把前端重做成编辑型研究刊物风格，并且按研究流程区分页面气质：

- `/` 今日入口：导读页
- `/fermentation` 主线发酵：专题栏目
- `/research` 低位研究：研究 dossier
- `/workbench` 工作台总览：分析总编台

## 关键约束

- 顶层只有一层正式导航
- 首页不再出现第二套导航式 CTA
- 保留 `/sprint-2 -> /workbench`
- 保留 `/low-position -> /research`
- 不改 runtime 数据 contract，继续复用 `dailySnapshot.ts` 与 `lowPositionWorkbench.ts`

## 验收口径

- 页面完成视觉重做，不只是结构拆页
- 首页明确收缩成入口页
- 三个专题页和总览页气质明显不同
- 文本清洗后无明显中文乱码
- 路由、跳转、空状态、部分状态和完整状态可正常工作

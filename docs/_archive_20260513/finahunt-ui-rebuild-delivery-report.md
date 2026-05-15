# Finahunt 前端 UI 重构交付报告

生成时间：2026-05-12

## 一、完成内容

1. 页面：已重构 `/`、`/fermentation`、`/research`、`/workbench`、`/low-position`、`/sprint-2`。
2. 组件：新增 `FinancialUI.tsx`，统一 Badge、卡片、指标、Hero、日期切换、分页、空状态、链接按钮；修复刷新与低位运行按钮中文文案。
3. 样式：重写 `globals.css`，采用 docs/UI 中白底、蓝色主色、顶部搜索、居中导航、卡片、排行、标签、表格、样例锁定卡与响应式布局。
4. 数据流：保留 `loadDailySnapshot`、`loadLowPositionWorkbench`、`resolveTargetDate`、`resolveWorkbenchDate` 等既有读取逻辑；真实数据优先，空数据仅展示保守 fallback。
5. API routes：确认保留 `/api/daily-snapshot`、`/api/refresh-latest`、`/api/run-low-position`，且 `git diff -- apps/web/src/app/api` 为空。
6. Mock fallback：未新增伪造业务数据文件；只新增空状态、默认说明、分类标签、锁定样例视觉。
7. UI 参考：使用 `docs/UI/contact-sheet.png`（最新修改 2026-05-12 18:26:23）以及 `financial_ui_html_pages` 下 HTML/CSS 原型。

## 二、修改文件清单

| 文件 | 类型 | 目的 |
| --- | --- | --- |
| `apps/web/src/app/layout.tsx` | 页面/壳层 | 重建顶部蓝线、品牌、搜索、导航、页脚；移除外部字体依赖。 |
| `apps/web/src/app/globals.css` | 样式 | 全局金融资讯系统视觉与响应式布局。 |
| `apps/web/src/app/page.tsx` | 页面 | 首页资讯流、热门题材、题材机会、样例预览。 |
| `apps/web/src/app/fermentation/page.tsx` | 页面 | 题材发现、阶段分布、证据带、发酵矩阵。 |
| `apps/web/src/app/research/page.tsx` | 页面 | 低位研究样例库、验证分组、链路阶段、消息卡。 |
| `apps/web/src/app/workbench/page.tsx` | 页面 | 主线/低位/事件/矩阵聚合工作台。 |
| `apps/web/src/app/low-position/page.tsx` | 页面 | 保留 route 并改成独立低位看板。 |
| `apps/web/src/app/sprint-2/page.tsx` | 页面 | 保留旧入口并改成验收导航页。 |
| `apps/web/src/components/FinancialUI.tsx` | 组件 | 新增共享 UI 基础组件。 |
| `apps/web/src/components/RefreshLatestButton.tsx` | 组件 | 修复中文状态文案，保留原 API 调用。 |
| `apps/web/src/components/RunLowPositionButton.tsx` | 组件 | 修复中文状态文案，保留原 API 调用。 |
| `apps/web/src/lib/webView.ts` | 数据/展示 helper | 修复展示 label/fallback，保留排序、格式化、链接和名称提取接口。 |
| `.omx/context/finahunt-ui-rebuild-20260512T143048Z.md` | 工作流 | Autopilot context snapshot。 |
| `.omx/plans/prd-finahunt-ui-rebuild-20260512T143048Z.md` | 工作流 | PRD artifact。 |
| `.omx/plans/test-spec-finahunt-ui-rebuild-20260512T143048Z.md` | 工作流 | Test spec artifact。 |
| `.omx/code-review-finahunt-ui-rebuild-20260512T143048Z.md` | 工作流 | 自审/code-review artifact。 |
| `docs/finahunt-ui-rebuild-delivery-report.md` | 文档 | 本报告。 |

## 三、UI 参考映射

| Route | 参考文件 | 说明 |
| --- | --- | --- |
| `/` | `contact-sheet.png` 第 1/11 张，`home.html`，`news.html`，`styles.css` | 首页顶部、资讯流、热门题材、分类、机会、样例预览。 |
| `/fermentation` | `topics.html`，`topic-category.html`，`topic-detail.html`，`contact-sheet.png` 第 3/5/6 张 | 题材卡、排行、阶段、详情矩阵。 |
| `/research` | `samples.html`，`search.html`，`sample-detail-locked.html`，`contact-sheet.png` 第 7/9 张 | 样例卡、锁定预览、候选公司标签。 |
| `/workbench` | `home.html`，`search.html`，`news.html` | 高密度总览、检索感、表格和事件带。 |
| `/low-position` | `samples.html`，`search.html` | 低位专题兼容入口。 |
| `/sprint-2` | `unlock.html`，`home.html` | 旧入口保留与验收路线。 |

取舍：`contact-sheet.png` 是最新参考，优先决定整体视觉；HTML 原型存在编码异常时，以图片视觉和 `styles.css` 为准；不引入登录、支付或真实解锁流程；保守保留现有业务数据语义。

## 四、路由验收

| Route | 保留 | 可访问 | UI 参考 | 数据来源 | 残余风险 |
| --- | --- | --- | --- | --- | --- |
| `/` | 是 | 是，smoke 200 | home/news/contact-sheet | `loadDailySnapshot` | 数据为空时展示空状态。 |
| `/fermentation` | 是 | 是，smoke 200 | topics/topic-detail | `loadDailySnapshot` | 尚未做单题材动态详情路由。 |
| `/research` | 是 | 是，smoke 200 | samples/search | `loadLowPositionWorkbench` | 依赖低位工作台数据存在。 |
| `/workbench` | 是 | 是，smoke 200 | home/search/news | 两套数据读取 | 小屏表格需人工最终验收。 |
| `/low-position` | 是 | 是，smoke 200 | samples/search | `loadLowPositionWorkbench` | 从重定向改成独立页，如外部依赖旧重定向需关注。 |
| `/sprint-2` | 是 | 是，smoke 200 | unlock/home | 两套数据读取 | 作为验收入口，不恢复旧 sprint-2 布局。 |

## 五、验证结果

1. `npm run build`（`apps/web`）：通过；输出包含六个页面 route 和三条 API route。
2. `python -m compileall -q agents packages graphs workflows tools skills tests`（根目录）：通过。
3. `python -m pytest -q`（根目录）：`32 passed, 1 failed`；失败为 `S6B-001 missing list field story_inputs`，判断为既有 S6B story 契约字段缺失，非本次前端改动导致，未弱化或删除测试。
4. 生产 smoke：最终使用 `npm run start -- -p 3029` 后请求 `/`、`/fermentation`、`/research`、`/workbench`、`/low-position`、`/sprint-2`、`/api/daily-snapshot` 均返回 200。
5. 中文扫描：生产 HTML 六个页面常见乱码片段扫描为 0；本轮编辑前端文件已写入正常 UTF-8 中文。

## 六、自审结果

1. API route：保留且未改动。
2. Python runtime：未误改。
3. 中文：无明显乱码；已修复页面、按钮与 helper 文案。
4. TypeScript：`npm run build` 通过。
5. 布局：生产 routes 可访问；使用响应式 grid、表格横向滚动和移动端 media query。
6. 用户资料：未删除 `docs/UI`、`.omx`、`workspace`、`tasks`、`docs`。
7. 依赖：未修改 package manager，未新增依赖。
8. 数据读取：未破坏现有 `src/lib` 真实数据读取。
9. Git 安全：未执行 `git reset`、`git clean`、强制覆盖或批量删除。
10. 已有未提交改动：初始未跟踪资料均保留。

## 七、残余风险

1. 视觉仍非逐像素复刻，登录/解锁/详情页未实现真实业务流程。
2. 某日期 runtime 数据缺失时只能展示空状态或展示层 fallback。
3. 需要人工最终验收桌面 1440/1536 宽度和移动端窄屏表现。
4. 后续可补单题材详情、单样例详情、真实搜索结果页。
5. 若后续有 Figma 或更精确截图，可继续 pixel-level 调整。
6. 建议后续补 Playwright/截图回归测试。

## 八、如何启动前端验收

```powershell
cd D:\lyhgentgent-frameinahuntpps\web
npm install   # 如 node_modules 已存在且依赖未变，可跳过
npm run dev -- -p 3021
```

生产模式：

```powershell
npm run build
npm run start -- -p 3021
```

本地访问：`http://127.0.0.1:3021/`

推荐验收：`/`、`/fermentation`、`/research`、`/workbench`、`/low-position`、`/sprint-2`。

人工重点：顶部导航与搜索、首页资讯流、题材卡、研究样例卡、工作台表格、中文显示、移动端是否溢出。

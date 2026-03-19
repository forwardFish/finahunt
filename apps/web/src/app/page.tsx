import type { Route } from "next";
import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, resolveTargetDate, type DailyEvent, type DailyTheme } from "@/lib/dailySnapshot";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type PageState = {
  tone: "ready" | "partial" | "empty";
  label: string;
  description: string;
};

function formatIso(value: string): string {
  if (!value) {
    return "-";
  }
  return value.replace("T", " ").replace("+00:00", " UTC");
}

function formatScore(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(1);
}

function themeName(theme: DailyTheme | undefined): string {
  if (!theme) {
    return "暂无主题";
  }
  return theme.themeName || theme.clusterId || "未命名主题";
}

function stageLabel(value: string): string {
  switch (value) {
    case "hot":
      return "拥挤扩散";
    case "fermenting":
      return "持续发酵";
    case "emerging":
      return "早期成形";
    case "watch-only":
    case "watching":
      return "观察等待";
    case "early":
      return "早期阶段";
    case "spreading":
      return "扩散阶段";
    case "crowded":
      return "拥挤阶段";
    default:
      return value || "观察等待";
  }
}

function topThemes(themes: DailyTheme[]): DailyTheme[] {
  return [...themes].sort((left, right) => right.fermentationScore - left.fermentationScore).slice(0, 4);
}

function lowPositionThemes(themes: DailyTheme[]): DailyTheme[] {
  return [...themes]
    .filter((item) => item.lowPositionScore !== null)
    .sort((left, right) => (right.lowPositionScore ?? 0) - (left.lowPositionScore ?? 0))
    .slice(0, 4);
}

function featuredEvents(events: DailyEvent[]): DailyEvent[] {
  return [...events].slice(0, 4);
}

function summarizePageState(
  runCount: number,
  themeCount: number,
  eventCount: number,
  sourceCount: number,
): PageState {
  if (runCount === 0) {
    return {
      tone: "empty",
      label: "空白状态",
      description: "当前日期还没有可展示的运行批次。请切换日期，或执行一次最新抓取。",
    };
  }
  if (themeCount === 0 || eventCount === 0 || sourceCount === 0) {
    return {
      tone: "partial",
      label: "部分数据",
      description: "今天已有运行结果，但部分研究板块仍缺少完整内容，页面会优先展示已确认信号。",
    };
  }
  return {
    tone: "ready",
    label: "已就绪",
    description: "今日主线、研究机会、证据回看和风险边界都已进入可浏览状态。",
  };
}

export default async function Page({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const latestRun = snapshot.runs[0];
  const leadThemes = topThemes(snapshot.themes);
  const researchLeads = lowPositionThemes(snapshot.themes);
  const leadTheme = leadThemes[0];
  const researchTheme = researchLeads[0];
  const eventLeads = featuredEvents(snapshot.events);
  const pageState = summarizePageState(
    snapshot.stats.runCount,
    snapshot.themes.length,
    snapshot.events.length,
    snapshot.sources.length,
  );

  return (
    <main className="page-stack">
      <section className="hero-shell home-hero" data-card>
        <div className="hero-grid home-hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Finahunt Daily Intelligence</span>
            <h1>把公开市场信号整理成可执行的研究入口。</h1>
            <p className="hero-copy-text">
              Finahunt 把每日运行结果压缩成“今日主线、低位研究、证据回看、风险边界”四段式入口，让研究员先看到判断，再决定是否进入 Sprint 2
              做深挖。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/" className="toolbar" method="get">
                <input aria-label="切换快照日期" defaultValue={snapshot.date} name="date" type="date" />
                <button type="submit">切换日期</button>
              </form>

              <div className="toolbar nav-links">
                <Link className="ghost-link" href={`/sprint-2?date=${snapshot.date}&focus=all&reason=compare` as Route}>
                  进入 Sprint 2 工作台
                </Link>
                <span className="pill">存储时区：{snapshot.storageTimezone}</span>
              </div>
            </div>

            <div className="status-strip" data-metric-strip>
              <article className={`status-card tone-${pageState.tone}`} data-stat="page-state">
                <span>页面状态</span>
                <strong>{pageState.label}</strong>
                <p>{pageState.description}</p>
              </article>
              <article className="status-card" data-stat="lead-theme">
                <span>今日主线</span>
                <strong>{themeName(leadTheme)}</strong>
                <p>{leadTheme?.coreNarrative || "先用首页判断今天是否已经出现明确主线。"}</p>
              </article>
              <article className="status-card" data-stat="research-priority">
                <span>研究优先级</span>
                <strong>{themeName(researchTheme)}</strong>
                <p>
                  {researchTheme?.lowPositionReason ||
                    "如果主线还不够清晰，就从低位研究入口切入，继续看证据和催化。"}
                </p>
              </article>
            </div>
          </div>

          <aside className="hero-aside panel-card" data-card>
            <div className="aside-head">
              <span className="pill accent">今日研究指引</span>
              <span className="aside-timestamp">{formatIso(latestRun?.createdAt ?? "")}</span>
            </div>
            <h2>先看主线，再看低位机会。</h2>
            <p className="aside-copy">
              首页是产品化入口，不是原始数据板。它负责帮你快速判断今天要不要深入 Sprint 2，以及优先从哪条主线开始研究。
            </p>

            <div className="aside-highlight-grid">
              <article className="aside-highlight">
                <span>Lead Fermentation Theme</span>
                <strong>{themeName(leadTheme)}</strong>
                <p>
                  发酵 {formatScore(leadTheme?.fermentationScore ?? null)} / 阶段{" "}
                  {stageLabel(leadTheme?.fermentationStage || "")}
                </p>
              </article>
              <article className="aside-highlight">
                <span>Research Priority</span>
                <strong>{themeName(researchTheme)}</strong>
                <p>低位优先级 {formatScore(researchTheme?.lowPositionScore ?? null)}</p>
              </article>
            </div>

            <div className="aside-stat-grid">
              <div className="aside-stat" data-stat="run-count">
                <span>运行批次</span>
                <strong>{snapshot.stats.runCount}</strong>
              </div>
              <div className="aside-stat" data-stat="theme-count">
                <span>主题总量</span>
                <strong>{snapshot.stats.themeCount}</strong>
              </div>
              <div className="aside-stat" data-stat="event-count">
                <span>事件总量</span>
                <strong>{snapshot.stats.canonicalEventCount}</strong>
              </div>
              <div className="aside-stat" data-stat="source-count">
                <span>来源覆盖</span>
                <strong>{snapshot.stats.sourceCount}</strong>
              </div>
            </div>

            <div className="aside-note" data-risk-section>
              <strong>风险边界</strong>
              <p>
                {snapshot.commonRiskNotices[0] ||
                  "本产品用于研究观察，不构成交易建议。重点是帮助团队更快判断该跟哪条主线、看哪组证据。"}
              </p>
            </div>

            <RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/" />
          </aside>
        </div>

        <div className="insight-strip">
          <article className="insight-card panel-card" data-card>
            <span className="section-kicker">Main Narrative</span>
            <h3>{themeName(leadTheme)}</h3>
            <p>{leadTheme?.coreNarrative || "如果今天还没有形成清晰主线，可以进入工作台继续查看证据带和阶段分布。"}</p>
            <div className="pill-row">
              <span className="pill accent">发酵 {formatScore(leadTheme?.fermentationScore ?? null)}</span>
              <span className="pill good">{stageLabel(leadTheme?.fermentationStage || "")}</span>
              <span className="pill">热度 {formatScore(leadTheme?.heatScore ?? null)}</span>
            </div>
          </article>

          <article className="insight-card panel-card" data-card data-evidence-block>
            <span className="section-kicker">Evidence Coverage</span>
            <h3>今天的信号覆盖了哪些研究入口</h3>
            <p>首页只保留最值得继续打开的入口：来源分布、运行批次、领先主题、最新事件，以及通往 Sprint 2 的桥接。</p>
            <div className="pill-row">
              <span className="pill">来源 {snapshot.stats.sourceCount}</span>
              <span className="pill">批次 {snapshot.stats.runCount}</span>
              <span className="pill">主题 {snapshot.stats.themeCount}</span>
            </div>
          </article>

          <article className="insight-card panel-card" data-card data-risk-section>
            <span className="section-kicker">Risk Boundary</span>
            <h3>研究工作流，不是交易指令面板。</h3>
            <p>首页只负责缩小研究入口，不替代交易决策。进入 Sprint 2 后，仍然需要结合证据、时间线和风险提示做进一步判断。</p>
            <div className="pill-row">
              <span className="pill">研究观察</span>
              <span className="pill warn">保留风险提示</span>
            </div>
          </article>
        </div>
      </section>

      <section className="section-shell">
        <div className="section-head">
          <div>
            <span className="section-kicker">Runtime Overview</span>
            <h2>来源覆盖与运行批次</h2>
            <p>先确认今天的数据来自哪些公开源，再决定是否继续深入到研究工作台。</p>
          </div>
        </div>

        {snapshot.runs.length ? (
          <div className="split-grid">
            <article className="panel-card" data-card>
              <div className="panel-head">
                <div>
                  <h3>公开来源分布</h3>
                  <p className="muted">确认今天的样本来自哪些渠道。</p>
                </div>
              </div>
              <div className="stack-list">
                {snapshot.sources.map((source) => (
                  <article className="list-card" key={source.sourceId}>
                    <div>
                      <strong>{source.sourceName}</strong>
                      <p className="muted">{source.sourceId}</p>
                    </div>
                    <span className="pill accent">{source.documentCount} 篇</span>
                  </article>
                ))}
              </div>
            </article>

            <article className="panel-card" data-card>
              <div className="panel-head">
                <div>
                  <h3>纳入日报的运行批次</h3>
                  <p className="muted">这里展示今天真正被吸收进日报入口的运行批次。</p>
                </div>
              </div>
              <div className="stack-list">
                {snapshot.runs.slice(0, 6).map((run) => (
                  <article className="list-card" key={run.runId}>
                    <div>
                      <strong>{run.runId}</strong>
                      <p className="muted">{formatIso(run.createdAt)}</p>
                    </div>
                    <div className="pill-row">
                      <span className="pill">{run.rawDocumentCount} 文档</span>
                      <span className="pill">{run.eventCount} 事件</span>
                      <span className="pill">{run.themeCount} 主题</span>
                    </div>
                  </article>
                ))}
              </div>
            </article>
          </div>
        ) : (
          <article className="empty-state-card tone-empty panel-card" data-card>
            <span className="section-kicker">Empty State</span>
            <h3>当前日期没有可展示的日报快照</h3>
            <p>你可以切换到有数据的日期，或者直接执行一次最新抓取，让首页重新组织今天的研究入口。</p>
          </article>
        )}
      </section>

      <section className="section-shell">
        <div className="section-head">
          <div>
            <span className="section-kicker">Theme Entry</span>
            <h2>今日主题入口</h2>
            <p>首页只展示最值得进一步打开的主题卡片，完整比较和证据追溯交给 Sprint 2。</p>
          </div>
          <Link className="ghost-link" href={`/sprint-2?date=${snapshot.date}&focus=fermentation&reason=compare` as Route}>
            打开发酵看板
          </Link>
        </div>

        {leadThemes.length ? (
          <div className="board-grid">
            {leadThemes.map((theme) => (
              <article className="board-card panel-card" data-card key={theme.key}>
                <div className="meta-row">
                  <span className="pill accent">{themeName(theme)}</span>
                  <span className="pill good">{stageLabel(theme.fermentationStage)}</span>
                  {theme.lowPositionScore !== null ? (
                    <span className="pill warn">低位 {formatScore(theme.lowPositionScore)}</span>
                  ) : null}
                </div>
                <h3>{themeName(theme)}</h3>
                <p>{theme.coreNarrative || "当前仍在形成叙事阶段，建议进入工作台继续检查证据和扩散节奏。"}</p>
                <div className="score-grid compact-score-grid">
                  <div>
                    <span>热度</span>
                    <strong>{formatScore(theme.heatScore)}</strong>
                  </div>
                  <div>
                    <span>催化</span>
                    <strong>{formatScore(theme.catalystScore)}</strong>
                  </div>
                  <div>
                    <span>持续性</span>
                    <strong>{formatScore(theme.continuityScore)}</strong>
                  </div>
                </div>
                <div className="card-actions">
                  <Link href={`/sprint-2?date=${snapshot.date}&focus=fermentation&reason=compare` as Route}>查看主题证据</Link>
                  <span className="muted">最近更新 {formatIso(theme.latestSeenTime)}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <article className="empty-state-card tone-partial panel-card" data-card>
            <span className="section-kicker">Partial State</span>
            <h3>今天还没有形成足够清晰的主题入口</h3>
            <p>页面会优先保留研究动作和刷新入口，等主题聚类完成后再恢复完整的主题板块。</p>
          </article>
        )}
      </section>

      <section className="section-shell">
        <div className="section-head">
          <div>
            <span className="section-kicker">Event Entry</span>
            <h2>最新事件入口</h2>
            <p>事件卡片把首页的产品入口感落回到真实信号，帮助研究员从入口页切到证据对象。</p>
          </div>
        </div>

        {eventLeads.length ? (
          <div className="event-grid">
            {eventLeads.map((event) => (
              <article className="event-card panel-card" data-card key={event.key}>
                <div className="meta-row">
                  <span className="pill accent">{event.sourceName || "未知来源"}</span>
                  <span className="pill">{event.eventType || "未分类"}</span>
                  <span className="pill">{event.impactDirection || "neutral"}</span>
                </div>
                <h3>{event.title || event.eventSubject || event.eventId}</h3>
                <p>{event.summary || "当前还没有生成事件摘要，建议进入工作台查看原始证据链。"}</p>
                <div className="pill-row">
                  {event.themes.slice(0, 3).map((theme) => (
                    <span className="pill good" key={`${event.key}-${theme}`}>
                      {theme}
                    </span>
                  ))}
                </div>
                <div className="card-actions">
                  <span className="muted">{formatIso(event.eventTime)}</span>
                  {event.sourceRefs[0] ? (
                    <a href={event.sourceRefs[0]} rel="noreferrer" target="_blank">
                      打开原始来源
                    </a>
                  ) : (
                    <Link href={`/sprint-2?date=${snapshot.date}&focus=all&reason=source` as Route}>查看证据模式</Link>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <article className="empty-state-card tone-partial panel-card" data-card>
            <span className="section-kicker">Partial State</span>
            <h3>当前日期还没有可浏览的事件入口</h3>
            <p>你仍然可以通过刷新入口获取最新运行结果，或进入 Sprint 2 查看已有主题和风控边界。</p>
          </article>
        )}
      </section>

      <section className="cta-banner panel-card" data-card>
        <div>
          <span className="section-kicker">Workbench Bridge</span>
          <h2>首页负责收敛入口，Sprint 2 负责做深研究。</h2>
          <p>如果今天的主线已经够清晰，就直接进入工作台；如果还不够清晰，也用工作台去看证据和风险，不需要回到原始日志里找。</p>
        </div>
        <div className="card-actions">
          <Link className="ghost-link" href={`/sprint-2?date=${snapshot.date}&focus=fermentation&reason=compare` as Route}>
            查看主线发酵
          </Link>
          <Link className="header-pill" href={`/sprint-2?date=${snapshot.date}&focus=research&reason=compare` as Route}>
            查看低位研究
          </Link>
        </div>
      </section>
    </main>
  );
}

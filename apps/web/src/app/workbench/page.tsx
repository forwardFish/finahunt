import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import { Badge, DateSwitch, EmptyState, LinkButton, MetricCard, PageHero, SectionCard } from "@/components/FinancialUI";
import type { DailyEvent, DailyTheme } from "@/lib/dailySnapshot";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import type { ThemeRow } from "@/lib/lowPositionWorkbench";
import { loadLowPositionWorkbench } from "@/lib/lowPositionWorkbench";
import { buildHref, featuredEvents, formatIso, formatScore, lowPositionThemeName, safeText, sourceLabel, stageLabel, summarizeResearchState, summarizeSnapshotState, themeName, topThemes, validationLabel } from "@/lib/webView";

type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

function firstParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function includesQuery(values: Array<string | null | undefined>, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return values.some((value) => safeText(value, "").toLowerCase().includes(normalized));
}

function themeMatches(theme: DailyTheme, query: string): boolean {
  return includesQuery([
    themeName(theme),
    theme.clusterId,
    theme.coreNarrative,
    theme.researchPositioningNote,
    theme.lowPositionReason,
    theme.fermentationStage,
    ...theme.latestCatalysts.map((item) => item.title),
    ...theme.topEvidence.map((item) => item.title),
  ], query);
}

function eventMatches(event: DailyEvent, query: string): boolean {
  return includesQuery([
    event.title,
    event.summary,
    event.eventType,
    event.sourceId,
    event.sourceName,
    ...(event.themes || []),
  ], query);
}

function lowPositionMatches(theme: ThemeRow, query: string): boolean {
  return includesQuery([
    lowPositionThemeName(theme),
    theme.low_position_reason,
    theme.fermentation_phase,
    theme.validation_bucket,
    ...theme.candidate_stocks.map((item) => String(item.company_name || item.name || item.company_code || "")),
  ], query);
}

export default async function WorkbenchPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const query = firstParam(params.q).trim();
  const hasQuery = query.length > 0;
  const snapshot = loadDailySnapshot(date);
  const workbench = loadLowPositionWorkbench(date);
  const feedState = summarizeSnapshotState(snapshot.stats.runCount, snapshot.themes.length, snapshot.events.length, snapshot.sources.length);
  const researchState = summarizeResearchState(workbench.state);
  const latestRun = snapshot.runs[0];

  const themePool = hasQuery ? snapshot.themes.filter((theme) => themeMatches(theme, query)) : snapshot.themes;
  const eventPool = hasQuery ? snapshot.events.filter((event) => eventMatches(event, query)) : snapshot.events;
  const lowPositionPool = hasQuery ? workbench.themes.filter((theme) => lowPositionMatches(theme, query)) : workbench.themes;
  const mainThemes = topThemes(themePool, 7);
  const events = featuredEvents(eventPool, 8);
  const searchHitCount = themePool.length + eventPool.length + lowPositionPool.length;

  return (
    <main className="fi-page">
      <PageHero eyebrow="Workbench" title="总编辑台：主线、低位、消息、证据放在一个可检索页面。" description="参考 search / home 的组合布局，工作台承担完整横向对照和表格信息密度；其他页面保留导读与专题化展示。" side={<><h2>总览动作</h2><p>刷新公开资讯或运行低位挖掘后，工作台会继续读取同一套本地 runtime 数据。</p><RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/workbench" /><RunLowPositionButton latestRunId={workbench.runId} /></>}>
        <DateSwitch action="/workbench" date={date} />
      </PageHero>

      {hasQuery ? (
        <section className="fi-card fi-search-state" aria-label="搜索状态">
          <div className="fi-section-head"><div><span className="fi-kicker">Search State</span><h2>搜索命中：{query}</h2></div><Link className="fi-section-action" href={buildHref("/workbench", { date })}>清除搜索</Link></div>
          <p className="fi-muted">已按 q 参数过滤题材、事件和低位研究结果，共命中 {searchHitCount} 项。</p>
        </section>
      ) : null}

      <section className="fi-three-col"><MetricCard label="主线状态" value={feedState.label} note={feedState.description} tone={feedState.tone === "ready" ? "green" : "orange"} /><MetricCard label="研究状态" value={researchState.label} note={researchState.description} tone={researchState.tone === "ready" ? "green" : "orange"} /><MetricCard label="运行时间" value={formatIso(latestRun?.createdAt || workbench.createdAt)} note="同时承接 daily snapshot 与 low-position workbench 聚合结果。" /></section>

      <div className="fi-main-grid">
        <SectionCard title="主线总览" eyebrow="Fermentation Overview" action={<Link href={buildHref("/fermentation", { date })}>进入题材页</Link>}>
          <div className="fi-topic-grid">{mainThemes.length ? mainThemes.map((theme) => <article className="fi-topic-card" key={theme.key}><div className="fi-topic-head"><h3>{themeName(theme)}</h3><Badge tone="red">{stageLabel(theme.fermentationStage)}</Badge></div><p>{safeText(theme.coreNarrative, "暂无主线叙事。")}</p><div className="fi-tags"><span className="fi-tag">发酵 {formatScore(theme.fermentationScore)}</span><span className="fi-tag">热度 {formatScore(theme.heatScore)}</span><span className="fi-tag">事件 {theme.relatedEventsCount}</span></div></article>) : <EmptyState title="暂无主线题材">当前搜索或日期没有可展示的主线题材。</EmptyState>}</div>
        </SectionCard>
        <aside className="fi-side"><SectionCard title="低位研究总览" eyebrow="Research Overview" action={<Link href={buildHref("/research", { date })}>进入样例</Link>}><div className="fi-news-list">{lowPositionPool.slice(0, 6).map((theme) => <article className="fi-news-item" key={theme.theme_name}><span className="fi-news-time">{formatScore(theme.low_position_score)}</span><div><strong>{lowPositionThemeName(theme)}</strong><p>{safeText(theme.low_position_reason, "暂无低位研究理由。")}</p></div></article>)}{!lowPositionPool.length ? <EmptyState title="暂无低位题材">当前搜索或日期没有低位工作台数据。</EmptyState> : null}</div></SectionCard></aside>
      </div>

      <SectionCard title="事件与证据带" eyebrow="Event Tape"><div className="fi-table-wrap"><table className="fi-table"><thead><tr><th>时间</th><th>来源</th><th>标题</th><th>类型</th><th>主题</th></tr></thead><tbody>{events.map((event) => <tr key={event.key}><td>{formatIso(event.eventTime)}</td><td>{sourceLabel(event.sourceId || event.sourceName)}</td><td>{safeText(event.title, "未命名事件")}</td><td>{safeText(event.eventType, "事件")}</td><td>{(event.themes || []).slice(0,3).map((tag) => safeText(tag, "主题")).join(" / ")}</td></tr>)}</tbody></table>{!events.length ? <EmptyState title="暂无事件证据">当前搜索或日期没有匹配事件。</EmptyState> : null}</div></SectionCard>
      <SectionCard title="低位题材矩阵" eyebrow="Low Position Matrix"><div className="fi-table-wrap"><table className="fi-table"><thead><tr><th>题材</th><th>低位分</th><th>阶段</th><th>验证桶</th><th>消息</th><th>候选公司</th></tr></thead><tbody>{lowPositionPool.map((theme) => <tr key={`lp-${theme.theme_name}`}><td>{lowPositionThemeName(theme)}</td><td>{formatScore(theme.low_position_score)}</td><td>{safeText(theme.fermentation_phase, "-")}</td><td>{validationLabel(theme.validation_bucket)}</td><td>{theme.messages.length}</td><td>{theme.candidate_stocks.length}</td></tr>)}</tbody></table>{!lowPositionPool.length ? <EmptyState title="暂无低位矩阵">当前搜索或日期没有匹配低位题材。</EmptyState> : null}</div></SectionCard>
      <section className="fi-card fi-section-head"><div><span className="fi-kicker">Compatibility</span><h2>旧入口继续保留。</h2></div><div className="fi-link-row"><LinkButton href={buildHref("/low-position", { date })} variant="secondary">/low-position</LinkButton><LinkButton href={buildHref("/sprint-2", { date })}>/sprint-2</LinkButton></div></section>
    </main>
  );
}

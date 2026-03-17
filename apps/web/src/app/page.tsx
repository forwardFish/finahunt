import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function formatIso(value: string): string {
  if (!value) {
    return "-";
  }
  return value.replace("T", " ").replace("+00:00", " UTC");
}

export default async function Page({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);

  return (
    <main className="page-shell">
      <section className="hero">
        <span className="eyebrow">Finahunt Daily Snapshot</span>
        <h1>{snapshot.date} 题材与事件总览</h1>
        <p>
          这里展示的是按存储时间聚合的自然日视图。页面会把当天纳入的 runtime 运行批次、题材簇、低位机会和事件对象统一汇总，
          方便你直接判断挖掘质量，而不是逐个翻单次 run。
        </p>
        <form className="toolbar" action="/" method="get">
          <input type="date" name="date" defaultValue={snapshot.date} />
          <button type="submit">切换日期</button>
          <RefreshLatestButton latestRunId={snapshot.runs[0]?.runId ?? ""} />
          <Link className="ghost-link" href={`/sprint-2?date=${snapshot.date}`}>
            查看 Sprint 2 总览
          </Link>
          <span className="pill">存储时间口径: {snapshot.storageTimezone}</span>
        </form>
        <div className="metric-grid">
          <article className="metric-card">
            <span>纳入运行批次</span>
            <strong>{snapshot.stats.runCount}</strong>
          </article>
          <article className="metric-card">
            <span>原始文档</span>
            <strong>{snapshot.stats.rawDocumentCount}</strong>
          </article>
          <article className="metric-card">
            <span>事件对象</span>
            <strong>{snapshot.stats.canonicalEventCount}</strong>
          </article>
          <article className="metric-card">
            <span>题材簇</span>
            <strong>{snapshot.stats.themeCount}</strong>
          </article>
          <article className="metric-card">
            <span>低位机会</span>
            <strong>{snapshot.stats.lowPositionCount}</strong>
          </article>
          <article className="metric-card">
            <span>发酵题材</span>
            <strong>{snapshot.stats.fermentingThemeCount}</strong>
          </article>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>来源分布</h2>
            <p>当前只接财联社快讯、韭研公社、雪球热点三类公开来源。</p>
          </div>
        </div>
        <div className="source-grid">
          {snapshot.sources.map((source) => (
            <article className="card" key={source.sourceId}>
              <h3>{source.sourceName}</h3>
              <p className="muted">{source.sourceId}</p>
              <div className="pill-row">
                <span className="pill accent">{source.documentCount} 篇文档</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>纳入的运行批次</h2>
            <p>这部分能让你看到当天总览具体是由哪些 runtime run 聚起来的。</p>
          </div>
        </div>
        <div className="run-grid">
          {snapshot.runs.map((run) => (
            <article className="card" key={run.runId}>
              <h3>{run.runId}</h3>
              <p>创建时间: {formatIso(run.createdAt)}</p>
              <div className="pill-row">
                <span className="pill">{run.rawDocumentCount} 文档</span>
                <span className="pill">{run.eventCount} 事件</span>
                <span className="pill">{run.themeCount} 题材</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>题材总览</h2>
            <p>按低位优先级和热度排序，优先展示当天真正值得判断的题材簇。</p>
          </div>
        </div>
        <div className="theme-grid">
          {snapshot.themes.map((theme) => (
            <article className="card" key={theme.key}>
              <div className="meta-row">
                <span className="pill accent">{theme.themeName || "未命名题材"}</span>
                <span className="pill good">{theme.fermentationStage || "watching"}</span>
                {theme.lowPositionScore !== null ? <span className="pill warn">低位分 {theme.lowPositionScore}</span> : null}
              </div>
              <h3>{theme.themeName || theme.clusterId}</h3>
              <p>{theme.coreNarrative || "当前还没有补足叙事摘要。"}</p>
              <div className="pill-row">
                <span className="pill">热度 {theme.heatScore}</span>
                <span className="pill">催化 {theme.catalystScore}</span>
                <span className="pill">持续性 {theme.continuityScore}</span>
                <span className="pill">发酵 {theme.fermentationScore}</span>
                <span className="pill">{theme.sourceCount} 个来源</span>
                <span className="pill">{theme.relatedEventsCount} 个事件</span>
              </div>
              {theme.lowPositionReason ? <p>低位判断: {theme.lowPositionReason}</p> : null}
              {theme.riskNotice ? <p>风险提示: {theme.riskNotice}</p> : null}
              <p className="muted">
                首次出现: {formatIso(theme.firstSeenTime)} | 最新出现: {formatIso(theme.latestSeenTime)}
              </p>
              {theme.candidateStocks.length ? (
                <div className="pill-row">
                  {theme.candidateStocks.map((stock) => (
                    <span className="pill" key={`${theme.key}-${stock.code}-${stock.name}`}>
                      {stock.name || stock.code}
                      {stock.score !== null ? ` / ${stock.score}` : ""}
                    </span>
                  ))}
                </div>
              ) : null}
              {theme.topEvidence.length ? (
                <div className="evidence-list">
                  {theme.topEvidence.slice(0, 3).map((evidence) => (
                    <div className="evidence-item" key={`${theme.key}-${evidence.title}`}>
                      <strong>{evidence.title}</strong>
                      <div className="muted">{formatIso(evidence.eventTime)}</div>
                      <div>{evidence.summary || "暂无摘要"}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <h2>事件总览</h2>
            <p>这里是当天被抽出来的事件对象，便于你判断事件抽取和题材归因是不是靠谱。</p>
          </div>
        </div>
        <div className="event-grid">
          {snapshot.events.map((event) => (
            <article className="card" key={event.key}>
              <div className="pill-row">
                <span className="pill accent">{event.sourceName || "未知来源"}</span>
                <span className="pill">{event.eventType || "未分类"}</span>
                <span className="pill">{event.impactDirection || "neutral"}</span>
                <span className="pill">{event.impactScope || "unknown"}</span>
              </div>
              <h3>{event.title || event.eventSubject || event.eventId}</h3>
              <p>{event.summary || "当前没有生成事件摘要。"}</p>
              <p className="muted">
                主体: {event.eventSubject || "-"} | 时间: {formatIso(event.eventTime)}
              </p>
              {event.themes.length ? (
                <div className="pill-row">
                  {event.themes.map((theme) => (
                    <span className="pill good" key={`${event.key}-${theme}`}>
                      {theme}
                    </span>
                  ))}
                </div>
              ) : null}
              {event.sourceRefs.length ? (
                <p className="muted">
                  <a href={event.sourceRefs[0]} target="_blank" rel="noreferrer">
                    查看原始来源
                  </a>
                </p>
              ) : null}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

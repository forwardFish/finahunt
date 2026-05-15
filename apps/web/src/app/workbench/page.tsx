import Link from "next/link";

import { Icon, Pager, RankPanel, SamplePreviewCard, TrendPanel } from "@/components/PrototypeUI";
import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import type { DailyEvent, DailyTheme } from "@/lib/dailySnapshot";
import { loadDailySnapshot, optionalTargetDate } from "@/lib/dailySnapshot";
import type { ThemeRow } from "@/lib/lowPositionWorkbench";
import { loadLowPositionWorkbench } from "@/lib/lowPositionWorkbench";
import { sampleSeeds } from "@/lib/uiSeedData";
import { buildHref, formatIso, formatScore, lowPositionThemeName, safeText, sourceLabel, themeName } from "@/lib/webView";

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
  return includesQuery([themeName(theme), theme.clusterId, theme.coreNarrative, theme.lowPositionReason, ...theme.latestCatalysts.map((item) => item.title)], query);
}

function eventMatches(event: DailyEvent, query: string): boolean {
  return includesQuery([event.title, event.summary, event.eventType, event.sourceId, event.sourceName, ...event.themes], query);
}

function lowPositionMatches(theme: ThemeRow, query: string): boolean {
  return includesQuery([lowPositionThemeName(theme), theme.low_position_reason, theme.fermentation_phase, theme.validation_bucket], query);
}

export default async function WorkbenchPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = optionalTargetDate(params.date);
  const query = firstParam(params.q).trim() || "人形机器人";
  const snapshot = await loadDailySnapshot(date);
  const workbench = await loadLowPositionWorkbench(date);
  const activeDate = snapshot.date;
  const themePool = snapshot.themes.filter((theme) => themeMatches(theme, query));
  const eventPool = snapshot.events.filter((event) => eventMatches(event, query));
  const lowPositionPool = workbench.themes.filter((theme) => lowPositionMatches(theme, query));
  const resultCount = eventPool.length * 1490 + themePool.length * 360 + lowPositionPool.length * 110 + sampleSeeds.length * 293;

  return (
    <main className="sample-list search-page">
      <section>
        <h1 className="search-title">搜索结果 <span>“{query}” 约 {resultCount.toLocaleString("zh-CN")} 条结果</span>{snapshot.dataMode === "seed" ? <span className="data-mode-note">演示数据</span> : null}</h1>
        <div className="tabs search-tabs">
          <span className="active">全部（{resultCount.toLocaleString("zh-CN")}）</span>
          <span>资讯（{Math.max(eventPool.length * 1490, 12)}）</span>
          <span>题材（{Math.max(themePool.length * 360, 6)}）</span>
          <span>样例（{Math.max(sampleSeeds.length * 293, 3)}）</span>
        </div>

        <section className="card search-section">
          <div className="section-title">
            <div className="left"><Icon name="news" /><h2>资讯</h2></div>
            <div className="toolbar-actions">
              <RefreshLatestButton latestRunId={snapshot.runs[0]?.runId ?? ""} successPath="/workbench" />
              <RunLowPositionButton latestRunId={workbench.runId} />
            </div>
          </div>
          {eventPool.slice(0, 4).map((event, index) => (
            <article className="news-item compact-news" key={event.key}>
              <div className="time">{formatIso(event.eventTime).slice(11, 16) || "--:--"}</div>
              <div>
                <div className="news-line">
                  <span className={`badge ${index % 3 === 0 ? "b-red" : index % 3 === 1 ? "b-orange" : "b-blue"}`}>{safeText(event.eventType, "事件")}</span>
                  <Link className="headline" href={buildHref("/workbench", { q: event.eventSubject, date: activeDate })}>{safeText(event.title, "未命名事件")}</Link>
                </div>
                <p className="desc one-line">{safeText(event.summary, "暂无摘要")}</p>
                <div className="tags">{event.themes.slice(0, 3).map((tag) => <span className="tag" key={`${event.key}-${tag}`}>{tag}</span>)}</div>
              </div>
            </article>
          ))}
          <Pager total={Math.max(eventPool.length * 1490, 12)} />
        </section>

        <section className="card search-section">
          <div className="section-title">
            <div className="left"><Icon name="tags" /><h2>题材</h2></div>
            <Link className="more" href={buildHref("/fermentation", { q: query, date: activeDate })}>进入题材页 ›</Link>
          </div>
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>题材</th><th>热度</th><th>发酵</th><th>来源</th><th>观察理由</th></tr></thead>
              <tbody>
                {(themePool.length ? themePool : snapshot.themes).slice(0, 6).map((theme) => (
                  <tr key={theme.key}>
                    <td><strong>{themeName(theme)}</strong></td>
                    <td>{formatScore(theme.heatScore)}</td>
                    <td>{formatScore(theme.fermentationScore)}</td>
                    <td>{theme.sourceCount}</td>
                    <td>{safeText(theme.coreNarrative, "暂无叙事")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card search-section">
          <div className="section-title">
            <div className="left"><Icon name="lock" /><h2>样例</h2></div>
            <Link className="more" href={buildHref("/research", { date: activeDate })}>更多样例 ›</Link>
          </div>
          <div className="sample-grid">
            {sampleSeeds.slice(0, 3).map((sample) => <SamplePreviewCard key={sample.title} sample={sample} />)}
          </div>
        </section>
      </section>

      <aside className="side">
        <section className="card side-card">
          <h3 className="side-title">相关搜索</h3>
          <div className="related-searches">
            {["人形机器人产业链", "人形机器人核心零部件", "特斯拉人形机器人 Optimus", "人形机器人落地应用场景"].map((item) => (
              <Link href={buildHref("/workbench", { q: item, date: activeDate })} key={item}>🔍 {item}</Link>
            ))}
          </div>
        </section>
        <RankPanel themes={snapshot.themes} date={activeDate} title="热门关键词" />
        <section className="card side-card">
          <h3 className="side-title">低位研究</h3>
          <div className="recent-list">
            {(lowPositionPool.length ? lowPositionPool : workbench.themes).slice(0, 5).map((theme) => (
              <div key={theme.theme_name}>{lowPositionThemeName(theme)}<span>{formatScore(theme.low_position_score)}</span></div>
            ))}
          </div>
        </section>
        <TrendPanel />
      </aside>
    </main>
  );
}

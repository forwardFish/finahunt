import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import {
  buildHref,
  formatIso,
  formatScore,
  safeText,
  stageLabel,
  summarizeSnapshotState,
  themeName,
  topThemes,
} from "@/lib/webView";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function stageSummary(themes: ReturnType<typeof loadDailySnapshot>["themes"]) {
  const counts = new Map<string, number>();
  themes.forEach((theme) => {
    const key = theme.fermentationStage || "watch-only";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });
  return Array.from(counts.entries())
    .map(([key, count]) => ({ key, count, label: stageLabel(key) }))
    .sort((left, right) => right.count - left.count);
}

export default async function FermentationPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const state = summarizeSnapshotState(
    snapshot.stats.runCount,
    snapshot.themes.length,
    snapshot.events.length,
    snapshot.sources.length,
  );
  const themes = topThemes(snapshot.themes, 8);
  const stages = stageSummary(snapshot.themes);
  const latestRun = snapshot.runs[0];
  const leadTheme = themes[0];

  return (
    <main className="edition edition-fermentation">
      <section className="edition-hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Fermentation Desk</span>
            <h1>今天什么在升温，升温到哪一步。</h1>
            <p className="hero-copy-text">
              这一页只回答主线发酵问题。你会先看到阶段分布，再看到主题卡和主线矩阵，不再被低位研究的候选公司和工作台大表格打断。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/fermentation" className="toolbar" method="get">
                <input aria-label="切换快照日期" defaultValue={snapshot.date} name="date" type="date" />
                <button type="submit">切换日期</button>
              </form>
              <div className="pill-row">
                <span className="pill is-accent">主线页</span>
                <span className="pill">{formatIso(latestRun?.createdAt)}</span>
              </div>
            </div>

            <div className="summary-grid">
              <article className="mini-card">
                <span>页面状态</span>
                <strong>{state.label}</strong>
                <p>{state.description}</p>
              </article>
              <article className="mini-card">
                <span>发酵主题数</span>
                <strong>{snapshot.stats.fermentingThemeCount}</strong>
                <p>已进入发酵链路、值得继续跟踪扩散的主题数量。</p>
              </article>
              <article className="mini-card">
                <span>当前领衔主题</span>
                <strong>{themeName(leadTheme)}</strong>
                <p>{safeText(leadTheme?.coreNarrative, "当前还没有形成特别明确的领衔主题。")}</p>
              </article>
            </div>
          </div>

          <aside className="edition-panel">
            <div className="pill-row">
              <span className="pill is-accent">编辑说明</span>
              <span className="pill">{snapshot.date}</span>
            </div>
            <h2>先看阶段，再看主线。</h2>
            <p>如果今天更多主题停留在早期成形，说明还不适合过早收窄研究对象。如果已经出现持续发酵或拥挤扩散，再进入工作台验证细节会更高效。</p>
            <div className="summary-grid">
              <div className="mini-card">
                <span>主题总量</span>
                <strong>{snapshot.stats.themeCount}</strong>
              </div>
              <div className="mini-card">
                <span>事件总量</span>
                <strong>{snapshot.stats.canonicalEventCount}</strong>
              </div>
              <div className="mini-card">
                <span>来源覆盖</span>
                <strong>{snapshot.stats.sourceCount}</strong>
              </div>
              <div className="mini-card">
                <span>运行批次</span>
                <strong>{snapshot.stats.runCount}</strong>
              </div>
            </div>
            <RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/fermentation" />
          </aside>
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Stage Ledger</span>
            <h2>今天的阶段分布</h2>
            <p>这组卡片相当于“市场主题版的版面提要”，帮助你先判断今天更像孕育期、发酵期还是扩散期。</p>
          </div>
        </div>
        <div className="stage-grid">
          {stages.length ? (
            stages.map((stage) => (
              <article key={stage.key} className="stage-card">
                <span>阶段</span>
                <strong>{stage.label}</strong>
                <p>{stage.count} 个主题</p>
              </article>
            ))
          ) : (
            <article className="empty-card">
              <h3>当前没有可展示的阶段分布</h3>
              <p>说明当天主题结果仍为空，或运行数据尚未进入快照。</p>
            </article>
          )}
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Theme Stories</span>
            <h2>主线主题卡</h2>
            <p>每张卡片像一篇短文，只讲一个主题的阶段、理由和证据，而不是把所有指标堆到同一行里。</p>
          </div>
        </div>
        <div className="story-grid">
          {themes.length ? (
            themes.map((theme) => (
              <article key={theme.key} className="story-card">
                <span className="section-kicker">{stageLabel(theme.fermentationStage)}</span>
                <h3>{themeName(theme)}</h3>
                <p>{safeText(theme.coreNarrative, "暂无核心叙事。")}</p>
                <div className="metric-row">
                  <div>
                    <span>发酵分</span>
                    <strong>{formatScore(theme.fermentationScore)}</strong>
                  </div>
                  <div>
                    <span>热度</span>
                    <strong>{formatScore(theme.heatScore)}</strong>
                  </div>
                  <div>
                    <span>持续性</span>
                    <strong>{formatScore(theme.continuityScore)}</strong>
                  </div>
                </div>
                <div>
                  <strong>关键证据</strong>
                  <ul className="list">
                    {(theme.topEvidence.length ? theme.topEvidence : theme.latestCatalysts.slice(0, 2)).map((item) => (
                      <li key={`${theme.key}-${item.title}`}>{safeText(item.title || item.summary, "暂无证据摘要")}</li>
                    ))}
                  </ul>
                </div>
              </article>
            ))
          ) : (
            <article className="empty-card">
              <h3>今天还没有可展示的发酵主题</h3>
              <p>可以切换日期，或刷新最新运行后再看主题板。</p>
            </article>
          )}
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Matrix</span>
            <h2>主线发酵矩阵</h2>
            <p>当你需要做横向比较时，再使用这张矩阵表，而不是直接把它塞进首页。</p>
          </div>
          <Link className="text-link" href={buildHref("/workbench", { date: snapshot.date })}>
            去工作台看完整对照
          </Link>
        </div>

        <div className="matrix-shell">
          <table className="matrix-table">
            <thead>
              <tr>
                <th>主题</th>
                <th>阶段</th>
                <th>发酵分</th>
                <th>热度</th>
                <th>催化</th>
                <th>持续性</th>
                <th>事件数</th>
              </tr>
            </thead>
            <tbody>
              {themes.map((theme) => (
                <tr key={`matrix-${theme.key}`}>
                  <td>{themeName(theme)}</td>
                  <td>{stageLabel(theme.fermentationStage)}</td>
                  <td>{formatScore(theme.fermentationScore)}</td>
                  <td>{formatScore(theme.heatScore)}</td>
                  <td>{formatScore(theme.catalystScore)}</td>
                  <td>{formatScore(theme.continuityScore)}</td>
                  <td>{theme.relatedEventsCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

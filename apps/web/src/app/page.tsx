import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import {
  buildHref,
  featuredEvents,
  formatIso,
  formatScore,
  lowPositionThemes,
  safeText,
  sourceLabel,
  summarizeSnapshotState,
  themeName,
  topThemes,
} from "@/lib/webView";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function TodayEntryPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const state = summarizeSnapshotState(
    snapshot.stats.runCount,
    snapshot.themes.length,
    snapshot.events.length,
    snapshot.sources.length,
  );
  const mainThemes = topThemes(snapshot.themes, 3);
  const researchThemes = lowPositionThemes(snapshot.themes, 3);
  const leadTheme = mainThemes[0];
  const leadResearch = researchThemes[0];
  const events = featuredEvents(snapshot.events, 4);
  const latestRun = snapshot.runs[0];

  return (
    <main className="edition edition-home">
      <section className="edition-hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Today Entry</span>
            <h1>先判断今天该从哪条研究路径开始。</h1>
            <p className="hero-copy-text">
              首页现在只做研究入口，不再承载完整工作台。你会先看到今天的主线判断、低位研究优先级和少量关键事件，然后再进入对应栏目继续阅读。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/" className="toolbar" method="get">
                <input aria-label="切换快照日期" defaultValue={snapshot.date} name="date" type="date" />
                <button type="submit">切换日期</button>
              </form>
              <div className="pill-row">
                <span className="pill is-navy">快照日期 {snapshot.date}</span>
                <span className="pill">时区 {snapshot.storageTimezone}</span>
              </div>
            </div>

            <div className="summary-grid">
              <article className="mini-card">
                <span>页面状态</span>
                <strong>{state.label}</strong>
                <p>{state.description}</p>
              </article>
              <article className="mini-card">
                <span>今日主线</span>
                <strong>{themeName(leadTheme)}</strong>
                <p>{safeText(leadTheme?.coreNarrative, "今天还没有形成非常明确的主线主题。")}</p>
              </article>
              <article className="mini-card">
                <span>研究优先级</span>
                <strong>{themeName(leadResearch)}</strong>
                <p>{safeText(leadResearch?.lowPositionReason, "当前还没有显著的低位机会，可以先观察主线发酵。")}</p>
              </article>
            </div>
          </div>

          <aside className="edition-panel">
            <div className="pill-row">
              <span className="pill is-gold">本期导读</span>
              <span className="pill">{formatIso(latestRun?.createdAt)}</span>
            </div>
            <h2>今天先看哪里</h2>
            <p>
              这里像一张研究刊物的封面页。它不负责塞满全部内容，只负责告诉你今天该先看哪一页、哪条主题最值得继续读，以及什么时候应该进入完整工作台。
            </p>

            <div className="summary-grid">
              <div className="mini-card">
                <span>运行批次</span>
                <strong>{snapshot.stats.runCount}</strong>
              </div>
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
            </div>

            <RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/" />
          </aside>
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Reading Paths</span>
            <h2>今日推荐阅读</h2>
            <p>下面不是第二套导航，而是三条今天最值得继续阅读的内容路径。</p>
          </div>
        </div>

        <div className="route-grid">
          <article className="route-card is-accent">
            <span className="section-kicker">推荐一</span>
            <h3>先看主线发酵</h3>
            <p>如果今天已有较明确的市场主线，优先去看发酵阶段、热度和催化延续，而不是直接钻到个股层面。</p>
            <div className="pill-row">
              <span className="pill is-accent">Top {themeName(leadTheme)}</span>
              <span className="pill">发酵 {formatScore(leadTheme?.fermentationScore)}</span>
            </div>
            <Link className="text-link" href={buildHref("/fermentation", { date: snapshot.date })}>
              继续阅读主线发酵
            </Link>
          </article>

          <article className="route-card is-sage">
            <span className="section-kicker">推荐二</span>
            <h3>继续低位研究</h3>
            <p>如果今天更适合找尚未充分拥挤的机会，就进入低位研究页，看题材、候选公司和验证状态。</p>
            <div className="pill-row">
              <span className="pill is-sage">Top {themeName(leadResearch)}</span>
              <span className="pill">低位 {formatScore(leadResearch?.lowPositionScore)}</span>
            </div>
            <Link className="text-link" href={buildHref("/research", { date: snapshot.date })}>
              继续阅读低位研究
            </Link>
          </article>

          <article className="route-card is-gold">
            <span className="section-kicker">推荐三</span>
            <h3>打开完整工作台</h3>
            <p>如果你已经准备做横向比较和深挖，就去总览页看矩阵、证据带和消息链路，而不是在首页继续下滑。</p>
            <div className="pill-row">
              <span className="pill is-gold">主题 {snapshot.stats.themeCount}</span>
              <span className="pill">事件 {snapshot.stats.canonicalEventCount}</span>
            </div>
            <Link className="text-link" href={buildHref("/workbench", { date: snapshot.date })}>
              打开工作台总览
            </Link>
          </article>
        </div>
      </section>

      <section className="two-column">
        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Mainline Brief</span>
              <h2>今日主线摘要</h2>
            </div>
          </div>
          <div className="mini-stack">
            {mainThemes.length ? (
              mainThemes.map((theme) => (
                <article key={theme.key} className="issue-card">
                  <h3>{themeName(theme)}</h3>
                  <p>{safeText(theme.coreNarrative, "暂无主线叙事摘要。")}</p>
                  <div className="pill-row">
                    <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                    <span className="pill">热度 {formatScore(theme.heatScore)}</span>
                  </div>
                </article>
              ))
            ) : (
              <article className="empty-card">
                <h3>今天还没有主线摘要</h3>
                <p>可以先刷新最新快照，或者直接进入工作台看完整运行结果。</p>
              </article>
            )}
          </div>
        </article>

        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Research Brief</span>
              <h2>低位研究摘要</h2>
            </div>
          </div>
          <div className="mini-stack">
            {researchThemes.length ? (
              researchThemes.map((theme) => (
                <article key={theme.key} className="issue-card">
                  <h3>{themeName(theme)}</h3>
                  <p>{safeText(theme.lowPositionReason || theme.researchPositioningNote, "暂无低位研究备注。")}</p>
                  <div className="pill-row">
                    <span className="pill is-sage">低位 {formatScore(theme.lowPositionScore)}</span>
                    <span className="pill">{theme.candidateStocks.length} 个候选</span>
                  </div>
                </article>
              ))
            ) : (
              <article className="empty-card">
                <h3>今天还没有低位研究摘要</h3>
                <p>如果需要，可以去低位研究页执行一次工作台刷新，或切换到有结果的日期。</p>
              </article>
            )}
          </div>
        </article>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Key Events</span>
            <h2>关键事件入口</h2>
            <p>首页只保留少量关键事件，帮助你决定是否需要继续进入专题页或工作台。</p>
          </div>
        </div>

        <div className="issue-grid">
          {events.length ? (
            events.map((event) => (
              <article key={event.key} className="issue-card">
                <span className="section-kicker">{sourceLabel(event.sourceId || event.sourceName)}</span>
                <h3>{safeText(event.title, "未命名事件")}</h3>
                <p>{safeText(event.summary, "暂无事件摘要。")}</p>
                <div className="pill-row">
                  <span className="pill">{formatIso(event.eventTime)}</span>
                  <span className="pill">{safeText(event.eventType, "事件")}</span>
                </div>
              </article>
            ))
          ) : (
            <article className="empty-card">
              <h3>当前日期没有关键事件</h3>
              <p>这通常意味着当天还没有有效运行，或者公开数据还没进入当前快照。</p>
            </article>
          )}
        </div>
      </section>

      <section className="cta-panel">
        <div>
          <span className="section-kicker">Method & Risk</span>
          <h2>这是一页导读，不是一页交易指令。</h2>
          <p>
            {safeText(
              snapshot.commonRiskNotices[0],
              "页面负责帮助你缩小研究范围、组织证据和安排阅读顺序，不直接替代交易决策。",
            )}
          </p>
        </div>
        <div className="link-row">
          <Link className="link-button is-secondary" href={buildHref("/fermentation", { date: snapshot.date })}>
            先看主线
          </Link>
          <Link className="link-button is-primary" href={buildHref("/workbench", { date: snapshot.date })}>
            进入完整总览
          </Link>
        </div>
      </section>
    </main>
  );
}

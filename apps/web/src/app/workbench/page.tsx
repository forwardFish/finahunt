import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";
import { loadLowPositionWorkbench } from "@/lib/lowPositionWorkbench";
import {
  buildHref,
  featuredEvents,
  formatIso,
  formatScore,
  lowPositionThemeName,
  messageCompanyNames,
  safeText,
  sourceLabel,
  stageLabel,
  summarizeResearchState,
  summarizeSnapshotState,
  themeName,
  topThemes,
  validationLabel,
} from "@/lib/webView";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function WorkbenchPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const snapshot = loadDailySnapshot(date);
  const workbench = loadLowPositionWorkbench(date);
  const feedState = summarizeSnapshotState(
    snapshot.stats.runCount,
    snapshot.themes.length,
    snapshot.events.length,
    snapshot.sources.length,
  );
  const researchState = summarizeResearchState(workbench.state);
  const mainThemes = topThemes(snapshot.themes, 5);
  const events = featuredEvents(snapshot.events, 5);
  const latestRun = snapshot.runs[0];

  return (
    <main className="edition edition-workbench">
      <section className="edition-hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Workbench Edition</span>
            <h1>完整总览只留在工作台这一页。</h1>
            <p className="hero-copy-text">
              当你需要横向比对主线、低位机会、关键事件和代表性消息时，才进入这里。它是一页总编辑台，不是一页导读或专题摘要。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/workbench" className="toolbar" method="get">
                <input aria-label="切换工作台日期" defaultValue={date} name="date" type="date" />
                <button type="submit">切换日期</button>
              </form>
              <div className="pill-row">
                <span className="pill is-gold">总览页</span>
                <span className="pill">{formatIso(latestRun?.createdAt || workbench.createdAt)}</span>
              </div>
            </div>

            <div className="summary-grid">
              <article className="mini-card">
                <span>主线状态</span>
                <strong>{feedState.label}</strong>
                <p>{feedState.description}</p>
              </article>
              <article className="mini-card">
                <span>研究状态</span>
                <strong>{researchState.label}</strong>
                <p>{researchState.description}</p>
              </article>
              <article className="mini-card">
                <span>运行时间</span>
                <strong>{formatIso(latestRun?.createdAt || workbench.createdAt)}</strong>
                <p>总览页同时承接 daily snapshot 和 low-position workbench 的聚合结果。</p>
              </article>
            </div>
          </div>

          <aside className="edition-panel">
            <div className="pill-row">
              <span className="pill is-gold">总览动作</span>
              <span className="pill">{snapshot.date}</span>
            </div>
            <h2>从这里进入完整深挖。</h2>
            <p>如果你已经确认今天值得花更长时间研究，这里会把主线主题、低位题材、证据带和消息卡放到一个分析视图里。</p>
            <RefreshLatestButton latestRunId={latestRun?.runId ?? ""} successPath="/workbench" />
            <RunLowPositionButton latestRunId={workbench.runId} />
          </aside>
        </div>
      </section>

      <section className="two-column">
        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Fermentation Overview</span>
              <h2>主线总览</h2>
            </div>
          </div>
          <div className="mini-stack">
            {mainThemes.map((theme) => (
              <article key={theme.key} className="issue-card">
                <h3>{themeName(theme)}</h3>
                <p>{safeText(theme.coreNarrative, "暂无主线叙事。")}</p>
                <div className="pill-row">
                  <span className="pill">{stageLabel(theme.fermentationStage)}</span>
                  <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Research Overview</span>
              <h2>低位研究总览</h2>
            </div>
          </div>
          <div className="mini-stack">
            {workbench.themes.slice(0, 5).map((theme) => (
              <article key={theme.theme_name} className="issue-card">
                <h3>{lowPositionThemeName(theme)}</h3>
                <p>{safeText(theme.low_position_reason, "暂无低位研究理由。")}</p>
                <div className="pill-row">
                  <span className="pill is-sage">低位 {formatScore(theme.low_position_score)}</span>
                  <span className="pill">{validationLabel(theme.validation_bucket)}</span>
                </div>
              </article>
            ))}
          </div>
        </article>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Panorama Matrix</span>
            <h2>全景矩阵</h2>
            <p>这张表用于横向比较主线发酵、低位分和候选公司密度，属于深挖阶段的工具，不属于首页。</p>
          </div>
        </div>

        <div className="matrix-shell">
          <table className="matrix-table">
            <thead>
              <tr>
                <th>主题</th>
                <th>阶段</th>
                <th>发酵分</th>
                <th>低位分</th>
                <th>热度</th>
                <th>催化</th>
                <th>候选数</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.themes.map((theme) => (
                <tr key={`panorama-${theme.key}`}>
                  <td>{themeName(theme)}</td>
                  <td>{stageLabel(theme.fermentationStage)}</td>
                  <td>{formatScore(theme.fermentationScore)}</td>
                  <td>{formatScore(theme.lowPositionScore)}</td>
                  <td>{formatScore(theme.heatScore)}</td>
                  <td>{formatScore(theme.catalystScore)}</td>
                  <td>{theme.candidateStocks.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Evidence Tape</span>
            <h2>关键证据带</h2>
            <p>保留少量事件卡作为总览证据带，帮助你快速决定下一步要深入哪条链路。</p>
          </div>
        </div>

        <div className="issue-grid">
          {events.map((event) => (
            <article key={event.key} className="issue-card">
              <span className="section-kicker">{sourceLabel(event.sourceId || event.sourceName)}</span>
              <h3>{safeText(event.title, "未命名事件")}</h3>
              <p>{safeText(event.summary, "暂无摘要。")}</p>
              <div className="pill-row">
                <span className="pill">{formatIso(event.eventTime)}</span>
                <span className="pill">{safeText(event.eventType, "事件")}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Message Deep Dive</span>
            <h2>代表性消息卡</h2>
            <p>保留几张消息卡用于对照“消息到题材、公司再到验证”的完整链路。</p>
          </div>
        </div>

        <div className="issue-grid">
          {workbench.messages.slice(0, 4).map((row) => (
            <article key={row.message.message_id} className="issue-card">
              <span className="section-kicker">{validationLabel(row.validation.validation_status)}</span>
              <h3>{safeText(row.message.title, "未命名消息")}</h3>
              <p>{safeText(row.impact.impact_summary || row.message.summary, "暂无消息摘要。")}</p>
              <div className="pill-row">
                <span className="pill">行动 {formatScore(row.score.recalibrated_actionability_score)}</span>
                <span className="pill">{safeText(row.impact.primary_theme, "-")}</span>
              </div>
              <p className="muted-copy">公司映射：{messageCompanyNames(row).join(" / ") || "暂无公司映射"}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cta-panel">
        <div>
          <span className="section-kicker">Compatibility Routes</span>
          <h2>旧链接保留兼容，但不再参与正式导航。</h2>
          <p>`/sprint-2` 进入工作台总览，`/low-position` 进入低位研究。正式导航只保留四个研究流程入口。</p>
        </div>
        <div className="pill-row">
          <span className="pill">/sprint-2 转到 /workbench</span>
          <span className="pill">/low-position 转到 /research</span>
          <Link className="link-button is-secondary" href={buildHref("/", { date })}>
            返回今日入口
          </Link>
        </div>
      </section>
    </main>
  );
}

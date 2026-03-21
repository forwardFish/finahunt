import Link from "next/link";

import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import { loadLowPositionWorkbench, resolveWorkbenchDate } from "@/lib/lowPositionWorkbench";
import {
  buildHref,
  candidateNames,
  fermentationVerdictLabel,
  formatIso,
  formatScore,
  lowPositionThemeName,
  messageCompanyNames,
  safeText,
  summarizeResearchState,
  validationLabel,
} from "@/lib/webView";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ResearchPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveWorkbenchDate(params.date);
  const workbench = loadLowPositionWorkbench(date);
  const state = summarizeResearchState(workbench.state);

  return (
    <main className="edition edition-research">
      <section className="edition-hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Research Desk</span>
            <h1>低位研究只看尚未走完的机会。</h1>
            <p className="hero-copy-text">
              这一页聚焦题材、候选公司、研究理由、验证状态和风险提示。它像一份研究 dossier，而不是主线页面的附属板块。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/research" className="toolbar" method="get">
                <input aria-label="切换工作台日期" defaultValue={workbench.date} name="date" type="date" />
                <button type="submit">切换日期</button>
              </form>
              <div className="pill-row">
                <span className="pill is-sage">低位页</span>
                <span className="pill">{formatIso(workbench.createdAt)}</span>
              </div>
            </div>

            <div className="summary-grid">
              <article className="mini-card">
                <span>页面状态</span>
                <strong>{state.label}</strong>
                <p>{state.description}</p>
              </article>
              <article className="mini-card">
                <span>消息数量</span>
                <strong>{workbench.messageCount}</strong>
                <p>当日进入低位挖掘链路的标准消息总数。</p>
              </article>
              <article className="mini-card">
                <span>题材数量</span>
                <strong>{workbench.themeCount}</strong>
                <p>工作台反推生成的低位题材总量。</p>
              </article>
            </div>
          </div>

          <aside className="edition-panel">
            <div className="pill-row">
              <span className="pill is-sage">研究说明</span>
              <span className="pill">{workbench.latestAvailableDate}</span>
            </div>
            <h2>先看题材，再看候选公司。</h2>
            <p>只有当低位题材初步成立时，才继续看公司映射和验证结果。这样可以避免研究视图一打开就被个股长列表淹没。</p>
            <div className="summary-grid">
              <div className="mini-card">
                <span>验证通过</span>
                <strong>{workbench.validatedThemes.length}</strong>
              </div>
              <div className="mini-card">
                <span>继续观察</span>
                <strong>{workbench.watchThemes.length}</strong>
              </div>
              <div className="mini-card">
                <span>降级处理</span>
                <strong>{workbench.downgradedThemes.length}</strong>
              </div>
              <div className="mini-card">
                <span>最近可用日期</span>
                <strong>{workbench.latestAvailableDate}</strong>
              </div>
            </div>
            <RunLowPositionButton latestRunId={workbench.runId} />
          </aside>
        </div>
      </section>

      <section className="two-column">
        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Validation Buckets</span>
              <h2>题材验证分组</h2>
            </div>
          </div>
          <div className="summary-grid">
            <article className="mini-card">
              <span>验证通过</span>
              <strong>{workbench.validatedThemes.length}</strong>
              <p>{workbench.validatedThemes.slice(0, 3).map(lowPositionThemeName).join(" / ") || "当前为空"}</p>
            </article>
            <article className="mini-card">
              <span>继续观察</span>
              <strong>{workbench.watchThemes.length}</strong>
              <p>{workbench.watchThemes.slice(0, 3).map(lowPositionThemeName).join(" / ") || "当前为空"}</p>
            </article>
            <article className="mini-card">
              <span>降级处理</span>
              <strong>{workbench.downgradedThemes.length}</strong>
              <p>{workbench.downgradedThemes.slice(0, 3).map(lowPositionThemeName).join(" / ") || "当前为空"}</p>
            </article>
          </div>
        </article>

        <article className="section-card">
          <div className="section-title">
            <div>
              <span className="section-kicker">Workflow Status</span>
              <h2>链路运行阶段</h2>
            </div>
          </div>
          <div className="stage-grid">
            {workbench.stages.length ? (
              workbench.stages.map((stage) => (
                <article key={stage.stage} className="stage-card">
                  <span>{safeText(stage.label, stage.stage)}</span>
                  <strong>{safeText(stage.status, "-")}</strong>
                  <p>用于说明工作台链路当前跑到了哪一步。</p>
                </article>
              ))
            ) : (
              <article className="empty-card">
                <h3>当前还没有阶段状态记录</h3>
                <p>如果你刚切换到空日期，先执行一次低位挖掘即可。</p>
              </article>
            )}
          </div>
        </article>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Opportunity Dossiers</span>
            <h2>低位题材卡</h2>
            <p>每张卡片像一份简版研究提要，承接题材判断、候选公司和风险提示。</p>
          </div>
        </div>
        <div className="story-grid">
          {workbench.themes.length ? (
            workbench.themes.map((theme) => (
              <article key={theme.theme_name} className="story-card">
                <span className="section-kicker">{validationLabel(theme.validation_bucket)}</span>
                <h3>{lowPositionThemeName(theme)}</h3>
                <p>{safeText(theme.low_position_reason, "暂无低位研究理由。")}</p>
                <div className="metric-row">
                  <div>
                    <span>低位分</span>
                    <strong>{formatScore(theme.low_position_score)}</strong>
                  </div>
                  <div>
                    <span>阶段</span>
                    <strong>{safeText(theme.fermentation_phase, "-")}</strong>
                  </div>
                  <div>
                    <span>候选数</span>
                    <strong>{candidateNames(theme).length}</strong>
                  </div>
                </div>
                <div>
                  <strong>候选公司</strong>
                  <p className="muted-copy">{candidateNames(theme).join(" / ") || "当前还没有稳定候选公司。"}</p>
                </div>
                <div>
                  <strong>风险提示</strong>
                  <p className="muted-copy">{safeText(theme.risk_notice, "暂无显式风险提示。")}</p>
                </div>
              </article>
            ))
          ) : (
            <article className="empty-card">
              <h3>当前日期没有低位研究题材</h3>
              <p>你可以点击右侧按钮执行一次低位挖掘，或者切换到已有结果的日期。</p>
            </article>
          )}
        </div>
      </section>

      <section className="section-card">
        <div className="section-title">
          <div>
            <span className="section-kicker">Message Dossiers</span>
            <h2>代表性消息链路</h2>
            <p>这里保留少量消息卡，帮助你理解某条消息为何进入低位研究，以及最终映射到了哪些公司。</p>
          </div>
          <Link className="text-link" href={buildHref("/workbench", { date: workbench.date })}>
            去总览页查看全链路
          </Link>
        </div>
        <div className="issue-grid">
          {workbench.messages.slice(0, 6).map((row) => (
            <article key={row.message.message_id} className="issue-card">
              <span className="section-kicker">{fermentationVerdictLabel(row.fermentation.fermentation_verdict)}</span>
              <h3>{safeText(row.message.title, "未命名消息")}</h3>
              <p>{safeText(row.impact.impact_summary || row.message.summary, "暂无消息摘要。")}</p>
              <div className="pill-row">
                <span className="pill">行动 {formatScore(row.score.recalibrated_actionability_score)}</span>
                <span className="pill">{validationLabel(row.validation.validation_status)}</span>
              </div>
              <p className="muted-copy">相关公司：{messageCompanyNames(row).join(" / ") || "暂无相关公司"}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="cta-panel">
        <div>
          <span className="section-kicker">Research Flow</span>
          <h2>这一页是专题研究页，不负责做全景对照。</h2>
          <p>当你需要横向比较主线、低位、证据带和消息链路时，再进入工作台总览。</p>
        </div>
        <div className="link-row">
          <Link className="link-button is-secondary" href={buildHref("/", { date: workbench.date })}>
            返回今日入口
          </Link>
          <Link className="link-button is-primary" href={buildHref("/workbench", { date: workbench.date })}>
            进入工作台总览
          </Link>
        </div>
      </section>
    </main>
  );
}

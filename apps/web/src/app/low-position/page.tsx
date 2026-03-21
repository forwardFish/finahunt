import type { Route } from "next";
import Link from "next/link";

import { RunLowPositionButton } from "@/components/RunLowPositionButton";
import { loadLowPositionWorkbench, resolveWorkbenchDate, type ThemeRow } from "@/lib/lowPositionWorkbench";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type ViewMode = "messages" | "themes";

function resolveViewMode(value: string | string[] | undefined): ViewMode {
  return value === "themes" ? "themes" : "messages";
}

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(1);
}

function formatTime(value: string): string {
  return value ? value.replace("T", " ").replace("+00:00", " UTC") : "-";
}

function buildHref(date: string, view: ViewMode): Route {
  return `/low-position?date=${date}&view=${view}` as Route;
}

function verdictLabel(value: string): string {
  const labels: Record<string, string> = {
    high: "高潜力",
    medium: "中潜力",
    low: "弱潜力",
    reject: "不进入发酵链路",
    confirmed: "验证通过",
    partial: "部分兑现",
    no_reaction: "无明显反应",
    delayed_reaction: "滞后反应",
    inverse_reaction: "反向反应",
    unverifiable: "待验证",
  };
  return labels[value] || value || "-";
}

function renderThemeGroup(title: string, themes: ThemeRow[]) {
  return (
    <section className="mini-panel">
      <h4>{title}</h4>
      {themes.length ? (
        <ul className="plain-list">
          {themes.map((theme) => (
            <li key={`${title}-${theme.theme_name}`}>
              <strong>{theme.theme_name}</strong>
              {` · 低位分 ${formatScore(theme.low_position_score)} · ${theme.validation_bucket}`}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted-copy">当前没有对应题材。</p>
      )}
    </section>
  );
}

export default async function LowPositionPage({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveWorkbenchDate(params.date);
  const view = resolveViewMode(params.view);
  const workbench = loadLowPositionWorkbench(date);

  return (
    <main className="page-stack">
      <section className="hero-shell home-hero" data-card>
        <div className="hero-grid home-hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Low-position Workbench</span>
            <h1>把当天消息压缩成一条可验证、可校正的低位挖掘链路。</h1>
            <p className="hero-copy-text">
              工作台固定围绕“消息、发酵判断、影响分析、相关公司、公司理由、市场验证与自我修复、综合评分”展开。
              你只需要执行一次，就能直接看到当天更值得研究的消息和题材。
            </p>

            <div className="toolbar toolbar-split">
              <form action="/low-position" className="toolbar" method="get">
                <input aria-label="切换工作台日期" defaultValue={workbench.date} name="date" type="date" />
                <input name="view" type="hidden" value={view} />
                <button type="submit">切换日期</button>
              </form>

              <div className="toolbar nav-links">
                <Link className="ghost-link" href={"/" as Route}>
                  返回首页
                </Link>
                <Link className="ghost-link" href={`/sprint-2?date=${workbench.date}&focus=all&reason=compare` as Route}>
                  查看 Sprint 2 页面
                </Link>
              </div>
            </div>

            <div className="status-strip" data-metric-strip>
              <article className={`status-card tone-${workbench.state}`} data-stat="run-state">
                <span>页面状态</span>
                <strong>
                  {workbench.state === "success" ? "已生成" : workbench.state === "partial" ? "部分可用" : "暂无数据"}
                </strong>
                <p>
                  {workbench.state === "success"
                    ? "当天消息链路和题材链路都已生成，可以直接核对每条消息的公司、理由和市场验证结果。"
                    : workbench.state === "partial"
                      ? "运行已完成，但仍有部分消息缺少市场验证数据或阶段结果。"
                      : "当前日期还没有低位挖掘工作台数据，请先执行一次一键运行。"}
                </p>
              </article>

              <article className="status-card" data-stat="message-count">
                <span>消息数量</span>
                <strong>{workbench.messageCount}</strong>
                <p>当天进入低位挖掘链路的标准消息数量。</p>
              </article>

              <article className="status-card" data-stat="theme-count">
                <span>题材数量</span>
                <strong>{workbench.themeCount}</strong>
                <p>从消息链路反推出的题材数量。</p>
              </article>
            </div>
          </div>

          <aside className="hero-aside panel-card" data-card>
            <div className="aside-head">
              <span className="pill accent">最新运行</span>
              <span className="aside-timestamp">{formatTime(workbench.createdAt)}</span>
            </div>
            <h2>一键执行低位挖掘</h2>
            <p className="aside-copy">
              这个入口会一次性跑完消息处理、发酵判断、影响分析、相关公司、理由、市场验证和校正评分，再刷新成可阅读的工作台结果。
            </p>

            <div className="aside-stat-grid">
              <div className="aside-stat">
                <span>Run ID</span>
                <strong>{workbench.runId || "-"}</strong>
              </div>
              <div className="aside-stat">
                <span>最近可用日期</span>
                <strong>{workbench.latestAvailableDate}</strong>
              </div>
            </div>

            <RunLowPositionButton latestRunId={workbench.runId} />
          </aside>
        </div>
      </section>

      <section className="section-shell">
        <div className="section-head">
          <div>
            <span className="eyebrow">View Switch</span>
            <h2>{view === "messages" ? "消息视图" : "题材视图"}</h2>
          </div>

          <div className="toolbar nav-links">
            <Link className={`focus-tab ${view === "messages" ? "is-active" : ""}`} href={buildHref(workbench.date, "messages")}>
              消息视图
            </Link>
            <Link className={`focus-tab ${view === "themes" ? "is-active" : ""}`} href={buildHref(workbench.date, "themes")}>
              题材视图
            </Link>
          </div>
        </div>

        <article className="panel-card" data-card>
          <h3>阶段状态</h3>
          <div className="workbench-stage-grid">
            {workbench.stages.length ? (
              workbench.stages.map((item) => (
                <div key={item.stage} className="stage-chip" data-stage-status={item.status}>
                  <span>{item.label}</span>
                  <strong>{item.status}</strong>
                </div>
              ))
            ) : (
              <p className="muted-copy">当前还没有阶段运行记录。</p>
            )}
          </div>
        </article>

        {view === "messages" ? (
          workbench.messages.length ? (
            workbench.messages.map((row) => (
              <article key={row.message.message_id} className="panel-card message-workbench-card" data-card>
                <div className="section-head">
                  <div>
                    <span className="eyebrow">{row.message.value_label}</span>
                    <h3>{row.message.title}</h3>
                    <p className="muted-copy">{row.message.summary || "暂无摘要。"}</p>
                  </div>
                  <div className="score-badge">
                    <span>校正后评分</span>
                    <strong>{formatScore(row.score.recalibrated_actionability_score)}</strong>
                  </div>
                </div>

                <div className="message-meta-grid">
                  <div className="mini-panel">
                    <span>消息时间</span>
                    <strong>{formatTime(row.message.event_time)}</strong>
                  </div>
                  <div className="mini-panel">
                    <span>消息来源</span>
                    <strong>{row.message.source_name || "-"}</strong>
                  </div>
                  <div className="mini-panel">
                    <span>主影响题材</span>
                    <strong>{row.impact.primary_theme || "-"}</strong>
                  </div>
                  <div className="mini-panel">
                    <span>预期时长</span>
                    <strong>{row.impact.impact_horizon || "-"}</strong>
                  </div>
                </div>

                <div className="workbench-grid">
                  <section className="mini-panel">
                    <h4>是否可能发酵</h4>
                    <p>{verdictLabel(row.fermentation.fermentation_verdict)}</p>
                    <ul className="plain-list">
                      <li>发酵分：{formatScore(row.fermentation.fermentation_score)}</li>
                      <li>共识阶段：{row.fermentation.consensus_stage || "-"}</li>
                    </ul>
                    <ul className="plain-list">
                      {(row.fermentation.why_it_may_ferment || []).map((item) => (
                        <li key={`ferment-${row.message.message_id}-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </section>

                  <section className="mini-panel">
                    <h4>可能带来的影响</h4>
                    <p>{row.impact.impact_summary || "当前还没有形成结构化影响分析。"}</p>
                    <ul className="plain-list">
                      <li>方向：{row.impact.impact_direction || "-"}</li>
                      <li>路径：{row.impact.impact_path || "-"}</li>
                      <li>题材置信度：{formatScore(row.impact.theme_confidence)}</li>
                    </ul>
                  </section>
                </div>

                <section className="mini-panel">
                  <h4>相关公司</h4>
                  {row.companies.length ? (
                    <div className="company-grid">
                      {row.companies.map((company) => (
                        <article key={`${row.message.message_id}-${company.company_code || company.company_name}`} className="company-card">
                          <div className="company-head">
                            <div>
                              <strong>{company.company_name}</strong>
                              <span>{company.company_code || "待补代码"}</span>
                            </div>
                            <span className="pill">{company.role_label}</span>
                          </div>

                          <p className="muted-copy">{company.reason_summary}</p>

                          <ul className="plain-list">
                            <li>相关度：{formatScore(company.relevance_score)}</li>
                            <li>正宗度：{formatScore(company.purity_score)}</li>
                            <li>候选状态：{company.candidate_status}</li>
                          </ul>

                          <div className="reason-block">
                            <strong>公开证据</strong>
                            <p>{company.source_reason || "pending_source_evidence"}</p>
                            {company.source_reason_url ? (
                              <a className="reason-link" href={company.source_reason_url} target="_blank" rel="noreferrer">
                                {company.source_reason_title || "打开来源"}
                              </a>
                            ) : null}
                            {company.source_evidence_items?.length ? (
                              <ul className="plain-list">
                                {company.source_evidence_items.map((item, index) => (
                                  <li key={`${company.company_name}-evidence-${index}`}>
                                    <strong>{item.source_title || item.source_site || "公开来源"}</strong>
                                    {item.source_excerpt ? `：${item.source_excerpt}` : ""}
                                  </li>
                                ))}
                              </ul>
                            ) : null}
                          </div>

                          <div className="reason-block">
                            <strong>LLM 总结</strong>
                            <p>{company.llm_reason || "当前还没有模型总结。"}</p>
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="muted-copy">当前还没有关联公司。</p>
                  )}
                </section>

                <div className="workbench-grid">
                  <section className="mini-panel">
                    <h4>市场验证与自我修复</h4>
                    <p>{row.validation.validation_summary || "当前还没有足够市场数据完成验证。"}</p>
                    <ul className="plain-list">
                      <li>验证状态：{verdictLabel(row.validation.validation_status)}</li>
                      <li>验证窗口：{row.validation.validation_window || "-"}</li>
                      <li>篮子 T1 涨幅：{formatScore(row.validation.observed_basket_move?.T1_CLOSE)}</li>
                      <li>基准 T1 涨幅：{formatScore(row.validation.observed_benchmark_move?.T1_CLOSE)}</li>
                      <li>超额收益：{formatScore(row.validation.excess_return)}</li>
                      <li>校正动作：{row.validation.calibration_action || "-"}</li>
                    </ul>
                    <p>{row.validation.prediction_gap || "-"}</p>
                    <p>{row.validation.calibration_reason || "-"}</p>
                  </section>

                  <section className="mini-panel">
                    <h4>综合评分</h4>
                    <ul className="plain-list">
                      <li>消息价值：{formatScore(row.score.importance_score)}</li>
                      <li>发酵质量：{formatScore(row.score.fermentation_score)}</li>
                      <li>影响质量：{formatScore(row.score.impact_quality_score)}</li>
                      <li>公司挖掘：{formatScore(row.score.company_discovery_score)}</li>
                      <li>理由质量：{formatScore(row.score.reason_quality_score)}</li>
                      <li>市场验证：{formatScore(row.score.market_validation_score)}</li>
                      <li>初始评分：{formatScore(row.score.initial_actionability_score)}</li>
                      <li>校正后评分：{formatScore(row.score.recalibrated_actionability_score)}</li>
                    </ul>
                    <p>{row.score.score_summary || "暂无评分总结。"}</p>
                  </section>
                </div>
              </article>
            ))
          ) : (
            <article className="empty-state-card" data-card>
              <h3>当前日期还没有消息工作台结果</h3>
              <p>请先点击“立即执行低位挖掘”，或者切换到已有结果的日期。</p>
            </article>
          )
        ) : (
          <>
            <div className="workbench-grid">
              {renderThemeGroup("验证通过题材", workbench.validatedThemes)}
              {renderThemeGroup("观察中题材", workbench.watchThemes)}
              {renderThemeGroup("被校正降级题材", workbench.downgradedThemes)}
            </div>

            {workbench.themes.length ? (
              workbench.themes.map((theme) => (
                <article key={theme.theme_name} className="panel-card theme-workbench-card" data-card>
                  <div className="section-head">
                    <div>
                      <span className="eyebrow">{theme.validation_bucket}</span>
                      <h3>{theme.theme_name}</h3>
                    </div>
                    <div className="score-badge">
                      <span>低位分</span>
                      <strong>{formatScore(theme.low_position_score)}</strong>
                    </div>
                  </div>

                  <p>{theme.low_position_reason || "当前还没有低位研究结论。"}</p>

                  <div className="workbench-grid">
                    <section className="mini-panel">
                      <h4>关联消息</h4>
                      <ul className="plain-list">
                        {theme.messages.length ? (
                          theme.messages.map((item) => (
                            <li key={item.message_id}>
                              {item.title} · {formatScore(item.score)} · {verdictLabel(item.validation_status)}
                            </li>
                          ))
                        ) : (
                          <li>当前还没有回挂到消息链路。</li>
                        )}
                      </ul>
                    </section>

                    <section className="mini-panel">
                      <h4>候选公司</h4>
                      <ul className="plain-list">
                        {theme.candidate_stocks.length ? (
                          theme.candidate_stocks.slice(0, 5).map((item, index) => (
                            <li key={`${theme.theme_name}-${index}`}>{String(item["stock_name"] || item["name"] || "未命名候选")}</li>
                          ))
                        ) : (
                          <li>当前还没有候选公司。</li>
                        )}
                      </ul>
                    </section>
                  </div>

                  <section className="mini-panel">
                    <h4>风险提示</h4>
                    <p>{theme.risk_notice || "当前没有新增风险提示。"}</p>
                  </section>
                </article>
              ))
            ) : (
              <article className="empty-state-card" data-card>
                <h3>当前日期还没有题材工作台结果</h3>
                <p>先执行一次低位挖掘，或者切换到已有结果的日期。</p>
              </article>
            )}
          </>
        )}
      </section>
    </main>
  );
}

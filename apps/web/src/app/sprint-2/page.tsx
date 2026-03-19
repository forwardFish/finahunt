import type { Route } from "next";
import Link from "next/link";

import { RefreshLatestButton } from "@/components/RefreshLatestButton";
import { loadDailySnapshot, resolveTargetDate, type DailyTheme } from "@/lib/dailySnapshot";

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type StageSummary = {
  key: string;
  label: string;
  count: number;
};

type FocusMode = "all" | "fermentation" | "research";
type ReasonMode = "source" | "llm" | "compare";

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

function resolveFocusMode(value: string | string[] | undefined): FocusMode {
  if (value === "fermentation" || value === "research") {
    return value;
  }
  return "all";
}

function resolveReasonMode(value: string | string[] | undefined): ReasonMode {
  if (value === "source" || value === "llm") {
    return value;
  }
  return "compare";
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

function summarizeStages(themes: DailyTheme[]): StageSummary[] {
  const stages = new Map<string, StageSummary>([
    ["hot", { key: "hot", label: "拥挤扩散", count: 0 }],
    ["fermenting", { key: "fermenting", label: "持续发酵", count: 0 }],
    ["emerging", { key: "emerging", label: "早期成形", count: 0 }],
    ["watch-only", { key: "watch-only", label: "观察等待", count: 0 }],
    ["watching", { key: "watching", label: "观察等待", count: 0 }],
  ]);

  for (const theme of themes) {
    const key = theme.fermentationStage || "watch-only";
    const current = stages.get(key);
    if (current) {
      current.count += 1;
      continue;
    }
    stages.set(key, { key, label: stageLabel(key), count: 1 });
  }

  return Array.from(stages.values()).filter((item) => item.count > 0);
}

function topThemes(themes: DailyTheme[]): DailyTheme[] {
  return [...themes].sort((left, right) => right.fermentationScore - left.fermentationScore).slice(0, 8);
}

function lowPositionThemes(themes: DailyTheme[]): DailyTheme[] {
  return [...themes]
    .filter((item) => item.lowPositionScore !== null)
    .sort((left, right) => (right.lowPositionScore ?? 0) - (left.lowPositionScore ?? 0))
    .slice(0, 8);
}

function focusLabel(mode: FocusMode): string {
  if (mode === "fermentation") {
    return "发酵主题";
  }
  if (mode === "research") {
    return "低位研究";
  }
  return "全景视图";
}

function focusDescription(mode: FocusMode): string {
  if (mode === "fermentation") {
    return "优先查看正在升温并逐步形成共识的主线主题。";
  }
  if (mode === "research") {
    return "优先查看仍在低位、但已经值得建立跟踪的研究机会。";
  }
  return "同时浏览主线发酵、低位研究、矩阵比较与证据带。";
}

function reasonLabel(mode: ReasonMode): string {
  if (mode === "source") {
    return "原始证据";
  }
  if (mode === "llm") {
    return "模型摘要";
  }
  return "对照视图";
}

function reasonDescription(mode: ReasonMode): string {
  if (mode === "source") {
    return "偏原始材料，适合核对事实和来源。";
  }
  if (mode === "llm") {
    return "偏研究摘要，适合快速扫清今天的主要结论。";
  }
  return "同时看原始证据和模型总结，便于判断概括是否失真。";
}

function buildFocusHref(date: string, focus: FocusMode, reasonMode: ReasonMode): Route {
  return `/sprint-2?date=${date}&focus=${focus}&reason=${reasonMode}` as Route;
}

function buildReasonHref(date: string, focus: FocusMode, reasonMode: ReasonMode): Route {
  return `/sprint-2?date=${date}&focus=${focus}&reason=${reasonMode}` as Route;
}

function similarityLabel(value: string): string {
  if (value === "reignited_logic") {
    return "再发酵参照";
  }
  if (value === "adjacent_pattern") {
    return "邻近路径";
  }
  if (value === "no_reference") {
    return "暂无历史映射";
  }
  return value || "暂无历史映射";
}

function themeName(theme: DailyTheme | undefined): string {
  if (!theme) {
    return "暂无主题";
  }
  return theme.themeName || theme.clusterId || "未命名主题";
}

function densityLabel(theme: DailyTheme | undefined): string {
  if (!theme) {
    return "暂无信号";
  }
  const density = theme.sourceCount + theme.relatedEventsCount;
  if (density >= 12) {
    return "高密度";
  }
  if (density >= 6) {
    return "中密度";
  }
  return "低密度";
}

function candidateReason(
  stock: DailyTheme["candidateStocks"][number],
  reasonMode: ReasonMode,
): string {
  if (reasonMode === "source") {
    return stock.sourceReason || stock.sourceReasonExcerpt || stock.mappingReason || "当前还没有提取到可直接核对的原始证据。";
  }
  if (reasonMode === "llm") {
    return stock.llmReason || stock.mappingReason || stock.judgeExplanation || "当前还没有生成可用的模型摘要。";
  }
  return (
    [
      stock.sourceReason ? `原始证据：${stock.sourceReason}` : "",
      stock.llmReason ? `模型摘要：${stock.llmReason}` : "",
    ]
      .filter(Boolean)
      .join(" | ") ||
    stock.mappingReason ||
    stock.judgeExplanation ||
    "当前还没有形成完整的双视角解释。"
  );
}

function summarizeWorkbenchState(
  runCount: number,
  leadersCount: number,
  researchCount: number,
): { tone: "ready" | "partial" | "empty"; label: string; description: string } {
  if (runCount === 0) {
    return {
      tone: "empty",
      label: "空白状态",
      description: "当前日期没有可展示的研究工作台数据，请先抓取最新运行或切换日期。",
    };
  }
  if (leadersCount === 0 || researchCount === 0) {
    return {
      tone: "partial",
      label: "部分数据",
      description: "今天已有工作台数据，但主线发酵或低位研究仍有一部分板块在补齐。",
    };
  }
  return {
    tone: "ready",
    label: "工作台已就绪",
    description: "主线发酵、低位研究、证据矩阵与风险边界都已进入可浏览状态。",
  };
}

export default async function Sprint2Page({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const focus = resolveFocusMode(params.focus);
  const reasonMode = resolveReasonMode(params.reason);
  const snapshot = loadDailySnapshot(date);
  const stages = summarizeStages(snapshot.themes);
  const leaders = topThemes(snapshot.themes);
  const lowPosition = lowPositionThemes(snapshot.themes);
  const topFermentation = leaders[0];
  const topResearch = lowPosition[0];
  const evidenceTape = leaders.flatMap((theme) =>
    theme.topEvidence.slice(0, 1).map((item) => ({
      key: `${theme.key}-${item.title}`,
      themeName: theme.themeName || theme.clusterId,
      title: item.title,
      summary: item.summary,
      eventTime: item.eventTime,
    })),
  );
  const workbenchState = summarizeWorkbenchState(snapshot.stats.runCount, leaders.length, lowPosition.length);
  const showFermentation = focus === "all" || focus === "fermentation";
  const showResearch = focus === "all" || focus === "research";
  const latestRun = snapshot.runs[0];
  const sharedRiskLead =
    snapshot.commonRiskNotices[0] || "本页用于研究观察，不构成交易建议，重点在于跟踪公开信息形成的节奏与证据。";

  return (
    <main className="page-stack sprint-page">
      <section className="hero-shell sprint-hero sprint-hero-product" data-card>
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="eyebrow">Sprint 2 Research Cockpit</span>
            <h1>把今天的主线、低位机会、证据和风险放进同一张研究桌面。</h1>
            <p className="hero-copy-text">
              Sprint 2 不是原始日志页，而是研究工作台。你可以在这里先看主线发酵是否成形，再看低位研究是否有足够证据，最后回到统一风险边界。
            </p>

            <div className="toolbar toolbar-split sprint-toolbar">
              <form action="/sprint-2" className="toolbar" method="get">
                <input aria-label="切换快照日期" defaultValue={snapshot.date} name="date" type="date" />
                <input name="focus" type="hidden" value={focus} />
                <input name="reason" type="hidden" value={reasonMode} />
                <button type="submit">切换日期</button>
              </form>

              <div className="toolbar nav-links">
                <Link className="ghost-link" href={`/?date=${snapshot.date}` as Route}>
                  回到首页入口
                </Link>
                <span className="pill">最新批次：{latestRun?.runId || "-"}</span>
              </div>
            </div>

            <div className="focus-tabs">
              {(["all", "fermentation", "research"] as const).map((item) => (
                <Link
                  className={`focus-tab ${focus === item ? "active" : ""}`}
                  href={buildFocusHref(snapshot.date, item, reasonMode)}
                  key={item}
                >
                  {focusLabel(item)}
                </Link>
              ))}
            </div>

            <div className="focus-tabs">
              {(["compare", "source", "llm"] as const).map((item) => (
                <Link
                  className={`focus-tab ${reasonMode === item ? "active" : ""}`}
                  href={buildReasonHref(snapshot.date, focus, item)}
                  key={item}
                >
                  {reasonLabel(item)}
                </Link>
              ))}
            </div>

            <div className="status-strip sprint-metric-grid" data-metric-strip>
              <article className={`status-card tone-${workbenchState.tone}`} data-stat="workbench-state">
                <span>工作台状态</span>
                <strong>{workbenchState.label}</strong>
                <p>{workbenchState.description}</p>
              </article>
              <article className="status-card" data-stat="focus-mode">
                <span>当前视图</span>
                <strong>{focusLabel(focus)}</strong>
                <p>{focusDescription(focus)}</p>
              </article>
              <article className="status-card" data-stat="reason-mode">
                <span>解释模式</span>
                <strong>{reasonLabel(reasonMode)}</strong>
                <p>{reasonDescription(reasonMode)}</p>
              </article>
              <article className="status-card" data-stat="risk-frame">
                <span>研究边界</span>
                <strong>研究观察优先</strong>
                <p>{sharedRiskLead}</p>
              </article>
            </div>
          </div>

          <aside className="hero-aside panel-card" data-card>
            <div className="aside-head">
              <span className="pill accent">今日判断</span>
              <span className="aside-timestamp">{formatIso(latestRun?.createdAt ?? "")}</span>
            </div>
            <h2>先判断，后深挖。</h2>
            <p className="aside-copy">工作台先告诉你今天最值得追哪条主线、最值得研究哪个低位机会，以及现在处在哪个证据密度区间。</p>

            <div className="aside-highlight-grid">
              <article className="aside-highlight">
                <span>Lead Fermentation</span>
                <strong>{themeName(topFermentation)}</strong>
                <p>{topFermentation ? `${stageLabel(topFermentation.fermentationStage)} / ${densityLabel(topFermentation)}` : "暂无发酵主线"}</p>
              </article>
              <article className="aside-highlight">
                <span>Research Priority</span>
                <strong>{themeName(topResearch)}</strong>
                <p>{topResearch ? `低位分数 ${formatScore(topResearch.lowPositionScore)}` : "暂无低位研究目标"}</p>
              </article>
            </div>

            <div className="aside-stat-grid">
              <div className="aside-stat" data-stat="run-count">
                <span>运行批次</span>
                <strong>{snapshot.stats.runCount}</strong>
              </div>
              <div className="aside-stat" data-stat="theme-count">
                <span>主题数量</span>
                <strong>{snapshot.stats.themeCount}</strong>
              </div>
              <div className="aside-stat" data-stat="low-position-count">
                <span>低位机会</span>
                <strong>{snapshot.stats.lowPositionCount}</strong>
              </div>
              <div className="aside-stat" data-stat="fermentation-count">
                <span>发酵主题</span>
                <strong>{snapshot.stats.fermentingThemeCount}</strong>
              </div>
            </div>

            <RefreshLatestButton
              latestRunId={latestRun?.runId ?? ""}
              successParams={{ focus, reason: reasonMode }}
              successPath="/sprint-2"
            />
          </aside>
        </div>

        <div className="insight-strip">
          <article className="insight-card panel-card" data-card>
            <span className="section-kicker">Decision Strip</span>
            <h3>{themeName(topFermentation)}</h3>
            <p>{topFermentation?.coreNarrative || "当前还没有形成稳定主线，建议继续查看证据带与矩阵对照。"}</p>
            <div className="pill-row">
              <span className="pill accent">发酵 {formatScore(topFermentation?.fermentationScore ?? null)}</span>
              <span className="pill good">{stageLabel(topFermentation?.fermentationStage || "")}</span>
              <span className="pill">{densityLabel(topFermentation)}</span>
            </div>
          </article>

          <article className="insight-card panel-card" data-card>
            <span className="section-kicker">Research Queue</span>
            <h3>{themeName(topResearch)}</h3>
            <p>{topResearch?.lowPositionReason || topResearch?.coreNarrative || "当前还没有形成稳定的低位研究结论。"}</p>
            <div className="pill-row">
              <span className="pill warn">低位 {formatScore(topResearch?.lowPositionScore ?? null)}</span>
              <span className="pill">催化 {formatScore(topResearch?.catalystScore ?? null)}</span>
              <span className="pill">持续性 {formatScore(topResearch?.continuityScore ?? null)}</span>
            </div>
          </article>

          <article className="insight-card panel-card" data-card data-risk-section>
            <span className="section-kicker">Risk Boundary</span>
            <h3>统一风险边界</h3>
            <p>{sharedRiskLead}</p>
            <div className="pill-row">
              <span className="pill">研究观察</span>
              <span className="pill warn">不构成交易建议</span>
            </div>
          </article>
        </div>
      </section>

      <section className="section-shell">
        <div className="section-head">
          <div>
            <span className="section-kicker">Stage Strip</span>
            <h2>主线阶段分布</h2>
            <p>先看今天的主题分布在哪些阶段，再决定接下来把注意力放在哪里。</p>
          </div>
        </div>

        <div className="stage-strip">
          {stages.map((stage) => (
            <article className="stage-card" data-stat={stage.key} key={stage.key}>
              <span>{stage.label}</span>
              <strong>{stage.count}</strong>
            </article>
          ))}
        </div>
      </section>

      {showFermentation ? (
        <section className="section-shell">
          <div className="section-head">
            <div>
              <span className="section-kicker">Fermentation Board</span>
              <h2>主线发酵主题</h2>
              <p>先看主线是否成形，再看证据密度、催化强度与当前阶段，不把发酵和原始卡片混在一起读。</p>
            </div>
          </div>

          {leaders.length ? (
            <div className="board-grid">
              {leaders.map((theme) => (
                <article className="board-card panel-card" data-card key={theme.key}>
                  <div className="meta-row">
                    <span className="pill accent">{themeName(theme)}</span>
                    <span className="pill good">{stageLabel(theme.fermentationStage)}</span>
                    <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                  </div>
                  <h3>{themeName(theme)}</h3>
                  <p>{theme.coreNarrative || "当前还没有补齐足够清晰的核心叙事，建议先看关键信号和时间线。"}</p>

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
                    <div>
                      <span>来源数</span>
                      <strong>{theme.sourceCount}</strong>
                    </div>
                  </div>

                  <p className="muted">首次出现 {formatIso(theme.firstSeenTime)} / 最近活跃 {formatIso(theme.latestSeenTime)}</p>

                  {theme.topEvidence.length ? (
                    <div className="detail-block" data-evidence-block>
                      <strong>关键证据</strong>
                      <div className="stack-list">
                        {theme.topEvidence.slice(0, 2).map((evidence) => (
                          <div className="evidence-card" key={`${theme.key}-${evidence.title}`}>
                            <strong>{evidence.title}</strong>
                            <span className="muted">{formatIso(evidence.eventTime)}</span>
                            <p>{evidence.summary || "暂无摘要。"}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  <div className="card-actions">
                    <span className="muted">{theme.relatedEventsCount} 个关联事件</span>
                    <Link href={buildReasonHref(snapshot.date, "fermentation", "compare")}>切到对照视图</Link>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <article className="empty-state-card tone-partial panel-card" data-card>
              <span className="section-kicker">Partial State</span>
              <h3>今天还没有形成稳定的发酵主线</h3>
              <p>保留研究工作台结构，等待更多公开信号把主线推到可浏览状态。</p>
            </article>
          )}
        </section>
      ) : null}

      {showResearch ? (
        <section className="section-shell">
          <div className="section-head">
            <div>
              <span className="section-kicker">Research Queue</span>
              <h2>低位研究机会</h2>
              <p>这里展示的是研究优先级，不是交易指令。重点是判断低位主题是否已经具备可跟踪的证据、候选标的和后续观察信号。</p>
            </div>
          </div>

          {lowPosition.length ? (
            <div className="board-grid">
              {lowPosition.map((theme) => (
                <article className="board-card research-card panel-card" data-card key={theme.key}>
                  <div className="meta-row">
                    <span className="pill warn">优先级 {formatScore(theme.lowPositionScore)}</span>
                    <span className="pill good">{stageLabel(theme.fermentationStage)}</span>
                    {theme.referenceType ? <span className="pill">{similarityLabel(theme.referenceType)}</span> : null}
                  </div>
                  <h3>{themeName(theme)}</h3>
                  <p>{theme.lowPositionReason || theme.coreNarrative || "当前还没有补齐足够完整的低位研究叙述。"}</p>

                  <div className="pill-row">
                    <span className="pill">热度 {formatScore(theme.heatScore)}</span>
                    <span className="pill">催化 {formatScore(theme.catalystScore)}</span>
                    <span className="pill">持续性 {formatScore(theme.continuityScore)}</span>
                    <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                    {theme.topCandidatePurityScore !== null ? (
                      <span className="pill accent">纯度 {formatScore(theme.topCandidatePurityScore)}</span>
                    ) : null}
                  </div>

                  {theme.candidateStocks.length ? (
                    <div className="detail-block" data-evidence-block>
                      <strong>候选标的与研究理由</strong>
                      <div className="stack-list">
                        {theme.candidateStocks.slice(0, 3).map((stock) => (
                          <article className="list-card" key={`${theme.key}-${stock.code}-${stock.name}`}>
                            <div>
                              <strong>{stock.name || stock.code || "候选标的"}</strong>
                              <p className="muted">{candidateReason(stock, reasonMode)}</p>
                            </div>
                            <div className="pill-row">
                              {stock.code ? <span className="pill">{stock.code}</span> : null}
                              {stock.score !== null ? <span className="pill warn">纯度 {formatScore(stock.score)}</span> : null}
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {theme.similarCases.length ? (
                    <div className="detail-block">
                      <strong>历史参照</strong>
                      <div className="stack-list">
                        {theme.similarCases.slice(0, 2).map((item) => (
                          <article className="list-card" key={`${theme.key}-${item.runId}-${item.themeName}`}>
                            <div>
                              <strong>{item.themeName || item.runId}</strong>
                              <p className="muted">{item.historicalPathSummary || "暂无历史路径摘要。"}</p>
                            </div>
                            <div className="pill-row">
                              <span className="pill">{similarityLabel(item.referenceType)}</span>
                              {item.similarityScore !== null ? (
                                <span className="pill">相似度 {formatScore(item.similarityScore)}</span>
                              ) : null}
                            </div>
                          </article>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {theme.futureWatchSignals.length ? (
                    <div className="detail-block">
                      <strong>后续观察信号</strong>
                      <ul className="signal-list">
                        {theme.futureWatchSignals.slice(0, 4).map((item) => (
                          <li key={`${theme.key}-${item}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {theme.latestCatalysts.length ? (
                    <div className="detail-block" data-evidence-block>
                      <strong>近 24h 关键催化</strong>
                      <div className="stack-list">
                        {theme.latestCatalysts.slice(0, 2).map((evidence) => (
                          <div className="evidence-card" key={`${theme.key}-${evidence.title}`}>
                            <strong>{evidence.title}</strong>
                            <span className="muted">{formatIso(evidence.eventTime)}</span>
                            <p>{evidence.summary || "暂无摘要。"}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {theme.riskFlags.length ? (
                    <div className="detail-block" data-risk-section>
                      <strong>风险与削弱提示</strong>
                      <ul className="signal-list">
                        {theme.riskFlags.slice(0, 4).map((item) => (
                          <li key={`${theme.key}-${item}`}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <article className="empty-state-card tone-partial panel-card" data-card>
              <span className="section-kicker">Partial State</span>
              <h3>今天还没有足够稳定的低位研究卡片</h3>
              <p>工作台结构会保留，但候选标的、历史参照与后续观察信号仍需要更多公开证据补齐。</p>
            </article>
          )}
        </section>
      ) : null}

      {focus === "all" ? (
        <>
          <section className="section-shell">
            <div className="section-head">
              <div>
                <span className="section-kicker">Matrix View</span>
                <h2>主题矩阵</h2>
                <p>把当天所有主题拉到一张对照表里，横向比较热度、催化、持续性和研究优先级。</p>
              </div>
            </div>

            <div className="table-shell product-table" data-matrix-section>
              <table className="board-table">
                <thead>
                  <tr>
                    <th>主题</th>
                    <th>阶段</th>
                    <th>研究优先级</th>
                    <th>发酵</th>
                    <th>热度</th>
                    <th>催化</th>
                    <th>持续性</th>
                    <th>来源</th>
                    <th>事件</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshot.themes.map((theme) => (
                    <tr key={theme.key}>
                      <td>{themeName(theme)}</td>
                      <td>{stageLabel(theme.fermentationStage)}</td>
                      <td>{formatScore(theme.lowPositionScore)}</td>
                      <td>{formatScore(theme.fermentationScore)}</td>
                      <td>{formatScore(theme.heatScore)}</td>
                      <td>{formatScore(theme.catalystScore)}</td>
                      <td>{formatScore(theme.continuityScore)}</td>
                      <td>{theme.sourceCount}</td>
                      <td>{theme.relatedEventsCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="section-shell">
            <div className="section-head">
              <div>
                <span className="section-kicker">Evidence Tape</span>
                <h2>一眼看懂今天的证据主线</h2>
                <p>把领先主题的第一条关键线索压成一条证据带，帮助你快速判断今天的研究是否有抓手。</p>
              </div>
            </div>

            {evidenceTape.length ? (
              <div className="evidence-grid" data-evidence-block>
                {evidenceTape.map((item) => (
                  <article className="evidence-card panel-card" data-card key={item.key}>
                    <span className="pill accent">{item.themeName}</span>
                    <h3>{item.title}</h3>
                    <p>{item.summary || "暂无摘要。"}</p>
                    <p className="muted">{formatIso(item.eventTime)}</p>
                  </article>
                ))}
              </div>
            ) : (
              <article className="empty-state-card tone-partial panel-card" data-card>
                <span className="section-kicker">Partial State</span>
                <h3>当前还没有足够稳定的证据带</h3>
                <p>工作台结构已经准备好，但领先主题仍需要更多可展示的证据对象才能形成完整证据带。</p>
              </article>
            )}
          </section>
        </>
      ) : null}

      <section className="section-shell" data-risk-section>
        <div className="section-head">
          <div>
            <span className="section-kicker">Risk & Method</span>
            <h2>统一风险提示与方法边界</h2>
            <p>把通用风险和研究边界集中放在最后，避免在每张卡片里重复稀释注意力。</p>
          </div>
        </div>

        <div className="split-grid">
          <article className="panel-card" data-card>
            <h3>统一风险提示</h3>
            {snapshot.commonRiskNotices.length ? (
              <ul className="signal-list">
                {snapshot.commonRiskNotices.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">当前没有集中风险提示，但仍建议保留单源噪音与时效性判断。</p>
            )}
          </article>

          <article className="panel-card legal-note" data-card>
            <h3>研究工作台，不是交易指令面。</h3>
            <p>
              Sprint 2 聚合的是公开信息抽取、主题聚类、低位研究排序和证据提示，目的是帮助你更快判断哪些主线值得继续跟踪，而不是替代交易决策。
            </p>
            <div className="pill-row">
              <span className="pill">研究观察</span>
              <span className="pill warn">不构成交易建议</span>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}

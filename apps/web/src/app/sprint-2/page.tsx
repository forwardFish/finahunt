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

function summarizeStages(themes: DailyTheme[]): StageSummary[] {
  const stages = new Map<string, StageSummary>([
    ["hot", { key: "hot", label: "拥挤扩散", count: 0 }],
    ["fermenting", { key: "fermenting", label: "持续发酵", count: 0 }],
    ["emerging", { key: "emerging", label: "早期成形", count: 0 }],
    ["watch-only", { key: "watch-only", label: "观察等待", count: 0 }],
    ["watching", { key: "watching", label: "观察等待", count: 0 }]
  ]);

  for (const theme of themes) {
    const key = theme.fermentationStage || "watch-only";
    const current = stages.get(key);
    if (current) {
      current.count += 1;
      continue;
    }
    stages.set(key, { key, label: key, count: 1 });
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
    return "发酵题材";
  }
  if (mode === "research") {
    return "低位研究机会";
  }
  return "全部视图";
}

function buildFocusHref(date: string, focus: FocusMode): string {
  return `/sprint-2?date=${date}&focus=${focus}`;
}

function similarityLabel(value: string): string {
  if (value === "reignited_logic") {
    return "再发酵参考";
  }
  if (value === "adjacent_pattern") {
    return "相邻模式";
  }
  return "暂无历史映射";
}

export default async function Sprint2Page({ searchParams }: PageProps) {
  const params = searchParams ? await searchParams : {};
  const date = resolveTargetDate(params.date);
  const focus = resolveFocusMode(params.focus);
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
      eventTime: item.eventTime
    }))
  );

  const showFermentation = focus === "all" || focus === "fermentation";
  const showResearch = focus === "all" || focus === "research";

  return (
    <main className="page-shell">
      <section className="hero sprint-hero">
        <span className="eyebrow">Sprint 2 Fermentation Board</span>
        <h1>{snapshot.date} 发酵题材总览</h1>
        <p>
          这页专门用来观察 `Sprint 2` 的聚合结果。现在除了“发酵题材”和“低位研究机会”，
          还会把 `S2A-007 / S2A-008` 产出的相似案例、研究卡和未来观察信号一起展开。
        </p>

        <div className="toolbar toolbar-split">
          <form className="toolbar" action="/sprint-2" method="get">
            <input type="date" name="date" defaultValue={snapshot.date} />
            <input type="hidden" name="focus" value={focus} />
            <button type="submit">切换日期</button>
            <RefreshLatestButton latestRunId={snapshot.runs[0]?.runId ?? ""} />
          </form>
          <div className="toolbar nav-links">
            <Link className="ghost-link" href={`/?date=${snapshot.date}`}>
              返回日汇总
            </Link>
            <span className="pill">当前视图: {focusLabel(focus)}</span>
            <span className="pill">存储口径: {snapshot.storageTimezone}</span>
          </div>
        </div>

        <div className="focus-tabs">
          <a className={`focus-tab${focus === "all" ? " active" : ""}`} href={buildFocusHref(snapshot.date, "all")}>
            全部
          </a>
          <a
            className={`focus-tab${focus === "fermentation" ? " active" : ""}`}
            href={buildFocusHref(snapshot.date, "fermentation")}
          >
            发酵题材
          </a>
          <a
            className={`focus-tab${focus === "research" ? " active" : ""}`}
            href={buildFocusHref(snapshot.date, "research")}
          >
            低位研究机会
          </a>
        </div>

        <div className="metric-grid">
          <article className="metric-card">
            <span>纳入运行批次</span>
            <strong>{snapshot.stats.runCount}</strong>
          </article>
          <article className="metric-card">
            <span>发酵题材</span>
            <strong>{snapshot.stats.fermentingThemeCount}</strong>
          </article>
          <article className="metric-card">
            <span>低位研究机会</span>
            <strong>{snapshot.stats.lowPositionCount}</strong>
          </article>
          <article className="metric-card">
            <span>题材总数</span>
            <strong>{snapshot.stats.themeCount}</strong>
          </article>
        </div>

        <div className="stage-strip">
          {stages.map((stage) => (
            <article className="stage-card" key={stage.key}>
              <span>{stage.label}</span>
              <strong>{stage.count}</strong>
            </article>
          ))}
        </div>

        <div className="duo-grid">
          <article className="duo-card card">
            <span className="pill accent">发酵领跑</span>
            <h3>{topFermentation?.themeName || "暂无题材"}</h3>
            <p>{topFermentation?.coreNarrative || "当前没有足够的发酵题材摘要。"}</p>
            <div className="pill-row">
              <span className="pill">发酵 {formatScore(topFermentation?.fermentationScore ?? null)}</span>
              <span className="pill">热度 {formatScore(topFermentation?.heatScore ?? null)}</span>
              <span className="pill good">{topFermentation?.fermentationStage || "-"}</span>
            </div>
          </article>
          <article className="duo-card card">
            <span className="pill warn">研究优先</span>
            <h3>{topResearch?.themeName || "暂无机会"}</h3>
            <p>{topResearch?.lowPositionReason || "当前没有低位研究机会说明。"}</p>
            <div className="pill-row">
              <span className="pill warn">优先级 {formatScore(topResearch?.lowPositionScore ?? null)}</span>
              <span className="pill">发酵 {formatScore(topResearch?.fermentationScore ?? null)}</span>
              <span className="pill good">{topResearch?.fermentationStage || "-"}</span>
            </div>
          </article>
        </div>
      </section>

      {showFermentation ? (
        <section className="section">
          <div className="section-head">
            <div>
              <h2>发酵题材</h2>
              <p>先看叙事是否已经成形，再看证据密度和阶段位置。</p>
            </div>
          </div>
          <div className="leader-grid">
            {leaders.map((theme) => (
              <article className="card leader-card" key={theme.key}>
                <div className="meta-row">
                  <span className="pill accent">{theme.themeName || "未命名题材"}</span>
                  <span className="pill good">{theme.fermentationStage || "watch-only"}</span>
                  <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                </div>
                <h3>{theme.themeName || theme.clusterId}</h3>
                <p>{theme.coreNarrative || "当前还没有补齐核心叙事。"}</p>
                <div className="score-grid">
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
                <p className="muted">
                  首次出现: {formatIso(theme.firstSeenTime)} | 最近活跃: {formatIso(theme.latestSeenTime)}
                </p>
                {theme.riskNotice ? <p className="muted">风险提示: {theme.riskNotice}</p> : null}
                {theme.topEvidence.length ? (
                  <div className="evidence-list">
                    {theme.topEvidence.slice(0, 2).map((evidence) => (
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
      ) : null}

      {showResearch ? (
        <section className="section">
          <div className="section-head">
            <div>
              <h2>低位研究机会</h2>
              <p>这里展示的是研究优先级，不是交易指令。相似案例、研究卡和未来观察信号会直接展开。</p>
            </div>
          </div>
          <div className="research-grid">
            {lowPosition.map((theme) => (
              <article className="card research-card" key={theme.key}>
                <div className="meta-row">
                  <span className="pill warn">研究优先级 {formatScore(theme.lowPositionScore)}</span>
                  <span className="pill good">{theme.fermentationStage || "watch-only"}</span>
                  {theme.referenceType ? <span className="pill">{similarityLabel(theme.referenceType)}</span> : null}
                </div>
                <h3>{theme.themeName || theme.clusterId}</h3>
                <p>{theme.lowPositionReason || theme.coreNarrative || "当前还没有足够完整的低位研究说明。"}</p>
                <div className="pill-row">
                  <span className="pill">热度 {formatScore(theme.heatScore)}</span>
                  <span className="pill">催化 {formatScore(theme.catalystScore)}</span>
                  <span className="pill">持续性 {formatScore(theme.continuityScore)}</span>
                  <span className="pill">发酵 {formatScore(theme.fermentationScore)}</span>
                  {theme.topCandidatePurityScore !== null ? (
                    <span className="pill accent">Purity {formatScore(theme.topCandidatePurityScore)}</span>
                  ) : null}
                </div>
                <p className="muted">
                  首次出现: {formatIso(theme.firstSeenTime)} | 最近活跃: {formatIso(theme.latestSeenTime)}
                </p>
                {theme.researchPositioningNote ? <p className="muted">{theme.researchPositioningNote}</p> : null}
                {theme.firstSourceUrl ? <p className="muted">最早来源: {theme.firstSourceUrl}</p> : null}
                {theme.candidateStocks.length ? (
                  <div className="pill-row">
                    {theme.candidateStocks.slice(0, 5).map((stock) => (
                      <span className="pill accent" key={`${theme.key}-${stock.code}-${stock.name}`}>
                        {stock.name || stock.code}
                        {stock.score !== null ? ` / ${formatScore(stock.score)}` : ""}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="muted">当前还没有沉淀出足够稳定的候选标的映射。</p>
                )}
                {theme.similarCases.length ? (
                  <div className="detail-block">
                    <strong>相似案例</strong>
                    <div className="evidence-list">
                      {theme.similarCases.slice(0, 2).map((item) => (
                        <div className="evidence-item" key={`${theme.key}-${item.runId}-${item.themeName}`}>
                          <div className="meta-row">
                            <span className="pill accent">{item.themeName || item.runId}</span>
                            <span className="pill">{similarityLabel(item.referenceType)}</span>
                            {item.similarityScore !== null ? (
                              <span className="pill">相似度 {formatScore(item.similarityScore)}</span>
                            ) : null}
                          </div>
                          <div>{item.historicalPathSummary || "暂无历史路径摘要"}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="muted">当前还没有足够可信的历史相似案例，可继续观察是否形成稳定模式。</p>
                )}
                {theme.futureWatchSignals.length ? (
                  <div className="detail-block">
                    <strong>未来观察信号</strong>
                    <ul className="signal-list">
                      {theme.futureWatchSignals.slice(0, 4).map((item) => (
                        <li key={`${theme.key}-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {(theme.latestCatalysts.length ? theme.latestCatalysts : theme.topEvidence).length ? (
                  <div className="detail-block">
                    <strong>近 24h 关键催化</strong>
                    <div className="evidence-list">
                      {(theme.latestCatalysts.length ? theme.latestCatalysts : theme.topEvidence).slice(0, 2).map((evidence) => (
                        <div className="evidence-item" key={`${theme.key}-evidence-${evidence.title}`}>
                          <strong>{evidence.title}</strong>
                          <div className="muted">{formatIso(evidence.eventTime)}</div>
                          <div>{evidence.summary || "暂无摘要"}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
                {theme.riskFlags.length ? (
                  <div className="detail-block">
                    <strong>风险与剔除提醒</strong>
                    <ul className="signal-list">
                      {theme.riskFlags.slice(0, 4).map((item) => (
                        <li key={`${theme.key}-risk-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {theme.riskNotice ? <p className="muted">风险提示: {theme.riskNotice}</p> : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {focus === "all" ? (
        <>
          <section className="section">
            <div className="section-head">
              <div>
                <h2>题材矩阵</h2>
                <p>把今天所有题材放到同一个表里，方便横向比较。</p>
              </div>
            </div>
            <div className="table-shell">
              <table className="board-table">
                <thead>
                  <tr>
                    <th>题材</th>
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
                      <td>{theme.themeName || theme.clusterId}</td>
                      <td>{theme.fermentationStage || "-"}</td>
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

          <section className="section">
            <div className="section-head">
              <div>
                <h2>证据走廊</h2>
                <p>把领跑题材的第一条关键线索摆出来，方便你快速抽查归因是否靠谱。</p>
              </div>
            </div>
            <div className="evidence-tape">
              {evidenceTape.map((item) => (
                <article className="card evidence-card" key={item.key}>
                  <span className="pill accent">{item.themeName}</span>
                  <h3>{item.title}</h3>
                  <p>{item.summary || "暂无摘要"}</p>
                  <p className="muted">{formatIso(item.eventTime)}</p>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </main>
  );
}

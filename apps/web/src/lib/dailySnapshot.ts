import fs from "node:fs";
import path from "node:path";

type JsonRecord = Record<string, unknown>;

export type DailyEvent = {
  key: string;
  eventId: string;
  title: string;
  eventType: string;
  eventSubject: string;
  eventTime: string;
  impactDirection: string;
  impactScope: string;
  summary: string;
  themes: string[];
  industries: string[];
  sourceRefs: string[];
  sourceId: string;
  sourceName: string;
};

export type DailyTheme = {
  key: string;
  themeName: string;
  clusterId: string;
  coreNarrative: string;
  firstSeenTime: string;
  latestSeenTime: string;
  relatedEventsCount: number;
  sourceCount: number;
  heatScore: number;
  catalystScore: number;
  continuityScore: number;
  fermentationScore: number;
  lowPositionScore: number | null;
  lowPositionReason: string;
  fermentationStage: string;
  riskNotice: string;
  genericRiskNotices: string[];
  candidateStocks: Array<{
    name: string;
    code: string;
    score: number | null;
    mappingReason: string;
    sourceReason: string;
    sourceReasonSourceSite: string;
    sourceReasonSourceUrl: string;
    sourceReasonTitle: string;
    sourceReasonExcerpt: string;
    llmReason: string;
    scarcityNote: string;
    judgeExplanation: string;
    riskFlags: string[];
  }>;
  topEvidence: Array<{ title: string; summary: string; eventTime: string }>;
  firstSourceUrl: string;
  topCandidatePurityScore: number | null;
  researchPositioningNote: string;
  referenceType: string;
  futureWatchSignals: string[];
  riskFlags: string[];
  similarCases: Array<{
    runId: string;
    themeName: string;
    referenceType: string;
    similarityScore: number | null;
    resultLabel: string;
    historicalPathSummary: string;
  }>;
  latestCatalysts: Array<{ title: string; summary: string; eventTime: string }>;
};

export type DailySnapshot = {
  date: string;
  storageTimezone: string;
  stats: {
    runCount: number;
    sourceCount: number;
    rawDocumentCount: number;
    canonicalEventCount: number;
    themeCount: number;
    lowPositionCount: number;
    fermentingThemeCount: number;
  };
  commonRiskNotices: string[];
  sources: Array<{ sourceId: string; sourceName: string; documentCount: number }>;
  runs: Array<{ runId: string; createdAt: string; rawDocumentCount: number; eventCount: number; themeCount: number }>;
  themes: DailyTheme[];
  events: DailyEvent[];
};

const STORAGE_TIMEZONE = "UTC";
const RUNTIME_ROOT = path.resolve(process.cwd(), "../../workspace/artifacts/runtime");

const GENERIC_RISK_PRIORITY = [
  "当前还没有高强度催化，建议继续观察。",
  "证据仍然偏单一来源，需防止单源噪音。",
  "当前题材已形成结构化研究对象，仍需继续跟踪后续证据与扩散。",
  "当前建议继续保持观察。",
  "仍需防止单一来源噪音。"
];

const GENERIC_RISK_SET = new Set(GENERIC_RISK_PRIORITY);
const MOJIBAKE_HINTS = ["锛", "銆", "鈥", "闂", "鏉", "鍙", "瑙", "绛", "鏈", "鐮", "鍌", "椋"];

const DIRECT_TEXT_REPLACEMENTS: Array<[string, string]> = [
  ["theme still sits in early recognition zone", "题材仍处于早期认知区间"],
  ["theme is early but still lacks enough consensus", "题材仍偏早期，市场共识还不充分"],
  ["theme has started to lift but is not fully crowded", "题材已经开始升温，但还没有完全拥挤"],
  ["theme is in early fermentation stage", "题材仍处于早期发酵阶段"],
  ["theme is still early but has first proofs", "题材仍偏早期，但已经出现第一批验证信号"],
  ["theme just entered active fermentation", "题材刚进入活跃发酵阶段"],
  ["fresh catalyst window", "催化仍处于新鲜窗口"],
  ["catalyst is still timely", "催化仍具备时效性"],
  ["high-strength catalyst exists", "已经出现高强度催化"],
  ["cross-source discussion has started", "跨来源讨论已经开始形成"],
  ["theme has follow-up catalyst continuity", "题材具备后续催化连续性"],
  ["single-source clue still shows early continuity", "单一来源线索仍显示出早期连续性"],
  ["candidate mapping already identifies a pure stock", "候选映射已经识别出较高正宗度标的"],
  ["candidate mapping is available", "候选标的映射已经可用"],
  [
    "single-source clue is still research-worthy because catalyst and purity align",
    "虽然仍是单一来源线索，但催化与正宗度已经对齐，仍值得优先研究"
  ],
  [
    "There is no high-strength catalyst yet. Keep the theme in observation mode.",
    "当前还没有高强度催化，建议继续观察。"
  ],
  ["Evidence is still concentrated in a single source. Guard against one-source noise.", "证据仍然偏单一来源，需防止单源噪音。"],
  ["Evidence is still concentrated in a single source.", "证据仍然偏单一来源。"],
  ["Keep the theme in observation mode.", "建议继续观察。"],
  ["Keep as watch-only for now.", "当前建议继续保持观察。"],
  ["Single-source noise remains possible.", "仍需防止单一来源噪音。"],
  ["Structured results are built from public information clustering and scoring for research use only.", "结构化结果基于公开信息聚类与评分生成，仅供研究观察。"],
  ["Structured output is based on public information extraction and ranking for research use only.", "结构化输出基于公开信息提取与排序生成，仅供研究观察。"],
  ["For research only. Not investment advice.", "仅供研究观察，不构成投资建议。"],
  ["Research priority only. This card is for tracking and review, not a trading instruction.", "仅供研究观察，用于跟踪和复盘，不构成交易指令。"],
  ["Research priority only。This card is for observation and review，not a trading instruction。", "仅供研究观察，用于跟踪和复盘，不构成交易指令。"],
  ["Research priority only.This card is for observation and review, not a trading instruction.", "仅供研究观察，用于跟踪和复盘，不构成交易指令。"],
  ["Low-position research cards rank observation priority only and do not provide trading instructions.", "低位研究卡只用于排序研究观察优先级，不构成交易指令。"],
  ["watch-only", "观察阶段"],
  ["watching", "观察阶段"],
  ["research-only", "仅供研究观察"],
  ["industry / policy", "产业 / 政策"],
  ["industry", "产业"],
  ["policy", "政策"],
  ["capital", "资金"],
  ["earnings", "业绩"],
  ["sentiment", "情绪"]
];

export function resolveTargetDate(value: string | string[] | undefined): string {
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }
  return latestAvailableDate();
}

export function loadDailySnapshot(date: string = latestAvailableDate()): DailySnapshot {
  const runDirs = listRunDirectories();
  const sourceCounter = new Map<string, { sourceId: string; sourceName: string; documentCount: number }>();
  const eventsByKey = new Map<string, DailyEvent>();
  const themesByKey = new Map<string, DailyTheme>();
  const lowPositionKeys = new Set<string>();
  const fermentingKeys = new Set<string>();
  const includedRuns: DailySnapshot["runs"] = [];
  let rawDocumentCount = 0;

  for (const runDir of runDirs) {
    const manifest = readJson<Record<string, unknown>>(path.join(runDir, "manifest.json"));
    if (!manifest) {
      continue;
    }

    const createdAt = asString(manifest.created_at);
    if (!matchesDate(createdAt, date)) {
      continue;
    }

    const rawDocuments = readJsonArray(path.join(runDir, "raw_documents.json"));
    if (!rawDocuments.length || isSyntheticRun(rawDocuments)) {
      continue;
    }

    const canonicalEvents = readJsonArray(path.join(runDir, "canonical_events.json"));
    const themeCandidates = readJsonArray(path.join(runDir, "theme_candidates.json"));
    const lowPosition = readJsonArray(path.join(runDir, "low_position_opportunities.json"));
    const fermenting = readJsonArray(path.join(runDir, "fermenting_theme_feed.json"));
    const dailyReview = readJson<Record<string, unknown>>(path.join(runDir, "daily_review.json")) ?? {};

    includedRuns.push({
      runId: asString(manifest.run_id) || path.basename(runDir),
      createdAt,
      rawDocumentCount: rawDocuments.length,
      eventCount: canonicalEvents.length,
      themeCount: themeCandidates.length
    });

    rawDocumentCount += rawDocuments.length;
    mergeSources(sourceCounter, rawDocuments);
    mergeEvents(eventsByKey, canonicalEvents);
    mergeThemes(themesByKey, themeCandidates);
    mergeLowPosition(themesByKey, lowPosition, lowPositionKeys);
    mergeFermenting(themesByKey, fermenting, fermentingKeys);
    mergeResearchCards(themesByKey, dailyReview);
  }

  const themes = Array.from(themesByKey.values()).map(normalizeTheme).sort(compareThemes);
  const events = Array.from(eventsByKey.values()).sort((left, right) => right.eventTime.localeCompare(left.eventTime));
  const sources = Array.from(sourceCounter.values()).sort((left, right) => right.documentCount - left.documentCount);
  const runs = includedRuns.sort((left, right) => right.createdAt.localeCompare(left.createdAt));

  return {
    date,
    storageTimezone: STORAGE_TIMEZONE,
    stats: {
      runCount: runs.length,
      sourceCount: sources.length,
      rawDocumentCount,
      canonicalEventCount: events.length,
      themeCount: themes.length,
      lowPositionCount: lowPositionKeys.size,
      fermentingThemeCount: fermentingKeys.size
    },
    commonRiskNotices: collectCommonRiskNotices(themes),
    sources,
    runs,
    themes,
    events
  };
}

function listRunDirectories(): string[] {
  if (!fs.existsSync(RUNTIME_ROOT)) {
    return [];
  }
  return fs
    .readdirSync(RUNTIME_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(RUNTIME_ROOT, entry.name));
}

function latestAvailableDate(): string {
  const dates = new Set<string>();
  for (const runDir of listRunDirectories()) {
    const manifest = readJson<Record<string, unknown>>(path.join(runDir, "manifest.json"));
    const rawDocuments = readJsonArray(path.join(runDir, "raw_documents.json"));
    if (!manifest || !rawDocuments.length || isSyntheticRun(rawDocuments)) {
      continue;
    }
    const createdAt = asString(manifest.created_at);
    if (createdAt) {
      dates.add(createdAt.slice(0, 10));
    }
  }
  return Array.from(dates).sort().at(-1) ?? "2026-03-16";
}

function mergeSources(
  counter: Map<string, { sourceId: string; sourceName: string; documentCount: number }>,
  rawDocuments: JsonRecord[]
): void {
  for (const item of rawDocuments) {
    const sourceId = asString(item.source_id) || "unknown";
    const sourceName = sourceNameFromId(sourceId);
    const current = counter.get(sourceId) ?? { sourceId, sourceName, documentCount: 0 };
    current.documentCount += 1;
    counter.set(sourceId, current);
  }
}

function mergeEvents(target: Map<string, DailyEvent>, items: JsonRecord[]): void {
  for (const item of items) {
    const eventTime = asString(item.event_time) || asString(item.occurred_at) || asString(item.first_disclosed_at);
    const key = normalizeKey(asString(item.canonical_key) || asString(item.event_id) || asString(item.title));
    if (!key) {
      continue;
    }

    const metadata = asRecord(item.metadata);
    const current: DailyEvent = {
      key,
      eventId: asString(item.event_id),
      title: asString(item.title),
      eventType: localizedString(item.event_type),
      eventSubject: asString(item.event_subject),
      eventTime,
      impactDirection: localizedString(item.impact_direction),
      impactScope: localizedString(item.impact_scope),
      summary: asString(item.summary),
      themes: asStringArray(item.related_themes),
      industries: asStringArray(item.related_industries),
      sourceRefs: asStringArray(item.source_refs),
      sourceId: asString(metadata.source_id),
      sourceName: sourceNameFromId(asString(metadata.source_id))
    };

    const previous = target.get(key);
    if (!previous || current.eventTime > previous.eventTime) {
      target.set(key, current);
    }
  }
}

function mergeThemes(target: Map<string, DailyTheme>, items: JsonRecord[]): void {
  for (const item of items) {
    const themeName = asString(item.theme_name);
    const key = normalizeKey(themeName || asString(item.cluster_id) || asString(item.theme_candidate_id));
    if (!key) {
      continue;
    }

    const topEvidence = toEvidenceArray(item.top_evidence);
    const current: DailyTheme = {
      key,
      themeName,
      clusterId: asString(item.cluster_id),
      coreNarrative: localizedString(item.core_narrative),
      firstSeenTime: asString(item.first_seen_time),
      latestSeenTime: asString(item.latest_seen_time),
      relatedEventsCount: asNumber(item.related_events_count),
      sourceCount: asNumber(item.source_count),
      heatScore: asNumber(item.heat_score),
      catalystScore: asNumber(item.catalyst_score),
      continuityScore: asNumber(item.continuity_score),
      fermentationScore: asNumber(item.fermentation_score),
      lowPositionScore: null,
      lowPositionReason: "",
      fermentationStage: asString(item.fermentation_stage) || "watching",
      riskNotice: localizedString(item.risk_notice),
      genericRiskNotices: [],
      candidateStocks: toCandidateStocks(item.candidate_stocks),
      topEvidence,
      firstSourceUrl: "",
      topCandidatePurityScore: null,
      researchPositioningNote: "",
      referenceType: "",
      futureWatchSignals: [],
      riskFlags: [],
      similarCases: [],
      latestCatalysts: []
    };

    const previous = target.get(key);
    if (!previous || current.fermentationScore > previous.fermentationScore) {
      target.set(key, { ...previous, ...current });
    }
  }
}

function mergeLowPosition(target: Map<string, DailyTheme>, items: JsonRecord[], keys: Set<string>): void {
  for (const item of items) {
    const themeName = asString(item.theme_name);
    const key = normalizeKey(themeName || asString(item.cluster_id) || asString(item.theme_candidate_id));
    if (!key) {
      continue;
    }

    keys.add(key);
    const existing = target.get(key) ?? emptyTheme(themeName, asString(item.cluster_id), key);
    const currentScore = asNullableNumber(item.low_position_score);
    const nextTheme: DailyTheme = {
      ...existing,
      themeName: existing.themeName || themeName,
      clusterId: existing.clusterId || asString(item.cluster_id),
      lowPositionScore:
        existing.lowPositionScore === null || (currentScore !== null && currentScore > existing.lowPositionScore)
          ? currentScore
          : existing.lowPositionScore,
      lowPositionReason: localizedString(item.low_position_reason) || existing.lowPositionReason,
      fermentationStage: asString(item.entry_stage) || existing.fermentationStage,
      riskNotice: localizedString(item.risk_notice) || existing.riskNotice,
      coreNarrative: existing.coreNarrative || localizedString(item.core_narrative),
      heatScore: Math.max(existing.heatScore, asNumber(item.heat_score)),
      catalystScore: Math.max(existing.catalystScore, asNumber(item.catalyst_score)),
      continuityScore: Math.max(existing.continuityScore, asNumber(item.continuity_score)),
      fermentationScore: Math.max(existing.fermentationScore, asNumber(item.fermentation_score)),
      sourceCount: Math.max(existing.sourceCount, asNumber(item.source_count)),
      candidateStocks: existing.candidateStocks.length ? existing.candidateStocks : toCandidateStocks(item.candidate_stocks),
      topEvidence: existing.topEvidence.length ? existing.topEvidence : toEvidenceArray(item.top_evidence)
    };
    target.set(key, nextTheme);
  }
}

function mergeFermenting(target: Map<string, DailyTheme>, items: JsonRecord[], keys: Set<string>): void {
  for (const item of items) {
    const themeName = asString(item.theme_name);
    const key = normalizeKey(themeName || asString(item.cluster_id) || asString(item.theme_candidate_id));
    if (!key) {
      continue;
    }

    keys.add(key);
    const existing = target.get(key) ?? emptyTheme(themeName, asString(item.cluster_id), key);
    const nextTheme: DailyTheme = {
      ...existing,
      themeName: existing.themeName || themeName,
      clusterId: existing.clusterId || asString(item.cluster_id),
      fermentationStage: asString(item.fermentation_stage) || existing.fermentationStage,
      riskNotice: localizedString(item.risk_notice) || existing.riskNotice,
      coreNarrative: existing.coreNarrative || localizedString(item.core_narrative),
      heatScore: Math.max(existing.heatScore, asNumber(item.theme_heat_score)),
      fermentationScore: Math.max(existing.fermentationScore, asNumber(item.theme_heat_score)),
      candidateStocks: existing.candidateStocks.length ? existing.candidateStocks : toCandidateStocks(item.candidate_stocks),
      topEvidence: existing.topEvidence.length ? existing.topEvidence : toEvidenceArray(item.top_evidence)
    };
    target.set(key, nextTheme);
  }
}

function mergeResearchCards(target: Map<string, DailyTheme>, dailyReview: Record<string, unknown>): void {
  const researchCards = Array.isArray(dailyReview.low_position_research_cards)
    ? dailyReview.low_position_research_cards.filter(isRecord)
    : [];

  for (const item of researchCards) {
    const themeName = asString(item.theme_name);
    const key = normalizeKey(themeName || asString(item.cluster_id) || asString(item.theme_candidate_id));
    if (!key) {
      continue;
    }

    const existing = target.get(key) ?? emptyTheme(themeName, asString(item.cluster_id), key);
    const localizedRiskFlags = localizedStringArray(item.risk_flags);
    const nextTheme: DailyTheme = {
      ...existing,
      themeName: existing.themeName || themeName,
      clusterId: existing.clusterId || asString(item.cluster_id),
      coreNarrative: existing.coreNarrative || localizedString(item.core_narrative),
      firstSourceUrl: asString(item.first_source_url) || existing.firstSourceUrl,
      topCandidatePurityScore: asNullableNumber(item.top_candidate_purity_score) ?? existing.topCandidatePurityScore,
      researchPositioningNote: localizedString(item.research_positioning_note) || existing.researchPositioningNote,
      referenceType: asString(item.reference_type) || existing.referenceType,
      futureWatchSignals: localizedStringArray(item.future_watch_signals),
      riskFlags: localizedRiskFlags.length ? localizedRiskFlags : existing.riskFlags,
      riskNotice: localizedString(item.risk_notice) || existing.riskNotice,
      similarCases: toSimilarCases(item.similar_cases),
      latestCatalysts: toEvidenceArray(item.latest_24h_key_catalysts),
      candidateStocks: existing.candidateStocks.length ? existing.candidateStocks : toCandidateStocks(item.candidate_stocks),
      topEvidence: existing.topEvidence.length ? existing.topEvidence : toEvidenceArray(item.latest_24h_key_catalysts)
    };
    target.set(key, nextTheme);
  }
}

function normalizeTheme(theme: DailyTheme): DailyTheme {
  const specificRisks: string[] = [];
  const genericRisks = new Set<string>();

  for (const item of [theme.riskNotice, ...theme.riskFlags]) {
    const normalized = localizedText(item);
    if (!normalized) {
      continue;
    }
    if (isGenericRisk(normalized)) {
      genericRisks.add(normalized);
      continue;
    }
    if (!specificRisks.includes(normalized)) {
      specificRisks.push(normalized);
    }
  }

  return {
    ...theme,
    coreNarrative: localizedText(theme.coreNarrative),
    lowPositionReason: localizedText(theme.lowPositionReason),
    riskNotice: specificRisks[0] ?? "",
    genericRiskNotices: sortGenericRisks(Array.from(genericRisks)),
    researchPositioningNote: localizedText(theme.researchPositioningNote),
    futureWatchSignals: localizedStringArray(theme.futureWatchSignals),
    riskFlags: specificRisks,
    candidateStocks: theme.candidateStocks.map((item) => normalizeCandidateStock(theme, item)),
    similarCases: theme.similarCases.map((item) => ({
      ...item,
      themeName: asString(item.themeName),
      resultLabel: localizedText(item.resultLabel),
      historicalPathSummary: localizedText(item.historicalPathSummary)
    }))
  };
}

function normalizeCandidateStock(
  theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): DailyTheme["candidateStocks"][number] {
  const mappingReason = localizedText(stock.mappingReason);
  const sourceReason = localizedText(stock.sourceReason);
  const sourceReasonSourceSite = localizedText(stock.sourceReasonSourceSite);
  const sourceReasonSourceUrl = localizedText(stock.sourceReasonSourceUrl);
  const sourceReasonTitle = localizedText(stock.sourceReasonTitle);
  const sourceReasonExcerpt = localizedText(stock.sourceReasonExcerpt);
  const llmReason = localizedText(stock.llmReason);
  const judgeExplanation = localizedText(stock.judgeExplanation);
  const scarcityNote = localizedText(stock.scarcityNote);
  const riskFlags = localizedStringArray(stock.riskFlags);
  const synthesizedMappingReason = buildMappingCandidateReasonClean(theme, {
    ...stock,
    sourceReason,
    sourceReasonSourceSite,
    sourceReasonSourceUrl,
    sourceReasonTitle,
    sourceReasonExcerpt,
    llmReason,
    mappingReason,
    judgeExplanation,
    scarcityNote,
    riskFlags
  });
  const synthesizedSourceReason = buildSourceCandidateReason(theme, {
    ...stock,
    sourceReason,
    sourceReasonSourceSite,
    sourceReasonSourceUrl,
    sourceReasonTitle,
    sourceReasonExcerpt,
    llmReason,
    mappingReason,
    judgeExplanation,
    scarcityNote,
    riskFlags
  });
  const synthesizedLlmReason = buildLlmCandidateReasonClean(theme, {
    ...stock,
    sourceReason,
    sourceReasonSourceSite,
    sourceReasonSourceUrl,
    sourceReasonTitle,
    sourceReasonExcerpt,
    llmReason,
    mappingReason,
    judgeExplanation,
    scarcityNote,
    riskFlags
  });

  return {
    ...stock,
    mappingReason: synthesizedMappingReason,
    sourceReason: synthesizedSourceReason,
    sourceReasonSourceSite,
    sourceReasonSourceUrl,
    sourceReasonTitle,
    sourceReasonExcerpt,
    llmReason: synthesizedLlmReason,
    judgeExplanation,
    scarcityNote,
    riskFlags
  };
}

function buildCandidateReasonV2(
  theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  const stockName = stock.name || stock.code || "候选标的";
  const evidence = pickCandidateEvidence(theme, stockName);
  const scoreLabel = stock.score !== null && stock.score >= 70 ? "核心跟踪候选" : "观察候选";
  const parts: string[] = [];

  if (evidence?.title) {
    const cleanedTitle = cleanEvidenceTitle(evidence.title);
    if (cleanedTitle) {
      if (cleanedTitle.includes(stockName) || evidence.summary.includes(stockName)) {
        parts.push(`${stockName}在《${cleanedTitle}》这条${theme.themeName || "题材"}线索中被直接点名`);
      } else {
        parts.push(`${stockName}与《${cleanedTitle}》这条${theme.themeName || "题材"}线索存在联动`);
      }
    }
  }

  if (!parts.length && stock.mappingReason) {
    parts.push(stock.mappingReason.replace(/。+$/u, ""));
  }

  if (!parts.length && stock.judgeExplanation) {
    parts.push(stock.judgeExplanation.replace(/。+$/u, ""));
  }

  parts.push(`当前归入${scoreLabel}`);

  if (stock.scarcityNote) {
    parts.push(`稀缺性上，${stock.scarcityNote.replace(/。+$/u, "")}`);
  }

  return `${parts.filter(Boolean).join("，")}。`;
}

function buildCandidateReason(
  theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  const stockName = stock.name || stock.code || "候选标的";
  const evidence = pickCandidateEvidence(theme, stockName);
  const scoreLabel = stock.score !== null && stock.score >= 70 ? "核心跟踪候选" : "观察候选";
  const parts: string[] = [];

  if (stock.sourceReason) {
    parts.push(stock.sourceReason.replace(/。+$/u, ""));
  } else if (evidence?.title) {
    const cleanedTitle = cleanEvidenceTitle(evidence.title);
    if (cleanedTitle) {
      if (cleanedTitle.includes(stockName) || evidence.summary.includes(stockName)) {
        parts.push(`${stockName}在《${cleanedTitle}》这条${theme.themeName || "题材"}线索中被直接点名`);
      } else {
        parts.push(`${stockName}与《${cleanedTitle}》这条${theme.themeName || "题材"}线索存在联动`);
      }
    }
  }

  if (!parts.length && stock.mappingReason) {
    parts.push(stock.mappingReason.replace(/。+$/u, ""));
  }

  if (!parts.length && stock.judgeExplanation) {
    parts.push(stock.judgeExplanation.replace(/。+$/u, ""));
  }

  if (stock.sourceReasonSourceSite) {
    parts.push(`证据来源：${stock.sourceReasonSourceSite}`);
  }

  parts.push(`当前归入${scoreLabel}`);

  if (stock.scarcityNote) {
    parts.push(`稀缺性上，${stock.scarcityNote.replace(/。+$/u, "")}`);
  }

  return `${parts.filter(Boolean).join("，")}。`;
}

function buildLlmCandidateReason(
  theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  const parts: string[] = [];

  if (stock.llmReason) {
    parts.push(stock.llmReason.replace(/。+$/u, ""));
  } else if (stock.mappingReason) {
    parts.push(stock.mappingReason.replace(/。+$/u, ""));
  } else if (stock.judgeExplanation) {
    parts.push(stock.judgeExplanation.replace(/。+$/u, ""));
  } else {
    parts.push(`${stock.name || stock.code || "候选标的"}已进入${theme.themeName || "该题材"}观察池`);
  }

  if (stock.scarcityNote) {
    parts.push(`稀缺性上，${stock.scarcityNote.replace(/。+$/u, "")}`);
  }

  return `${parts.filter(Boolean).join("，")}。`;
}

function buildMappingCandidateReasonClean(
  theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  const stockName = stock.name || stock.code || "候选标的";
  const evidence = pickCandidateEvidence(theme, stockName);
  const scoreLabel = stock.score !== null && stock.score >= 70 ? "核心跟踪候选" : "观察候选";
  const parts: string[] = [];

  if (stock.mappingReason) {
    parts.push(stock.mappingReason.replace(/。+$/u, ""));
  } else if (stock.judgeExplanation) {
    parts.push(stock.judgeExplanation.replace(/。+$/u, ""));
  } else if (evidence?.title) {
    parts.push(`${stockName}与《${cleanEvidenceTitle(evidence.title)}》这条${theme.themeName || "题材"}线索存在联动`);
  }

  parts.push(`当前归入${scoreLabel}`);
  if (stock.scarcityNote) {
    parts.push(`稀缺性补充：${stock.scarcityNote.replace(/。+$/u, "")}`);
  }
  return `${parts.filter(Boolean).join("；")}。`;
}

function buildSourceCandidateReason(
  _theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  if (stock.sourceReason) {
    return stock.sourceReason.replace(/。+$/u, "") + "。";
  }
  if (stock.sourceReasonTitle && stock.sourceReasonExcerpt) {
    return `雪球帖子《${stock.sourceReasonTitle}》提到${stock.name || stock.code || "该标的"}，核心依据是：${stock.sourceReasonExcerpt.replace(/。+$/u, "")}。`;
  }
  if (stock.sourceReasonTitle) {
    return `已找到雪球帖子《${stock.sourceReasonTitle}》，但当前摘录不足，建议点开原帖继续核对。`;
  }
  return "";
}

function buildLlmCandidateReasonClean(
  _theme: DailyTheme,
  stock: DailyTheme["candidateStocks"][number]
): string {
  const parts: string[] = [];
  if (stock.llmReason) {
    parts.push(stock.llmReason.replace(/。+$/u, ""));
  }
  if (stock.scarcityNote) {
    parts.push(`稀缺性补充：${stock.scarcityNote.replace(/。+$/u, "")}`);
  }
  return parts.length ? `${parts.join("；")}。` : "";
}

function pickCandidateEvidence(
  theme: DailyTheme,
  stockName: string
): { title: string; summary: string; eventTime: string } | null {
  const evidenceItems = [...theme.latestCatalysts, ...theme.topEvidence];
  for (const item of evidenceItems) {
    if (item.title.includes(stockName) || item.summary.includes(stockName)) {
      return item;
    }
  }
  return evidenceItems[0] ?? null;
}

function cleanEvidenceTitle(value: string): string {
  return value.replace(/\s+-\s+.*$/u, "").replace(/^#+/u, "").trim();
}

function collectCommonRiskNotices(themes: DailyTheme[]): string[] {
  const counts = new Map<string, number>();
  for (const theme of themes) {
    for (const notice of theme.genericRiskNotices) {
      counts.set(notice, (counts.get(notice) ?? 0) + 1);
    }
  }

  const repeated = Array.from(counts.entries())
    .filter(([, count]) => count >= 2)
    .map(([notice]) => notice);

  if (repeated.length) {
    return sortGenericRisks(repeated);
  }

  return sortGenericRisks(Array.from(counts.keys()));
}

function emptyTheme(themeName: string, clusterId: string, key: string): DailyTheme {
  return {
    key,
    themeName,
    clusterId,
    coreNarrative: "",
    firstSeenTime: "",
    latestSeenTime: "",
    relatedEventsCount: 0,
    sourceCount: 0,
    heatScore: 0,
    catalystScore: 0,
    continuityScore: 0,
    fermentationScore: 0,
    lowPositionScore: null,
    lowPositionReason: "",
    fermentationStage: "watching",
    riskNotice: "",
    genericRiskNotices: [],
    candidateStocks: [],
    topEvidence: [],
    firstSourceUrl: "",
    topCandidatePurityScore: null,
    researchPositioningNote: "",
    referenceType: "",
    futureWatchSignals: [],
    riskFlags: [],
    similarCases: [],
    latestCatalysts: []
  };
}

function compareThemes(left: DailyTheme, right: DailyTheme): number {
  const leftPriority = left.lowPositionScore ?? left.heatScore;
  const rightPriority = right.lowPositionScore ?? right.heatScore;
  if (rightPriority !== leftPriority) {
    return rightPriority - leftPriority;
  }
  return right.latestSeenTime.localeCompare(left.latestSeenTime);
}

function matchesDate(value: string, date: string): boolean {
  return typeof value === "string" && value.slice(0, 10) === date;
}

function readJson<T>(filePath: string): T | null {
  if (!fs.existsSync(filePath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return null;
  }
}

function readJsonArray(filePath: string): JsonRecord[] {
  const payload = readJson<unknown>(filePath);
  return Array.isArray(payload) ? (payload.filter(isRecord) as JsonRecord[]) : [];
}

function isSyntheticRun(rawDocuments: JsonRecord[]): boolean {
  let syntheticCount = 0;
  for (const item of rawDocuments) {
    const url = asString(item.url);
    const documentId = asString(item.document_id);
    const title = asString(item.title);
    if (
      /\/detail\/[12]$/.test(url) ||
      /#(?:abc123|sample-\d+)/.test(url) ||
      /\/hashtag\/demo$/.test(url) ||
      /^rawc-00\d$/.test(documentId) ||
      title.includes("示例")
    ) {
      syntheticCount += 1;
    }
  }
  return syntheticCount > 0 && syntheticCount >= Math.ceil(rawDocuments.length / 2);
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asRecord(value: unknown): JsonRecord {
  return isRecord(value) ? value : {};
}

function asString(value: unknown): string {
  return typeof value === "string" ? repairMojibake(value).trim() : "";
}

function localizedString(value: unknown): string {
  return localizedText(asString(value));
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

function localizedStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => localizedText(asString(item)))
    .filter((item) => item.length > 0)
    .filter((item, index, array) => array.indexOf(item) === index);
}

function asNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function asNullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function normalizeKey(value: string): string {
  return value.trim().toLowerCase();
}

function sourceNameFromId(sourceId: string): string {
  switch (sourceId) {
    case "cls-telegraph":
      return "财联社快讯";
    case "jiuyangongshe-live":
      return "韭研公社";
    case "xueqiu-hot-spot":
      return "雪球热点";
    default:
      return sourceId || "未知来源";
  }
}

function repairMojibake(value: string): string {
  if (!value || !looksLikeUtf8Mojibake(value)) {
    return value;
  }
  try {
    const repaired = Buffer.from(value, "latin1").toString("utf8");
    if (looksMoreReadable(repaired, value)) {
      return repaired;
    }
  } catch {
    return value;
  }
  return value;
}

function looksLikeUtf8Mojibake(value: string): boolean {
  return MOJIBAKE_HINTS.some((item) => value.includes(item));
}

function looksMoreReadable(candidate: string, original: string): boolean {
  return readabilityScore(candidate) > readabilityScore(original);
}

function readabilityScore(value: string): number {
  let score = 0;
  for (const char of value) {
    if (/[\u4e00-\u9fff]/.test(char)) {
      score += 3;
      continue;
    }
    if (/[a-zA-Z0-9]/.test(char)) {
      score += 1;
      continue;
    }
    if ("，。！？：；、“”‘’（）()[]【】#%+-_ ".includes(char)) {
      score += 0.5;
      continue;
    }
    if (MOJIBAKE_HINTS.some((item) => item.includes(char))) {
      score -= 1;
    }
  }
  return score;
}

function toCandidateStocks(value: unknown): Array<{
  name: string;
  code: string;
  score: number | null;
  mappingReason: string;
  sourceReason: string;
  sourceReasonSourceSite: string;
  sourceReasonSourceUrl: string;
  sourceReasonTitle: string;
  sourceReasonExcerpt: string;
  llmReason: string;
  scarcityNote: string;
  judgeExplanation: string;
  riskFlags: string[];
}> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(isRecord)
    .map((item) => ({
      name: asString(item.stock_name) || asString(item.name),
      code: asString(item.stock_code) || asString(item.code),
      score: asNullableNumber(item.candidate_purity_score) ?? asNullableNumber(item.purity_score),
      mappingReason: localizedString(item.mapping_reason),
      sourceReason: localizedString(item.source_reason),
      sourceReasonSourceSite: localizedString(item.source_reason_source_site),
      sourceReasonSourceUrl: localizedString(item.source_reason_source_url),
      sourceReasonTitle: localizedString(item.source_reason_title),
      sourceReasonExcerpt: localizedString(item.source_reason_excerpt),
      llmReason: localizedString(item.llm_reason),
      scarcityNote: localizedString(item.scarcity_note),
      judgeExplanation: localizedString(item.judge_explanation),
      riskFlags: localizedStringArray(item.risk_flags)
    }))
    .filter((item) => item.name || item.code);
}

function toEvidenceArray(value: unknown): Array<{ title: string; summary: string; eventTime: string }> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(isRecord)
    .map((item) => ({
      title: asString(item.title),
      summary: asString(item.summary),
      eventTime: asString(item.event_time)
    }))
    .filter((item) => item.title);
}

function toSimilarCases(
  value: unknown
): Array<{
  runId: string;
  themeName: string;
  referenceType: string;
  similarityScore: number | null;
  resultLabel: string;
  historicalPathSummary: string;
}> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(isRecord)
    .map((item) => ({
      runId: asString(item.run_id),
      themeName: asString(item.theme_name),
      referenceType: asString(item.reference_type),
      similarityScore: asNullableNumber(item.similarity_score),
      resultLabel: localizedString(item.result_label),
      historicalPathSummary: localizedString(item.historical_path_summary)
    }))
    .filter((item) => item.runId || item.themeName);
}

function localizedText(value: string): string {
  if (!value) {
    return "";
  }

  let result = repairMojibake(value).trim();
  for (const [source, target] of DIRECT_TEXT_REPLACEMENTS) {
    result = result.replaceAll(source, target);
  }

  result = result.replace(
    /^(.+?) is clustering around (.+?), with narrative anchors in (.+)\.$/i,
    (_, theme, subject, anchors) => `${theme}当前围绕${subject}形成叙事聚合，关键锚点包括${anchors}。`
  );
  result = result.replace(/^(.+?) is clustering around (.+)\.$/i, (_, theme, subject) => `${theme}当前围绕${subject}形成叙事聚合。`);
  result = result.replace(/^(.+?) has formed an early theme cluster\.$/i, (_, theme) => `${theme}已形成早期题材聚合。`);
  result = result.replace(/^(.+?) is mainly driven by (.+?) catalysts\.$/i, (_, theme, catalysts) => `${theme}当前主要由${catalysts}类催化驱动。`);
  result = result.replace(
    /^(.+?) has early clues, but catalyst type still needs follow-up\.$/i,
    (_, theme) => `${theme}已经出现早期线索，但催化类型仍需继续确认。`
  );
  result = result.replace(
    /^(.+?) entered the focus page in (.+?) at (.+?), with research priority score ([\d.]+)\.$/i,
    (_, theme, runId, stage, score) => `${theme}在${runId}中以${stageLabelFromEnglish(stage)}进入重点关注页，研究优先级为${score}。`
  );
  result = result.replace(
    /^(.+?) stayed in (.+?) in (.+?), as a watch reference, with research priority score ([\d.]+)\.$/i,
    (_, theme, stage, runId, score) => `${theme}在${runId}中停留在${stageLabelFromEnglish(stage)}，作为观察参考保留，研究优先级为${score}。`
  );
  result = result.replace("same theme already appeared in a historical run", "同名题材在历史运行中出现过");
  result = result.replace("core narrative overlaps with the historical case", "核心叙事与历史案例存在重合");
  result = result.replace("current research stage is close to the historical path", "当前研究阶段与历史路径接近");
  result = result.replace("historical path behaves more like reignited logic", "历史路径更像旧逻辑再发酵");
  result = result.replace("historical path can be used as an adjacent pattern reference", "历史路径可作为相邻模式参考");
  result = result.replace("current theme is heating up faster than the historical case", "当前题材升温速度快于历史案例");
  result = result.replace("historical case spread faster at the same stage", "历史案例在同阶段的扩散更快");
  result = result.replace(
    "current structure is close to the historical path but still needs follow-up confirmation",
    "当前结构与历史路径接近，但仍需后续证据确认"
  );

  if (result.startsWith("Watch whether")) {
    result = result
      .replace("Watch whether a second public source appears to confirm the theme.", "观察是否出现第二个公开来源来确认该题材。")
      .replace("Watch whether stronger catalysts appear, such as policy, orders, or formal announcements.", "观察是否出现更强催化，例如政策、订单或正式公告。")
      .replace(
        "Watch whether clearer core beneficiary mapping and higher purity candidates emerge.",
        "观察是否出现更清晰的核心受益标的映射与更高正宗度候选。"
      )
      .replace("Watch whether the narrative continues to spread beyond current sources.", "观察叙事是否能从当前来源继续扩散。")
      .replace("Watch whether the theme starts to form a recognizable historical path.", "观察该题材是否开始呈现可识别的历史路径。");
  }

  return normalizePunctuation(result);
}

function normalizePunctuation(value: string): string {
  return value
    .replace(/\s+/g, " ")
    .replace(/\s*;\s*/g, "；")
    .replace(/\s*,\s*/g, "，")
    .replace(/\s*\.\s*/g, "。")
    .replace(/\?+/g, "？")
    .replace(/!+/g, "！")
    .replace(/；。/g, "。")
    .trim();
}

function stageLabelFromEnglish(value: string): string {
  const normalized = value.trim().toLowerCase();
  switch (normalized) {
    case "watch-only":
    case "watching":
      return "观察阶段";
    case "emerging":
      return "早期成形阶段";
    case "fermenting":
      return "持续发酵阶段";
    case "hot":
      return "拥挤扩散阶段";
    case "early":
      return "早期阶段";
    case "spreading":
      return "扩散阶段";
    case "crowded":
      return "拥挤阶段";
    default:
      return value;
  }
}

function isGenericRisk(value: string): boolean {
  if (!value) {
    return false;
  }
  if (GENERIC_RISK_SET.has(value)) {
    return true;
  }
  return (
    value.includes("建议继续观察") ||
    value.includes("单一来源噪音") ||
    value.includes("仅供研究观察") ||
    value.includes("继续保持观察") ||
    value.includes("继续跟踪后续证据")
  );
}

function sortGenericRisks(items: string[]): string[] {
  return [...new Set(items)].sort((left, right) => {
    const leftIndex = GENERIC_RISK_PRIORITY.indexOf(left);
    const rightIndex = GENERIC_RISK_PRIORITY.indexOf(right);
    if (leftIndex !== -1 || rightIndex !== -1) {
      return (leftIndex === -1 ? 999 : leftIndex) - (rightIndex === -1 ? 999 : rightIndex);
    }
    return left.localeCompare(right, "zh-CN");
  });
}

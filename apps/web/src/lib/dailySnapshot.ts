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
  candidateStocks: Array<{ name: string; code: string; score: number | null }>;
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
  sources: Array<{ sourceId: string; sourceName: string; documentCount: number }>;
  runs: Array<{ runId: string; createdAt: string; rawDocumentCount: number; eventCount: number; themeCount: number }>;
  themes: DailyTheme[];
  events: DailyEvent[];
};

const STORAGE_TIMEZONE = "UTC";
const RUNTIME_ROOT = path.resolve(process.cwd(), "../../workspace/artifacts/runtime");

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

  const themes = Array.from(themesByKey.values()).sort(compareThemes);
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
      eventType: asString(item.event_type),
      eventSubject: asString(item.event_subject),
      eventTime,
      impactDirection: asString(item.impact_direction),
      impactScope: asString(item.impact_scope),
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
      coreNarrative: asString(item.core_narrative),
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
      fermentationStage: "watching",
      riskNotice: "",
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
      lowPositionReason: asString(item.low_position_reason) || existing.lowPositionReason,
      fermentationStage: asString(item.entry_stage) || existing.fermentationStage,
      riskNotice: asString(item.risk_notice) || existing.riskNotice,
      coreNarrative: existing.coreNarrative || asString(item.core_narrative),
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
      riskNotice: asString(item.risk_notice) || existing.riskNotice,
      coreNarrative: existing.coreNarrative || asString(item.core_narrative),
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
    const nextTheme: DailyTheme = {
      ...existing,
      themeName: existing.themeName || themeName,
      clusterId: existing.clusterId || asString(item.cluster_id),
      coreNarrative: existing.coreNarrative || asString(item.core_narrative),
      firstSourceUrl: asString(item.first_source_url) || existing.firstSourceUrl,
      topCandidatePurityScore: asNullableNumber(item.top_candidate_purity_score) ?? existing.topCandidatePurityScore,
      researchPositioningNote: asString(item.research_positioning_note) || existing.researchPositioningNote,
      referenceType: asString(item.reference_type) || existing.referenceType,
      futureWatchSignals: asStringArray(item.future_watch_signals),
      riskFlags: asStringArray(item.risk_flags),
      similarCases: toSimilarCases(item.similar_cases),
      latestCatalysts: toEvidenceArray(item.latest_24h_key_catalysts),
      candidateStocks: existing.candidateStocks.length ? existing.candidateStocks : toCandidateStocks(item.candidate_stocks),
      topEvidence: existing.topEvidence.length ? existing.topEvidence : toEvidenceArray(item.latest_24h_key_catalysts)
    };
    target.set(key, nextTheme);
  }
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

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
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
  return /[À-ÿ]/.test(value);
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
    if ("，。！？：；、“”‘’（）()[]【】/#%+-_ ".includes(char)) {
      score += 0.5;
      continue;
    }
    if (/[À-ÿ]/.test(char)) {
      score -= 1;
    }
  }
  return score;
}

function toCandidateStocks(value: unknown): Array<{ name: string; code: string; score: number | null }> {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter(isRecord)
    .map((item) => ({
      name: asString(item.stock_name) || asString(item.name),
      code: asString(item.stock_code) || asString(item.code),
      score: asNullableNumber(item.purity_score)
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
      resultLabel: asString(item.result_label),
      historicalPathSummary: asString(item.historical_path_summary)
    }))
    .filter((item) => item.runId || item.themeName);
}

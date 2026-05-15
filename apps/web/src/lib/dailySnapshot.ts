import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { createSeedSnapshot, SEED_DATE } from "@/lib/uiSeedData";

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
  similarCases: Array<{ runId: string; themeName: string; referenceType: string; similarityScore: number | null; resultLabel: string; historicalPathSummary: string }>;
  latestCatalysts: Array<{ title: string; summary: string; eventTime: string }>;
};

export type DailySnapshot = {
  date: string;
  storageTimezone: string;
  dataMode?: "postgres" | "json" | "seed";
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

const execFileAsync = promisify(execFile);
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const FINAHUNT_ROOT = process.env.FINAHUNT_ROOT || path.resolve(process.cwd(), "../..");
const QUERY_SCRIPT = path.resolve(FINAHUNT_ROOT, "tools/query_web_data.py");

export function resolveTargetDate(value: string | string[] | undefined | null): string {
  const text = Array.isArray(value) ? value[0] : value;
  return typeof text === "string" && /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : SEED_DATE;
}

export function optionalTargetDate(value: string | string[] | undefined | null): string | undefined {
  const text = Array.isArray(value) ? value[0] : value;
  return typeof text === "string" && /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : undefined;
}

export function normalizeDailySnapshot(payload: unknown, date = SEED_DATE): DailySnapshot {
  const seed = createSeedSnapshot(date);
  if (!payload || typeof payload !== "object") {
    return seed;
  }

  const candidate = payload as Partial<DailySnapshot>;
  return {
    ...seed,
    ...candidate,
    date: candidate.date || date,
    stats: { ...seed.stats, ...(candidate.stats || {}) },
    sources: Array.isArray(candidate.sources) && candidate.sources.length ? candidate.sources : seed.sources,
    runs: Array.isArray(candidate.runs) && candidate.runs.length ? candidate.runs : seed.runs,
    themes: Array.isArray(candidate.themes) && candidate.themes.length ? candidate.themes : seed.themes,
    events: Array.isArray(candidate.events) && candidate.events.length ? candidate.events : seed.events,
    commonRiskNotices: Array.isArray(candidate.commonRiskNotices) && candidate.commonRiskNotices.length ? candidate.commonRiskNotices : seed.commonRiskNotices,
  };
}

function shouldUseSeedFallback(payload: DailySnapshot): boolean {
  if (process.env.SEED_UI_FALLBACK === "false") {
    return false;
  }
  return payload.dataMode === "seed" || payload.themes.length === 0 || payload.events.length === 0;
}

async function queryDailySnapshot(date?: string): Promise<unknown> {
  const args = date ? [QUERY_SCRIPT, "daily-snapshot", "--date", date] : [QUERY_SCRIPT, "daily-snapshot"];
  const { stdout } = await execFileAsync(PYTHON_BIN, args, {
    cwd: FINAHUNT_ROOT,
    env: process.env,
    timeout: 20_000,
    maxBuffer: 10 * 1024 * 1024,
  });
  return JSON.parse(stdout) as unknown;
}

export async function loadDailySnapshot(date?: string): Promise<DailySnapshot> {
  const fallbackDate = date || SEED_DATE;
  try {
    const payload = normalizeDailySnapshot(await queryDailySnapshot(date), fallbackDate);
    return shouldUseSeedFallback(payload) ? createSeedSnapshot(payload.date || fallbackDate) : payload;
  } catch {
    return createSeedSnapshot(fallbackDate);
  }
}

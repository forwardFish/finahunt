import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { createSeedWorkbench, SEED_DATE } from "@/lib/uiSeedData";

export type WorkbenchStageStatus = { stage: string; label: string; status: string };

export type MessageRow = {
  message: {
    message_id: string;
    title: string;
    summary: string;
    event_time: string;
    source_name: string;
    source_url: string;
    value_label: string;
    value_score: number;
  };
  fermentation: {
    fermentation_verdict: string;
    fermentation_score: number;
    why_it_may_ferment: string[];
    why_it_may_not_ferment: string[];
    consensus_stage: string;
  };
  impact: {
    primary_theme: string;
    impact_summary: string;
    impact_horizon: string;
    impact_direction: string;
    impact_path: string;
    theme_confidence: number;
    counter_themes: string[];
  };
  companies: Array<{
    company_name: string;
    company_code: string;
    role_label: string;
    relevance_score: number;
    purity_score: number | null;
    candidate_status: string;
    source_reason: string;
    source_reason_title: string;
    source_reason_url: string;
    llm_reason: string;
    crosscheck_status: string;
    reason_summary: string;
  }>;
  validation: {
    validation_status: string;
    validation_window: string;
    observed_company_moves: Array<{ company_code: string; windows: Record<string, number>; latest_return: number | null }>;
    observed_basket_move: Record<string, number>;
    observed_benchmark_move: Record<string, number>;
    excess_return: number | null;
    lagging_signal: boolean;
    calibration_action: string;
    calibration_reason: string;
    prediction_gap: string;
    validation_summary: string;
  };
  score: {
    importance_score: number;
    fermentation_score: number;
    impact_quality_score: number;
    company_discovery_score: number;
    reason_quality_score: number;
    market_validation_score: number | null;
    initial_actionability_score: number;
    recalibrated_actionability_score: number;
    final_verdict: string;
    score_summary: string;
  };
};

export type ThemeRow = {
  theme_name: string;
  low_position_score: number | null;
  low_position_reason: string;
  fermentation_phase: string;
  risk_notice: string;
  candidate_stocks: Array<Record<string, unknown>>;
  validation_bucket: string;
  messages: Array<{ message_id: string; title: string; summary: string; event_time: string; score: number | null; validation_status: string }>;
};

export type LowPositionWorkbench = {
  date: string;
  runId: string;
  createdAt: string;
  latestAvailableDate: string;
  dataMode?: "postgres" | "json" | "seed";
  state: "success" | "partial" | "empty";
  messageCount: number;
  themeCount: number;
  stages: WorkbenchStageStatus[];
  messages: MessageRow[];
  themes: ThemeRow[];
  validatedThemes: ThemeRow[];
  watchThemes: ThemeRow[];
  downgradedThemes: ThemeRow[];
};

const execFileAsync = promisify(execFile);
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const FINAHUNT_ROOT = process.env.FINAHUNT_ROOT || path.resolve(process.cwd(), "../..");
const QUERY_SCRIPT = path.resolve(FINAHUNT_ROOT, "tools/query_web_data.py");

export function resolveWorkbenchDate(value: string | string[] | undefined | null): string {
  const text = Array.isArray(value) ? value[0] : value;
  return typeof text === "string" && /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : SEED_DATE;
}

export function optionalWorkbenchDate(value: string | string[] | undefined | null): string | undefined {
  const text = Array.isArray(value) ? value[0] : value;
  return typeof text === "string" && /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : undefined;
}

export function normalizeLowPositionWorkbench(payload: unknown, date = SEED_DATE): LowPositionWorkbench {
  const seed = createSeedWorkbench(date);
  if (!payload || typeof payload !== "object") {
    return seed;
  }

  const candidate = payload as Partial<LowPositionWorkbench>;
  const themes = Array.isArray(candidate.themes) && candidate.themes.length ? candidate.themes : seed.themes;
  return {
    ...seed,
    ...candidate,
    date: candidate.date || date,
    stages: Array.isArray(candidate.stages) && candidate.stages.length ? candidate.stages : seed.stages,
    messages: Array.isArray(candidate.messages) && candidate.messages.length ? candidate.messages : seed.messages,
    themes,
    validatedThemes: Array.isArray(candidate.validatedThemes) && candidate.validatedThemes.length ? candidate.validatedThemes : themes.filter((item) => item.validation_bucket === "validated"),
    watchThemes: Array.isArray(candidate.watchThemes) && candidate.watchThemes.length ? candidate.watchThemes : themes.filter((item) => item.validation_bucket !== "validated"),
    downgradedThemes: Array.isArray(candidate.downgradedThemes) ? candidate.downgradedThemes : [],
    messageCount: candidate.messageCount ?? seed.messageCount,
    themeCount: candidate.themeCount ?? themes.length,
  };
}

function shouldUseSeedFallback(payload: LowPositionWorkbench): boolean {
  if (process.env.SEED_UI_FALLBACK === "false") {
    return false;
  }
  return payload.dataMode === "seed" || payload.themes.length === 0 || payload.messages.length === 0;
}

async function queryLowPositionWorkbench(date?: string): Promise<unknown> {
  const args = date ? [QUERY_SCRIPT, "low-position-workbench", "--date", date] : [QUERY_SCRIPT, "low-position-workbench"];
  const { stdout } = await execFileAsync(PYTHON_BIN, args, {
    cwd: FINAHUNT_ROOT,
    env: process.env,
    timeout: 20_000,
    maxBuffer: 10 * 1024 * 1024,
  });
  return JSON.parse(stdout) as unknown;
}

export async function loadLowPositionWorkbench(date?: string): Promise<LowPositionWorkbench> {
  const fallbackDate = date || SEED_DATE;
  try {
    const payload = normalizeLowPositionWorkbench(await queryLowPositionWorkbench(date), fallbackDate);
    return shouldUseSeedFallback(payload) ? createSeedWorkbench(payload.date || fallbackDate) : payload;
  } catch {
    return createSeedWorkbench(fallbackDate);
  }
}

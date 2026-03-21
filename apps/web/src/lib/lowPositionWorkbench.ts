import fs from "node:fs";
import path from "node:path";

type JsonRecord = Record<string, unknown>;

export type WorkbenchStageStatus = {
  stage: string;
  label: string;
  status: string;
};

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
    source_evidence_items?: Array<{
      source_site: string;
      source_url: string;
      source_title: string;
      source_excerpt: string;
      reason: string;
    }>;
    llm_reason: string;
    crosscheck_status: string;
    reason_summary: string;
  }>;
  validation: {
    validation_status: string;
    validation_window: string;
    observed_company_moves: Array<{
      company_code: string;
      windows: Record<string, number>;
      latest_return: number | null;
    }>;
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
  messages: Array<{
    message_id: string;
    title: string;
    summary: string;
    event_time: string;
    score: number | null;
    validation_status: string;
  }>;
};

export type LowPositionWorkbench = {
  date: string;
  runId: string;
  createdAt: string;
  latestAvailableDate: string;
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

const RUNTIME_ROOT = path.resolve(process.cwd(), "../../workspace/artifacts/runtime");

export function resolveWorkbenchDate(value: string | string[] | undefined): string {
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }
  return latestWorkbenchDate();
}

export function latestWorkbenchDate(): string {
  for (const runDir of listRunDirectories()) {
    const manifest = readJson<JsonRecord>(path.join(runDir, "manifest.json"));
    if (!manifest) {
      continue;
    }
    const createdAt = asString(manifest.created_at);
    if (!createdAt) {
      continue;
    }
    if (fs.existsSync(path.join(runDir, "daily_message_workbench.json"))) {
      return createdAt.slice(0, 10);
    }
  }
  return new Date().toISOString().slice(0, 10);
}

export function loadLowPositionWorkbench(date: string): LowPositionWorkbench {
  const match = findLatestWorkbenchRun(date);
  if (!match) {
    return {
      date,
      runId: "",
      createdAt: "",
      latestAvailableDate: latestWorkbenchDate(),
      state: "empty",
      messageCount: 0,
      themeCount: 0,
      stages: [],
      messages: [],
      themes: [],
      validatedThemes: [],
      watchThemes: [],
      downgradedThemes: [],
    };
  }

  const messageWorkbench = readJson<JsonRecord>(path.join(match.runDir, "daily_message_workbench.json")) ?? {};
  const themeWorkbench = readJson<JsonRecord>(path.join(match.runDir, "daily_theme_workbench.json")) ?? {};
  const orchestrator = readStageContent(match.runDir, "low_position_orchestrator");
  const statusRows = Array.isArray(orchestrator.workbench_stage_statuses)
    ? (orchestrator.workbench_stage_statuses as WorkbenchStageStatus[])
    : [];
  const messages = Array.isArray(messageWorkbench.messages) ? (messageWorkbench.messages as MessageRow[]) : [];
  const themes = Array.isArray(themeWorkbench.themes) ? (themeWorkbench.themes as ThemeRow[]) : [];
  const validatedThemes = Array.isArray(themeWorkbench.validated_themes) ? (themeWorkbench.validated_themes as ThemeRow[]) : [];
  const watchThemes = Array.isArray(themeWorkbench.watch_themes) ? (themeWorkbench.watch_themes as ThemeRow[]) : [];
  const downgradedThemes = Array.isArray(themeWorkbench.downgraded_themes) ? (themeWorkbench.downgraded_themes as ThemeRow[]) : [];
  const failedStages = statusRows.filter((item) => item.status === "fail").length;
  const hasUnverifiable = messages.some((item) => item.validation?.validation_status === "unverifiable");

  return {
    date,
    runId: match.runId,
    createdAt: match.createdAt,
    latestAvailableDate: latestWorkbenchDate(),
    state: failedStages > 0 || hasUnverifiable ? "partial" : messages.length > 0 ? "success" : "empty",
    messageCount: Number(messageWorkbench.message_count ?? messages.length ?? 0),
    themeCount: Number(themeWorkbench.theme_count ?? themes.length ?? 0),
    stages: statusRows,
    messages,
    themes,
    validatedThemes,
    watchThemes,
    downgradedThemes,
  };
}

function findLatestWorkbenchRun(date: string): { runId: string; runDir: string; createdAt: string } | null {
  for (const runDir of listRunDirectories()) {
    const manifest = readJson<JsonRecord>(path.join(runDir, "manifest.json"));
    if (!manifest) {
      continue;
    }
    const createdAt = asString(manifest.created_at);
    if (!createdAt || !createdAt.startsWith(date)) {
      continue;
    }
    if (!fs.existsSync(path.join(runDir, "daily_message_workbench.json"))) {
      continue;
    }
    return {
      runId: asString(manifest.run_id) || path.basename(runDir),
      runDir,
      createdAt,
    };
  }
  return null;
}

function readStageContent(runDir: string, stage: string): JsonRecord {
  const fallback = readJson<JsonRecord>(path.join(runDir, `${stage}.json`));
  return fallback ?? {};
}

function listRunDirectories(): string[] {
  if (!fs.existsSync(RUNTIME_ROOT)) {
    return [];
  }
  return fs
    .readdirSync(RUNTIME_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(RUNTIME_ROOT, entry.name))
    .sort((left, right) => fs.statSync(right).mtimeMs - fs.statSync(left).mtimeMs);
}

function readJson<T>(filePath: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return null;
  }
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

import { Buffer } from "node:buffer";
import type { Route } from "next";

import type { DailyEvent, DailyTheme } from "@/lib/dailySnapshot";
import type { MessageRow, ThemeRow } from "@/lib/lowPositionWorkbench";

const BROKEN_FRAGMENTS = ["锟", "�", "鐮", "涓", "閫", "鍙", "棰", "浣", "鎶", "杩", "鏃", "褰", "绌", "龚"];

export function safeText(value: string | null | undefined, fallback = "-"): string {
  if (!value) return fallback;
  const trimmed = value.trim();
  if (!trimmed) return fallback;
  if (!looksBroken(trimmed)) return trimmed;

  for (const candidate of decodeCandidates(trimmed)) {
    if (candidate && !looksBroken(candidate)) return candidate;
    if (candidate && candidate.length > 1 && brokenScore(candidate) < brokenScore(trimmed)) return candidate;
  }
  return trimmed;
}

function decodeCandidates(value: string): string[] {
  const candidates: string[] = [];
  try { candidates.push(Buffer.from(value, "latin1").toString("utf8").trim()); } catch {}
  try { candidates.push(Buffer.from(value, "binary").toString("utf8").trim()); } catch {}
  return [...new Set(candidates.filter(Boolean))];
}

function looksBroken(value: string): boolean { return brokenScore(value) >= 2; }
function brokenScore(value: string): number { return BROKEN_FRAGMENTS.reduce((score, fragment) => score + (value.includes(fragment) ? 1 : 0), 0); }

export function formatIso(value: string | null | undefined): string {
  const text = safeText(value, "");
  if (!text) return "-";
  return text.replace("T", " ").replace("+00:00", " UTC").replace("Z", " UTC");
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return value.toFixed(1);
}

export function themeName(theme: Partial<DailyTheme> | null | undefined): string {
  if (!theme) return "暂无主题";
  return safeText(theme.themeName || theme.clusterId || "", "未命名主题");
}

export function lowPositionThemeName(theme: Partial<ThemeRow> | null | undefined): string {
  if (!theme) return "暂无题材";
  return safeText(theme.theme_name || "", "未命名题材");
}

export function stageLabel(value: string | null | undefined): string {
  const key = (value || "").trim().toLowerCase();
  const labels: Record<string, string> = { hot: "拥挤扩散", fermenting: "持续发酵", emerging: "早期成形", "watch-only": "观察等待", watching: "观察等待", early: "早期阶段", spreading: "扩散阶段", crowded: "拥挤阶段" };
  return labels[key] || safeText(value, "观察等待");
}

export function validationLabel(value: string | null | undefined): string {
  const key = (value || "").trim().toLowerCase();
  const labels: Record<string, string> = { validated: "验证通过", watch: "继续观察", watching: "继续观察", downgraded: "降级处理", confirmed: "验证通过", partial: "部分兑现", no_reaction: "暂无反应", delayed_reaction: "滞后反应", inverse_reaction: "反向反应", unverifiable: "待验证" };
  return labels[key] || safeText(value, "-");
}

export function fermentationVerdictLabel(value: string | null | undefined): string {
  const key = (value || "").trim().toLowerCase();
  const labels: Record<string, string> = { high: "高潜力", medium: "中潜力", low: "弱潜力", reject: "暂不进入发酵链路" };
  return labels[key] || safeText(value, "-");
}

export function sourceLabel(sourceIdOrName: string | null | undefined): string {
  const value = (sourceIdOrName || "").trim();
  const labels: Record<string, string> = { "cls-telegraph": "财联社电报", "jiuyangongshe-live": "韭研公社", "xueqiu-hot-spot": "雪球热点" };
  return labels[value] || safeText(value, "未知来源");
}

export function buildHref(path: string, params?: Record<string, string | undefined>): Route {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => { if (value) query.set(key, value); });
  const suffix = query.toString();
  return (suffix ? `${path}?${suffix}` : path) as Route;
}

export function topThemes(themes: DailyTheme[], count = 4): DailyTheme[] { return [...themes].sort((left, right) => right.fermentationScore - left.fermentationScore).slice(0, count); }
export function lowPositionThemes(themes: DailyTheme[], count = 4): DailyTheme[] { return [...themes].filter((item) => item.lowPositionScore !== null).sort((left, right) => (right.lowPositionScore ?? 0) - (left.lowPositionScore ?? 0)).slice(0, count); }
export function featuredEvents(events: DailyEvent[], count = 4): DailyEvent[] { return [...events].slice(0, count); }

export function summarizeSnapshotState(runCount: number, themeCount: number, eventCount: number, sourceCount: number): { tone: "ready" | "partial" | "empty"; label: string; description: string } {
  if (runCount === 0) return { tone: "empty", label: "空白状态", description: "当前日期还没有可展示的运行批次，可刷新最新公开数据或切换到已有数据日期。" };
  if (themeCount === 0 || eventCount === 0 || sourceCount === 0) return { tone: "partial", label: "部分可用", description: "已有运行结果，但部分研究模块仍在补齐，页面先展示已形成判断的内容。" };
  return { tone: "ready", label: "已就绪", description: "今日入口、主线发酵、低位研究和工作台总览都具备可浏览的数据基础。" };
}

export function summarizeResearchState(state: "success" | "partial" | "empty"): { tone: "ready" | "partial" | "empty"; label: string; description: string } {
  if (state === "success") return { tone: "ready", label: "研究链路已就绪", description: "低位机会、候选公司、验证状态和工作台产物都已可浏览。" };
  if (state === "partial") return { tone: "partial", label: "部分可用", description: "低位研究链路已跑通，但还有部分消息或题材缺少完整验证结果。" };
  return { tone: "empty", label: "暂无研究结果", description: "当前日期还没有低位研究工作台数据，可执行低位挖掘或切换到已有结果的日期。" };
}

export function candidateNames(theme: ThemeRow, count = 5): string[] {
  return theme.candidate_stocks.map((item) => safeText(String(item.company_name || item.name || item.company_code || ""), "")).filter(Boolean).slice(0, count);
}

export function messageCompanyNames(row: MessageRow, count = 3): string[] {
  return row.companies.map((item) => safeText(item.company_name || item.company_code || "", "")).filter(Boolean).slice(0, count);
}

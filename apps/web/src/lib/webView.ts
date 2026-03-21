import { Buffer } from "node:buffer";
import type { Route } from "next";

import type { DailyEvent, DailyTheme } from "@/lib/dailySnapshot";
import type { MessageRow, ThemeRow } from "@/lib/lowPositionWorkbench";

const BROKEN_FRAGMENTS = [
  "鏆傛",
  "鍙",
  "鐨勮",
  "鏈",
  "闃舵",
  "杩愯",
  "鐮旂",
  "涓婚",
  "鍏抽",
  "浣庝",
  "鎸佺",
  "鍒囨",
  "鏃ユ",
  "璇佹",
  "娑堟",
  "棰樻",
  "鍙戦",
  "鈥",
  "Ã",
  "Â",
  "â",
  "�",
];

export function safeText(value: string | null | undefined, fallback = "-"): string {
  if (!value) {
    return fallback;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return fallback;
  }

  if (!looksBroken(trimmed)) {
    return trimmed;
  }

  try {
    const repaired = Buffer.from(trimmed, "latin1").toString("utf8").trim();
    if (looksMoreReadable(trimmed, repaired)) {
      return repaired || fallback;
    }
  } catch {
    // Keep original text when repair is unsafe.
  }

  return trimmed;
}

export function formatIso(value: string | null | undefined): string {
  const text = safeText(value, "");
  return text ? text.replace("T", " ").replace("+00:00", " UTC") : "-";
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return value.toFixed(1);
}

export function themeName(theme: Partial<DailyTheme> | null | undefined): string {
  if (!theme) {
    return "暂无主题";
  }
  return safeText(theme.themeName || theme.clusterId || "", "未命名主题");
}

export function lowPositionThemeName(theme: Partial<ThemeRow> | null | undefined): string {
  if (!theme) {
    return "暂无题材";
  }
  return safeText(theme.theme_name || "", "未命名题材");
}

export function stageLabel(value: string | null | undefined): string {
  switch ((value || "").trim().toLowerCase()) {
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
      return safeText(value, "观察等待");
  }
}

export function validationLabel(value: string | null | undefined): string {
  const key = (value || "").trim().toLowerCase();
  const labels: Record<string, string> = {
    confirmed: "验证通过",
    partial: "部分兑现",
    no_reaction: "无明显反应",
    delayed_reaction: "滞后反应",
    inverse_reaction: "反向反应",
    unverifiable: "待验证",
  };
  return labels[key] || safeText(value, "-");
}

export function fermentationVerdictLabel(value: string | null | undefined): string {
  const key = (value || "").trim().toLowerCase();
  const labels: Record<string, string> = {
    high: "高潜力",
    medium: "中潜力",
    low: "弱潜力",
    reject: "不进入发酵链路",
  };
  return labels[key] || safeText(value, "-");
}

export function sourceLabel(sourceIdOrName: string | null | undefined): string {
  const value = (sourceIdOrName || "").trim();
  switch (value) {
    case "cls-telegraph":
      return "财联社快讯";
    case "jiuyangongshe-live":
      return "韭研公社";
    case "xueqiu-hot-spot":
      return "雪球热点";
    default:
      return safeText(value, "未知来源");
  }
}

export function buildHref(path: string, params?: Record<string, string | undefined>): Route {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  const suffix = query.toString();
  return (suffix ? `${path}?${suffix}` : path) as Route;
}

export function topThemes(themes: DailyTheme[], count = 4): DailyTheme[] {
  return [...themes].sort((left, right) => right.fermentationScore - left.fermentationScore).slice(0, count);
}

export function lowPositionThemes(themes: DailyTheme[], count = 4): DailyTheme[] {
  return [...themes]
    .filter((item) => item.lowPositionScore !== null)
    .sort((left, right) => (right.lowPositionScore ?? 0) - (left.lowPositionScore ?? 0))
    .slice(0, count);
}

export function featuredEvents(events: DailyEvent[], count = 4): DailyEvent[] {
  return [...events].slice(0, count);
}

export function summarizeSnapshotState(
  runCount: number,
  themeCount: number,
  eventCount: number,
  sourceCount: number,
): { tone: "ready" | "partial" | "empty"; label: string; description: string } {
  if (runCount === 0) {
    return {
      tone: "empty",
      label: "空白状态",
      description: "当前日期还没有可展示的运行批次，请先刷新最新公开数据或切换到已有数据的日期。",
    };
  }
  if (themeCount === 0 || eventCount === 0 || sourceCount === 0) {
    return {
      tone: "partial",
      label: "部分可用",
      description: "今天已有运行结果，但部分研究模块仍在补齐，页面先展示已经形成判断的内容入口。",
    };
  }
  return {
    tone: "ready",
    label: "已就绪",
    description: "今日入口、主线发酵、低位研究和工作台总览都已经具备可浏览的数据基础。",
  };
}

export function summarizeResearchState(
  state: "success" | "partial" | "empty",
): { tone: "ready" | "partial" | "empty"; label: string; description: string } {
  if (state === "success") {
    return {
      tone: "ready",
      label: "研究链路已就绪",
      description: "低位机会、候选公司、验证状态和工作台产物都已经可浏览。",
    };
  }
  if (state === "partial") {
    return {
      tone: "partial",
      label: "部分可用",
      description: "低位研究链路已经跑通，但还有部分消息或题材缺少完整验证结果。",
    };
  }
  return {
    tone: "empty",
    label: "暂无研究结果",
    description: "当前日期还没有低位研究工作台数据，请先执行低位挖掘或切换到已有结果的日期。",
  };
}

export function candidateNames(theme: ThemeRow, count = 5): string[] {
  if (!Array.isArray(theme.candidate_stocks)) {
    return [];
  }
  return theme.candidate_stocks
    .map((item) => {
      const name =
        typeof item["stock_name"] === "string"
          ? item["stock_name"]
          : typeof item["name"] === "string"
            ? item["name"]
            : "";
      return safeText(name, "");
    })
    .filter(Boolean)
    .slice(0, count);
}

export function messageCompanyNames(row: MessageRow, count = 3): string[] {
  return row.companies
    .map((item) => safeText(item.company_name, ""))
    .filter(Boolean)
    .slice(0, count);
}

function looksBroken(value: string): boolean {
  return BROKEN_FRAGMENTS.some((fragment) => value.includes(fragment));
}

function looksMoreReadable(original: string, repaired: string): boolean {
  const originalScore = readabilityScore(original);
  const repairedScore = readabilityScore(repaired);
  return repairedScore > originalScore + 2;
}

function readabilityScore(value: string): number {
  let score = 0;
  for (const char of value) {
    if (/[\u4e00-\u9fff]/.test(char)) {
      score += 2;
    } else if (/[a-zA-Z0-9]/.test(char)) {
      score += 1;
    } else if ("，。！？；：“”‘’（）()[]{}-_/ ".includes(char)) {
      score += 0.2;
    }
  }

  for (const fragment of BROKEN_FRAGMENTS) {
    if (value.includes(fragment)) {
      score -= 3;
    }
  }

  return score;
}

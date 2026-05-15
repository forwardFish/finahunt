import type { Route } from "next";
import type { DailyEvent, DailyTheme } from "@/lib/dailySnapshot";
import type { MessageRow, ThemeRow } from "@/lib/lowPositionWorkbench";
export function safeText(value: string | null | undefined, fallback = "-"): string { return value && value.trim() ? value.trim() : fallback; }
export function formatIso(value: string | null | undefined): string { return safeText(value, "").replace("T", " ").replace("+08:00", "").replace("Z", " UTC") || "-"; }
export function formatScore(value: number | null | undefined): string { return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "-"; }
export function themeName(theme: Partial<DailyTheme> | null | undefined): string { return safeText(theme?.themeName || theme?.clusterId, "未命名题材"); }
export function lowPositionThemeName(theme: Partial<ThemeRow> | null | undefined): string { return safeText(theme?.theme_name, "未命名低位题材"); }
export function stageLabel(value: string | null | undefined): string { const labels: Record<string,string> = { fermenting: "发酵中", spreading: "扩散中", watching: "观察中", hot: "高热度" }; return labels[(value || "").toLowerCase()] || safeText(value, "观察中"); }
export function validationLabel(value: string | null | undefined): string { const labels: Record<string,string> = { validated: "已验证", watch: "观察", downgraded: "降级", high: "高", medium: "中", low: "低" }; return labels[(value || "").toLowerCase()] || safeText(value, "观察"); }
export function fermentationVerdictLabel(value: string | null | undefined): string { return validationLabel(value); }
export function sourceLabel(value: string | null | undefined): string { const labels: Record<string,string> = { policy: "公开政策", company: "公司公告", media: "财经媒体" }; return labels[value || ""] || safeText(value, "公开来源"); }
export function buildHref(path: string, params?: Record<string, string | undefined>): Route { const query = new URLSearchParams(); Object.entries(params || {}).forEach(([key, value]) => { if (value) query.set(key, value); }); const suffix = query.toString(); return (suffix ? `${path}?${suffix}` : path) as Route; }
export function topThemes(themes: DailyTheme[], count = 4): DailyTheme[] { return [...themes].sort((a, b) => b.fermentationScore - a.fermentationScore).slice(0, count); }
export function lowPositionThemes(themes: DailyTheme[], count = 4): DailyTheme[] { return [...themes].filter((item) => item.lowPositionScore !== null).sort((a, b) => (b.lowPositionScore ?? 0) - (a.lowPositionScore ?? 0)).slice(0, count); }
export function featuredEvents(events: DailyEvent[], count = 4): DailyEvent[] { return [...events].slice(0, count); }
export function summarizeSnapshotState(runCount: number, themeCount: number, eventCount: number, sourceCount: number): { tone: "ready" | "partial" | "empty"; label: string; description: string } { if (!runCount) return { tone: "empty", label: "待生成", description: "暂无本地运行批次。" }; if (!themeCount || !eventCount || !sourceCount) return { tone: "partial", label: "部分可用", description: "已有数据，但部分模块证据不足。" }; return { tone: "ready", label: "可验收", description: "事件、题材、来源和研究工作台均有可浏览证据。" }; }
export function summarizeResearchState(state: "success" | "partial" | "empty"): { tone: "ready" | "partial" | "empty"; label: string; description: string } { if (state === "success") return { tone: "ready", label: "研究链闭环", description: "低位研究卡、消息和验证桶已生成。" }; if (state === "partial") return { tone: "partial", label: "部分研究", description: "研究链路存在待补证据。" }; return { tone: "empty", label: "待运行", description: "暂无低位研究工作台数据。" }; }
export function candidateNames(theme: ThemeRow, count = 5): string[] { return theme.candidate_stocks.map((item) => String(item.company_name || item.name || item.company_code || "")).filter(Boolean).slice(0, count); }
export function messageCompanyNames(row: MessageRow, count = 3): string[] { return row.companies.map((item) => safeText(item.company_name || item.company_code, "")).filter(Boolean).slice(0, count); }

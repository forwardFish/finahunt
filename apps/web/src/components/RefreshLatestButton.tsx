"use client";

import { startTransition, useState } from "react";

type RefreshResponse = {
  ok?: boolean;
  run_id?: string;
  latestDate?: string;
  low_position_count?: number;
  fermenting_theme_count?: number;
  error?: string;
};

type RefreshLatestButtonProps = {
  latestRunId: string;
  successPath?: string;
  successParams?: Record<string, string>;
};

function buildSuccessHref(
  latestDate: string | undefined,
  successPath: string,
  successParams: Record<string, string>,
): string {
  const params = new URLSearchParams(successParams);
  if (latestDate) {
    params.set("date", latestDate);
  }
  const query = params.toString();
  return query ? `${successPath}?${query}` : successPath;
}

export function RefreshLatestButton({
  latestRunId,
  successPath = "/",
  successParams = {},
}: RefreshLatestButtonProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [message, setMessage] = useState(
    latestRunId ? `当前最新 run：${latestRunId}` : "当前还没有可展示的运行批次。",
  );

  async function handleRefresh(): Promise<void> {
    setIsRunning(true);
    setStatus("running");
    setMessage("正在抓取最新公开资讯，通常需要 60 到 120 秒。");

    try {
      const response = await fetch("/api/refresh-latest", { method: "POST" });
      const payload = (await response.json()) as RefreshResponse;
      if (!response.ok || payload.ok === false) {
        throw new Error(payload.error || "refresh_failed");
      }

      setStatus("success");
      setMessage(
        `抓取完成：${payload.run_id || "-"}，低位机会 ${payload.low_position_count ?? 0}，发酵主题 ${
          payload.fermenting_theme_count ?? 0
        }`,
      );

      startTransition(() => {
        const nextHref = buildSuccessHref(payload.latestDate, successPath, successParams);
        window.location.assign(nextHref);
      });
    } catch (error) {
      const text = error instanceof Error ? error.message : "unknown_error";
      setStatus("error");
      setMessage(`抓取失败：${text}。请稍后重试，或检查本地运行脚本与公开源连接状态。`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="refresh-box" data-refresh-state={status}>
      <button type="button" className="secondary-button" onClick={handleRefresh} disabled={isRunning}>
        {isRunning ? "抓取中..." : "立即抓最新"}
      </button>
      <span aria-live="polite" className="refresh-text">
        {message}
      </span>
    </div>
  );
}

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
};

export function RefreshLatestButton({ latestRunId }: RefreshLatestButtonProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState(
    latestRunId ? `当前最新 run: ${latestRunId}` : "当前还没有可展示的运行批次。"
  );

  async function handleRefresh(): Promise<void> {
    setIsRunning(true);
    setMessage("正在抓取最新公开资讯，可能需要 60-120 秒...");
    try {
      const response = await fetch("/api/refresh-latest", { method: "POST" });
      const payload = (await response.json()) as RefreshResponse;
      if (!response.ok || payload.ok === false) {
        throw new Error(payload.error || "refresh_failed");
      }
      setMessage(
        `抓取完成: ${payload.run_id || "-"}，低位机会 ${payload.low_position_count ?? 0}，发酵题材 ${
          payload.fermenting_theme_count ?? 0
        }`
      );
      startTransition(() => {
        const nextHref = payload.latestDate ? `/?date=${payload.latestDate}` : "/";
        window.location.assign(nextHref);
      });
    } catch (error) {
      const text = error instanceof Error ? error.message : "unknown_error";
      setMessage(`抓取失败: ${text}`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="refresh-box">
      <button type="button" className="secondary-button" onClick={handleRefresh} disabled={isRunning}>
        {isRunning ? "抓取中..." : "立即抓最新"}
      </button>
      <span className="refresh-text">{message}</span>
    </div>
  );
}

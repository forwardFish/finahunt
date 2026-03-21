"use client";

import { startTransition, useState } from "react";

type RunResponse = {
  ok?: boolean;
  run_id?: string;
  latestDate?: string;
  message_count?: number;
  theme_count?: number;
  error?: string;
};

export function RunLowPositionButton({ latestRunId }: { latestRunId: string }) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState(
    latestRunId ? `当前最新 run：${latestRunId}` : "当前还没有低位挖掘工作台运行记录。",
  );

  async function handleRun(): Promise<void> {
    setIsRunning(true);
    setMessage("正在执行低位挖掘一键链路，通常需要 60 到 180 秒。");

    try {
      const response = await fetch("/api/run-low-position", { method: "POST" });
      const payload = (await response.json()) as RunResponse;
      if (!response.ok || payload.ok === false) {
        throw new Error(payload.error || "run_low_position_failed");
      }

      setMessage(`执行完成：${payload.run_id || "-"}，消息 ${payload.message_count ?? 0} 条，题材 ${payload.theme_count ?? 0} 个。`);
      startTransition(() => {
        const params = new URLSearchParams();
        if (payload.latestDate) {
          params.set("date", payload.latestDate);
        }
        window.location.assign(`/research?${params.toString()}`);
      });
    } catch (error) {
      setMessage(`执行失败：${error instanceof Error ? error.message : "unknown_error"}`);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="refresh-box" data-refresh-state={isRunning ? "running" : "idle"}>
      <button type="button" className="secondary-button" onClick={handleRun} disabled={isRunning}>
        {isRunning ? "执行中..." : "运行低位挖掘"}
      </button>
      <span aria-live="polite" className="refresh-text">
        {message}
      </span>
    </div>
  );
}

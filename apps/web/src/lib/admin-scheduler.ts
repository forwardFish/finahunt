import path from "node:path";
import { spawn } from "node:child_process";

import { adminQuery, ensureAdminSchema } from "@/lib/admin-db";

declare global {
  // eslint-disable-next-line no-var
  var __finahuntAdminSchedulerStarted: boolean | undefined;
}

const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const FINAHUNT_ROOT = process.env.FINAHUNT_ROOT || path.resolve(process.cwd(), "../..");
const CRAWLER_SCRIPT = path.resolve(FINAHUNT_ROOT, "scripts/run_admin_crawler.py");

export function startAdminCrawlerProcess(sourceId = "all", runId = createRunId()): { runId: string; started: boolean } {
  const child = spawn(PYTHON_BIN, [CRAWLER_SCRIPT, "--source", sourceId, "--run-id", runId], {
    cwd: FINAHUNT_ROOT,
    env: process.env,
    stdio: "ignore",
    windowsHide: true,
    detached: false,
  });
  child.unref();
  return { runId, started: true };
}

export function ensureAdminScheduler(): void {
  if (globalThis.__finahuntAdminSchedulerStarted) {
    return;
  }
  globalThis.__finahuntAdminSchedulerStarted = true;
  setInterval(() => {
    void tickScheduler();
  }, 60_000).unref();
  void tickScheduler();
}

async function tickScheduler(): Promise<void> {
  try {
    await ensureAdminSchema();
    const settings = await adminQuery<{ enabled: boolean; schedule_time: string; source_id: string }>(
      "SELECT enabled, schedule_time, source_id FROM admin_crawler_settings WHERE id = 1"
    );
    const setting = settings[0];
    if (!setting?.enabled) {
      return;
    }
    const now = new Date();
    const current = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    if (current !== setting.schedule_time) {
      return;
    }
    const today = now.toISOString().slice(0, 10);
    const rows = await adminQuery<{ count: string }>(
      "SELECT count(*)::text AS count FROM crawl_runs WHERE source_id = $1 AND started_at::date = $2::date",
      [setting.source_id || "all", today]
    );
    if (Number(rows[0]?.count || 0) > 0) {
      return;
    }
    startAdminCrawlerProcess(setting.source_id || "all");
  } catch {
    // Scheduler is best-effort for the local admin page.
  }
}

export function createRunId(): string {
  const now = new Date();
  const stamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0"),
  ].join("");
  return `admin-${stamp}`;
}

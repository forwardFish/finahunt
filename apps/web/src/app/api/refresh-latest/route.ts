import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { NextResponse } from "next/server";

import { resolveTargetDate } from "@/lib/dailySnapshot";

const execFileAsync = promisify(execFile);
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const FINAHUNT_ROOT = path.resolve(process.cwd(), "../..");
const RUN_SCRIPT = path.resolve(FINAHUNT_ROOT, "tools/run_latest_snapshot.py");

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(): Promise<NextResponse> {
  try {
    const { stdout } = await execFileAsync(PYTHON_BIN, [RUN_SCRIPT], {
      cwd: FINAHUNT_ROOT,
      timeout: 10 * 60 * 1000,
      maxBuffer: 10 * 1024 * 1024,
    });
    const payload = JSON.parse(stdout) as Record<string, unknown>;
    return NextResponse.json({
      ok: true,
      ...payload,
      latestDate: resolveTargetDate(undefined),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "refresh_failed";
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

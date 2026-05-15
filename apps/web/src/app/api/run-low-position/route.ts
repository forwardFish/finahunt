import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { NextResponse } from "next/server";

import { loadLowPositionWorkbench, optionalWorkbenchDate } from "@/lib/lowPositionWorkbench";

const execFileAsync = promisify(execFile);
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const FINAHUNT_ROOT = path.resolve(process.cwd(), "../..");
const RUN_SCRIPT = path.resolve(FINAHUNT_ROOT, "tools/run_low_position_workbench.py");
const RUN_ARGS = process.env.FINAHUNT_ACCEPTANCE_SMOKE === "1" ? [RUN_SCRIPT, "--acceptance-smoke"] : [RUN_SCRIPT];

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<NextResponse> {
  const { searchParams } = new URL(request.url);
  const date = optionalWorkbenchDate(searchParams.get("date") ?? undefined);
  return NextResponse.json(await loadLowPositionWorkbench(date));
}

export async function POST(): Promise<NextResponse> {
  try {
    const { stdout } = await execFileAsync(PYTHON_BIN, RUN_ARGS, {
      cwd: FINAHUNT_ROOT,
      timeout: 10 * 60 * 1000,
      maxBuffer: 10 * 1024 * 1024,
    });
    const payload = JSON.parse(stdout) as Record<string, unknown>;
    return NextResponse.json({
      ok: true,
      ...payload,
      latestDate: typeof payload.latestDate === "string" ? payload.latestDate : undefined,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "run_low_position_failed";
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}

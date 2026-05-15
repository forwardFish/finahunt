import { NextResponse } from "next/server";

import { ensureAdminScheduler, startAdminCrawlerProcess } from "@/lib/admin-scheduler";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(): Promise<NextResponse> {
  ensureAdminScheduler();
  try {
    return NextResponse.json(startAdminCrawlerProcess("all"));
  } catch (error) {
    return NextResponse.json({ started: false, error: error instanceof Error ? error.message : "crawler_start_failed" }, { status: 500 });
  }
}

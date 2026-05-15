import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";
import { ensureAdminScheduler } from "@/lib/admin-scheduler";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(): Promise<NextResponse> {
  ensureAdminScheduler();
  try {
    const rows = await adminQuery<{
      last_run_at: Date | null;
      last_status: string | null;
      today_fetched: string;
      today_inserted: string;
      today_duplicated: string;
      today_failed: string;
    }>(`
      SELECT
        (SELECT COALESCE(finished_at, started_at) FROM crawl_runs ORDER BY started_at DESC LIMIT 1) AS last_run_at,
        (SELECT status FROM crawl_runs ORDER BY started_at DESC LIMIT 1) AS last_status,
        COALESCE(SUM(fetched_count) FILTER (WHERE started_at::date = CURRENT_DATE), 0)::text AS today_fetched,
        COALESCE(SUM(inserted_count) FILTER (WHERE started_at::date = CURRENT_DATE), 0)::text AS today_inserted,
        COALESCE(SUM(duplicate_count) FILTER (WHERE started_at::date = CURRENT_DATE), 0)::text AS today_duplicated,
        COALESCE(SUM(failed_count) FILTER (WHERE started_at::date = CURRENT_DATE), 0)::text AS today_failed
      FROM crawl_runs
    `);
    const row = rows[0];
    return NextResponse.json({
      postgresConnected: true,
      lastRunAt: row?.last_run_at ? row.last_run_at.toISOString() : "",
      lastStatus: row?.last_status || "",
      todayFetched: Number(row?.today_fetched || 0),
      todayInserted: Number(row?.today_inserted || 0),
      todayDuplicated: Number(row?.today_duplicated || 0),
      todayFailed: Number(row?.today_failed || 0),
    });
  } catch (error) {
    return NextResponse.json({
      postgresConnected: false,
      error: error instanceof Error ? error.message : "postgres_status_failed",
      lastRunAt: "",
      lastStatus: "",
      todayFetched: 0,
      todayInserted: 0,
      todayDuplicated: 0,
      todayFailed: 0,
    });
  }
}

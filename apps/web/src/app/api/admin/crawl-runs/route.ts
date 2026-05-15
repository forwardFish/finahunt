import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type CrawlRunRow = {
  run_id: string;
  source_id: string;
  status: string;
  started_at: Date;
  finished_at: Date | null;
  fetched_count: number;
  inserted_count: number;
  duplicate_count: number;
  failed_count: number;
  error_message: string;
};

export async function GET(): Promise<NextResponse> {
  const rows = await adminQuery<CrawlRunRow>(`
    SELECT run_id, source_id, status, started_at, finished_at, fetched_count, inserted_count, duplicate_count, failed_count, error_message
    FROM crawl_runs
    ORDER BY started_at DESC
    LIMIT 10
  `);
  return NextResponse.json({
    runs: rows.map((row) => ({
      runId: row.run_id,
      sourceId: row.source_id,
      status: row.status,
      startedAt: row.started_at?.toISOString?.() || "",
      finishedAt: row.finished_at?.toISOString?.() || "",
      fetchedCount: row.fetched_count,
      insertedCount: row.inserted_count,
      duplicateCount: row.duplicate_count,
      failedCount: row.failed_count,
      errorMessage: row.error_message,
    })),
  });
}

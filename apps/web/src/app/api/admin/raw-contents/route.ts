import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RawRow = {
  document_id: string;
  run_id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  published_at: string;
  content_length: number;
  source_hash: string;
  truth_score: number;
  authenticity_status: string;
  review_status: string;
  created_at: Date;
};

export async function GET(): Promise<NextResponse> {
  const rows = await adminQuery<RawRow>(`
    SELECT document_id, run_id, source_id, source_name, title, url, published_at, content_length,
           source_hash, truth_score, authenticity_status, review_status, created_at
    FROM raw_contents
    ORDER BY created_at DESC
    LIMIT 50
  `);
  return NextResponse.json({
    items: rows.map((row) => ({
      documentId: row.document_id,
      runId: row.run_id,
      sourceId: row.source_id,
      sourceName: row.source_name,
      title: row.title,
      url: row.url,
      publishedAt: row.published_at,
      contentLength: row.content_length,
      sourceHash: row.source_hash,
      truthScore: row.truth_score,
      authenticityStatus: row.authenticity_status,
      reviewStatus: row.review_status,
      createdAt: row.created_at?.toISOString?.() || "",
    })),
  });
}

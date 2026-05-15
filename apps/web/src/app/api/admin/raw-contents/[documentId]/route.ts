import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ documentId: string }> };

type DetailRow = {
  document_id: string;
  run_id: string;
  source_id: string;
  source_name: string;
  title: string;
  url: string;
  published_at: string;
  content_text: string;
  http_status: number | null;
  content_length: number;
  source_hash: string;
  truth_score: number;
  authenticity_status: string;
  review_status: string;
  reviewer_note: string;
  payload: Record<string, unknown>;
  created_at: Date;
};

export async function GET(_request: Request, context: RouteContext): Promise<NextResponse> {
  const { documentId } = await context.params;
  const rows = await adminQuery<DetailRow>(
    `
      SELECT document_id, run_id, source_id, source_name, title, url, published_at, content_text,
             http_status, content_length, source_hash, truth_score, authenticity_status, review_status,
             reviewer_note, payload, created_at
      FROM raw_contents
      WHERE document_id = $1
      LIMIT 1
    `,
    [decodeURIComponent(documentId)]
  );
  const row = rows[0];
  if (!row) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
  return NextResponse.json({
    documentId: row.document_id,
    runId: row.run_id,
    sourceId: row.source_id,
    sourceName: row.source_name,
    title: row.title,
    url: row.url,
    publishedAt: row.published_at,
    contentText: row.content_text,
    httpStatus: row.http_status,
    contentLength: row.content_length,
    sourceHash: row.source_hash,
    truthScore: row.truth_score,
    authenticityStatus: row.authenticity_status,
    reviewStatus: row.review_status,
    reviewerNote: row.reviewer_note,
    payload: row.payload,
    createdAt: row.created_at?.toISOString?.() || "",
  });
}

import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ documentId: string }> };

const ACTION_STATUS: Record<string, { reviewStatus: string; authenticityStatus: string }> = {
  trusted: { reviewStatus: "trusted", authenticityStatus: "trusted" },
  untrusted: { reviewStatus: "untrusted", authenticityStatus: "blocked" },
  garbled: { reviewStatus: "garbled", authenticityStatus: "blocked" },
  recrawl: { reviewStatus: "recrawl", authenticityStatus: "needs_review" },
};

export async function POST(request: Request, context: RouteContext): Promise<NextResponse> {
  const { documentId } = await context.params;
  const body = (await request.json().catch(() => ({}))) as Partial<{ action: string; reviewerNote: string }>;
  const action = body.action || "";
  const status = ACTION_STATUS[action];
  if (!status) {
    return NextResponse.json({ error: "unsupported_action" }, { status: 400 });
  }
  const id = decodeURIComponent(documentId);
  const note = typeof body.reviewerNote === "string" ? body.reviewerNote : "";
  const rows = await adminQuery<{ document_id: string; review_status: string; authenticity_status: string }>(
    `
      UPDATE raw_contents
      SET review_status = $2,
          authenticity_status = $3,
          reviewer_note = $4
      WHERE document_id = $1
      RETURNING document_id, review_status, authenticity_status
    `,
    [id, status.reviewStatus, status.authenticityStatus, note]
  );
  if (!rows[0]) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
  await adminQuery(
    `
      INSERT INTO admin_review_logs (target_type, target_id, action, reviewer_note, payload)
      VALUES ('raw_content', $1, $2, $3, $4::jsonb)
    `,
    [id, action, note, JSON.stringify({ authenticityStatus: status.authenticityStatus, reviewStatus: status.reviewStatus })]
  );
  return NextResponse.json({
    documentId: rows[0].document_id,
    reviewStatus: rows[0].review_status,
    authenticityStatus: rows[0].authenticity_status,
  });
}

import { NextResponse } from "next/server";

import { adminQuery } from "@/lib/admin-db";
import { ensureAdminScheduler } from "@/lib/admin-scheduler";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type SettingRow = { enabled: boolean; schedule_time: string; source_id: string; updated_at: Date };

function serialize(row: SettingRow) {
  return {
    enabled: Boolean(row.enabled),
    scheduleTime: row.schedule_time || "09:00",
    sourceId: row.source_id || "all",
    updatedAt: row.updated_at?.toISOString?.() || "",
  };
}

export async function GET(): Promise<NextResponse> {
  ensureAdminScheduler();
  const rows = await adminQuery<SettingRow>("SELECT enabled, schedule_time, source_id, updated_at FROM admin_crawler_settings WHERE id = 1");
  return NextResponse.json(serialize(rows[0] ?? { enabled: false, schedule_time: "09:00", source_id: "all", updated_at: new Date(0) }));
}

export async function POST(request: Request): Promise<NextResponse> {
  ensureAdminScheduler();
  const body = (await request.json().catch(() => ({}))) as Partial<{ enabled: boolean; scheduleTime: string; sourceId: string }>;
  const scheduleTime = typeof body.scheduleTime === "string" && /^\d{2}:\d{2}$/.test(body.scheduleTime) ? body.scheduleTime : "09:00";
  const sourceId = typeof body.sourceId === "string" && body.sourceId.trim() ? body.sourceId.trim() : "all";
  const rows = await adminQuery<SettingRow>(
    `
      INSERT INTO admin_crawler_settings (id, enabled, schedule_time, source_id, updated_at)
      VALUES (1, $1, $2, $3, now())
      ON CONFLICT (id) DO UPDATE
      SET enabled = EXCLUDED.enabled,
          schedule_time = EXCLUDED.schedule_time,
          source_id = EXCLUDED.source_id,
          updated_at = now()
      RETURNING enabled, schedule_time, source_id, updated_at
    `,
    [Boolean(body.enabled), scheduleTime, sourceId]
  );
  return NextResponse.json(serialize(rows[0]));
}

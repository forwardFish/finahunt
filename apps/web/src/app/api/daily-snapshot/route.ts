import { NextResponse } from "next/server";

import { loadDailySnapshot, resolveTargetDate } from "@/lib/dailySnapshot";

export async function GET(request: Request): Promise<NextResponse> {
  const { searchParams } = new URL(request.url);
  const date = resolveTargetDate(searchParams.get("date") ?? undefined);
  return NextResponse.json(loadDailySnapshot(date));
}

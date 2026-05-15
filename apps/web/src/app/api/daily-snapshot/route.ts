import { NextResponse } from "next/server";

import { loadDailySnapshot, optionalTargetDate } from "@/lib/dailySnapshot";

export async function GET(request: Request): Promise<NextResponse> {
  const { searchParams } = new URL(request.url);
  const date = optionalTargetDate(searchParams.get("date") ?? undefined);
  return NextResponse.json(await loadDailySnapshot(date));
}

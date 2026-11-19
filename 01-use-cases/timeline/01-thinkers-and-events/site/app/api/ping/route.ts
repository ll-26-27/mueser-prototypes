import { NextResponse } from "next/server";
import { meta } from "@/lib/data";
import { CASE_ID, readLog } from "@/lib/log";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({ case_id: CASE_ID, data_id: meta().data_id, who: process.env.TIMELINE_WHO || "", events: readLog().length });
}

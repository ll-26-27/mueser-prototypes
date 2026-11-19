import { NextResponse } from "next/server";
import { band, edgesOf, hasNode } from "@/lib/data";

export const dynamic = "force-dynamic";

/** Bars for a span of years: ?y0=&y1=&sel=<node id>. Bars connected to the chosen node come first. */
export async function GET(req: Request) {
  const p = new URL(req.url).searchParams;
  const y0 = Number(p.get("y0")), y1 = Number(p.get("y1"));
  if (!Number.isFinite(y0) || !Number.isFinite(y1) || y1 <= y0 || y1 - y0 > 6000) return NextResponse.json({ error: "y0 and y1 are years, y1 after y0" }, { status: 400 });
  const sel = p.get("sel");
  const connected = new Set<string>();
  if (sel && hasNode(sel)) for (const e of edgesOf(sel)) if (e.status !== "rejected") connected.add(e.src === sel ? e.dst : e.src);
  return NextResponse.json(band(y0, y1, sel && hasNode(sel) ? sel : null, connected));
}

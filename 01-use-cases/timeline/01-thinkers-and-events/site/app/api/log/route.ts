import { NextResponse } from "next/server";
import { appendEvent, CASE_ID, LOG_PATH, readLog, validate } from "@/lib/log";
import { hasNode } from "@/lib/data";
import type { LogEvent } from "@/lib/model";
import fs from "node:fs";

export const dynamic = "force-dynamic";

/** GET: the log as written (newline-delimited JSON). POST: validate one event and append it. */
export async function GET() {
  const body = fs.existsSync(LOG_PATH) ? fs.readFileSync(LOG_PATH) : Buffer.alloc(0);
  return new NextResponse(body, { headers: { "Content-Type": "application/x-ndjson; charset=utf-8", "Cache-Control": "no-store" } });
}

export async function POST(req: Request) {
  const caseId = req.headers.get("X-Timeline-Case");
  if (caseId && caseId !== CASE_ID) return NextResponse.json({ error: "this page belongs to another timeline case; reload before saving" }, { status: 409 });
  let ev: unknown;
  try { ev = await req.json(); } catch { return NextResponse.json({ error: "invalid JSON" }, { status: 400 }); }
  const err = validate(ev);
  if (err) return NextResponse.json({ error: `invalid event: ${err}` }, { status: 400 });
  const e = ev as LogEvent;
  const body = (e.body || {}) as Record<string, string>;
  if (e.type === "edge" && !(hasNode(body.src) && hasNode(body.dst))) return NextResponse.json({ error: "an edge joins two nodes of the set" }, { status: 400 });
  if (e.anchor?.node && !hasNode(e.anchor.node)) return NextResponse.json({ error: "anchor names a node not in the set" }, { status: 400 });
  const r = appendEvent(e);
  if (r.duplicate) return NextResponse.json({ ok: true, duplicate: true, id: e.id });
  return NextResponse.json({ ok: true, id: e.id, stored: e, events: readLog().length }, { status: 201 });
}

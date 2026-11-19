/* The append-only log, shared with the Python side: one JSON object per line in outputs/timeline/log.jsonl,
   the same shape `python -m mueser.timeline` reads (src/mueser/timeline/log.py). Nothing here rewrites it. */
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import type { Edge, LogEvent } from "./model";

const CASE = process.env.TIMELINE_CASE || path.resolve(process.cwd(), "..");
export const LOG_PATH = process.env.TIMELINE_LOG || path.join(CASE, "outputs", "timeline", "log.jsonl");
export const CASE_ID = createHash("sha256").update(path.resolve(LOG_PATH)).digest("hex").slice(0, 24);

const TYPES = new Set(["comment", "issue", "question", "decision", "status", "excerpt", "edge"]);

export function readLog(): LogEvent[] {
  if (!fs.existsSync(LOG_PATH)) return [];
  const out: LogEvent[] = [];
  for (const line of fs.readFileSync(LOG_PATH, "utf8").split("\n")) {
    const s = line.trim();
    if (!s) continue;
    try { out.push(JSON.parse(s) as LogEvent); } catch { /* a bad line is skipped here; the Python reader reports it */ }
  }
  return out;
}

export function logIds(): Set<string> { return new Set(readLog().map(e => e.id)); }

/** Validate the shape the Python model enforces (pydantic, extra fields forbidden). Returns an error or null. */
export function validate(ev: unknown): string | null {
  if (!ev || typeof ev !== "object" || Array.isArray(ev)) return "not an object";
  const e = ev as Record<string, unknown>;
  const allowed = new Set(["id", "ts", "who", "client", "data_id", "type", "anchor", "body", "ref"]);
  for (const k of Object.keys(e)) if (!allowed.has(k)) return `unknown field ${k}`;
  if (typeof e.id !== "string" || !e.id) return "id missing";
  if (typeof e.ts !== "string" || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d/.test(e.ts)) return "ts missing or not ISO";
  if (typeof e.type !== "string" || !TYPES.has(e.type)) return "type not one of the event types";
  for (const k of ["who", "client"]) if (k in e && typeof e[k] !== "string") return `${k} not a string`;
  for (const k of ["data_id", "ref"]) if (e[k] != null && typeof e[k] !== "string") return `${k} not a string`;
  if (e.anchor != null) {
    if (typeof e.anchor !== "object" || Array.isArray(e.anchor)) return "anchor not an object";
    const a = e.anchor as Record<string, unknown>;
    for (const k of Object.keys(a)) if (!["node", "edge", "field", "quote"].includes(k)) return `unknown anchor field ${k}`;
    for (const k of ["node", "edge", "field"]) if (a[k] != null && typeof a[k] !== "string") return `anchor ${k} not a string`;
    if ("quote" in a && typeof a.quote !== "string") return "anchor quote not a string";
  }
  if ("body" in e && (!e.body || typeof e.body !== "object" || Array.isArray(e.body))) return "body not an object";
  const body = (e.body || {}) as Record<string, unknown>;
  const anchor = (e.anchor || {}) as Record<string, unknown>;
  if (e.type === "decision" && !(anchor.edge && ["accept", "reject"].includes(String(body.choice)))) return "a decision names an edge and a choice of accept or reject";
  if (e.type === "edge" && ![body.src, body.dst, body.type].every(v => typeof v === "string" && v.length > 0)) return "an edge event carries string src, dst and type";
  return null;
}

export function appendEvent(ev: LogEvent): { stored: boolean; duplicate: boolean } {
  if (logIds().has(ev.id)) return { stored: false, duplicate: true };
  fs.mkdirSync(path.dirname(LOG_PATH), { recursive: true });
  fs.appendFileSync(LOG_PATH, JSON.stringify(ev) + "\n", "utf8");
  return { stored: true, duplicate: false };
}

/** Latest decision per edge id. */
export function decisions(events: LogEvent[]): Map<string, { choice: string; who: string; ts: string; note: string }> {
  const out = new Map();
  for (const e of events) {
    if (e.type !== "decision" || !e.anchor?.edge) continue;
    out.set(e.anchor.edge, { choice: String(e.body?.choice), who: e.who || "", ts: e.ts, note: String(e.body?.note || "") });
  }
  return out;
}

/** Connections people added in the page, as edges with status `person`. */
export function personEdges(events: LogEvent[], has: (id: string) => boolean): Edge[] {
  const out: Edge[] = [];
  for (const e of events) {
    if (e.type !== "edge") continue;
    const b = (e.body || {}) as Record<string, string>;
    if (!(b.src && b.dst && b.type) || !has(b.src) || !has(b.dst)) continue;
    const id = `${b.type}:${b.src}:${b.dst}`;
    if (out.some(x => x.id === id)) continue;
    out.push({ id, type: b.type, src: b.src, dst: b.dst, source: `person:${e.who || "unnamed"}`, status: "person",
               reason: b.reason || "", evidence: b.evidence || "" });
  }
  return out;
}

/** Current status of every issue and question: open until a status event that references it says otherwise. */
export function issueStatus(events: LogEvent[]): Map<string, string> {
  const st = new Map<string, string>();
  for (const e of events) {
    if (e.type === "issue" || e.type === "question") st.set(e.id, "open");
    else if (e.type === "status" && e.ref) st.set(e.ref, String(e.body?.status || "open"));
  }
  return st;
}

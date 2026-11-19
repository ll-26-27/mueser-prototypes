/* The data behind the site: timeline.json, written by `python -m mueser.timeline db`, read once into memory and
   indexed. Nothing is fetched from the network; the log is read on each request so decisions show at once. */
import fs from "node:fs";
import path from "node:path";
import {
  CLASS_NAME, HEAD, INVERSE, MID, PLACE, type Column, type Edge, type LogEvent, type Node, type NodeType, type Placed,
  type Summary, defaultWindow, firstSentence, fold, relationClass,
} from "./model";
import { CASE_ID, decisions, personEdges, readLog } from "./log";

const CASE = process.env.TIMELINE_CASE || path.resolve(process.cwd(), "..");
export const JSON_PATH = process.env.TIMELINE_JSON || path.join(CASE, "outputs", "timeline", "timeline.json");

interface Data {
  data_id: string; collect_run: string; proposals_run: string | null; accessed: string; model: string | null; built: string;
  edge_types: Record<string, { label: string; kind: string }>;
  nodes: Node[]; edges: Edge[];
}

interface Index {
  D: Data; N: Map<string, Node>; bySrc: Map<string, Edge[]>; byDst: Map<string, Edge[]>; E: Map<string, Edge>;
  classes: Record<string, number>; periods: Node[]; events: Node[]; search: { id: string; label: string; desc: string; sl_n: number }[];
  mtime: number;
}

declare global { var __timelineIndex: Index | undefined }

function load(): Index {
  const stat = fs.statSync(JSON_PATH);
  if (globalThis.__timelineIndex && globalThis.__timelineIndex.mtime === stat.mtimeMs) return globalThis.__timelineIndex;
  const D = JSON.parse(fs.readFileSync(JSON_PATH, "utf8")) as Data;
  const N = new Map(D.nodes.map(n => [n.id, n]));
  const bySrc = new Map<string, Edge[]>(), byDst = new Map<string, Edge[]>(), E = new Map<string, Edge>();
  const classes: Record<string, number> = {};
  const push = (m: Map<string, Edge[]>, k: string, e: Edge) => { const a = m.get(k); if (a) a.push(e); else m.set(k, [e]); };
  for (const e of D.edges) {
    E.set(e.id, e); push(bySrc, e.src, e); push(byDst, e.dst, e);
    const a = N.get(e.src), b = N.get(e.dst);
    if (a && b) { const c = relationClass(a.type, b.type); classes[c] = (classes[c] || 0) + 1; }
  }
  const periods = D.nodes.filter(n => (n.type === "period" || (n.type === "concept" && n.ey != null)) && n.sy != null);
  const events = D.nodes.filter(n => n.type === "event" && n.sy != null);
  const search = D.nodes.map(n => ({ id: n.id, label: fold(n.label), desc: fold(n.desc), sl_n: n.sl_n }));
  const idx: Index = { D, N, bySrc, byDst, E, classes, periods, events, search, mtime: stat.mtimeMs };
  globalThis.__timelineIndex = idx;
  return idx;
}

export function meta() {
  const { D, classes } = load();
  return { case_id: CASE_ID, data_id: D.data_id, collect_run: D.collect_run, proposals_run: D.proposals_run, accessed: D.accessed, model: D.model,
           built: D.built, edge_types: D.edge_types, nodes: D.nodes.length, edges: D.edges.length, classes,
           class_names: CLASS_NAME };
}

export function getNode(id: string): Node | undefined { return load().N.get(id); }
export function hasNode(id: string): boolean { return load().N.has(id); }

export function summary(n: Node): Summary {
  return { id: n.id, type: n.type, label: n.label, desc: n.desc, sy: n.sy, sl: n.sl, ey: n.ey, el: n.el, pt: n.pt, img: n.img,
           sl_n: n.sl_n, blurb: firstSentence(n.text?.t) };
}

export function defaultNode(): string {
  const { N, D } = load();
  if (N.has("Q37621")) return "Q37621";
  const ps = D.nodes.filter(n => n.type === "person").sort((a, b) => b.sl_n - a.sl_n);
  return ps[0]?.id || D.nodes[0].id;
}

export function search(q: string, limit = 40): Summary[] {
  const { search: S, N } = load();
  const f = fold(q.trim());
  const hits = (f ? S.filter(s => s.label.includes(f) || s.desc.includes(f)) : S.slice())
    .sort((a, b) => (Number(b.label.startsWith(f)) - Number(a.label.startsWith(f))) || (b.sl_n - a.sl_n))
    .slice(0, limit);
  return hits.map(h => summary(N.get(h.id)!));
}

/** Every connection of a node, with the log's decisions applied and the person-made edges added. */
export function edgesOf(id: string, events: LogEvent[] = readLog()): Edge[] {
  const { bySrc, byDst, E, N } = load();
  const dec = decisions(events);
  const out: Edge[] = [...(bySrc.get(id) || []), ...(byDst.get(id) || [])].map(e => ({ ...e }));
  for (const pe of personEdges(events, x => N.has(x))) if ((pe.src === id || pe.dst === id) && !E.has(pe.id)) out.push(pe);
  for (const e of out) {
    const d = dec.get(e.id);
    if (d && (d.choice === "accept" || d.choice === "reject")) {
      e.status = d.choice === "accept" ? "accepted" : "rejected"; e.decided_by = d.who; e.decided_at = d.ts; e.decision_note = d.note;
    }
  }
  return out;
}

export function placed(node: Node, edges: Edge[]): Placed[] {
  const { N, D } = load();
  const out: Placed[] = [];
  for (const e of edges) {
    const asSrc = e.src === node.id;
    const other = N.get(asSrc ? e.dst : e.src);
    if (!other) continue;
    const column = (PLACE[e.type] || ["out", "in"])[asSrc ? 0 : 1];
    const rel = asSrc ? (D.edge_types[e.type]?.label || e.type) : (INVERSE[e.type] || e.type);
    out.push({ e, other: summary(other), rel, column, cls: relationClass(N.get(e.src)!.type, N.get(e.dst)!.type) });
  }
  out.sort((a, b) => (a.other.sy ?? 9999) - (b.other.sy ?? 9999));
  return out;
}

export function worksOf(p: Node): Node[] {
  const { bySrc, byDst, N } = load();
  const ws = [...(byDst.get(p.id) || []).filter(e => e.type === "author").map(e => N.get(e.src)),
              ...(bySrc.get(p.id) || []).filter(e => e.type === "notable_work").map(e => N.get(e.dst))].filter((w): w is Node => !!w);
  return ws.filter((w, i, a) => a.indexOf(w) === i).sort((a, b) => (a.sy ?? 9999) - (b.sy ?? 9999));
}
export function authorsOf(w: Node): Node[] {
  const { bySrc, N } = load();
  return (bySrc.get(w.id) || []).filter(e => e.type === "author").map(e => N.get(e.dst)).filter((n): n is Node => !!n);
}

export interface Bar extends Summary { connected: boolean }
export interface BandData {
  window: [number, number]; periods: Bar[]; events: Bar[];
  life: { label0: string; label1: string; sy: number | null; ey: number | null; isPerson: boolean; works: { id: string; label: string; sy: number }[] } | null;
}

/** The bars for a span of years: periods (at most 6) and events (at most 14), those connected to the chosen node first. */
export function band(y0: number, y1: number, sel: string | null, connected: Set<string>): BandData {
  const { periods, events, N } = load();
  const overlaps = (n: Node) => n.sy != null && n.sy <= y1 && (n.ey != null ? n.ey : n.sy) >= y0;
  const rank = (a: Node, b: Node) => (Number(connected.has(b.id)) - Number(connected.has(a.id))) || (b.sl_n - a.sl_n);
  const bar = (n: Node): Bar => ({ ...summary(n), connected: connected.has(n.id) });
  const P = periods.filter(overlaps).sort(rank).slice(0, 6).map(bar);
  let EV = events.filter(n => overlaps(n) && n.id !== sel).sort(rank).slice(0, 14).map(bar);
  const S = sel ? N.get(sel) : undefined;
  if (S && S.type === "event" && S.sy != null) EV = [bar(S), ...EV];
  let life: BandData["life"] = null;
  if (S) {
    let a: Node = S;
    if (S.type === "work") { const au = authorsOf(S)[0]; if (au && au.sy != null) a = au; }
    const isPerson = a.type === "person";
    life = { label0: isPerson ? "Born" : a.pt ? "" : "Began", label1: isPerson ? "Died" : "Ended", sy: a.sy, ey: a.ey, isPerson,
             works: isPerson ? worksOf(a).filter(w => w.sy != null).map(w => ({ id: w.id, label: w.label, sy: w.sy as number })) : [] };
  }
  return { window: [y0, y1], periods: P, events: EV, life };
}

export interface Bundle {
  node: Node; placed: Placed[]; columns: { left: Column; mid: Column; right: Column }; heads: { left: string; mid: string; right: string };
  works: Summary[]; authors: Summary[]; eras: Summary[]; band: BandData; meta: ReturnType<typeof meta>;
}

/** Everything the node page needs, in one object. */
export function bundle(id: string): Bundle | null {
  const { D } = load();
  const node = getNode(id);
  if (!node) return null;
  const events = readLog();
  const edges = edgesOf(id, events);
  const pl = placed(node, edges);
  const connected = new Set(pl.filter(p => p.e.status !== "rejected").map(p => p.other.id));
  const authors = node.type === "work" ? authorsOf(node) : [];
  const win = defaultWindow(node, authors[0] || null);
  // A period is the node's era when it overlaps the node's years and names no country, or one of the node's
  // countries: so a dynasty of another land that merely coincides in time stays out.
  const mine = new Set(node.countries || []);
  const eras = node.sy != null
    ? D.nodes.filter(n => n.type === "period" && n.sy != null && n.sy <= (node.ey ?? node.sy!) && (n.ey ?? n.sy) >= node.sy!
                          && (!n.countries?.length || !mine.size || n.countries.some(c => mine.has(c))))
        .sort((a, b) => b.sl_n - a.sl_n).slice(0, 4).map(summary)
    : [];
  const t = node.type;
  return {
    node, placed: pl,
    columns: { left: "in", mid: MID[t], right: "out" },
    heads: { left: HEAD.in[t] || "Before", mid: HEAD.mid[t] || "Events", right: HEAD.out[t] || "After" },
    works: node.type === "person" ? worksOf(node).map(summary) : [],
    authors: authors.map(summary), eras,
    band: band(win[0], win[1], id, connected),
    meta: meta(),
  };
}

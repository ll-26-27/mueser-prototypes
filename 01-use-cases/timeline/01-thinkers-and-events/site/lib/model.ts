/* Shared, pure definitions: node and edge shapes as timeline.json holds them, and the tables that say where a
   connection appears for the chosen node, how it is named from each side, and how it is coloured. Used on the
   server (grouping) and in the browser (layers, legend). */

export type NodeType = "person" | "work" | "event" | "period" | "concept";

export interface Link { scheme: string; name: string; kind: string; id: string; url: string }
export interface Cite { scheme: string; name: string; plain: string; csl: Record<string, unknown> }
export interface Text { t: string; title: string; url: string; lang: string; rev: number | string; ts: string }
export interface Sep { title: string; authors: string[]; pubinfo: string; url: string }

export interface Node {
  id: string; type: NodeType; label: string; desc: string; rule: string;
  sy: number | null; sl: string; ey: number | null; el: string; pt: boolean;
  place: { birth?: string; death?: string; at?: string[] };
  countries: string[]; occ: string[]; lang: string | null; genres: string[]; inst: string[];
  img: string | null; sl_n: number; links: Link[]; text: Text | null; sep: Sep | null; cite: Cite[];
}

export interface Edge {
  id: string; type: string; src: string; dst: string; source: string; status: string;
  reason?: string; evidence?: string; verified?: boolean; work?: string;
  decided_by?: string; decided_at?: string; decision_note?: string;
}

/** The light form of a node that travels with every connection and band bar. */
export interface Summary {
  id: string; type: NodeType; label: string; desc: string; sy: number | null; sl: string; ey: number | null; el: string;
  pt: boolean; img: string | null; sl_n: number; blurb: string;
}

export type Perspective = "record" | "model" | "person";
export const PERSPECTIVES: Record<Perspective, string> = {
  record: "The record (Wikidata statements)",
  model: "The model’s reading of the Wikipedia extracts",
  person: "Added in this site",
};
export function persp(e: Edge): Perspective {
  return e.source.startsWith("wikidata") ? "record" : e.source.startsWith("model") ? "model" : "person";
}

export const TYPE_NAME: Record<NodeType, string> = { person: "Thinker", work: "Work", event: "Event", period: "Period", concept: "Concept" };
export const ORDER: Record<string, number> = { person: 0, work: 1, event: 2, concept: 3 };
export const bucket = (t: NodeType) => (t === "period" ? "event" : t);

/** The relation class of an edge: what kinds of node it joins, in canonical order. */
export function relationClass(srcType: NodeType, dstType: NodeType): string {
  const a = bucket(srcType), b = bucket(dstType);
  return ORDER[a] <= ORDER[b] ? `${a}–${b}` : `${b}–${a}`;
}
export const CLASS_NAME: Record<string, string> = {
  "person–person": "Thinkers to thinkers", "person–event": "Thinkers to events", "person–work": "Thinkers to works",
  "person–concept": "Thinkers to concepts", "work–work": "Works to works", "work–event": "Works to events",
  "work–concept": "Works to concepts", "event–event": "Events to events", "event–concept": "Events to concepts",
  "concept–concept": "Concepts to concepts",
};
export const EDGE_COLOR: Record<string, string> = {
  "person–person": "#2a5fb0", "person–event": "#b03a2a", "person–work": "#8a5a2a", "person–concept": "#2f7d4f",
  "work–work": "#8a5a2a", "work–event": "#b03a2a", "work–concept": "#2f7d4f", "event–event": "#5e5e5e",
  "event–concept": "#2f7d4f", "concept–concept": "#2f7d4f",
};

export type Column = "in" | "out" | "events" | "people" | "about" | "works" | "schools";
/** Where an edge appears for the chosen node: [when the node is the edge's src, when it is its dst]. */
export const PLACE: Record<string, [Column, Column]> = {
  influenced_by: ["in", "out"], student_of: ["in", "out"], doctoral_advisor: ["in", "out"], teacher_of: ["out", "in"],
  doctoral_student: ["out", "in"], author: ["in", "works"], notable_work: ["works", "in"],
  member_of_movement: ["schools", "people"], field_of_work: ["schools", "people"], main_subject: ["about", "out"],
  part_of: ["in", "out"], follows: ["in", "out"], followed_by: ["out", "in"], has_cause: ["in", "out"], has_effect: ["out", "in"],
  significant_event: ["events", "people"], participant_in: ["events", "people"], participant: ["people", "events"],
  lived_through: ["events", "people"], took_part_in: ["events", "people"], wrote_in_response_to: ["events", "people"],
  suffered_under: ["events", "people"], shaped_by: ["events", "people"],
};
/** How the relation reads from the dst side. */
export const INVERSE: Record<string, string> = {
  influenced_by: "influenced", student_of: "taught", doctoral_advisor: "supervised", teacher_of: "student of",
  doctoral_student: "advised by", author: "work", notable_work: "author", member_of_movement: "member",
  field_of_work: "worked on by", main_subject: "treated in", part_of: "contains", follows: "followed by",
  followed_by: "follows", has_cause: "led to", has_effect: "caused by", significant_event: "significant for",
  participant_in: "participant", participant: "took part in", lived_through: "lived through by",
  took_part_in: "participant", wrote_in_response_to: "answered by", suffered_under: "bore on", shaped_by: "shaped",
};
export const HEAD: Record<"in" | "mid" | "out", Partial<Record<NodeType, string>>> = {
  in: { person: "Influenced by", work: "Author and influences", event: "Context", period: "Context", concept: "Influenced by" },
  mid: { person: "Events", event: "People", period: "People", work: "About", concept: "Thinkers" },
  out: { person: "Influenced", work: "Influenced", event: "Outcome", period: "Outcome", concept: "Works and followers" },
};
export const MID: Record<NodeType, Column> = { person: "events", event: "people", period: "people", work: "about", concept: "people" };

export const fmtYear = (y: number | null | undefined) => (y == null ? "?" : y < 0 ? `${-y} BCE` : String(y));
export const span = (n: { sy: number | null; ey: number | null }) =>
  n.sy == null ? "" : n.ey != null && n.ey !== n.sy ? `${fmtYear(n.sy)}–${fmtYear(n.ey)}` : fmtYear(n.sy);
export const fold = (s: string) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export function firstSentence(t: string | undefined | null): string {
  if (!t) return "";
  const m = t.match(/^.{40,260}?[.!?](\s|$)/);
  return (m ? m[0] : t.slice(0, 220)).trim();
}

/** The default span of years for a node: a life with margins, an event with its own length on each side. */
export function defaultWindow(n: { type: NodeType; sy: number | null; ey: number | null } | null,
                              author?: { sy: number | null; ey: number | null } | null): [number, number] {
  if (!n || n.sy == null) return [1500, 1800];
  if (n.type === "person") return [n.sy - 30, (n.ey != null ? n.ey : n.sy + 80) + 30];
  if (n.type === "work") {
    if (author && author.sy != null) return [author.sy - 30, (author.ey != null ? author.ey : author.sy + 80) + 30];
    return [n.sy - 80, n.sy + 80];
  }
  const e = n.ey != null ? n.ey : n.sy;
  const w = Math.max(e - n.sy, 60);
  return [n.sy - w, e + w];
}

/** One connection as the page shows it: the edge, the other node, and the relation read from the chosen node's side. */
export interface Placed { e: Edge; other: Summary; rel: string; column: Column; cls: string }

export interface LogEvent {
  id: string; ts: string; who?: string; client?: string; data_id?: string | null;
  type: "comment" | "issue" | "question" | "decision" | "status" | "excerpt" | "edge";
  anchor?: { node?: string | null; edge?: string | null; field?: string | null; quote?: string } | null;
  body?: Record<string, unknown>; ref?: string | null;
}

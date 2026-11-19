"use client";
/* The ego graph: the chosen node in the middle, its neighbours on an ellipse grouped by type, every edge coloured
   by what it joins, dashed when proposed, dotted when a reader added it, faded when rejected. */
import { useRouter } from "next/navigation";
import React from "react";
import { CLASS_NAME, EDGE_COLOR, ORDER, type Node, type Placed, type Summary, bucket, persp, span } from "@/lib/model";

const W = 640, H = 320;
const FILL: Record<string, string> = { person: "var(--person)", work: "var(--work)", event: "var(--event)", period: "var(--period)", concept: "var(--concept)" };

export function ConnectionMap({ node, edges }: { node: Node; edges: Placed[] }) {
  const router = useRouter();
  const es = edges.slice(0, 48);
  const others: Summary[] = [];
  const seen = new Set<string>();
  for (const p of es) if (!seen.has(p.other.id)) { seen.add(p.other.id); others.push(p.other); }
  others.sort((a, b) => (ORDER[bucket(a.type)] - ORDER[bucket(b.type)]) || ((a.sy ?? 9999) - (b.sy ?? 9999)));
  const cx = W / 2, cy = H / 2 - 6, rx = W / 2 - 110, ry = H / 2 - 40;
  const pos = new Map<string, [number, number]>([[node.id, [cx, cy]]]);
  // Trig can differ at the last decimal between Node and Chrome; SVG coordinates must hydrate identically.
  const coord = (n: number) => Math.round(n * 1000) / 1000;
  others.forEach((o, i) => { const a = -Math.PI / 2 + (i / Math.max(others.length, 1)) * Math.PI * 2; pos.set(o.id, [coord(cx + rx * Math.cos(a)), coord(cy + ry * Math.sin(a))]); });
  const classes = [...new Set(es.map(p => p.cls))];
  const dot = (n: Summary | Node, r: number) => {
    const [x, y] = pos.get(n.id)!;
    const anchor = x < cx - 10 ? "end" : x > cx + 10 ? "start" : "middle";
    const tx = x + (x < cx - 10 ? -r - 4 : x > cx + 10 ? r + 4 : 0);
    const ty = y + (Math.abs(x - cx) <= 10 ? (y < cy ? -r - 5 : r + 13) : 4);
    return (
      <g className="n" key={n.id} onClick={() => { if (n.id !== node.id) router.push(`/node/${n.id}`); }}>
        <circle cx={x} cy={y} r={r} fill={FILL[n.type] || "#777"} />
        <text x={coord(tx)} y={coord(ty)} textAnchor={anchor}>{n.label.length > 26 ? n.label.slice(0, 25) + "…" : n.label}</text>
        <title>{`${n.label} (${span(n)})`}</title>
      </g>);
  };
  return (
    <div className="tl-map">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Connections of ${node.label}`}>
        {es.map(p => {
          const a = pos.get(p.e.src), b = pos.get(p.e.dst);
          if (!a || !b) return null;
          const k = persp(p.e);
          return (
            <line key={p.e.id} className={"e " + (k === "model" ? "proposed" : k === "person" ? "personal" : "") + (p.e.status === "rejected" ? " rejected" : "")}
              x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={EDGE_COLOR[p.cls] || "#777"}>
              <title>{`${p.e.src === node.id ? node.label : p.other.label} — ${p.e.type.replace(/_/g, " ")} → ${p.e.dst === node.id ? node.label : p.other.label} (${k}, ${p.e.status})`}</title>
            </line>);
        })}
        {others.map(o => dot(o, 5))}
        {dot(node, 8)}
      </svg>
      <div className="cap">Connection map</div>
      <div className="legend">
        {classes.map(c => <span className="l" key={c}><i style={{ borderColor: EDGE_COLOR[c] || "#777" }} />{CLASS_NAME[c] || c}</span>)}
        {es.some(p => persp(p.e) === "model") && <span className="l"><i style={{ borderColor: "#777", borderTopStyle: "dashed" }} />proposed</span>}
      </div>
    </div>
  );
}

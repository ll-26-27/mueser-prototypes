"use client";
/* The grey bar: brand and counts, the search box, Layers and Legend, who is reading, the connection badge,
   export of unsent events, and the link to the log. */
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useRef, useState } from "react";
import { CLASS_NAME, EDGE_COLOR, PERSPECTIVES, TYPE_NAME, type NodeType, type Perspective, type Summary, span } from "@/lib/model";
import { Popover } from "./Popover";
import { useStore } from "./Store";

function Search() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Summary[]>([]);
  const [open, setOpen] = useState(false);
  const [idx, setIdx] = useState(-1);
  const t = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!open) return;
    if (t.current) clearTimeout(t.current);
    t.current = setTimeout(async () => {
      try { const r = await fetch(`/api/search?q=${encodeURIComponent(q)}`); setItems(await r.json()); setIdx(-1); } catch { setItems([]); }
    }, 120);
  }, [q, open]);
  const go = (n: Summary) => { setOpen(false); setQ(""); router.push(`/node/${n.id}`); };
  return (
    <div className="tl-pick">
      <input type="text" value={q} placeholder="Search a thinker, work, event, concept…" aria-label="Choose a node"
        onChange={e => setQ(e.target.value)} onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={e => {
          if (!open) return;
          if (e.key === "ArrowDown") { e.preventDefault(); setIdx(i => Math.min(items.length - 1, i + 1)); }
          else if (e.key === "ArrowUp") { e.preventDefault(); setIdx(i => Math.max(0, i - 1)); }
          else if (e.key === "Enter") { e.preventDefault(); const n = items[idx >= 0 ? idx : 0]; if (n) go(n); }
          else if (e.key === "Escape") setOpen(false);
        }} />
      <span className="caret">▾</span>
      {open && (
        <div className="tl-pick-list">
          {items.length === 0 && <div className="muted" style={{ padding: 8 }}>Nothing matches</div>}
          {items.map((n, i) => (
            <a key={n.id} href={`/node/${n.id}`} aria-selected={i === idx} onMouseDown={e => { e.preventDefault(); go(n); }}>
              <span className="t">{TYPE_NAME[n.type]}</span><span>{n.label}</span><span className="y">{span(n)}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export function TopBar() {
  const s = useStore();
  const [pop, setPop] = useState<"layers" | "legend" | null>(null);
  const layersBtn = useRef<HTMLButtonElement>(null), legendBtn = useRef<HTMLButtonElement>(null);
  const classes = Object.keys(s.meta.class_names).sort((a, b) => (s.meta.classes[b] || 0) - (s.meta.classes[a] || 0));
  return (
    <div className="tl-top">
      <div className="tl-bar">
        <Link className="brand" href="/">Thinkers and events<small>{s.meta.nodes.toLocaleString()} nodes · {s.meta.edges.toLocaleString()} connections</small></Link>
        <div className="spacer" />
        <Search />
        <div className="spacer" />
        <button className="tool" ref={layersBtn} aria-expanded={pop === "layers"} onClick={() => setPop(pop === "layers" ? null : "layers")}>Layers</button>
        <button className="tool" ref={legendBtn} aria-expanded={pop === "legend"} onClick={() => setPop(pop === "legend" ? null : "legend")}>Legend</button>
        <label className="tl-who">Reading as <input value={s.who} placeholder="your name" onChange={e => s.setWho(e.target.value)} /></label>
        <span className={"tl-conn" + (s.online ? "" : " off")}>
          {s.online ? `${s.serverEvents} saved · ${s.pending} unsent` : `offline · ${s.pending} unsent`}
        </span>
        {s.pending > 0 && <button className="tool" onClick={s.exportLocal}>Export unsent</button>}
        <Link className="tool" href="/log">Log</Link>
      </div>
      {!s.online && <p className="tl-notice">Not connected to the site’s server: what you do here stays in this browser until it reconnects, or until you export it and drop the file into <code>outputs/timeline/inbox/</code>.</p>}
      {pop === "layers" && (
        <Popover anchor={layersBtn.current} title="Layers" onClose={() => setPop(null)}>
          <p className="sub">Which connections the columns, the band and the map show.</p>
          <div className="group eyebrow">By what they connect</div>
          {classes.map(c => (
            <label className="check" key={c}><input type="checkbox" checked={s.layers.has(c)} onChange={() => s.toggleLayer(c)} />
              {CLASS_NAME[c] || c} <span className="muted">({(s.meta.classes[c] || 0).toLocaleString()} in dataset)</span></label>
          ))}
          <div className="group eyebrow">By whose connections</div>
          {(Object.keys(PERSPECTIVES) as Perspective[]).map(p => (
            <label className="check" key={p}><input type="checkbox" checked={s.persp.has(p)} onChange={() => s.togglePersp(p)} />{PERSPECTIVES[p]}</label>
          ))}
          <label className="check"><input type="checkbox" checked={s.showRejected} onChange={e => s.setShowRejected(e.target.checked)} />Show rejected proposals</label>
          <p className="sub">A further perspective, the connections one commentator draws across these nodes, would appear here as its own line once ingested; see the README.</p>
          <div className="actions"><button className="ghost" onClick={s.allOn}>All</button><button className="primary" onClick={() => setPop(null)}>Close</button></div>
        </Popover>
      )}
      {pop === "legend" && (
        <Popover anchor={legendBtn.current} title="Legend" onClose={() => setPop(null)}>
          <div className="group eyebrow">Nodes</div>
          {(Object.keys(TYPE_NAME) as NodeType[]).map(t => <div className="legend-row" key={t}><span className={`dot ${t}`} />{TYPE_NAME[t]}s</div>)}
          <div className="group eyebrow">Connections</div>
          {Object.keys(CLASS_NAME).filter(c => s.meta.classes[c]).map(c => <div className="legend-row" key={c}><i style={{ borderColor: EDGE_COLOR[c] }} />{CLASS_NAME[c]}</div>)}
          <div className="group eyebrow">Standing</div>
          <div className="legend-row"><i style={{ borderColor: "#555" }} />recorded: a Wikidata statement, with its property</div>
          <div className="legend-row"><i className="dash" style={{ borderColor: "#555" }} />proposed: the model read it in the Wikipedia extract; accept or reject</div>
          <div className="legend-row"><i className="dots" style={{ borderColor: "#555" }} />added here: a reader drew it, with a reason</div>
          <div className="group eyebrow">Band</div>
          <p className="sub">Periods in the upper lanes, events below them; bars connected to the chosen node are darker, the chosen event is pale blue. Drag to move through time, scroll to zoom, Fit to return. Beneath the axis: the chosen thinker’s life with their works as ticks.</p>
          <div className="actions"><button className="primary" onClick={() => setPop(null)}>Close</button></div>
        </Popover>
      )}
    </div>
  );
}

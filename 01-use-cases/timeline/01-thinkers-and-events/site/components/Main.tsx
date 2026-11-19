"use client";
/* The middle column: image, name, dates, descriptor; the overview with its attribution; notable works; school of
   thought and era; the references with Cite; the connection map; Note and Add a connection. */
import Link from "next/link";
import React, { useRef, useState } from "react";
import type { Bundle } from "@/lib/data";
import { TYPE_NAME, type Cite, type Node, type Placed, type Summary, span } from "@/lib/model";
import { ConnectionMap } from "./ConnectionMap";
import { NoteButton } from "./Columns";
import { Popover } from "./Popover";
import { useStore } from "./Store";

function CiteButton({ node, scheme, label = "Cite" }: { node: Node; scheme?: string; label?: string }) {
  const s = useStore();
  const btn = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const cs = node.cite || [];
  const [cur, setCur] = useState<Cite | undefined>(() => cs.find(c => c.scheme === scheme) || cs[0]);
  if (!cur) return null;
  const copy = async (text: string, form: string) => {
    try { await navigator.clipboard.writeText(text); s.toast("Copied"); } catch { s.toast("Copy failed; select the text"); }
    await s.add(s.make("excerpt", { node: node.id, quote: node.label }, { scheme: cur.scheme, form, text: text.slice(0, 2000) }));
  };
  return (
    <>
      <button className="ghost" ref={btn} onClick={() => setOpen(true)}>{label}</button>
      {open && (
        <Popover anchor={btn.current} title="Cite" onClose={() => setOpen(false)}>
          <label>Source</label>
          <select value={cur.scheme} onChange={e => setCur(cs.find(c => c.scheme === e.target.value))}>{cs.map(c => <option key={c.scheme} value={c.scheme}>{c.name}</option>)}</select>
          <label>Citation</label><pre>{cur.plain}</pre>
          <label>CSL-JSON (paste into Zotero: File → Import from Clipboard)</label><pre>{JSON.stringify(cur.csl, null, 1)}</pre>
          <div className="actions">
            <button className="ghost" onClick={() => copy(cur.plain, "plain")}>Copy citation</button>
            <button className="ghost" onClick={() => copy(JSON.stringify(cur.csl), "csl")}>Copy CSL-JSON</button>
            <button className="ghost" onClick={() => copy(`> ${node.label}${node.sy != null ? " (" + span(node) + ")" : ""}[^1]\n\n[^1]: ${cur.plain}`, "markdown")}>Copy as Markdown</button>
            <button className="primary" onClick={() => setOpen(false)}>Close</button>
          </div>
        </Popover>
      )}
    </>
  );
}

function AddConnection({ node, onAdded }: { node: Node; onAdded: () => void }) {
  const s = useStore();
  const btn = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState(""); const [hits, setHits] = useState<Summary[]>([]); const [target, setTarget] = useState<Summary | null>(null);
  const [type, setType] = useState("lived_through"); const [why, setWhy] = useState(""); const [evd, setEvd] = useState("");
  const t = useRef<ReturnType<typeof setTimeout> | null>(null);
  const look = (v: string) => { setQ(v); if (t.current) clearTimeout(t.current); t.current = setTimeout(async () => { if (!v.trim()) { setHits([]); return; } const r = await fetch(`/api/search?q=${encodeURIComponent(v)}`); setHits(((await r.json()) as Summary[]).filter(n => n.id !== node.id).slice(0, 12)); }, 120); };
  const types = Object.entries(s.meta.edge_types);
  return (
    <>
      <button className="ghost" ref={btn} onClick={() => setOpen(true)}>+ Add a connection</button>
      {open && (
        <Popover anchor={btn.current} title="Add a connection" onClose={() => setOpen(false)}>
          <p className="sub">From {node.label} to another node. It is recorded as yours (“added here”), beside the record and the model’s proposals.</p>
          <label>To</label><input type="text" value={q} placeholder="search…" onChange={e => look(e.target.value)} autoFocus />
          {hits.length > 0 && <div className="pick-results">{hits.map(n => <button key={n.id} onClick={() => { setTarget(n); setHits([]); setQ(n.label); }}>{n.label} · {TYPE_NAME[n.type].toLowerCase()}{n.sy != null ? ", " + span(n) : ""}</button>)}</div>}
          {target && <p className="sub">→ {target.label}</p>}
          <label>Type</label>
          <select value={type} onChange={e => setType(e.target.value)}>{types.map(([k, v]) => <option key={k} value={k}>{v.label}{v.kind === "proposed" ? "" : " (as the record uses it)"}</option>)}</select>
          <label>Why (one sentence)</label><textarea value={why} onChange={e => setWhy(e.target.value)} />
          <label>Evidence: a quotation or a reference, with page</label><input type="text" value={evd} onChange={e => setEvd(e.target.value)} />
          <div className="actions">
            <button className="ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="primary" onClick={async () => { if (!target) return; await s.add(s.make("edge", { node: node.id, quote: `${node.label} → ${target.label}` }, { src: node.id, dst: target.id, type, reason: why.trim(), evidence: evd.trim() })); s.toast("Connection added"); setOpen(false); onAdded(); }}>Add</button>
          </div>
        </Popover>
      )}
    </>
  );
}

const KIND_GROUP: Record<string, string> = { entry: "Reference works", article: "Encyclopedias", text: "Texts", record: "Library and authority records", other: "Data" };
const kindOf = (l: { kind: string }) => /^(entry|overview|bibliography)/.test(l.kind) ? "entry" : l.kind === "article" ? "article" : /^(text|ebook|scan|editions|author)/.test(l.kind) ? "text" : /record/.test(l.kind) ? "record" : "other";

export function Main({ b, groups, mapEdges, onAdded }: { b: Bundle; groups: Record<string, Placed[]>; mapEdges: Placed[]; onAdded: () => void }) {
  const S = b.node;
  const where: string[] = [];
  if (S.desc) where.push(S.desc);
  if (S.place?.birth) where.push(S.place.birth + (S.place.death && S.place.death !== S.place.birth ? " – " + S.place.death : ""));
  if (S.place?.at) where.push(S.place.at.join(", "));
  if (S.lang) where.push(S.lang);
  const schools = (groups.schools || []).map(p => p.other);
  const worksAbout = S.type === "concept" ? (groups.out || []).filter(p => p.e.type === "main_subject").map(p => p.other) : [];
  const refs = ["entry", "article", "text", "record", "other"].map(k => [k, (S.links || []).filter(l => kindOf(l) === k)] as const).filter(([, ls]) => ls.length);
  return (
    <div className="tl-col tl-main">
      <div className="tl-hero">
        {S.img ? <img className="portrait" src={S.img} alt={`Image of ${S.label} from Wikimedia Commons`} /> : <div className="portrait none">{TYPE_NAME[S.type]}</div>}
        <div>
          <h1>{S.label}</h1>
          <p className="dates">{S.sy != null ? span(S) : "undated"}</p>
          <p className="where">{where.join(" · ")}</p>
          <div className="secondary">
            {S.type === "work" && b.authors.length > 0 && <><h3>Author</h3><p>{b.authors.map((a, i) => <React.Fragment key={a.id}>{i > 0 && ", "}<Link href={`/node/${a.id}`}>{a.label}</Link></React.Fragment>)}</p></>}
            {S.occ?.length > 0 && <><h3>Occupations, as recorded</h3><p>{S.occ.join(", ")}</p></>}
            {S.countries?.length > 0 && <><h3>{S.type === "person" ? "Citizenship, as recorded" : "Country"}</h3><p>{S.countries.join(", ")}</p></>}
            {S.inst?.length > 0 && S.type !== "person" && <><h3>Kind</h3><p>{S.inst.join(", ")}</p></>}
          </div>
        </div>
      </div>
      <hr className="tl-rule" />
      <div className="tl-grid">
        <div>
          <section className="overview">
            <h3>Overview</h3>
            {S.text ? (
              <>
                {S.text.t.split(/\n+/).map((p, i) => <p key={i}>{p}</p>)}
                <p className="attrib">From <a href={S.text.url} target="_blank" rel="noopener">“{S.text.title}”, Wikipedia ({S.text.lang})</a>, revision {S.text.rev} of {(S.text.ts || "").slice(0, 10)}, CC BY-SA 4.0. The lead section of the article, as fetched; not a claim of this site.</p>
              </>
            ) : <p className="muted">No Wikipedia summary was fetched for this node.</p>}
            <div className="row">
              <CiteButton node={S} label="Cite this node" />
              <NoteButton anchor={{ node: S.id, quote: S.label }} />
              <AddConnection node={S} onAdded={onAdded} />
            </div>
          </section>
          <section><ConnectionMap node={S} edges={mapEdges} /></section>
        </div>
        <div>
          {(S.type === "person" || S.type === "concept") && (
            <section>
              <h3>{S.type === "person" ? "Notable works" : "Works about it"}</h3>
              {(S.type === "person" ? b.works : worksAbout).length ? (
                <ul className="plain">{(S.type === "person" ? b.works : worksAbout).map(w => <li key={w.id}><Link href={`/node/${w.id}`}>{w.label}</Link>{w.sy != null && <span className="y">({w.sy < 0 ? `${-w.sy} BCE` : w.sy})</span>}</li>)}</ul>
              ) : <p className="muted">None recorded.</p>}
            </section>
          )}
          {(schools.length > 0 || b.eras.length > 0) && (
            <section className="inline-tags"><h3>School of thought / era</h3>
              <p>{[...schools, ...b.eras].map((n, i) => <React.Fragment key={n.id}>{i > 0 && ", "}<Link href={`/node/${n.id}`}>{n.label}</Link></React.Fragment>)}</p></section>
          )}
          {S.type === "work" && (groups.about || []).length > 0 && (
            <section className="inline-tags"><h3>About</h3><p>{groups.about.map((p, i) => <React.Fragment key={p.other.id}>{i > 0 && ", "}<Link href={`/node/${p.other.id}`}>{p.other.label}</Link></React.Fragment>)}</p></section>
          )}
          <section className="refs">
            <h3>Where to read about it</h3>
            <ul className="plain">
              {refs.map(([k, ls]) => (
                <React.Fragment key={k}>
                  <li><span className="eyebrow">{KIND_GROUP[k]}</span></li>
                  {ls.map(l => (
                    <li key={l.scheme + l.id}>
                      <a href={l.url} target="_blank" rel="noopener">{l.name}</a>
                      <span className="what">{l.kind}{l.scheme.startsWith("P") || l.scheme === "wikidata" ? ` · ${l.id}` : ""}</span>
                      {(S.cite || []).some(c => c.scheme === l.scheme) && <CiteButton node={S} scheme={l.scheme} />}
                    </li>))}
                </React.Fragment>))}
            </ul>
            {S.sep && <p className="attrib">Stanford Encyclopedia entry “{S.sep.title}” by {S.sep.authors.join("; ")}: {S.sep.pubinfo}.</p>}
            <p className="attrib">Node {S.id}, admitted by rule “{S.rule}”; {S.sl_n} Wikipedia articles. Dates and identifiers as Wikidata holds them, fetched {b.meta.accessed}.</p>
          </section>
        </div>
      </div>
    </div>
  );
}

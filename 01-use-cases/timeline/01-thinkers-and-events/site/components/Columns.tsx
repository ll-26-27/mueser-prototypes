"use client";
/* One column of cards: the connections placed there for the chosen node, each with its standing, the model's
   reason and evidence where it is a proposal, Accept/Reject, and a Note button. */
import Link from "next/link";
import React, { useRef, useState } from "react";
import { TYPE_NAME, type Placed, type Summary, persp, span } from "@/lib/model";
import { Popover } from "./Popover";
import { useStore } from "./Store";

export function Badge({ p }: { p: Placed }) {
  const e = p.e, k = persp(e), st = e.status;
  const text = k === "record" ? "record" : k === "person" ? (st === "accepted" ? "added · accepted" : st === "rejected" ? "added · rejected" : "added here") : st;
  const title = k === "record" ? `Wikidata statement (${e.source.replace("wikidata:", "")})` : k === "model" ? `Proposed by ${e.source.replace("model:", "")} from the Wikipedia extract` : e.source;
  return <span className={"badge " + (k === "person" ? "person" : st)} title={title}>{text}</span>;
}

export function NoteButton({ anchor, label = "Note" }: { anchor: { node?: string; edge?: string; quote?: string }; label?: string }) {
  const s = useStore();
  const btn = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<"issue" | "question" | "comment">("issue");
  const [text, setText] = useState("");
  return (
    <>
      <button className="ghost" ref={btn} title="Leave an issue, a question or a comment" onClick={() => setOpen(true)}>{label}</button>
      {open && (
        <Popover anchor={btn.current} title="Leave a note" onClose={() => setOpen(false)}>
          <label>Kind</label>
          <select value={kind} onChange={e => setKind(e.target.value as typeof kind)}><option value="issue">issue</option><option value="question">question</option><option value="comment">comment</option></select>
          <label>On</label><p className="sub">{anchor.quote || anchor.node}</p>
          <label>Text</label><textarea value={text} onChange={e => setText(e.target.value)} autoFocus />
          <div className="actions">
            <button className="ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="primary" onClick={async () => { if (!text.trim()) return; await s.add(s.make(kind, anchor, { text: text.trim() })); s.toast("Saved to the log"); setOpen(false); setText(""); }}>Save</button>
          </div>
        </Popover>
      )}
    </>
  );
}

export function Card({ p, selId, big, onDecide }: { p: Placed; selId: string; big: boolean; onDecide: (p: Placed, choice: "accept" | "reject") => void }) {
  const n: Summary = p.other, e = p.e, k = persp(e), st = e.status;
  return (
    <div className={"card" + (n.id === selId ? " hi" : "")}>
      {n.img && <img className={"thumb" + (big ? "" : " small")} loading="lazy" src={n.img} alt="" />}
      <Link className="name" href={`/node/${n.id}`}>{n.label}</Link>
      <div className="kind"><span className="rel">{p.rel}</span>, {TYPE_NAME[n.type].toLowerCase()}{n.sy != null ? `, ${span(n)}` : ""}</div>
      {big && n.blurb && <p className="blurb">{n.blurb}</p>}
      {e.reason && <p className="reason">{e.reason}</p>}
      {e.evidence && <p className={"evidence" + (e.verified === false ? " unverified" : "")}>“{e.evidence}”{e.verified === false ? " (not found verbatim in the extract)" : ""}</p>}
      <div className="row">
        <Badge p={p} />
        {(k === "model" || k === "person") && st !== "accepted" && <button className="ghost" onClick={() => onDecide(p, "accept")}>Accept</button>}
        {(k === "model" || k === "person") && st !== "rejected" && <button className="ghost" onClick={() => onDecide(p, "reject")}>Reject</button>}
        <NoteButton anchor={{ node: selId, edge: e.id, quote: `${p.rel}: ${n.label}` }} />
        <Link className="more" href={`/node/${n.id}`}>Read more →</Link>
      </div>
    </div>
  );
}

export function Column({ title, items, selId, onDecide }: { title: string; items: Placed[]; selId: string; onDecide: (p: Placed, choice: "accept" | "reject") => void }) {
  return (
    <div className="tl-col">
      <div className="tl-col-head"><span className="arrow">▶</span>{title}<span className="n">{items.length}</span></div>
      {items.length === 0 && <p className="muted">Nothing in the chosen layers.</p>}
      {items.map((p, i) => <Card key={p.e.id} p={p} selId={selId} big={i < 4} onDecide={onDecide} />)}
    </div>
  );
}

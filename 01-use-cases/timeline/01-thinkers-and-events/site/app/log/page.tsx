import Link from "next/link";
import { getNode } from "@/lib/data";
import { issueStatus, readLog } from "@/lib/log";

export const dynamic = "force-dynamic";

export default function LogPage() {
  const events = readLog().filter(e => e.type !== "status").reverse();
  const st = issueStatus(readLog());
  return (
    <main className="tl-logpage">
      <h1>Log</h1>
      <p className="muted">Every decision, added connection, note and excerpt, newest first; the file is <code>outputs/timeline/log.jsonl</code>.</p>
      {events.length === 0 && <p className="muted">Nothing yet.</p>}
      {events.map(e => {
        const b = (e.body || {}) as Record<string, string>;
        const nid = e.anchor?.node || b.src;
        const n = nid ? getNode(nid) : undefined;
        const text = e.type === "decision" ? `${b.choice} · ${e.anchor?.quote || b.target}`
          : e.type === "edge" ? `${getNode(b.src)?.label} — ${b.type} → ${getNode(b.dst)?.label}${b.reason ? ": " + b.reason : ""}`
          : e.type === "excerpt" ? `${b.scheme || ""} citation copied` : b.text || b.note || "";
        return (
          <div className="item" key={e.id}>
            <div className="head"><span className={`type ${e.type}`}>{e.type}</span><span>{e.who || "unnamed"}</span><span>{e.ts.slice(0, 16).replace("T", " ")}</span>
              {st.has(e.id) && <span className={`st ${st.get(e.id)}`}>{st.get(e.id)}</span>}</div>
            <div className="body">{text}</div>
            {e.anchor?.quote && e.type !== "decision" && <div className="muted">“{e.anchor.quote.slice(0, 160)}”</div>}
            {n && <Link className="jump" href={`/node/${n.id}`}>Go to {n.label}</Link>}
          </div>
        );
      })}
    </main>
  );
}

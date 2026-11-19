"use client";
/* The node page: the band above, three columns below. Holds the connections with their current standing;
   a decision updates the card at once and goes to the log through the store. Layers and perspectives from the
   store filter what the columns, the band and the map show. */
import { useRouter } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";
import type { Bundle } from "@/lib/data";
import { type Placed, persp } from "@/lib/model";
import { Band } from "./Band";
import { Column } from "./Columns";
import { Main } from "./Main";
import { useStore } from "./Store";

export function NodeView({ bundle }: { bundle: Bundle }) {
  const s = useStore();
  const router = useRouter();
  const [placed, setPlaced] = useState<Placed[]>(bundle.placed);
  useEffect(() => { setPlaced(bundle.placed); }, [bundle]);

  const active = useMemo(() => placed.filter(p => s.layers.has(p.cls) && s.persp.has(persp(p.e)) && (s.showRejected || p.e.status !== "rejected")),
    [placed, s.layers, s.persp, s.showRejected]);
  const groups = useMemo(() => {
    const g: Record<string, Placed[]> = { in: [], out: [], events: [], people: [], about: [], works: [], schools: [] };
    for (const p of active) (g[p.column] ||= []).push(p);
    return g;
  }, [active]);

  const decide = async (p: Placed, choice: "accept" | "reject") => {
    const ev = s.make("decision", { node: bundle.node.id, edge: p.e.id, quote: `${p.rel}: ${p.other.label}` },
      { choice, target: `edge:${p.e.id}`, type: p.e.type, src: p.e.src, dst: p.e.dst });
    setPlaced(ps => ps.map(x => x.e.id === p.e.id ? { ...x, e: { ...x.e, status: choice === "accept" ? "accepted" : "rejected", decided_by: s.who, decided_at: ev.ts } } : x));
    const ok = await s.add(ev);
    s.toast(ok ? (choice === "accept" ? "Accepted" : "Rejected") : "Kept here; not yet saved");
  };
  const S = bundle.node;
  return (
    <div className="tl-main-wrap">
      <Band initial={bundle.band} sel={S.id} />
      <div className="tl-body">
        <Column title={bundle.heads.left} items={groups[bundle.columns.left] || []} selId={S.id} onDecide={decide} />
        <Main b={bundle} groups={groups} mapEdges={active} onAdded={() => router.refresh()} />
        <Column title={bundle.heads.mid} items={groups[bundle.columns.mid] || []} selId={S.id} onDecide={decide} />
        <Column title={bundle.heads.right} items={groups[bundle.columns.right] || []} selId={S.id} onDecide={decide} />
      </div>
    </div>
  );
}

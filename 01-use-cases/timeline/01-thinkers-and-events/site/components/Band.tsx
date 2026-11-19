"use client";
/* The band: periods and events of the span in view, packed into lanes over a year axis, and the chosen node's
   own span beneath it. Drag to pan, wheel to zoom; each change asks /api/band for the bars of the new span. */
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useRef, useState } from "react";
import type { Bar, BandData } from "@/lib/data";
import { TYPE_NAME, fmtYear, span } from "@/lib/model";

const LANE = 34, TOP = 18, PAD_L = 24, PAD_R = 24;

function niceStep(w: number) { const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]; return steps.find(s => w / s <= 10) || 1000; }

function pack(items: Bar[], x: (y: number) => number) {
  const lanes: { end: number; items: Bar[] }[] = [];
  for (const n of [...items].sort((a, b) => (a.sy as number) - (b.sy as number))) {
    const s = x(n.sy as number), e = Math.max(x(n.ey != null ? n.ey : (n.sy as number)), s + 8);
    let i = lanes.findIndex(l => l.end + 6 < s);
    if (i < 0) { lanes.push({ end: e, items: [] }); i = lanes.length - 1; }
    lanes[i].end = Math.max(lanes[i].end, e); lanes[i].items.push(n);
  }
  return lanes;
}

export function Band({ initial, sel }: { initial: BandData; sel: string }) {
  const router = useRouter();
  const [data, setData] = useState<BandData>(initial);
  const [win, setWin] = useState<[number, number]>(initial.window);
  const [width, setWidth] = useState(1200);
  const box = useRef<HTMLDivElement>(null);
  const drag = useRef<{ x: number; win: [number, number]; moved: boolean } | null>(null);
  const fetchT = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => { setData(initial); setWin(initial.window); }, [initial]);
  useEffect(() => {
    const ro = new ResizeObserver(() => { if (box.current) setWidth(Math.max(600, box.current.clientWidth)); });
    if (box.current) { ro.observe(box.current); setWidth(Math.max(600, box.current.clientWidth)); }
    return () => ro.disconnect();
  }, []);

  const refetch = useCallback((w: [number, number]) => {
    if (fetchT.current) clearTimeout(fetchT.current);
    fetchT.current = setTimeout(async () => {
      try { const r = await fetch(`/api/band?y0=${w[0]}&y1=${w[1]}&sel=${encodeURIComponent(sel)}`); if (r.ok) setData(await r.json()); } catch { /* keep what we have */ }
    }, 180);
  }, [sel]);
  const setWindow = (w: [number, number]) => { setWin(w); refetch(w); };

  const [y0, y1] = win;
  const W = width;
  const x = (y: number) => PAD_L + (y - y0) / (y1 - y0) * (W - PAD_L - PAD_R);
  const pl = pack(data.periods, x), evl = pack(data.events, x);
  let y = TOP;
  const H = TOP + (pl.length + evl.length) * LANE + 56 + 96;
  const step = niceStep(y1 - y0);
  const ticks: number[] = [];
  for (let t = Math.ceil(y0 / step) * step; t <= y1; t += step) ticks.push(t);

  const lanesSvg: React.ReactNode[] = [];
  const draw = (lanes: { items: Bar[] }[]) => lanes.forEach(l => {
    for (const n of l.items) {
      const s = Math.max(PAD_L - 400, x(n.sy as number)), e = Math.min(W - PAD_R + 400, Math.max(x(n.ey != null ? n.ey : (n.sy as number)), s + 8));
      const vis = Math.min(e, W - PAD_R) - Math.max(s, PAD_L);
      const cls = "bar" + (n.id === sel ? " hi" : n.connected ? " connected" : "");
      const label = vis > 140 ? n.label : n.label.slice(0, Math.max(3, Math.floor(vis / 9))) + (n.label.length > vis / 9 ? "…" : "");
      const yy = y;
      lanesSvg.push(
        <g className="bar-g" key={n.id} tabIndex={0} onClick={() => router.push(`/node/${n.id}`)} onKeyDown={ev => { if (ev.key === "Enter") router.push(`/node/${n.id}`); }}>
          <rect className={cls} x={s} y={yy} width={e - s} height={LANE - 8} rx={1} />
          {vis > 60 && <text x={Math.max(s, PAD_L) + 10} y={yy + LANE / 2 + 1}>{label}</text>}
          {vis > 230 + n.label.length * 7 && <text className="yrs" x={Math.min(e, W - PAD_R) - 10} y={yy + LANE / 2 + 1} textAnchor="end">{span(n)}</text>}
          <title>{`${n.label} (${span(n)}) · ${TYPE_NAME[n.type]}`}</title>
        </g>);
    }
    y += LANE;
  });
  draw(pl); draw(evl);
  y += 14;
  const axisY = y; y += 40;
  const life = data.life;

  const zoom = (f: number) => { const c = (y0 + y1) / 2, w = (y1 - y0) * f / 2; setWindow([Math.round(c - w), Math.round(c + w)]); };

  return (
    <div className="tl-band" ref={box}
      onPointerDown={e => { if ((e.target as HTMLElement).closest(".window-ctl")) return; drag.current = { x: e.clientX, win: [y0, y1], moved: false }; (e.currentTarget as HTMLElement).classList.add("dragging"); e.currentTarget.setPointerCapture(e.pointerId); }}
      onPointerMove={e => { const d = drag.current; if (!d) return; const dx = e.clientX - d.x; if (Math.abs(dx) > 3) d.moved = true; const yrs = dx / (W - PAD_L - PAD_R) * (d.win[1] - d.win[0]); setWindow([Math.round(d.win[0] - yrs), Math.round(d.win[1] - yrs)]); }}
      onPointerUp={e => { drag.current = null; (e.currentTarget as HTMLElement).classList.remove("dragging"); }}
      onPointerCancel={e => { drag.current = null; (e.currentTarget as HTMLElement).classList.remove("dragging"); }}
      onWheel={e => { if (!e.deltaY) return; e.preventDefault(); const rect = e.currentTarget.getBoundingClientRect(); const px = (e.clientX - rect.left) / rect.width; const w = y1 - y0, f = e.deltaY > 0 ? 1.15 : 1 / 1.15; const nw = Math.max(20, Math.min(3000, w * f)); const c = y0 + px * w; setWindow([Math.round(c - px * nw), Math.round(c + (1 - px) * nw)]); }}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-label="Timeline band">
        {lanesSvg}
        <g className="axis">
          {ticks.map(t => <g key={t}><line x1={x(t)} x2={x(t)} y1={axisY + 18} y2={axisY + 30} /><text x={x(t)} y={axisY + 12} textAnchor="middle">{fmtYear(t)}</text></g>)}
          <line x1={PAD_L} x2={W - PAD_R} y1={axisY + 30} y2={axisY + 30} />
        </g>
        {life && life.sy != null && (() => {
          const s = x(life.sy), e = life.ey != null ? x(life.ey) : (life.isPerson ? x(life.sy + 80) : s);
          return (
            <g className="life">
              {!life.isPerson && life.ey != null && life.ey !== life.sy && <rect x={s} y={y + 2} width={e - s} height={18} />}
              <line x1={s} x2={e} y1={y + 11} y2={y + 11} strokeDasharray={life.ey == null && life.isPerson ? "3 3" : undefined} />
              <circle cx={s} cy={y + 11} r={6} /><text x={s} y={y + 36} textAnchor="middle">{life.label0 ? `${life.label0} (${fmtYear(life.sy)})` : `(${fmtYear(life.sy)})`}</text>
              {life.ey != null && <><circle cx={e} cy={y + 11} r={6} /><text x={e} y={y + 36} textAnchor="middle">{`${life.label1} (${fmtYear(life.ey)})`}</text></>}
              {life.works.map((w, i, arr) => (
                <g className="work-tick" key={w.id} onClick={() => router.push(`/node/${w.id}`)}>
                  <line x1={x(w.sy)} x2={x(w.sy)} y1={y + 46} y2={y + 60 + (w.id === sel ? 6 : 0)} />
                  {(i === 0 || x(w.sy) - x(arr[i - 1].sy) > 70) && (i === arr.length - 1 || x(arr[i + 1].sy) - x(w.sy) > 70 || i === 0) && <text x={x(w.sy)} y={y + 74} textAnchor="middle">{w.label.length > 22 ? w.label.slice(0, 21) + "…" : w.label}</text>}
                  <title>{`${w.label} (${fmtYear(w.sy)})`}</title>
                </g>))}
            </g>);
        })()}
      </svg>
      {data.periods.length === 0 && data.events.length === 0 && <div className="empty">No periods or events in this span of years</div>}
      <div className="window-ctl">
        <button title="Zoom out" onClick={() => zoom(1.5)}>−</button>
        <button title="Zoom in" onClick={() => zoom(1 / 1.5)}>+</button>
        <button className="wide" title="Back to this node’s span" onClick={() => setWindow(initial.window)}>Fit</button>
      </div>
    </div>
  );
}

"use client";
/* Browser-side state shared by every component: who is reading, which layers and perspectives are on, whether
   the server answers, and the queue that posts events to /api/log and keeps them in localStorage until the
   server has acknowledged each one (the same contract as the static page's queue). */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { LogEvent, Perspective } from "@/lib/model";

export interface Meta {
  case_id: string; data_id: string; nodes: number; edges: number; classes: Record<string, number>; class_names: Record<string, string>;
  edge_types: Record<string, { label: string; kind: string }>; model: string | null;
}

interface StoreValue {
  meta: Meta;
  who: string; setWho: (w: string) => void;
  layers: Set<string>; toggleLayer: (c: string) => void;
  persp: Set<Perspective>; togglePersp: (p: Perspective) => void;
  showRejected: boolean; setShowRejected: (b: boolean) => void;
  allOn: () => void;
  online: boolean; serverEvents: number; pending: number; unsent: LogEvent[];
  make: (type: LogEvent["type"], anchor?: LogEvent["anchor"], body?: Record<string, unknown>, ref?: string) => LogEvent;
  add: (ev: LogEvent) => Promise<boolean>;
  exportLocal: () => void;
  toast: (msg: string) => void;
}

const Ctx = createContext<StoreValue | null>(null);
export const useStore = () => { const v = useContext(Ctx); if (!v) throw new Error("Store missing"); return v; };

function ts(): string {
  const d = new Date(), p = (n: number) => String(n).padStart(2, "0"), o = -d.getTimezoneOffset(), s = o >= 0 ? "+" : "-";
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}${s}${p(Math.floor(Math.abs(o) / 60))}${p(Math.abs(o) % 60)}`;
}
function uid(): string {
  const h = (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(16).slice(2) + Date.now().toString(16)).replace(/-/g, "");
  return "evt_" + h;
}

export function Store({ meta, children }: { meta: Meta; children: React.ReactNode }) {
  // A rebuild changes data_id, but pending work still belongs to the same case log.
  const KEY = "mueser.timeline.site." + meta.case_id;
  const [who, setWhoState] = useState("");
  const [layers, setLayers] = useState<Set<string>>(() => new Set(Object.keys(meta.class_names)));
  const [persp, setPersp] = useState<Set<Perspective>>(() => new Set<Perspective>(["record", "model", "person"]));
  const [showRejected, setShowRejected] = useState(false);
  const [online, setOnline] = useState(false);
  const [serverEvents, setServerEvents] = useState(0);
  const [unsent, setUnsent] = useState<LogEvent[]>([]);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [storageError, setStorageError] = useState(false);
  const toastT = useRef<ReturnType<typeof setTimeout> | null>(null);
  const queue = useRef<LogEvent[]>([]);
  const connected = useRef(false);
  const flushing = useRef<Promise<void> | null>(null);
  const save = useCallback((list: LogEvent[]) => {
    queue.current = list;
    setUnsent(list);
    try { localStorage.setItem(KEY, JSON.stringify({ unsent: list })); setStorageError(false); }
    catch { setStorageError(true); }
  }, [KEY]);

  // load what the browser kept
  useEffect(() => {
    try {
      setWhoState(localStorage.getItem("mueser.timeline.who") || "");
      const raw = localStorage.getItem(KEY) ?? localStorage.getItem("mueser.timeline.site." + meta.data_id);
      if (raw) {
        const list = JSON.parse(raw).unsent;
        if (!Array.isArray(list)) throw new Error("invalid saved queue");
        save(list);
      }
      const prefs = localStorage.getItem("mueser.timeline.prefs");
      if (prefs) { const p = JSON.parse(prefs); if (p.showRejected != null) setShowRejected(!!p.showRejected); }
    } catch { setStorageError(true); }
  }, [KEY, meta.data_id, save]);
  const setWho = useCallback((w: string) => { setWhoState(w); try { localStorage.setItem("mueser.timeline.who", w); } catch { /* ignore */ } }, []);
  useEffect(() => { try { localStorage.setItem("mueser.timeline.prefs", JSON.stringify({ showRejected })); } catch { /* ignore */ } }, [showRejected]);

  const toast = useCallback((msg: string) => { setToastMsg(msg); if (toastT.current) clearTimeout(toastT.current); toastT.current = setTimeout(() => setToastMsg(null), 1800); }, []);

  const ping = useCallback(async () => {
    try {
      const r = await fetch("/api/ping", { cache: "no-store" });
      if (!r.ok) throw new Error(String(r.status));
      const j = await r.json();
      if (j.case_id !== meta.case_id) throw new Error("not this timeline case");
      connected.current = true; setOnline(true); setServerEvents(j.events);
      if (j.who) setWhoState(w => w || j.who);
      return true;
    } catch { connected.current = false; setOnline(false); return false; }
  }, [meta.case_id]);

  const post = useCallback(async (ev: LogEvent): Promise<boolean> => {
    try {
      const r = await fetch("/api/log", { method: "POST", headers: { "Content-Type": "application/json", "X-Timeline-Case": meta.case_id }, body: JSON.stringify(ev) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) { toast("Not saved: " + (j.error || r.status)); return false; }
      if (!j.ok || j.id !== ev.id) return false;
      if (!j.duplicate) setServerEvents(n => n + 1);
      return true;
    } catch { connected.current = false; setOnline(false); return false; }
  }, [toast, meta.case_id]);

  const flush = useCallback(async () => {
    if (flushing.current) return flushing.current;
    const run = async () => {
      while (queue.current.length) {
        const ev = queue.current[0];
        if (!await post(ev)) break;
        // Read the current queue after the await: another note may have arrived meanwhile.
        save(queue.current.filter(x => x.id !== ev.id));
      }
    };
    flushing.current = run().finally(() => { flushing.current = null; });
    return flushing.current;
  }, [post, save]);

  useEffect(() => {
    let alive = true;
    const reconnect = async () => { if (await ping() && alive) await flush(); };
    void reconnect();
    const t = setInterval(reconnect, 15000);
    return () => { alive = false; clearInterval(t); };
  }, [ping, flush]);

  const make = useCallback<StoreValue["make"]>((type, anchor, body, ref) =>
    ({ id: uid(), ts: ts(), who: who || "", client: "timeline-site", data_id: meta.data_id, type, anchor: anchor || undefined, body: body || {}, ref: ref || undefined }),
    [who, meta.data_id]);

  const add = useCallback(async (ev: LogEvent) => {
    if (!queue.current.some(x => x.id === ev.id)) save([...queue.current, ev]);
    if (connected.current) await flush();
    return !queue.current.some(x => x.id === ev.id);
  }, [flush, save]);

  const exportLocal = useCallback(() => {
    const lines = unsent.map(e => JSON.stringify(e)).join("\n") + "\n";
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines], { type: "application/x-ndjson" }));
    a.download = `timeline-log-${(who || "reader").replace(/\W+/g, "-")}-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.jsonl`;
    a.click();
  }, [unsent, who]);

  const value = useMemo<StoreValue>(() => ({
    meta, who, setWho, layers,
    toggleLayer: c => setLayers(s => { const n = new Set(s); if (n.has(c)) n.delete(c); else n.add(c); return n; }),
    persp, togglePersp: p => setPersp(s => { const n = new Set(s); if (n.has(p)) n.delete(p); else n.add(p); return n; }),
    showRejected, setShowRejected,
    allOn: () => { setLayers(new Set(Object.keys(meta.class_names))); setPersp(new Set<Perspective>(["record", "model", "person"])); },
    online, serverEvents, pending: unsent.length, unsent, make, add, exportLocal, toast,
  }), [meta, who, setWho, layers, persp, showRejected, online, serverEvents, unsent, make, add, exportLocal, toast]);

  return (
    <Ctx.Provider value={value}>
      {children}
      {storageError && <p className="tl-notice" role="alert">Browser storage is unavailable. Keep this tab open and export any unsent events before leaving.</p>}
      {toastMsg && <div className="tl-toast" role="status">{toastMsg}</div>}
    </Ctx.Provider>
  );
}

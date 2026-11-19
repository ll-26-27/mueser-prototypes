"use client";
/* A small anchored dialog, closed by Escape or a click outside. */
import React, { useEffect, useLayoutEffect, useRef, useState } from "react";

export function Popover({ anchor, title, onClose, children }: { anchor: HTMLElement | null; title: string; onClose: () => void; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number }>({ left: 16, top: 80 });
  useLayoutEffect(() => {
    const p = ref.current; if (!p) return;
    const r = anchor ? anchor.getBoundingClientRect() : { left: 16, bottom: 70 };
    setPos({ left: Math.max(8, Math.min(window.innerWidth - p.offsetWidth - 8, r.left)), top: Math.min(window.innerHeight - p.offsetHeight - 8, r.bottom + 6) });
  }, [anchor]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    const click = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node) && !(anchor && anchor.contains(e.target as Node))) onClose(); };
    document.addEventListener("keydown", key); document.addEventListener("mousedown", click);
    return () => { document.removeEventListener("keydown", key); document.removeEventListener("mousedown", click); };
  }, [onClose, anchor]);
  return (
    <div className="tl-pop" role="dialog" aria-label={title} ref={ref} style={{ left: pos.left, top: pos.top }}>
      <h4>{title}</h4>
      {children}
    </div>
  );
}

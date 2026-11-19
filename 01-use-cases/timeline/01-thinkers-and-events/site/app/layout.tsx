import type { Metadata } from "next";
import "./globals.css";
import { meta } from "@/lib/data";
import { Store } from "@/components/Store";
import { TopBar } from "@/components/TopBar";

export const metadata: Metadata = { title: "Thinkers and events", description: "Thinkers, works, events, periods and concepts on one band of years, every node cited." };
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const m = meta();
  return (
    <html lang="en">
      <body>
        <Store meta={m}>
          <TopBar />
          {children}
          <footer className="tl-foot">
            Data {m.data_id}: nodes and recorded connections from Wikidata (collect run {m.collect_run}), encyclopedia and Wikipedia texts fetched {m.accessed}
            {m.proposals_run ? `, proposed connections from ${m.model || "a model"} (run ${m.proposals_run})` : ""}. Built {(m.built || "").slice(0, 10)}.
            Decisions, notes and excerpts are appended to <code>outputs/timeline/log.jsonl</code>.
          </footer>
        </Store>
      </body>
    </html>
  );
}

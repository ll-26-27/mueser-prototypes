# Thinkers and events, the site

A Next.js site over the timeline case's data. It reads `../outputs/timeline/timeline.json` (written by `python -m mueser.timeline db`) once into memory and serves one node per page, so the browser receives about 90 KB per thinker instead of the 35 MB single-file page. It writes to the same log, `../outputs/timeline/log.jsonl`, in the same event shape, so `python -m mueser.timeline db` and `build` read its decisions like the static page's.

## Run it

```sh
cd 01-use-cases/timeline/01-thinkers-and-events/site
npm install
npm run dev          # http://localhost:3001, opens on Thomas Hobbes
```

Node 20.9 or later (`.node-version` says 26.10.0; with fnm, `fnm use` picks it). `npm run build && npm start` serves the production build on the same port. `TIMELINE_WHO=ben npm run dev` fills *Reading as* for a visitor who leaves it empty.

## What is where

| path | what it is |
|---|---|
| `lib/model.ts` | the node and edge shapes, the tables that place a connection in a column and name it from each side, colours, the default span of years |
| `lib/data.ts` | loads and indexes the JSON (once per process, reloaded when the file changes); search; the bars of a span of years; the bundle one node page needs |
| `lib/log.ts` | reads, validates and appends events; decisions and reader-added edges derived from the log |
| `app/node/[id]/page.tsx` | the node page (server component) rendering `NodeView` |
| `app/log/page.tsx` | the log, newest first |
| `app/api/search`, `band`, `node/[id]`, `log`, `ping` | JSON for the search box, the band after a pan or zoom, a node's bundle, the log (GET and POST), and the badge |
| `components/Store.tsx` | who is reading; layers and perspectives; the queue that posts events and keeps them in the browser until the server acknowledges each |
| `components/TopBar.tsx` | brand, search, Layers, Legend, Reading as, the badge, Export unsent, Log |
| `components/Band.tsx`, `Columns.tsx`, `Main.tsx`, `ConnectionMap.tsx`, `NodeView.tsx` | the band, the three columns of cards, the middle column, the ego graph, and the page that assembles them |
| `app/globals.css` | the static page's stylesheet with a few additions, so the two look the same |

## How it relates to the Python side

The pipeline (`collect`, `sources`, `connect`, `db`) is unchanged and remains the source of truth; the site is a reader of its JSON and a writer to its log. After decisions in the site, `python -m mueser.timeline db` and `build` rebuild the database and the static page with them applied; the site shows them at once because it reads the log on every request. Events the site could not deliver stay in the browser and can be exported as a `.jsonl` for `python -m mueser.timeline ingest`.

A further perspective (one commentator's connections) would reach the site the same way every other edge does: through `timeline.json`, with its own `source` prefix, and would appear in the Layers menu under *By whose connections*.

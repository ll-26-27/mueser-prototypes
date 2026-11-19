"""journal report: review.csv as one page, grouped by rule, with the command that records a decision."""

from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path

from .check import read_review
from .rules import BY_ID

CSS = """body{font:15px/1.5 Georgia,serif;max-width:68rem;margin:2rem auto;padding:0 1rem;color:#222}
h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:2.2rem;border-top:2px solid #222;padding-top:.6rem}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-top:1px solid #ccc;padding:.35rem .5rem;vertical-align:top;text-align:left}
code,pre{font:12.5px/1.4 ui-monospace,Menlo,monospace;background:#f4f1ea;padding:.1rem .3rem;white-space:pre-wrap}
mark{background:#fde9a8}ins{background:#dfd;text-decoration:none}.flag{color:#a33}.accepted{color:#161}.rejected{color:#888}
small{color:#666}.where{white-space:nowrap}"""


def _ctx(row: dict) -> str:
    c = html.escape(row["context"] or row["match"])
    c = c.replace("«", "<mark>").replace("»", "</mark>")
    if row["proposed"]:
        c += f"<br>→ <ins>{html.escape(row['proposed'])}</ins>"
    return c


def report(run: Path, echo=print) -> Path:
    rows = read_review(run / "review.csv")
    manifest = json.loads((run / "run.json").read_text(encoding="utf-8"))
    p = manifest["params"]
    by_rule: dict[str, list[dict]] = {}
    for r in rows:
        by_rule.setdefault(r["rule"], []).append(r)
    summary = "".join(
        f"<tr><td><a href='#{rid}'>{rid}</a></td><td>{html.escape(p['decisions'].get(rid, 'journal examples'))}</td>"
        + "".join(f"<td>{Counter(x['status'] for x in rs)[s] or ''}</td>" for s in ("proposed", "accepted", "rejected", "flag"))
        + f"<td>{p['skipped_inside_quotation_or_italics'].get(rid, '')}</td></tr>" for rid, rs in by_rule.items())
    cite = p.get("citations_pass", {})
    out = [f"<!doctype html><html lang='en'><meta charset='utf-8'><title>House-style review</title><style>{CSS}</style>",
           f"<h1>{html.escape(manifest['inputs'][0].split('/')[-1])} against {html.escape(str(p.get('journal')))}</h1>",
           f"<p>{len(rows)} findings. Nothing in the draft has been changed. A row is applied only after it is accepted, and only to a copy.</p>",
           "<table><tr><th>rule</th><th>the journal has</th><th>proposed</th><th>accepted</th><th>rejected</th><th>flag only</th>"
           "<th>left alone in quotations or italics</th></tr>" + summary + "</table>",
           f"<p><small>Rules with no decision in the profile, not checked: {', '.join(p['rules_without_a_decision']) or 'none'}.<br>"
           f"Citations counted in the draft: {html.escape(json.dumps(p['citations_counted_in_article']))}; in the journal's samples: "
           f"{html.escape(json.dumps(p['citations_counted_in_samples']))}.<br>Citation pass: {html.escape(json.dumps(cite))}</small></p>"]
    for rid, rs in by_rule.items():
        title = BY_ID[rid].title if rid in BY_ID else "Citations restyled after the journal's examples (model proposals)"
        out.append(f"<h2 id='{rid}'>{html.escape(title)} <small>{rid} · {len(rs)}</small></h2>")
        if any(x["status"] != "flag" for x in rs):
            out.append(f"<p>To decide every row of this rule at once:<br><code>uv run python -m mueser.style journal decide --run {html.escape(str(run))} "
                       f"--rule {rid} --accept --who YOUR-NAME</code> (or <code>--reject</code>; for single rows, <code>--id</code> with the id below, "
                       "or write accepted / rejected in the status column of review.csv)</p>")
        out.append("<table><tr><th>where</th><th>text</th><th>status</th><th>id</th></tr>")
        for r in sorted(rs, key=lambda x: not ("NOT IN THE ARTICLE" in x["flag"] or "CHECK:" in x["flag"])):
            where = f"note {r['note']}" if r["note"] else f"{r['part']} ¶{int(r['para']) + 1}"
            flag = f"<br><span class='flag'>{html.escape(r['flag'])}</span>" if r["flag"] else ""
            who = f"<br><small>{html.escape(r['decided_by'])} {html.escape(r['decided_at'])}</small>" if r["decided_by"] else ""
            out.append(f"<tr><td class='where'>{where}</td><td>{_ctx(r)}{flag}</td><td class='{r['status']}'>{r['status']}{who}</td>"
                       f"<td><small>{html.escape(r['finding_id'])}</small></td></tr>")
        out.append("</table>")
    path = run / "report.html"
    path.write_text("\n".join(out) + "</html>", encoding="utf-8")
    echo(f"wrote {path}")
    return path

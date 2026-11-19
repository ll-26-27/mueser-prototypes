"""journal check: every place a draft departs from the journal's profile, as a row in review.csv.

Rules run first and need no model. With ``--citations`` a model restyles the footnotes after the
journal's own example citations; each restyled note is a proposal, compared with the original word by
word so that anything the model added is named on the row. Nothing here changes the draft.
"""

from __future__ import annotations

import csv
import difflib
import json
import re
import time
from collections import Counter
from pathlib import Path

import yaml

from mueser.shared import openrouter
from mueser.shared.cache import sha256_file, sha256_text
from mueser.shared.runs import RunManifest, rel, run_id
from mueser.style.shared.docx import Docx, apply_edits, italic_spans, para_text, q, style_id

from . import MODEL, REASONING
from .rules import BY_ID, RANGE, RULES, citation_measures, protected_spans

FIELDS = ["finding_id", "rule", "part", "para", "note", "match", "proposed", "context", "flag", "edits", "model",
          "prompt_sha256", "cache_key", "status", "decided_by", "decided_at"]
BIB_HEADINGS = {"bibliography", "references", "works cited", "select bibliography", "sources", "literatur", "literaturverzeichnis"}
QUOTE_STYLE = re.compile(r"quote|zitat|block", re.IGNORECASE)
HEADING_STYLE = re.compile(r"heading|title|berschrift", re.IGNORECASE)

# words a restyled citation may introduce without their being new information
STYLE_WORDS = set(["ibid", "n", "nn", "edn", "ed", "eds", "tr", "trans", "vol", "vols", "p", "pp", "ch", "chs", "para", "paras", "no", "nos", "cf", "see", "at", "in", "and", "ff", "art", "arts", "s", "ss", "above", "below", "also"])

RESTYLE_SYSTEM = """You restyle the citations in an article's footnotes to match a journal's form.
Change only the form of citations: order of elements, punctuation, abbreviations, quotation marks, shortened later citations, ibid and cross-references.
Leave every sentence of discussion exactly as written. Never add information (a name, title word, place, publisher, year, page) that is not in the note itself or in an earlier note of the same article.
If a note cannot be restyled with what is given, return it unchanged. Return every note, each under its number, as plain text with no markup."""

RESTYLE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["notes"],
    "properties": {"notes": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["n", "text"],
        "properties": {"n": {"type": "integer"}, "text": {"type": "string"}}}}},
}

RESTYLE_USER = """THE JOURNAL'S CONVENTIONS, as a model described them from the journal's articles:
{rules}

EXAMPLE CITATIONS, copied word for word from the journal's articles:
{examples}

THE ARTICLE'S FOOTNOTES, all of them, in order:
{notes}"""


def paragraphs(doc: Docx) -> list[dict]:
    """Every paragraph of the body and of the notes with the part it belongs to and what must not be touched in it."""
    out, part = [], "body"
    for i, p in enumerate(doc.document.iter(q("p"))):
        text = para_text(p)
        style = style_id(p)
        if text.strip().lower().rstrip(":") in BIB_HEADINGS:
            part = "bibliography"
            here = "heading"
        elif part == "bibliography" and HEADING_STYLE.search(style):
            part, here = "body", "body"
        else:
            here = "blockquote" if QUOTE_STYLE.search(style) else part
        out.append({"key": f"b{i}", "part": here, "para": i, "note": None, "el": p, "text": text, "italics": italic_spans(p)})
    for n, _, f in doc.footnote_list():
        for j, p in enumerate(f.iter(q("p"))):
            out.append({"key": f"n{n}.{j}", "part": "note", "para": j, "note": n, "el": p, "text": para_text(p), "italics": italic_spans(p)})
    return out


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < b and a < end for a, b in spans)


def _context(text: str, start: int, end: int) -> str:
    return ("…" if start > 50 else "") + text[max(0, start - 50):start] + "«" + text[start:end] + "»" + text[end:end + 50] + ("…" if end + 50 < len(text) else "")


def rule_findings(paras: list[dict], decisions: dict[str, str]) -> tuple[list[dict], Counter]:
    rows, skipped = [], Counter()
    for para in paras:
        if para["part"] in ("heading", "blockquote"):
            continue
        text = para["text"]
        guard = protected_spans(text) + para["italics"]
        for rule in RULES:
            target = decisions.get(rule.id)
            if not target or (rule.scope == "body" and para["part"] != "body"):
                continue
            for h in rule.find(text):
                if h.variant == target:
                    continue
                if rule.protect and _overlaps(h.start, h.end, guard):
                    skipped[rule.id] += 1  # inside a quotation or italics: the source's own words or a title
                    continue
                edits = rule.convert(text, h, target) if rule.convert else None
                proposed = ""
                if edits:
                    delta = sum(len(new) - (e - s) for s, e, new in edits)
                    proposed = apply_edits(text, edits)[h.start:h.end + delta]
                flag = h.note if edits else "; ".join(x for x in (f"flag only: the journal has '{target}', this is '{h.variant}'", h.note) if x)
                rows.append({"finding_id": f"{para['key']}-{rule.id}-{h.start}", "rule": rule.id, "part": para["part"],
                             "para": para["para"], "note": para["note"] or "", "match": text[h.start:h.end], "proposed": proposed,
                             "context": _context(text, h.start, h.end), "flag": flag, "edits": json.dumps(edits) if edits else "",
                             "model": "", "prompt_sha256": "", "cache_key": "", "status": "proposed" if edits else "flag",
                             "decided_by": "", "decided_at": ""})
    return rows, skipped


def words(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", text.lower())


def word_check(original: str, proposed: str, earlier: set[str], n: int) -> str:
    """Name what a restyled note holds that the original does not, and any page range that stopped being one."""
    have = Counter(words(original))
    numbers = [w for w in have if w.isdigit()]
    new = [w for w in Counter(words(proposed)) - have if w not in STYLE_WORDS]
    refs = {int(x) for x in re.findall(r"\(n (\d+)\)", proposed)}
    new = [w for w in new if not (w.isdigit() and int(w) in refs)]
    new = [w for w in new if not (w.isdigit() and any(x.endswith(w) for x in numbers))]  # 88–89 written 88–9
    bad_refs = sorted(r for r in refs if r >= n)
    ranges_after = {m.group(1) for m in RANGE.finditer(proposed)}
    lost = [m.group(0) for m in RANGE.finditer(original) if m.group(1) not in ranges_after]
    from_earlier = sorted(w for w in new if w in earlier)
    nowhere = sorted(w for w in new if w not in earlier)
    bits = []
    if nowhere:
        bits.append("NOT IN THE ARTICLE'S NOTES: " + ", ".join(nowhere))
    if lost:
        bits.append("CHECK: a range in the note is not a range in the proposal: " + ", ".join(lost))
    if bad_refs:
        bits.append("CHECK: cross-reference to a note that is not earlier: " + ", ".join(map(str, bad_refs)))
    if from_earlier:
        bits.append("taken from earlier notes: " + ", ".join(from_earlier))
    return "; ".join(bits)


def diff_edits(old: str, new: str, offset: int = 0) -> list[tuple[int, int, str]]:
    """The smallest word-level edits that turn old into new, as character spans of old."""
    a, b = re.findall(r"\w+|\s+|[^\w\s]", old), re.findall(r"\w+|\s+|[^\w\s]", new)
    starts = [0]
    for tok in a:
        starts.append(starts[-1] + len(tok))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [(starts[i1] + offset, starts[i2] + offset, "".join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]


def citation_findings(paras: list[dict], profile: dict, model: str, echo=print) -> tuple[list[dict], dict]:
    from_model = (profile.get("citations") or {}).get("from_model") or {}
    examples = [e for e in from_model.get("examples", []) if e.get("verbatim_in_samples")]
    if not examples:
        echo("citations: the profile holds no verified example citations (run `journal profile --citations`); pass skipped")
        return [], {"status": "skipped", "reason": "no verified example citations in the profile"}
    notes: dict[int, list[dict]] = {}
    for p in paras:
        if p["part"] == "note":
            notes.setdefault(p["note"], []).append(p)
    if not notes:
        return [], {"status": "skipped", "reason": "the article has no footnotes"}
    listing = "\n".join(f"[{n}] " + " ¶ ".join(x["text"].strip() for x in ps) for n, ps in notes.items())
    user = RESTYLE_USER.format(rules="\n".join("- " + r for r in from_model.get("rules_as_described_by_the_model", [])),
                               examples="\n".join(f"- ({e['kind']}) {e['text']}" for e in examples), notes=listing)
    info = {"model": model, "prompt_sha256": sha256_text(RESTYLE_SYSTEM + "\n" + user), "notes_sent": len(notes)}
    try:
        res = openrouter.chat(model=model, system=RESTYLE_SYSTEM, user_text=user, schema=RESTYLE_SCHEMA, schema_name="restyled_notes",
                              max_tokens=32000, step="style.journal.check", timeout=900, reasoning=REASONING)
    except openrouter.MissingCredential as e:
        echo(f"citations: skipped, {e}")
        return [], {**info, "status": "skipped", "reason": str(e)}
    except (openrouter.JSONReplyError, RuntimeError) as e:
        echo(f"citations: the call failed; no citation rows were written: {e}")
        return [], {**info, "status": "error", "reason": str(e)[:500]}
    info.update(status="ok", model=res["model"], requested_model=model, cache_key=res["key"], cost_usd=res["cost_usd"], cached=res["cached"])
    replies = {int(x["n"]): x["text"] for x in (res["parsed"] or {}).get("notes", [])}
    rows, earlier = [], set()
    base = {"rule": "citation-form", "part": "note", "para": 0, "model": info["model"], "prompt_sha256": info["prompt_sha256"],
            "cache_key": info["cache_key"], "decided_by": "", "decided_at": ""}
    for n, ps in notes.items():
        original = ps[0]["text"]
        core = original.strip()
        lead = len(original) - len(original.lstrip())
        row = {**base, "finding_id": f"n{n}.0-citation-form", "note": n, "match": core, "proposed": "", "context": "", "edits": ""}
        if n not in replies:
            rows.append({**row, "flag": "the model returned no text for this note", "status": "flag"})
        elif len(ps) > 1:
            if " ".join(replies[n].split()) != " ".join(" ¶ ".join(x["text"].strip() for x in ps).split()):
                rows.append({**row, "match": " ¶ ".join(x["text"].strip() for x in ps), "proposed": replies[n],
                             "flag": "flag only: a note of several paragraphs is not edited automatically", "status": "flag"})
        elif replies[n].strip() != core:
            new = replies[n].strip()
            rows.append({**row, "proposed": new, "flag": word_check(core, new, earlier, n),
                         "edits": json.dumps(diff_edits(core, new, lead), ensure_ascii=False), "status": "proposed"})
        earlier.update(words(" ".join(x["text"] for x in ps)))
    info["notes_changed"] = sum(1 for r in rows if r["status"] == "proposed")
    info["notes_to_check_first"] = sum(1 for r in rows if "NOT IN THE ARTICLE" in r["flag"] or "CHECK:" in r["flag"])
    return rows, info


def write_review(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_review(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check(article: Path, profile_path: Path, out_root: Path, with_citations: bool = False, model: str = MODEL,
          rid: str | None = None, echo=print) -> Path:
    t0 = time.time()
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    decisions = {k: v["decision"] for k, v in profile["rules"].items() if v.get("decision")}
    unknown = {k: v for k, v in decisions.items() if k not in BY_ID or v not in BY_ID[k].variants}
    if unknown:
        raise SystemExit(f"{profile_path.name}: these decisions are not variants of their rules: {unknown}")
    doc = Docx(article)
    paras = paragraphs(doc)
    rows, skipped = rule_findings(paras, decisions)
    cite_info = {"status": "not requested"}
    if with_citations:
        cite_rows, cite_info = citation_findings(paras, profile, model, echo)
        rows += cite_rows

    rid = rid or run_id("journal-check-")
    folder = out_root / rid
    if folder.exists():
        raise SystemExit(f"{folder} exists; a run folder is never overwritten")
    (folder / "work").mkdir(parents=True)
    with (folder / "work" / "paragraphs.jsonl").open("w", encoding="utf-8") as f:
        for p in paras:
            f.write(json.dumps({k: p[k] for k in ("key", "part", "para", "note", "text", "italics")}, ensure_ascii=False) + "\n")
    write_review(folder / "review.csv", rows)
    body_text = " ".join(p["text"] for p in paras)
    counts = Counter(r["rule"] for r in rows)
    params = {"article_sha256": sha256_file(article), "profile_sha256": sha256_file(profile_path), "journal": profile.get("journal"),
              "decisions": decisions, "rules_without_a_decision": [r.id for r in RULES if r.id not in decisions],
              "findings_by_rule": dict(counts), "skipped_inside_quotation_or_italics": dict(skipped),
              "paragraphs": Counter(p["part"] for p in paras), "citations_pass": cite_info,
              "citations_counted_in_article": {**citation_measures(body_text), "footnotes": len(doc.footnote_list())},
              "citations_counted_in_samples": (profile.get("citations") or {}).get("counted_in_samples", {})}
    RunManifest(run_id=rid, step="style.journal.check", params=params, inputs=[rel(article), rel(profile_path)],
                outputs=[rel(folder / "review.csv"), rel(folder / "work" / "paragraphs.jsonl")],
                cost_usd=float(cite_info.get("cost_usd") or 0), seconds=round(time.time() - t0, 2)).write(folder)
    echo(f"{article.name} against {profile.get('journal')}: {len(rows)} findings")
    for rule_id, n in counts.most_common():
        echo(f"  {rule_id:28} {n:5}" + (f"   ({skipped[rule_id]} more left alone inside quotations or italics)" if skipped.get(rule_id) else ""))
    echo(f"wrote {folder / 'review.csv'}")
    return folder


def decide(run: Path, who: str, accept: bool, rules: list[str], ids: list[str], echo=print) -> int:
    """Record a decision on every proposal of the named rules, or on the named findings. Flags have nothing to decide."""
    path = run / "review.csv"
    rows = read_review(path)
    now, n = time.strftime("%Y-%m-%dT%H:%M:%S"), 0
    with (run / "decisions.jsonl").open("a", encoding="utf-8") as log:
        for r in rows:
            if r["status"] == "flag" or not (r["rule"] in rules or r["finding_id"] in ids):
                continue
            r.update(status="accepted" if accept else "rejected", decided_by=who, decided_at=now)
            log.write(json.dumps({"finding_id": r["finding_id"], "status": r["status"], "by": who, "at": now}) + "\n")
            n += 1
    write_review(path, rows)
    echo(f"{n} rows {'accepted' if accept else 'rejected'} by {who}")
    return n

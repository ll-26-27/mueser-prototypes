"""journal profile: what a journal does, counted in its own articles.

For every rule the variants are counted in each sample, with examples. A convention is recorded as the
journal's only when one variant holds at least the threshold share of at least ``MIN_HITS`` hits;
otherwise ``decision`` is left empty for a person to fill. With ``--citations`` a model is asked to pick
out example citations from the samples; an example is kept only if it occurs in a sample word for word.
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import yaml

from mueser.shared import openrouter
from mueser.shared.cache import sha256_file, sha256_text

from . import MODEL, REASONING, read_sample, squash
from .rules import RULES, citation_measures

MIN_HITS = 5
EXAMPLES = 3

HEADER = """\
# A journal's conventions, counted by `journal profile` in the sample articles listed below.
# `decision` is what `journal check` holds a draft to. It was filled in only where one variant had at
# least the threshold share of the hits; where it is empty, read the counts and examples and write one of
# the listed variants yourself, or leave it empty to skip the rule. You may overrule any decision.
"""

CITE_SYSTEM = """You read published articles from one journal and report how the journal cites sources.
Copy example citations exactly as printed, character for character, each from a single footnote, endnote or reference-list entry.
Do not correct, complete or normalise anything. Do not invent an example for a kind of source the articles do not cite."""

CITE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["system", "rules", "examples"],
    "properties": {
        "system": {"type": "string", "enum": ["notes", "author-date", "mixed"]},
        "rules": {"type": "array", "items": {"type": "string"}},
        "examples": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["kind", "text"],
            "properties": {"kind": {"type": "string"}, "text": {"type": "string"}}}},
    },
}

CITE_USER = """Below are {n} articles from the journal, whole.

Return:
- system: whether sources are cited in notes, by author and date in the text, or both.
- rules: the citation conventions you can see, one per line, each concrete enough to apply (order of elements, punctuation between them, italics or quotation marks for titles as far as the text shows, how pages are given, how a later citation of the same work is shortened, how ibid or cross-references are used).
- examples: up to four verbatim examples for each of these kinds, where the articles have them: book-first, book-later, article-first, article-later, chapter-first, chapter-later, edited-or-translated, ibid, cross-reference, case, statute, archival, other.

{articles}"""


def measure(text: str) -> dict[str, dict]:
    """rule id -> {counts, examples}; examples are the hit with 40 characters either side."""
    out = {}
    for rule in RULES:
        counts: Counter[str] = Counter()
        examples: dict[str, list[str]] = {}
        for h in rule.find(text):
            counts[h.variant] += 1
            ex = examples.setdefault(h.variant, [])
            if len(ex) < EXAMPLES:
                ex.append("…" + text[max(0, h.start - 40):h.start] + "«" + text[h.start:h.end] + "»" + text[h.end:h.end + 40] + "…")
        out[rule.id] = {"counts": dict(counts), "examples": examples}
    return out


def decide(counts: dict[str, int], threshold: float) -> tuple[str | None, float | None, str]:
    total = sum(counts.values())
    if total < MIN_HITS:
        return None, None, f"{total} hits in the samples; fewer than {MIN_HITS}, so nothing was concluded"
    variant, top = max(counts.items(), key=lambda kv: kv[1])
    share = round(top / total, 3)
    if share < threshold:
        return None, share, f"the samples are mixed: '{variant}' has {share:.0%} of {total} hits, below the {threshold:.0%} threshold"
    return variant, share, f"'{variant}' in {share:.0%} of {total} hits"


def citations(samples: list[dict], model: str, echo=print) -> dict:
    articles = "\n\n".join(f"===== ARTICLE {i + 1}: {s['file']} =====\n{s['text']}" for i, s in enumerate(samples))
    user = CITE_USER.format(n=len(samples), articles=articles)
    try:
        res = openrouter.chat(model=model, system=CITE_SYSTEM, user_text=user, schema=CITE_SCHEMA, schema_name="citations",
                              max_tokens=16000, step="style.journal.profile", timeout=600, reasoning=REASONING)
    except openrouter.MissingCredential as e:
        echo(f"citation examples skipped: {e}")
        return {"status": "skipped", "reason": str(e)}
    except (openrouter.JSONReplyError, RuntimeError) as e:
        echo(f"citation examples: the call failed and nothing was recorded as a result: {e}")
        return {"status": "error", "reason": str(e)[:500], "model": model}
    parsed = res["parsed"] or {}
    haystack = squash(" ".join(s["text"] for s in samples))
    examples = []
    for ex in parsed.get("examples", []):
        text = squash(ex.get("text", ""))
        examples.append({"kind": ex.get("kind", "other"), "text": text, "verbatim_in_samples": bool(text) and text in haystack})
    kept = sum(e["verbatim_in_samples"] for e in examples)
    echo(f"citation examples: {kept} of {len(examples)} occur word for word in the samples; the rest are recorded as not found and are not used")
    return {"status": "ok", "model": res["model"], "requested_model": model, "prompt_sha256": sha256_text(CITE_SYSTEM + "\n" + user),
            "cache_key": res["key"], "cost_usd": res["cost_usd"], "system": parsed.get("system"),
            "rules_as_described_by_the_model": parsed.get("rules", []), "examples": examples}


def profile(sample_paths: list[Path], out: Path, name: str, threshold: float = 0.8, with_citations: bool = False,
            model: str = MODEL, echo=print) -> dict:
    t0 = time.time()
    if out.exists():
        raise SystemExit(f"{out} exists; it may hold decisions made by hand. Move it or choose another --out.")
    samples = []
    for p in sample_paths:
        raw, pages = read_sample(p)
        text = squash(raw)
        if len(text) < 500:
            raise SystemExit(f"{p.name}: only {len(text)} characters of text could be read (a scanned PDF?). Nothing was profiled.")
        samples.append({"file": p.name, "sha256": sha256_file(p), "characters": len(text), "pages": pages, "text": text})
    per_sample = [measure(s["text"]) for s in samples]
    rules = {}
    for rule in RULES:
        total: Counter[str] = Counter()
        examples: dict[str, list[str]] = {}
        for m in per_sample:
            total.update(m[rule.id]["counts"])
            for variant, ex in m[rule.id]["examples"].items():
                examples.setdefault(variant, [])
                examples[variant] += ex[:max(0, EXAMPLES - len(examples[variant]))]
        decision, share, why = decide(dict(total), threshold)
        rules[rule.id] = {"title": rule.title, "decision": decision, "basis": why, "variants": list(rule.variants),
                          "proposes_edits": rule.convert is not None, "counts": dict(total),
                          "counts_by_sample": {s["file"]: m[rule.id]["counts"] for s, m in zip(samples, per_sample)},
                          "examples": examples}
    measured: Counter[str] = Counter()
    for s in samples:
        measured.update(citation_measures(s["text"]))
    data = {"journal": name, "made": time.strftime("%Y-%m-%d"), "threshold": threshold, "minimum_hits": MIN_HITS,
            "samples": [{k: v for k, v in s.items() if k != "text"} for s in samples],
            "rules": rules, "citations": {"counted_in_samples": dict(measured)}}
    if with_citations:
        data["citations"]["from_model"] = citations(samples, model, echo)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HEADER + "\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    echo(f"{name}: {len(samples)} samples, {sum(s['characters'] for s in samples)} characters, {time.time() - t0:.1f} s")
    for rid, r in rules.items():
        echo(f"  {rid:28} {r['decision'] or '(undecided)':16} {r['basis']}")
    echo(f"  citations counted: {dict(measured)}")
    echo(f"wrote {out}")
    return data

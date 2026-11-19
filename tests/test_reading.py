"""The reading room: settled layer, span remapping, anchoring, translation alignment, log, citations, server.

Every fixture here is invented (synthetic) text; nothing is measured about a real page."""

from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

from mueser.reading import cite, log
from mueser.reading.anchor import SegLine, align_lines
from mueser.reading.settle import apply_decisions, line_offsets, map_local, norm_cum, spans_to_lines
from mueser.reading.translate import align_segments, mark_divergence, verify_segments
from mueser.text.evaluate import normalize

LINES = ["Erſte Zeile mit aͤ", "und einer Trennung am Zei-", "lenende, dann Schluſs."]


def test_norm_cum_tracks_folded_characters():
    cum = norm_cum("Aſchenputtel aͤ  b")
    assert cum[-1] == len(normalize("Aſchenputtel aͤ  b"))
    assert cum[0] == 1 and cum[1] == 2            # ſ -> s is one character
    assert cum[12] == 12                          # a trailing space has no width until the next character
    assert cum[13] == cum[14] == 14               # 'a' then the combining mark: 'ä' is one normalised char
    assert cum[15] == cum[16] == 14 and cum[17] == 16   # the two spaces collapse into the next character's range


def test_line_offsets_follow_hyphen_join_and_spaces():
    base = normalize("\n".join(LINES))
    offs = line_offsets(LINES)
    assert all(o["ok"] for o in offs)
    assert offs[1]["joined"] is True and offs[0]["joined"] is False
    assert base[offs[0]["start"]:offs[0]["end"]] == "Erste Zeile mit ä"
    assert base[offs[1]["start"]:offs[1]["end"]] == "und einer Trennung am Zei"
    assert offs[2]["start"] == offs[1]["end"]     # no space after a joined hyphen


def test_span_across_hyphenated_line_break_becomes_two_pieces():
    base = normalize("\n".join(LINES))
    s = base.index("Zeilenende"); e = s + len("Zeilenende")
    per_line = spans_to_lines(LINES, [{"start": s, "end": e, "base": "Zeilenende", "alternatives": {"x": "Zeilende"}, "weight": 0.5}])
    pieces = [(i, p) for i, pl in enumerate(per_line) for p in pl]
    assert [i for i, _ in pieces] == [1, 2]
    assert LINES[1][pieces[0][1]["start"]:pieces[0][1]["end"]] == "Zei-"
    assert LINES[2][pieces[1][1]["start"]:pieces[1][1]["end"]] == "lenende"
    assert pieces[0][1]["of"] == 2 and pieces[1][1]["piece"] == 1


def test_map_local_handles_insertion():
    cum = norm_cum("abc def")
    assert map_local(cum, 4, 7) == (4, 7)
    assert map_local(cum, 4, 4) == (4, 4)


def test_align_lines_match_merge_split_gap_and_ornament():
    settled = ["Die erste Zeile", "zweite Zeile hier", "Ein ganz anderer Satz ohne Gegenstück im Bild", "vierte und fünfte", "Zeile zusammen", "letzte Zeile"]
    seg = [SegLine(0, "", [0, 0, 10, 10]),                       # empty polygon (ornament): dropped cheaply
           SegLine(1, "Die erſte Zeile", [0, 10, 100, 10]),
           SegLine(2, "zweite Zeile", [0, 20, 50, 10]), SegLine(3, "hier", [60, 20, 40, 10]),   # split: one line, two polygons
           SegLine(4, "vierte und fünfte Zeile zuſammen", [0, 40, 100, 10]),                   # merge: two lines, one polygon
           SegLine(5, "letzte Zeile", [0, 50, 100, 10])]
    anchors, summary = align_lines(settled, seg)
    ops = [a.op for a in anchors]
    assert ops == ["match", "split", "unanchored", "merge", "merge", "match"]
    assert anchors[1].bbox == [0, 20, 100, 10]
    assert anchors[3].bbox == anchors[4].bbox == [0, 40, 100, 10]
    assert summary["dropped_polygons"] == 1 and summary["unanchored"] == 1 and summary["split"] == 1 and summary["merged"] == 2


def test_align_lines_all_unreadable_is_unanchored():
    anchors, summary = align_lines(["[...]", "[...]"], [SegLine(0, "ganz anderer Text hier", [0, 0, 1, 1]), SegLine(1, "noch mehr Text", [0, 2, 1, 1])])
    assert all(a.op == "unanchored" for a in anchors) and summary["mean_confidence"] is None


def _lines(*texts):
    return [{"line_id": f"l{i + 1}", "settled": t} for i, t in enumerate(texts)]


def test_verify_segments_corrects_and_flags():
    lines = _lines("Meine Freude wurde", "verdoppelt, als ich", "den Vater unter den", "Zuhörern ſah.")
    segs = [{"line_start": "l2", "line_end": "l4", "first_words": "Meine Freude wurde", "last_words": "unter den Zuhörern", "translation": "…", "note": ""},
            {"line_start": "l1", "line_end": "l2", "first_words": "ganz erfundene Worte", "last_words": "als ich", "translation": "…", "note": ""}]
    out, uncovered = verify_segments(segs, lines)
    assert out[0]["verified"] == "corrected" and out[0]["line_start"] == "l1" and out[0]["line_end"] == "l4"
    assert out[1]["verified"] is False
    assert uncovered == []


def test_verify_segments_accepts_words_across_a_line_break():
    lines = _lines("Pantoffel und was sonst dazu gehörte. Aschen-", "puttel trug alles nach Haus")
    segs = [{"line_start": "l1", "line_end": "l2", "first_words": "Aschen- puttel trug", "last_words": "alles nach Haus", "translation": "…", "note": ""}]
    out, _ = verify_segments(segs, lines)
    assert out[0]["verified"] is True


def test_align_segments_merges_until_line_ranges_coincide():
    ids = ["l1", "l2", "l3", "l4"]
    a = [{"segment_id": "s01", "lines": ["l1", "l2"], "translation": "One two."}, {"segment_id": "s02", "lines": ["l3"], "translation": "Three."}, {"segment_id": "s03", "lines": ["l4"], "translation": "Four."}]
    b = [{"segment_id": "s01", "lines": ["l1"], "translation": "One."}, {"segment_id": "s02", "lines": ["l2", "l3"], "translation": "Two three."}, {"segment_id": "s03", "lines": ["l4"], "translation": "Quite different words."}]
    blocks = align_segments(a, b, ids)
    assert [bl["lines"] for bl in blocks] == [["l1", "l2", "l3"], ["l4"]]
    mark_divergence(blocks, 0.35)
    assert blocks[0]["divergent"] is False and blocks[1]["divergent"] is True and "diff" in blocks[1]


def test_log_append_read_ingest_and_latest_decision(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    e1 = log.make("decision", who="ben", body={"target": "span:p1:3", "choice": "alt", "reader": "r", "text": "x"})
    e2 = log.make("decision", who="ben", body={"target": "span:p1:3", "choice": "custom", "text": "y"})
    e2.ts = "2099-01-01T00:00:00+0000"
    log.append(p, e1); log.append(p, e2)
    assert [e.id for e in log.read(p)] == [e1.id, e2.id]
    assert log.latest_decisions(log.read(p))["span:p1:3"].body["text"] == "y"
    inbox = tmp_path / "inbox"; inbox.mkdir()
    e3 = log.make("issue", who="ben", anchor={"doc": "d", "page": "p1", "lines": ["l1"], "quote": "q"}, body={"text": "?"})
    (inbox / "ben.jsonl").write_text(json.dumps(e1.model_dump()) + "\n" + json.dumps(e3.model_dump()) + "\nnot json\n", encoding="utf-8")
    rep = log.ingest(inbox, p)
    assert rep["ben.jsonl"] == {"added": 1, "duplicate": 1, "invalid": 1}
    assert log.current_status(log.read(p))[e3.id] == "open"


def test_apply_decisions_changes_exactly_one_line():
    settled = {"build_id": "b-1", "pages": {"p1": {"lines": [
        {"line_id": "l1", "diplomatic": "die Tauben wieder", "settled": "die Tauben wieder", "spans": [{"span_id": "0", "piece": 0, "of": 1, "start": 4, "end": 10, "base": "Tauben", "alternatives": {"k": "Taubem"}, "weight": 0.5, "status": "open", "decision_event": None}]},
        {"line_id": "l2", "diplomatic": "herein", "settled": "herein", "spans": []}]}}}
    ev = log.make("decision", who="ben", body={"target": "span:p1:0", "choice": "custom", "text": "Täubchen"})
    new, applied = apply_decisions(settled, [ev])
    assert new["pages"]["p1"]["lines"][0]["settled"] == "die Täubchen wieder"
    assert new["pages"]["p1"]["lines"][0]["diplomatic"] == "die Tauben wieder"
    assert new["pages"]["p1"]["lines"][1]["settled"] == "herein"
    assert new["pages"]["p1"]["lines"][0]["spans"][0]["status"] == "decided" and len(applied) == 1
    keep = log.make("decision", who="ben", body={"target": "span:p1:0", "choice": "keep"})
    keep.ts = "2099-01-01T00:00:00+0000"
    new2, _ = apply_decisions(settled, [ev, keep])
    assert new2["pages"]["p1"]["lines"][0]["settled"] == "die Tauben wieder"


def test_citation_formats_and_synthetic_label():
    meta = {"docs": {"d": {"type": "book", "title": "Erfundenes Buch", "author": ["Anna Beispiel", "Karl Muster"], "date": "1801", "place": "Weimar",
                           "publisher": "Verlag", "url": "https://example.org", "synthetic": True, "pages": {"p1": {"label": "p. 7"}}},
                     "m": {"type": "manuscript", "title": "Brief", "author": ["Muster, Karl"], "date": "1864", "archive": "Archiv", "shelfmark": "A 1", "pages": {"p2": {"label": "fol. 3r"}}}}}
    c = cite.citation(meta, "d", "p1", ["l2", "l3", "l4"], quote="q", provenance={"transcription": {"reader": "r", "run_id": "run", "build_id": "b", "decisions": 2, "who": "ben"}})
    assert c["plain"].startswith("Beispiel and Muster, Erfundenes Buch (Weimar, 1801), p. 7, ll. 2–4.")
    assert "Synthetic page" in c["plain"] and "2 decisions by ben" in c["plain"]
    assert c["csl"]["issued"] == {"date-parts": [[1801]]} and c["csl"]["locator"] == "7, ll. 2–4" and c["csl"]["author"][0] == {"family": "Beispiel", "given": "Anna"}
    assert c["markdown"].startswith("> q\n\n[^1]: ")
    m = cite.citation(meta, "m", "p2", ["l1"])
    assert m["plain"] == "Muster, Brief (1864), fol. 3r, l. 1. Archiv, A 1."
    assert m["csl"]["archive_location"] == "A 1" and m["csl"]["author"] == [{"family": "Muster", "given": "Karl"}]


def test_serve_accepts_valid_and_rejects_invalid_events(tmp_path: Path):
    from mueser.reading.serve import serve
    case = tmp_path / "case"; (case / "outputs" / "reading").mkdir(parents=True)
    httpd = serve(case, port=0, who="t", open_browser=False)
    t = threading.Thread(target=httpd.serve_forever, daemon=True); t.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        ping = json.loads(urllib.request.urlopen(base + "/api/ping").read())
        assert ping["who"] == "t" and ping["events"] == 0
        ev = log.make("question", who="t", body={"text": "?"}).model_dump()
        r = urllib.request.urlopen(urllib.request.Request(base + "/api/log", data=json.dumps(ev).encode(), headers={"Content-Type": "application/json"}, method="POST"))
        assert json.loads(r.read())["ok"] is True
        try:
            urllib.request.urlopen(urllib.request.Request(base + "/api/log", data=b'{"nope": 1}', headers={"Content-Type": "application/json"}, method="POST"))
            raise AssertionError("invalid event accepted")
        except urllib.error.HTTPError as e:
            assert e.code == 400
        assert len(log.read(case / "outputs" / "reading" / "log.jsonl")) == 1
        (case / ".env").write_text("SECRET=1", encoding="utf-8")
        try:
            urllib.request.urlopen(base + "/.env")
            raise AssertionError("dotfile served")
        except urllib.error.HTTPError as e:
            assert e.code == 403
    finally:
        httpd.shutdown(); httpd.server_close()

"""The journal-style commands on synthetic files: a profile counted from samples, findings, decisions, a checked copy.

No test touches the network; the model pass is given a canned reply.
"""

import hashlib
import json

import pytest
import yaml

from mueser.shared import openrouter
from mueser.style.fixtures import synth_article, synth_samples
from mueser.style.journal.apply import apply
from mueser.style.journal.check import check, decide, diff_edits, read_review, word_check
from mueser.style.journal.profile import decide as decide_variant
from mueser.style.journal.profile import profile
from mueser.style.journal.report import report
from mueser.style.journal.rules import BY_ID, quote_spans
from mueser.style.shared.docx import Docx, apply_edits, italic_spans, para_text, q, replace_span

QUIET = lambda *a, **k: None


def _convert(rule_id, text, target):
    rule = BY_ID[rule_id]
    edits = [e for h in rule.find(text) if h.variant != target for e in (rule.convert(text, h, target) or [])]
    return apply_edits(text, edits)


def test_quotes_swap_with_nesting_and_leave_apostrophes():
    text = "took the “sovereign’s ‘right of nature’” as the judges’ theme"
    assert [(s["kind"], s["depth"]) for s in quote_spans(text)] == [("double", 0), ("single", 1)]
    assert _convert("quote-primary", text, "single") == "took the ‘sovereign’s “right of nature”’ as the judges’ theme"
    assert _convert("quote-primary", "he said ‘no “never” again’ twice", "double") == "he said “no ‘never’ again” twice"


def test_spelling_rules_know_the_words_with_one_spelling():
    assert [h.variant for h in BY_ID["spelling-ize"].find("They promised to exercise and to capsize; we organized and realised.")] == ["ize", "ise"]
    assert _convert("spelling-ize", "Organizing the civilization", "ise") == "Organising the civilisation"
    assert _convert("spelling-british-american", "Color and Centre, honorary, laborious", "british") == "Colour and Centre, honorary, laborious"
    assert _convert("spelling-british-american", "the neighbour’s programme", "american") == "the neighbor’s program"


def test_mechanical_conversions():
    assert _convert("dash", "changed—not slowly—at once", "spaced-en") == "changed – not slowly – at once"
    assert _convert("range-dash", "pp. 12-14 and 2026-11-19 and 88–89", "en-dash") == "pp. 12–14 and 2026-11-19 and 88–89"
    assert _convert("date-order", "On March 12, 1651 and 3 June 1660", "day-month-year") == "On 12 March 1651 and 3 June 1660"
    assert _convert("date-order", "On 12 March 1651", "month-day-year") == "On March 12, 1651"
    assert _convert("century", "The 17th century. 21st-century readers", "words") == "The seventeenth century. Twenty-first-century readers"
    assert _convert("century", "the seventeenth century", "numerals") == "the 17th century"
    assert _convert("latin-abbrev", "see, e.g., the die and i.e. this", "no-points") == "see, eg, the die and ie this"
    assert _convert("page-abbrev", "pp. 12 and p.3", "no-point") == "pp 12 and p 3"
    assert _convert("ibid-form", "Ibid., 90.", "no-point") == "Ibid, 90."
    assert _convert("ibid-form", "Ibid.", "no-point") == "Ibid."  # the point ends the note; left for a person


def test_a_convention_is_recorded_only_above_the_threshold():
    assert decide_variant({"single": 9, "double": 1}, 0.8)[0] == "single"
    assert decide_variant({"single": 6, "double": 4}, 0.8)[0] is None
    assert decide_variant({"single": 3}, 0.8)[0] is None  # too few hits to conclude anything


def test_replace_span_keeps_the_runs_and_refuses_structure(tmp_path):
    doc = Docx(synth_article(tmp_path / "a.docx"))
    p = list(doc.document.iter(q("p")))[4]
    text = para_text(p)
    at = text.index("12-14")
    replace_span(p, at + 2, at + 3, "–")
    replace_span(p, text.index("analyzed"), text.index("analyzed") + 8, "analysed")
    assert para_text(p) == text.replace("12-14", "12–14").replace("analyzed", "analysed")
    assert [para_text(p)[a:b] for a, b in italic_spans(p)] == ["The Organization of Labor"]


@pytest.fixture
def run(tmp_path):
    article = synth_article(tmp_path / "draft.docx")
    prof = tmp_path / "journal.yml"
    profile(synth_samples(tmp_path / "samples"), prof, "Synthetic Review", echo=QUIET)
    return article, prof, tmp_path


def test_profile_counts_the_samples(run):
    _, prof, _ = run
    data = yaml.safe_load(prof.read_text(encoding="utf-8"))
    got = {k: v["decision"] for k, v in data["rules"].items()}
    assert got["quote-primary"] == "single" and got["quote-punct"] == "outside" and got["spelling-ize"] == "ise"
    assert got["spelling-british-american"] == "british" and got["dash"] == "spaced-en" and got["range-dash"] == "en-dash"
    assert got["latin-abbrev"] == "no-points" and got["ibid-form"] == "no-point" and got["date-order"] == "day-month-year"
    assert got["spelling-yse"] is None and got["page-abbrev"] is None  # too few hits: left for a person
    assert len(data["samples"]) == 3 and all(len(s["sha256"]) == 64 for s in data["samples"])
    assert data["rules"]["quote-primary"]["examples"]["single"]
    with pytest.raises(SystemExit):  # a profile may hold decisions made by hand; never written over
        profile([tmp for tmp in (run[2] / "samples").iterdir()], prof, "Synthetic Review", echo=QUIET)


def test_check_finds_what_differs_and_spares_quoted_matter(run):
    article, prof, tmp = run
    folder = check(article, prof, tmp / "out", rid="c1", echo=QUIET)
    rows = read_review(folder / "review.csv")
    got = {(r["finding_id"].split("-")[0], r["rule"], r["match"], r["proposed"]) for r in rows}
    for expected in [("b1", "spelling-ize", "organized", "organised"), ("b2", "spelling-british-american", "color", "colour"),
                     ("b2", "dash", "—", " – "), ("b2", "century", "17th century", "seventeenth century"),
                     ("b3", "date-order", "March 12, 1651", "12 March 1651"), ("b3", "percent", "percent", "per cent"),
                     ("b4", "range-dash", "12-14", "12–14"), ("b4", "latin-abbrev", "e.g.", "eg"),
                     ("b6", "quote-primary", "“a civilized honor”", "‘a civilized honor’"), ("n1.0", "range-dash", "88-89", "88–89")]:
        assert expected in got
    matches = [(r["finding_id"].split("-")[0], r["match"]) for r in rows if r["rule"].startswith("spelling")]
    assert ("b4", "Organization") not in matches   # an italic title
    assert ("b6", "civilized") not in matches      # inside a quotation
    assert not any(k in ("b5", "b8") for k, _ in matches)  # the block quotation and the bibliography
    assert not any(k.startswith("n") for k, _ in matches)  # notes hold titles; spelling is not touched there
    params = json.loads((folder / "run.json").read_text())["params"]
    assert params["skipped_inside_quotation_or_italics"] == {"spelling-ize": 2, "spelling-british-american": 2}
    assert {r["status"] for r in rows if r["rule"] == "quote-punct"} == {"flag"}
    assert "organised" in report(folder, echo=QUIET).read_text(encoding="utf-8")


def test_apply_writes_only_accepted_rows_to_a_copy(run):
    article, prof, tmp = run
    sha = hashlib.sha256(article.read_bytes()).hexdigest()
    folder = check(article, prof, tmp / "out", rid="c1", echo=QUIET)
    assert decide(folder, "tester", True, ["spelling-ize", "range-dash", "quote-primary"], [], echo=QUIET) == 8
    decide(folder, "tester", False, ["dash"], [], echo=QUIET)
    out = apply(article, folder, tmp / "out", rid="a1", echo=QUIET)
    assert hashlib.sha256(article.read_bytes()).hexdigest() == sha
    before, after = Docx(article).text().split("\n"), Docx(out).text().split("\n")
    assert after[1] == before[1].replace("“", "‘").replace("”", "’").replace("organized", "organised")
    assert after[2] == before[2]  # the dash was rejected; colour and century were never decided
    assert after[3] == before[3].replace("“sovereign’s ‘right of nature’”", "‘sovereign’s “right of nature”’")
    assert after[5] == before[5] and after[8] == before[8]
    assert after[-4].endswith("pp. 88–89.") and "‘The Organization of Liberty,’" in after[-2] and "123–124" in after[-2]
    manifest = json.loads((out.parent / "run.json").read_text())
    assert len(manifest["params"]["applied"]) == 8 and manifest["params"]["refused"] == []
    rows = {r["finding_id"]: r for r in read_review(folder / "review.csv")}
    assert rows["b1-spelling-ize-84"]["decided_by"] == "tester" and rows["b2-dash-53"]["status"] == "rejected"
    other = synth_article(tmp / "other.docx")
    doc = Docx(other)
    next(doc.document.iter(q("t"))).text = "Another Draft"
    doc.touch()
    changed = doc.save(tmp / "changed.docx")
    with pytest.raises(SystemExit, match="not the file"):
        apply(changed, folder, tmp / "out", rid="a2", echo=QUIET)


def test_word_check_names_what_a_restyle_added():
    original = "Invented Author, A Made-Up Treatise, ed. Sample Editor (Exampletown: Sample University Press, 1996), pp. 88-89."
    assert word_check(original, "Invented Author, A Made-Up Treatise (Sample Editor ed, Sample University Press 1996) 88–9.", set(), 1) == ""
    assert "NOT IN THE ARTICLE'S NOTES: oxford" in word_check(original, "Invented Author, A Made-Up Treatise (Oxford 1996) 88–9.", set(), 1)
    assert "a range in the note is not a range" in word_check("J 12 (2001): 123-124.", "(2001) 12 J 123, 124.", set(), 3)
    assert word_check("Ibid., p. 90.", "Author (n 1) 90.", {"author"}, 2) == "taken from earlier notes: author"
    assert "not earlier" in word_check("Ibid.", "Author (n 5).", {"author"}, 2)
    old, new = "Ibid., p. 90.", "ibid 90."
    assert apply_edits(old, diff_edits(old, new)) == new


def test_citation_pass_is_a_proposal_with_provenance(run, monkeypatch):
    article, prof, tmp = run
    data = yaml.safe_load(prof.read_text(encoding="utf-8"))
    data["citations"]["from_model"] = {"rules_as_described_by_the_model": ["ibid in lower case, no point"],
                                       "examples": [{"kind": "ibid", "text": "ibid 127.", "verbatim_in_samples": True},
                                                    {"kind": "book-first", "text": "made up", "verbatim_in_samples": False}]}
    prof2 = tmp / "journal-c.yml"
    prof2.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    seen = {}

    def fake_chat(**kw):
        seen.update(kw)
        return {"parsed": {"notes": [{"n": 1, "text": "Invented Author, A Made-Up Treatise (Oxford 1996) 88–9."}, {"n": 2, "text": "ibid 90."},
                                     {"n": 3, "text": "Fictional Writer, “The Organization of Liberty,” Journal of Examples 12 (2001): 123-124."}]},
                "model": "test/model", "key": "k" * 64, "cost_usd": 0.0, "cached": False}

    monkeypatch.setattr(openrouter, "chat", fake_chat)
    folder = check(article, prof2, tmp / "out", with_citations=True, rid="c2", echo=QUIET)
    assert "made up" not in seen["user_text"] and "ibid 127." in seen["user_text"]  # only examples found in the samples are shown
    assert "[4] Ibid." in seen["user_text"]  # every note is sent, whole
    rows = {r["note"]: r for r in read_review(folder / "review.csv") if r["rule"] == "citation-form"}
    assert set(rows) == {"1", "2", "4"}  # note 3 came back unchanged; note 4 got no reply
    assert rows["1"]["status"] == "proposed" and "NOT IN THE ARTICLE'S NOTES: oxford" in rows["1"]["flag"]
    assert rows["2"]["proposed"] == "ibid 90." and rows["2"]["model"] == "test/model" and len(rows["2"]["prompt_sha256"]) == 64
    assert rows["4"]["status"] == "flag" and "no text for this note" in rows["4"]["flag"]
    decide(folder, "tester", True, ["ibid-form"], ["n2.0-citation-form"], echo=QUIET)
    out = apply(article, folder, tmp / "out", rid="a3", echo=QUIET)
    assert Docx(out).text().split("\n")[-3] == "[2]  ibid 90."
    refused = json.loads((out.parent / "run.json").read_text())["params"]["refused"]
    assert [r["finding_id"] for r in refused] == ["n2.0-ibid-form-1"]  # the whole-note restyle was applied instead


def test_citation_pass_skips_without_a_key_or_examples(run, monkeypatch):
    article, prof, tmp = run
    said = []
    check(article, prof, tmp / "out", with_citations=True, rid="c3", echo=said.append)
    assert any("no verified example citations" in s for s in said)
    data = yaml.safe_load(prof.read_text(encoding="utf-8"))
    data["citations"]["from_model"] = {"examples": [{"kind": "ibid", "text": "ibid 127.", "verbatim_in_samples": True}]}
    prof2 = tmp / "p2.yml"
    prof2.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    def no_key(**kw):
        raise openrouter.MissingCredential("OPENROUTER_API_KEY is not set in .env")

    monkeypatch.setattr(openrouter, "chat", no_key)
    folder = check(article, prof2, tmp / "out", with_citations=True, rid="c4", echo=said.append)
    assert json.loads((folder / "run.json").read_text())["params"]["citations_pass"]["status"] == "skipped"
    assert not [r for r in read_review(folder / "review.csv") if r["rule"] == "citation-form"]

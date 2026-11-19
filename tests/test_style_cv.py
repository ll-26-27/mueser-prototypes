"""The CV commands on a synthetic CV: a new entry is its neighbour's XML with new text, and nothing else moves."""

import hashlib

import pytest
import yaml

from mueser.style.cv import cells, unit_text, units
from mueser.style.cv.check import check
from mueser.style.cv.extract import extract
from mueser.style.cv.render import render
from mueser.style.fixtures import synth_cv
from mueser.style.shared import pdf
from mueser.style.shared.docx import Docx, c14n, parse_markup, q, run_flags, run_of, segments, to_markup

QUIET = lambda *a, **k: None


def _setup(tmp_path):
    src = synth_cv(tmp_path / "cv.docx")
    yml = tmp_path / "cv.yml"
    extract(src, yml, echo=QUIET)
    return src, yml, yaml.safe_load(yml.read_text(encoding="utf-8"))


def _section(data, title):
    return next(s for s in data["sections"] if s["title"] == title)


def test_extract_reads_sections_rows_and_geometry(tmp_path):
    src, yml, data = _setup(tmp_path)
    assert [s["title"] for s in data["sections"]] == ["Ada Synthetic", "Education", "Publications", "TALKS"]
    assert [len(s["entries"]) for s in data["sections"]] == [1, 3, 3, 3]
    assert _section(data, "Education")["entries"][0]["kind"] == "row"
    assert _section(data, "Publications")["entries"][0]["text"] == "2023\t“A Synthetic Article,” *Journal of Examples* 12 (2023): 1–20."
    assert "left=720 hanging=720 tabs=720L,9000R" in _section(data, "Publications")["entries"][0]["fingerprint"]
    assert data["document"]["page_mm"] == {"width": 215.9, "height": 279.4}
    with pytest.raises(FileExistsError):  # a cv.yml may hold entries added by hand; never written over
        extract(src, yml, echo=QUIET)


def test_markup_round_trips():
    for s in ["2024\tplain *italic* **bold** ***both*** end", "a \\* star and a \\\\ slash", "line\nbreak"]:
        doc_runs = parse_markup(s)
        assert "".join(t for t, _, _ in doc_runs)  # parsed to something
    assert parse_markup("a *b* **c**") == [("a ", False, False), ("b", False, True), (" ", False, False), ("c", True, False)]


def test_render_clones_the_neighbour_and_leaves_the_rest_identical(tmp_path):
    src, yml, data = _setup(tmp_path)
    before_bytes = hashlib.sha256(src.read_bytes()).hexdigest()
    _section(data, "Education")["entries"].insert(0, {"text": "2026\tDLitt, Invented Studies, *Example Academy*"})
    pubs = _section(data, "Publications")["entries"]
    pubs.insert(1, {"text": "2022\t“An Added Article,” *Journal of Examples* 11 (2022): 5–9."})
    pubs[0]["text"] = pubs[0]["text"].replace("1–20", "1–22")  # reword an existing entry
    _section(data, "TALKS")["entries"].append({"text": "2019\t“Talk Zero,” *Example Society*"})
    _section(data, "Education")["entries"].append({"text": "too\tmany\tcells"})  # refused: the row has two cells
    data["sections"].append({"title": "Awards", "source_index": None, "entries": [{"text": "2025\tA prize"}]})  # refused: no sibling
    yml.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    out = render(yml, src, tmp_path / "out", echo=QUIET)
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before_bytes  # the source is never written to
    source_units, new_units = units(Docx(src)), units(Docx(out))
    texts = [unit_text(u) for u in new_units]
    assert len(new_units) == len(source_units) + 4  # three entries and one copied blank paragraph

    # the table row went in first, with the neighbour's cell properties
    edu = texts.index("2026\tDLitt, Invented Studies, Example Academy")
    assert texts[edu + 1].startswith("2015\t")
    assert [c14n(tc.find(q("tcPr"))) for tc in cells(new_units[edu]["el"])] == [c14n(tc.find(q("tcPr"))) for tc in cells(new_units[edu + 1]["el"])]

    # the publication sits between 2023 and 2021 with the 2023 entry's paragraph properties, italics where marked
    pub = texts.index("2022\t“An Added Article,” Journal of Examples 11 (2022): 5–9.")
    assert texts[pub - 1].startswith("2023\t") and texts[pub - 1].endswith("1–22.") and texts[pub + 1].startswith("2021\t")
    assert c14n(new_units[pub]["el"].find(q("pPr"))) == c14n(source_units[7]["el"].find(q("pPr")))
    italic = [t for node, kind, t in segments(new_units[pub]["el"]) if kind == "t" and run_flags(run_of(node))[1]]
    assert italic == ["Journal of Examples"]
    fonts = {r.find(q("rPr")).find(q("rFonts")).get(q("ascii")) for r in new_units[pub]["el"].iter(q("r"))}
    assert fonts == {"Garamond"}

    # the talk follows the last talk's blank paragraph, and brings a blank paragraph of its own
    talk = texts.index("2019\t“Talk Zero,” Example Society")
    assert texts[talk - 2].startswith("2020\t") and texts[talk - 1] == "" and texts[talk + 1] == ""

    report = (out.parent / "report.txt").read_text(encoding="utf-8")
    assert "added     3" in report and "reworded  1" in report and "refused   2" in report
    assert "this row has 2 cells" in report and "no existing entry to copy the format from" in report
    # every unit that was not reworded reads exactly as before
    kept = [unit_text(u) for i, u in enumerate(source_units) if i != 7]
    assert [t for t in texts if t in kept or t == ""].count("") >= 3 and all(k in texts for k in kept)


def test_render_refuses_a_data_file_from_another_document(tmp_path):
    src, yml, _ = _setup(tmp_path)
    other = tmp_path / "other.docx"
    doc = Docx(src)
    next(doc.document.iter(q("t"))).text = "Someone Else"
    doc.touch()
    doc.save(other)
    with pytest.raises(SystemExit, match="different file"):
        render(yml, other, tmp_path / "out", echo=QUIET)


def test_to_markup_matches_what_extract_wrote(tmp_path):
    src, _, data = _setup(tmp_path)
    us = units(Docx(src))
    assert to_markup(us[7]["el"]) == _section(data, "Publications")["entries"][0]["text"]


def test_check_says_so_when_libreoffice_is_absent(tmp_path, monkeypatch):
    src, _, _ = _setup(tmp_path)
    monkeypatch.setattr(pdf, "soffice", lambda: None)
    said = []
    assert check(src, src, echo=said.append) == 0
    assert "LibreOffice is not installed" in said[0]

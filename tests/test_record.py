from pathlib import Path

from mueser.shared.record import Record, Source, parse_edtf_years, read_csv, read_jsonl, validate_against_schema, write_csv, write_jsonl


def make():
    return Record.new(type="place", surface_form="Breßlau", normalized="Breslau",
                      source=Source(doc_id="d", page_id="p001", line_index=3, transcription_backend="tesseract/frak2021"),
                      date_start="1786~")


def test_edtf_years():
    assert parse_edtf_years("1743") == (1743, 1743)
    assert parse_edtf_years("1743-05-02") == (1743, 1743)
    assert parse_edtf_years("1743~") == (1743, 1743)
    assert parse_edtf_years("174X") == (1740, 1749)
    assert parse_edtf_years("17XX") == (1700, 1799)
    assert parse_edtf_years("1743/1745") == (1743, 1745)
    assert parse_edtf_years("[1743,1745]") == (1743, 1745)
    assert parse_edtf_years("..1745") == (None, 1745)
    assert parse_edtf_years("garbage") == (None, None)


def test_record_derives_years_and_validates():
    r = make()
    assert r.year_start == 1786 and r.year_end == 1786
    assert len(r.id) == 16
    validate_against_schema(r)


def test_id_is_stable():
    assert make().id == make().id


def test_roundtrip_jsonl_and_csv(tmp_path: Path):
    r = make()
    r.source.bbox = [1, 2, 3, 4]
    write_jsonl([r], tmp_path / "r.jsonl")
    write_csv([r], tmp_path / "r.csv")
    assert read_jsonl(tmp_path / "r.jsonl")[0] == r
    back = read_csv(tmp_path / "r.csv")[0]
    assert back == r

from pathlib import Path

from mueser.text.backends.base import Line, PageResult
from mueser.text.formats import from_page_xml, to_page_xml


def test_page_xml_roundtrip(tmp_path: Path):
    res = PageResult(page_id="p001", lines=[Line("Erſte Zeile", bbox=[10, 20, 300, 40], confidence=0.9), Line("Zweite", bbox=None)],
                     raw={}, backend="test", model="m")
    xml = to_page_xml(res, "p001.png", 1000, 1500)
    p = tmp_path / "p001.xml"
    p.write_text(xml, encoding="utf-8")
    lines = from_page_xml(p)
    assert [l.text for l in lines] == ["Erſte Zeile", "Zweite"]
    assert lines[0].bbox == [10.0, 20.0, 300.0, 40.0]
    assert lines[1].bbox is None

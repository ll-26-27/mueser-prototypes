from mueser.maps.gazetteer.base import Candidate, name_similarity
from mueser.maps.reconcile import decide


def c(source, score, label="X", lat=51.0, lon=17.0, uri=None):
    return Candidate(uri=uri or f"{source}:{label}", label=label, lat=lat, lon=lon, source=source, score=score)


def test_auto_accept_clear_winner():
    d = decide("Breslau", [c("gov", 1.0, "Breslau"), c("wikidata", 0.6, "Breslau (ship)")])
    assert d.status == "auto" and d.chosen.source == "gov"


def test_unresolved_when_close():
    d = decide("Neustadt", [c("gov", 1.0, "Neustadt", lat=49.0), c("gov", 1.0, "Neustadt", lat=53.0, uri="gov:2")])
    assert d.status == "unresolved"


def test_agreeing_sources_accept():
    d = decide("Breslau", [c("gov", 1.0, "Breslau"), c("wikidata", 1.0, "Wrocław", lat=51.01, lon=17.01)])
    assert d.status == "auto"


def test_manual_choice_wins():
    cands = [c("gov", 0.5, "A"), c("wikidata", 0.5, "B")]
    d = decide("Neustadt", cands, manual={"Neustadt": "wikidata:B"})
    assert d.status == "reviewed" and d.chosen.label == "B"


def test_name_similarity():
    assert name_similarity("Breßlau", "Bresslau") == 1.0
    assert name_similarity("Königsberg", "Konigsberg") == 1.0
    assert 0.7 < name_similarity("Breslau", "Breslaw") < 1.0

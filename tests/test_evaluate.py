from mueser.text.evaluate import char_diff, levenshtein, normalize, score


def test_levenshtein():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3


def test_cer_raw_vs_normalised():
    gt = "Die Verfaſſung der Stadt\nBreßlau im Jahre 1786."
    hyp = "Die Verfassung der Stadt\nBreßlau im Jahre 1786."
    s = score(gt, hyp)
    assert s.cer > 0           # raw: ſ→s counts
    assert s.cer_norm == 0.0   # normalised: identical
    assert s.gt_lines == 2 and s.hyp_lines == 2


def test_normalize_joins_hyphenation():
    assert normalize("Ver-\nzeichnis") == "Verzeichnis"


def test_char_diff_tags():
    tags = {t for t, _ in char_diff("abc", "abd")}
    assert tags == {"equal", "delete", "insert"}

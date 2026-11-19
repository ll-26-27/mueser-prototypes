"""House-style conventions as rules that can be counted in a journal's articles and looked for in a draft.

Each rule finds every place a convention shows itself and names the variant used there. Counting the
variants over sample articles gives the journal's practice; a draft's hits in any other variant are the
findings. A rule proposes an edit only where the change is mechanical. Where it depends on meaning
(whether a comma belongs to a quotation, whether a list wants a serial comma) it flags and proposes nothing.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

Edit = tuple[int, int, str]


@dataclass
class Hit:
    variant: str
    start: int
    end: int
    note: str = ""
    data: dict = field(default_factory=dict)


@dataclass
class Rule:
    id: str
    title: str
    variants: tuple[str, ...]
    find: Callable[[str], list[Hit]]
    convert: Callable[[str, Hit, str], list[Edit] | None] | None = None  # None: flag only
    scope: str = "all"      # "body": not in notes or bibliography, where titles are quoted matter
    protect: bool = True    # skip hits inside quotations and italics


def _case_like(src: str, new: str) -> str:
    if src.isupper() and len(src) > 1:
        return new.upper()
    return new[:1].upper() + new[1:] if src[:1].isupper() else new


# -- quotation marks -----------------------------------------------------------------------------

OPENERS = set(" \t\n([{—–-/“‘")


def quote_spans(text: str) -> list[dict]:
    """Curly-quote spans: {kind, open, close, depth}. An apostrophe is a ’ followed by a letter, or one with
    no single quotation open. A plural possessive inside single quotes can close a span early; the
    finding says so when more than one ’ could be the closing mark."""
    spans, stack = [], []
    for i, ch in enumerate(text):
        if ch == "“":
            stack.append(("double", i))
        elif ch == "”" and stack and stack[-1][0] == "double":
            kind, start = stack.pop()
            spans.append({"kind": kind, "open": start, "close": i, "depth": len(stack)})
        elif ch == "‘" and (i == 0 or text[i - 1] in OPENERS):
            stack.append(("single", i))
        elif ch == "’" and stack and stack[-1][0] == "single" and not (i + 1 < len(text) and text[i + 1].isalnum()):
            kind, start = stack.pop()
            spans.append({"kind": kind, "open": start, "close": i, "depth": len(stack)})
    return sorted(spans, key=lambda s: s["open"])


def protected_spans(text: str) -> list[tuple[int, int]]:
    return [(s["open"], s["close"] + 1) for s in quote_spans(text) if s["depth"] == 0]


def _find_quotes(text: str) -> list[Hit]:
    spans = quote_spans(text)
    hits = []
    for s in (x for x in spans if x["depth"] == 0):
        inner = [x for x in spans if s["open"] < x["open"] and x["close"] < s["close"]]
        closers = sum(1 for i in range(s["open"] + 1, s["close"] + 1) if text[i] == "’"
                      and not (i + 1 < len(text) and text[i + 1].isalnum())) if s["kind"] == "single" else 1
        hits.append(Hit(s["kind"], s["open"], s["close"] + 1,
                        note="check where this quotation ends: an apostrophe after a plural can look like the closing mark" if closers > 1 else "",
                        data={"marks": [s] + inner}))
    return hits


SWAP = {("double", "open"): "‘", ("double", "close"): "’", ("single", "open"): "“", ("single", "close"): "”"}


def _convert_quotes(text: str, hit: Hit, target: str) -> list[Edit] | None:
    if hit.variant == target:
        return None
    edits = []
    for m in hit.data["marks"]:  # the outer marks become the target's; every mark nested inside alternates
        edits.append((m["open"], m["open"] + 1, SWAP[(m["kind"], "open")]))
        edits.append((m["close"], m["close"] + 1, SWAP[(m["kind"], "close")]))
    return edits


def _find_quote_punct(text: str) -> list[Hit]:
    hits = []
    for s in (x for x in quote_spans(text) if x["depth"] == 0):
        c = s["close"]
        if c > 0 and text[c - 1] in ",.":
            hits.append(Hit("inside", c - 1, c + 1))
        elif c + 1 < len(text) and text[c + 1] in ",.":
            hits.append(Hit("outside", c, c + 2))
    return hits


# -- spelling ------------------------------------------------------------------------------------

IZE = re.compile(r"\b([A-Za-z]{3,}?)(i)([sz])(e|es|ed|ing|ation|ations|ational|able)\b")
ISE_ONLY = set(["advertise", "advise", "anise", "appraise", "apprise", "arise", "braise", "bruise", "chastise", "chemise", "circumcise", "comprise", "compromise", "concise", "cruise", "demise", "despise", "devise", "disfranchise", "disguise", "enfranchise", "enterprise", "excise", "exercise", "expertise", "franchise", "guise", "imprecise", "improvise", "incise", "liaise", "likewise", "louise", "malaise", "marquise", "merchandise", "mortise", "noise", "otherwise", "paradise", "poise", "porpoise", "practise", "praise", "precise", "premise", "promise", "raise", "reprise", "revise", "rise", "sunrise", "supervise", "surmise", "surprise", "televise", "tortoise", "treatise", "turquoise", "unwise", "uprise", "valise", "wise", "anywise", "clockwise", "otherwise"])
IZE_ONLY = set(["assize", "capsize", "downsize", "resize", "outsize"])


def _find_ize(text: str) -> list[Hit]:
    hits = []
    for m in IZE.finditer(text):
        stem = m.group(1).lower()
        if stem + "ise" in ISE_ONLY or stem + "ize" in IZE_ONLY:  # words with one spelling on both sides of the Atlantic
            continue
        hits.append(Hit("ize" if m.group(3).lower() == "z" else "ise", m.start(), m.end(), data={"at": m.start(3)}))
    return hits


def _convert_ize(text: str, hit: Hit, target: str) -> list[Edit]:
    at = hit.data["at"]
    new = "z" if target == "ize" else "s"
    return [(at, at + 1, new.upper() if text[at].isupper() else new)]


YSE = re.compile(r"\b(anal|paral|catal|hydrol|electrol)y([sz])(e|ed|ing)\b", re.IGNORECASE)


def _find_yse(text: str) -> list[Hit]:
    return [Hit("yze" if m.group(2).lower() == "z" else "yse", m.start(), m.end(), data={"at": m.start(2)}) for m in YSE.finditer(text)]


def _convert_yse(text: str, hit: Hit, target: str) -> list[Edit]:
    at = hit.data["at"]
    new = "z" if target == "yze" else "s"
    return [(at, at + 1, new.upper() if text[at].isupper() else new)]


OUR_STEMS = ["colo", "favo", "hono", "labo", "behavio", "neighbo", "humo", "rumo", "vigo", "endeavo", "harbo", "armo", "savo", "odo", "splendo", "valo", "cando", "rigo", "fervo", "demeano", "parlo", "tumo", "clamo", "flavo"]
OUR_SUFFIXES = ("", "s", "ed", "ing", "able", "ful", "less", "er", "ers", "hood", "ly", "ite", "ites")
PAIRS = """centre center|centres centers|centred centered|theatre theater|theatres theaters|fibre fiber|sceptre scepter|spectre specter
sombre somber|calibre caliber|meagre meager|defence defense|offence offense|pretence pretense|travelled traveled|travelling traveling
traveller traveler|travellers travelers|labelled labeled|labelling labeling|modelled modeled|modelling modeling|cancelled canceled
cancelling canceling|counsellor counselor|marvellous marvelous|fulfil fulfill|fulfilment fulfillment|skilful skillful|wilful willful
enrol enroll|enrolment enrollment|instalment installment|grey gray|sceptic skeptic|sceptics skeptics|sceptical skeptical
scepticism skepticism|catalogue catalog|plough plow|mould mold|programme program|programmes programs|ageing aging
acknowledgement acknowledgment|artefact artifact|artefacts artifacts|manoeuvre maneuver"""
BRITISH: dict[str, str] = {}
for _pair in PAIRS.replace("\n", "|").split("|"):
    _b, _a = _pair.split()
    BRITISH[_b] = _a
for _stem in OUR_STEMS:
    for _suf in OUR_SUFFIXES:
        BRITISH[_stem + "ur" + _suf] = _stem + "r" + _suf
AMERICAN = {a: b for b, a in BRITISH.items()}
BA = re.compile(r"\b(" + "|".join(sorted(set(BRITISH) | set(AMERICAN), key=len, reverse=True)) + r")\b", re.IGNORECASE)


def _find_ba(text: str) -> list[Hit]:
    return [Hit("british" if m.group(0).lower() in BRITISH else "american", m.start(), m.end()) for m in BA.finditer(text)]


def _convert_ba(text: str, hit: Hit, target: str) -> list[Edit] | None:
    word = text[hit.start:hit.end]
    other = (BRITISH if hit.variant == "british" else AMERICAN).get(word.lower())
    return [(hit.start, hit.end, _case_like(word, other))] if other else None


# -- punctuation ---------------------------------------------------------------------------------

SERIAL = re.compile(r"\b[^\W\d]+, [^\W\d]+(,?) (?:and|or) [^\W\d]+")
DASH = re.compile(r"(?<=[^\s\d–—-])(\s?[–—]\s?)(?=[^\s\d–—-])")
DASH_FORMS = {" – ": "spaced-en", "—": "closed-em", " — ": "spaced-em"}
DASH_TEXT = {v: k for k, v in DASH_FORMS.items()}
RANGE = re.compile(r"(?<![\d–-])(\d{1,4})([-–])(\d{1,4})(?![\d–-])")


def _find_serial(text: str) -> list[Hit]:
    return [Hit("with" if m.group(1) else "without", m.start(), m.end()) for m in SERIAL.finditer(text)]


def _find_dash(text: str) -> list[Hit]:
    return [Hit(DASH_FORMS[m.group(1)], m.start(1), m.end(1)) for m in DASH.finditer(text) if m.group(1) in DASH_FORMS]


def _convert_dash(text: str, hit: Hit, target: str) -> list[Edit]:
    return [(hit.start, hit.end, DASH_TEXT[target])]


def _find_range(text: str) -> list[Hit]:
    return [Hit("en-dash" if m.group(2) == "–" else "hyphen", m.start(), m.end(), data={"at": m.start(2)}) for m in RANGE.finditer(text)]


def _convert_range(text: str, hit: Hit, target: str) -> list[Edit]:
    return [(hit.data["at"], hit.data["at"] + 1, "–" if target == "en-dash" else "-")]


def _find_elision(text: str) -> list[Hit]:
    hits = []
    for m in RANGE.finditer(text):
        a, b = m.group(1), m.group(3)
        if len(a) < 3:
            continue
        if len(b) < len(a):
            hits.append(Hit("elided", m.start(), m.end()))
        elif len(b) == len(a) and a[0] == b[0] and int(b) > int(a):
            hits.append(Hit("full", m.start(), m.end()))
    return hits


# -- abbreviations, numbers, dates ---------------------------------------------------------------

PAGE = re.compile(r"\b(pp?)(\.?)(\s?)(?=\d)")
LATIN = re.compile(r"(?<![\w.])(e\.g\.|i\.e\.|cf\.|eg|ie|cf)(?=[,\s])")
LATIN_OTHER = {"e.g.": "eg", "i.e.": "ie", "cf.": "cf", "eg": "e.g.", "ie": "i.e.", "cf": "cf."}
IBID = re.compile(r"\b([Ii]bid)(\.?)")
PERCENT = re.compile(r"\b(per cent|percent)\b|(?<=\d)(\s?%)")
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DMY = re.compile(rf"\b(\d{{1,2}}) ({MONTHS}) (\d{{4}})\b")
MDY = re.compile(rf"\b({MONTHS}) (\d{{1,2}}), (\d{{4}})\b")
ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "twenty-first"]
CENT_WORDS = re.compile(r"\b(" + "|".join(sorted(ORDINALS, key=len, reverse=True)) + r")([ -])(centur(?:y|ies))\b", re.IGNORECASE)
CENT_NUM = re.compile(r"\b(\d{1,2})(st|nd|rd|th)([ -])(centur(?:y|ies))\b", re.IGNORECASE)


def _find_page(text: str) -> list[Hit]:
    return [Hit("with-point" if m.group(2) else "no-point", m.start(), m.end(), data={"p": m.group(1)})
            for m in PAGE.finditer(text) if m.group(2) or m.group(3)]


def _convert_page(text: str, hit: Hit, target: str) -> list[Edit]:
    return [(hit.start, hit.end, hit.data["p"] + (". " if target == "with-point" else " "))]


def _find_latin(text: str) -> list[Hit]:
    return [Hit("with-points" if "." in m.group(1) else "no-points", m.start(1), m.end(1)) for m in LATIN.finditer(text)]


def _convert_latin(text: str, hit: Hit, target: str) -> list[Edit]:
    return [(hit.start, hit.end, LATIN_OTHER[text[hit.start:hit.end]])]


def _find_ibid(text: str) -> list[Hit]:
    return [Hit("with-point" if m.group(2) else "no-point", m.start(), m.end()) for m in IBID.finditer(text)]


def _convert_ibid(text: str, hit: Hit, target: str) -> list[Edit] | None:
    if target == "with-point":
        return [(hit.end, hit.end, ".")]
    if not text[hit.end:].strip():
        hit.note = "this point also ends the note, so it was left"
        return None
    return [(hit.end - 1, hit.end, "")]


def _find_percent(text: str) -> list[Hit]:
    return [Hit("symbol", m.start(2), m.end(2)) if m.group(2) else Hit(m.group(1).lower(), m.start(1), m.end(1))
            for m in PERCENT.finditer(text)]


def _convert_percent(text: str, hit: Hit, target: str) -> list[Edit] | None:
    if "symbol" in (hit.variant, target):
        return None  # between a symbol and a word the number's form changes too
    return [(hit.start, hit.end, _case_like(text[hit.start:hit.end], target))]


def _find_date(text: str) -> list[Hit]:
    hits = [Hit("day-month-year", m.start(), m.end(), data={"d": m.group(1), "m": m.group(2), "y": m.group(3)}) for m in DMY.finditer(text)]
    hits += [Hit("month-day-year", m.start(), m.end(), note="check the comma after the year",
                 data={"d": m.group(2), "m": m.group(1), "y": m.group(3)}) for m in MDY.finditer(text)]
    return sorted(hits, key=lambda h: h.start)


def _convert_date(text: str, hit: Hit, target: str) -> list[Edit]:
    d = hit.data
    return [(hit.start, hit.end, f"{d['d']} {d['m']} {d['y']}" if target == "day-month-year" else f"{d['m']} {d['d']}, {d['y']}")]


def _suffix(n: int) -> str:
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _find_century(text: str) -> list[Hit]:
    hits = [Hit("words", m.start(), m.end(), data={"n": ORDINALS.index(m.group(1).lower()) + 1, "sep": m.group(2), "c": m.group(3),
                                                   "cap": m.group(1)[0].isupper()}) for m in CENT_WORDS.finditer(text)]
    hits += [Hit("numerals", m.start(), m.end(), data={"n": int(m.group(1)), "sep": m.group(3), "c": m.group(4), "cap": False})
             for m in CENT_NUM.finditer(text) if 1 <= int(m.group(1)) <= 21]
    return sorted(hits, key=lambda h: h.start)


def _convert_century(text: str, hit: Hit, target: str) -> list[Edit]:
    d = hit.data
    if target == "numerals":
        return [(hit.start, hit.end, f"{d['n']}{_suffix(d['n'])}{d['sep']}{d['c']}")]
    word = ORDINALS[d["n"] - 1]
    start_of_sentence = hit.start == 0 or text[max(0, hit.start - 2):hit.start] in (". ", "! ", "? ")
    return [(hit.start, hit.end, f"{word.capitalize() if start_of_sentence else word}{d['sep']}{d['c']}")]


RULES: list[Rule] = [
    Rule("quote-primary", "Quotation marks: double or single first", ("double", "single"), _find_quotes, _convert_quotes, protect=False),
    Rule("quote-punct", "Comma or full stop inside or outside the closing quotation mark", ("inside", "outside"), _find_quote_punct, None, protect=False),
    Rule("spelling-ize", "-ize or -ise", ("ize", "ise"), _find_ize, _convert_ize, scope="body"),
    Rule("spelling-yse", "analyse or analyze", ("yse", "yze"), _find_yse, _convert_yse, scope="body"),
    Rule("spelling-british-american", "British or American spelling (colour, centre, travelled …)", ("british", "american"), _find_ba, _convert_ba, scope="body"),
    Rule("serial-comma", "Comma before the last item of a list", ("with", "without"), _find_serial, None, scope="body"),
    Rule("dash", "Dash in a sentence: spaced en rule or closed em rule", ("spaced-en", "closed-em", "spaced-em"), _find_dash, _convert_dash, scope="body"),
    Rule("range-dash", "Number ranges: en rule or hyphen", ("en-dash", "hyphen"), _find_range, _convert_range),
    Rule("range-elision", "Number ranges: 123–4 or 123–124", ("elided", "full"), _find_elision, None),
    Rule("page-abbrev", "p. and pp. with or without the point", ("with-point", "no-point"), _find_page, _convert_page),
    Rule("latin-abbrev", "e.g., i.e., cf. with or without points", ("with-points", "no-points"), _find_latin, _convert_latin),
    Rule("ibid-form", "ibid with or without the point", ("with-point", "no-point"), _find_ibid, _convert_ibid, protect=False),
    Rule("percent", "per cent, percent or %", ("per cent", "percent", "symbol"), _find_percent, _convert_percent, scope="body"),
    Rule("date-order", "Dates: 12 March 1651 or March 12, 1651", ("day-month-year", "month-day-year"), _find_date, _convert_date, scope="body"),
    Rule("century", "Centuries in words or numerals", ("words", "numerals"), _find_century, _convert_century, scope="body"),
]
BY_ID = {r.id: r for r in RULES}

# -- how the samples cite: measured, never converted ----------------------------------------------

AUTHOR_DATE = re.compile(r"\((?:[A-Z][\w’'-]+(?: (?:and|&) [A-Z][\w’'-]+| et al\.)?),? \d{4}[a-z]?(?:[:,] ?(?:pp?\. ?)?\d+(?:[–-]\d+)?)?\)")
CROSS_REF = re.compile(r"\(n \d+\)|\bn\. \d+ above|\bsupra note \d+", re.IGNORECASE)


def citation_measures(text: str) -> dict[str, int]:
    return {"author_date_in_parentheses": len(AUTHOR_DATE.findall(text)), "ibid": len(IBID.findall(text)),
            "cross_references_to_earlier_notes": len(CROSS_REF.findall(text))}

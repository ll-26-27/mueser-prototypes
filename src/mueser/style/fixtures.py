"""Synthetic documents for tests and demonstrations. Every person, title and journal in them is invented.

Results on these files show that the commands do what they say. They say nothing about how any real CV,
draft or journal will fare.
"""

from __future__ import annotations

from pathlib import Path

from .shared.mkdocx import TAB, para, table, write_docx

ENTRY = {"left": 720, "hanging": 720, "tabs": ((720, "left"), (9000, "right")), "font": "Garamond", "size": 22}


def synth_cv(path: Path) -> Path:
    def pub(year, title, journal, rest):
        return para([year, TAB, f"“{title},” ", (journal, "i"), rest], **ENTRY)

    def talk(year, text):
        return para([year, TAB, text], **ENTRY)

    def edu(year, degree, place):
        return [para(year, font="Garamond", size=22), para([degree + ", ", (place, "i")], font="Garamond", size=22)]

    blocks = [
        para([("Ada Synthetic", "b")], font="Garamond", size=32),
        para("Department of Examples · Example University · ada@example.org", font="Garamond", size=22),
        para("Education", style="Heading1"),
        table([edu("2015", "PhD, Political Theory", "University of Examples"),
               edu("2009", "MPhil, Intellectual History", "Example College"),
               edu("2007", "BA, History", "Sample University")], widths=(1440, 7920)),
        para("Publications", style="Heading1"),
        pub("2023", "A Synthetic Article", "Journal of Examples", " 12 (2023): 1–20."),
        pub("2021", "Another Invented Piece", "Review of Samples", " 8 (2021): 45–67."),
        pub("2019", "The First Fabricated Essay", "Journal of Examples", " 5 (2019): 101–130."),
        para("TALKS", font="Garamond", size=22),
        talk("2024", "“Talk One,” Example University"),
        para(),
        talk("2022", "“Talk Two,” Sample Institute"),
        para(),
        talk("2020", "“Talk Three,” Workshop on Placeholders"),
        para(),
    ]
    return write_docx(path, blocks)


def synth_article(path: Path) -> Path:
    """An invented draft in American spelling with Chicago-style notes, with one of each thing the rules look for."""
    blocks = [
        para("An Invented Draft", style="Heading1"),
        para(["The author wrote that “the condition of man is a condition of war,” and the critics organized their replies around it.", ("fn", 1)]),
        para(["The color of the argument changed in the 17th century—not gradually, but at once.", ("fn", 2)]),
        para("On March 12, 1651, roughly 40 percent of the pamphlets, sermons, and tracts took the “sovereign’s ‘right of nature’” as their theme."),
        para(["He analyzed ", ("The Organization of Labor", "i"), " and cited pp. 12-14, e.g., on labor.", ("fn", 3)]),
        para("“Organized color” stays as the source has it, because this paragraph is a block quotation.", style="Quote"),
        para(["She called it “a civilized honor” in passing.", ("fn", 4)]),
        para("Bibliography", style="Heading1"),
        para(["Author, Invented. ", ("A Made-Up Treatise", "i"), ". Exampletown: Sample University Press, 1996. On labor and color."]),
    ]
    notes = {
        1: [" Invented Author, ", ("A Made-Up Treatise", "i"), ", ed. Sample Editor (Exampletown: Sample University Press, 1996), pp. 88-89."],
        2: [" Ibid., p. 90."],
        3: [" Fictional Writer, “The Organization of Liberty,” ", ("Journal of Examples", "i"), " 12 (2001): 123-124."],
        4: [" Ibid."],
    }
    return write_docx(path, blocks, footnotes=notes)


SAMPLE = """{title}

The {noun} of the argument was set in the seventeenth century – not gradually, but at once. Writers of the eighteenth century
organised their replies around what one of them called ‘the condition of man’, and a later critic spoke of ‘a civilised honour’.
On {day} March 1651 roughly {pc} per cent of the pamphlets, sermons and tracts took the theme up, eg in the centre of the debate.
The colour of the reply mattered; its authors recognised the labour involved, analysed the sources and emphasised the defence.
A second group – smaller, and later – travelled to the theatre of the dispute and favoured what they called ‘the neighbour’s claim’.
By {day2} June 1660 another {pc2} per cent had, ie on the same grounds, realised the point and apologised for the behaviour of the first.
Compare the treatment of ‘sovereignty’, ‘liberty’ and ‘right’, cf the earlier account, and the programme set out at the start.

Notes
1 Invented Author, A Made-Up Treatise (Sample Editor ed, Sample University Press 1996) {a}–{b}.
2 ibid {c}.
3 Fictional Writer, ‘The Organisation of Liberty’ (2001) 12 Journal of Examples 123, 130–34.
4 Author (n 1) 201–9; see eg Writer (n 3) 125–6.
5 ibid 127.
6 Another Person, ‘A Further Invented Title’ in Sample Editor (ed), A Collection of Examples (Sample University Press 2010) 310–45.
"""


def synth_samples(folder: Path) -> list[Path]:
    """Three invented 'published articles' in one house style (British spelling, single quotation marks, notes without points)."""
    folder.mkdir(parents=True, exist_ok=True)
    variants = [("First Invented Article", "colour", 12, 40, 3, 15, "88", "9", "90"),
                ("Second Invented Article", "flavour", 14, 35, 7, 22, "101", "4", "112"),
                ("Third Invented Article", "vigour", 21, 60, 9, 31, "210", "15", "214")]
    out = []
    for i, (title, noun, day, pc, day2, pc2, a, b, c) in enumerate(variants, 1):
        p = folder / f"synth-journal-sample-{i}.txt"
        p.write_text(SAMPLE.format(title=title, noun=noun, day=day, pc=pc, day2=day2, pc2=pc2, a=a, b=b, c=c), encoding="utf-8")
        out.append(p)
    return out

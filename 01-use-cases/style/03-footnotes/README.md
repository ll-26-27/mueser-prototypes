# Footnotes and bibliography, checked

*Scoped, not yet built.* [`HANDOFF.md`](HANDOFF.md) is the brief.

What it will do: pull every footnote and every bibliography entry out of
a book-length manuscript, then run nine named rules over them: gaps in
numbering, ibid. after a note that cites something else, hyphens where
the style wants en dashes, missing or doubled terminal punctuation, mixed
quotation marks, short-form notes with no matching entry, first
citations that are not in full form, entries never cited, and one work
cited under different titles or years. The report lists every finding
with the note's text, its chapter, the rule and a proposed fix. Where a
short form could match more than one entry, a model may be asked which,
and its answer is a proposal in `review.csv` until you decide. Only
decided rows are applied, to a copy, with a diff.

Commands, once built, from the repository root:

```sh
uv run python -m mueser.style book extract <manuscript.docx> --out 01-use-cases/style/03-footnotes/outputs/out/<run>/work/
uv run python -m mueser.style book check   --work 01-use-cases/style/03-footnotes/outputs/out/<run>/work/ --config 01-use-cases/style/03-footnotes/inputs/config/book.yml [--model]
uv run python -m mueser.style book report  --work … --out 01-use-cases/style/03-footnotes/outputs/out/<run>/report.html
uv run python -m mueser.style book apply   --source <manuscript.docx> --decisions …/review.csv --out 01-use-cases/style/03-footnotes/outputs/out/<run2>/
```

What you supply: one manuscript or chapter as `.docx` (or `main.tex` with
its `.bib`) in `inputs/book/` (not committed; see
[`inputs/README.md`](inputs/README.md)); the citation style and its
conventions (`S.` or `p.`, German or English quotation marks); and, if
you use Zotero, an export of your library, which makes the matching much
stronger.

## Your question, answered

You asked what context to give when you ask Claude to make the footnotes
consistent with the OUP law style and to see what is missing from the
bibliography, and whether to tell it to ask you rather than guess what a
note like *Woods 2006* refers to. Yes to the second, and here is the first,
in the order that matters most.

1. **The style as rules, not as a name.** OUP's law list uses OSCOLA
   (*Oxford University Standard for Citation of Legal Authorities*, 4th
   edition, 2012) unless your editor's guidelines say otherwise; those
   guidelines settle it. Give the actual rules for the kinds of source you
   cite (books, chapters, articles, cases, statutes, archival material), or
   the OSCOLA CSL file (`oscola.csl` in the Citation Style Language
   repository), and name the edition. "The OUP law style" leaves the model
   to supply the rules from memory, which is where variants creep in.
2. **Your bibliography, whole.** It is the list of things a note is allowed
   to resolve to. A Zotero export (CSL-JSON or Better BibTeX) is better still,
   because every entry is already parsed into author, title and year. No
   plugin is needed: it is one file, exported once.
3. **Ten footnotes you have already made right**, as the target form. A
   worked example of each kind of source is worth more than a page of
   description.
4. **The chapter whole**, never excerpts, so ibid. chains and first-citation
   rules can be checked in sequence.
5. **The rule for short forms, stated as a rule.** "Ask me if you are not
   sure" is weaker than it sounds, because a model asked that is usually
   sure. Better: *a short form may be expanded only when it matches exactly
   one bibliography entry by author and year (and title word, if one is
   given); otherwise list it as unresolved and change nothing.* Then
   *Woods 2006* with two Woods entries, or none, comes back to you as a
   question, and so does a note that cites something not in the
   bibliography, which is the "what is missing" you wanted anyway.
6. **The output you want: a list of proposed changes, not a rewritten
   chapter.** Note number, the text as it stands, the text as proposed, and
   the rule behind the change. You read that list, accept or strike, and
   only then is anything written. Nothing outside the notes and the
   bibliography is touched.

The same answer is built into this case. `check` resolves a short form only
to a single entry above a recorded threshold; a pair between the thresholds
goes to `review.csv` as a proposal, and a note that matches nothing is an
`unresolved` finding, never a guess. The model, when it is asked at all,
sees only candidate entries from your own bibliography. `report` is the
list in point 6, with a decision cell on every row, and `apply` writes only
the rows you decided, to a copy, with a diff. That last step is the check
you asked about, made into a command.

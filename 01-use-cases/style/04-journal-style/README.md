# An article brought to a journal's house style

Built 19 November 2026, from your request: give it a few recent articles
from the journal you are submitting to, and have your draft converted to
match.

It works in three steps. First it counts what the journal does, in the
journal's own articles. Then it lists every place your draft does
something else, each with the change it proposes. Then it writes the
changes you accepted, and only those, into a copy of your draft.

## The commands

From the repository root. Put the journal's articles in `inputs/samples/`
and your draft in `inputs/draft/` in this folder; neither is committed.

```sh
# 1. Count the journal's conventions in three or more of its articles (PDF, Word or text)
uv run python -m mueser.style journal profile 01-use-cases/style/04-journal-style/inputs/samples/*.pdf \
    --name "Journal Name" --citations

# 2. List where the draft departs from them (writes review.csv and report.html; changes nothing)
uv run python -m mueser.style journal check 01-use-cases/style/04-journal-style/inputs/draft/article.docx \
    --profile 01-use-cases/style/04-journal-style/inputs/config/journal-name.yml --citations

# 3. Decide, a rule at a time or a row at a time
uv run python -m mueser.style journal decide --run <the check's run folder> --rule spelling-ize --accept --who ben

# 4. Write the accepted rows into a copy
uv run python -m mueser.style journal apply --source <the same draft> --run <the check's run folder>
```

To try it on the synthetic files in `inputs/fixtures/`, run the scripts in
[`operations/`](operations/).

## Step 1: the profile

`journal profile` reads each sample whole and counts fifteen conventions:

| rule | what it counts | proposes a change |
|---|---|---|
| `quote-primary` | double or single quotation marks first | yes, with nested marks alternated |
| `quote-punct` | comma or full stop inside or outside the closing mark | no, flags |
| `spelling-ize` | -ize or -ise | yes |
| `spelling-yse` | analyse or analyze | yes |
| `spelling-british-american` | colour/color, centre/center, travelled/traveled: 360 word forms in all | yes |
| `serial-comma` | a comma before the last item of a list | no, flags |
| `dash` | spaced en rule, closed em rule or spaced em rule | yes |
| `range-dash` | en rule or hyphen in number ranges | yes |
| `range-elision` | 123–4 or 123–124 | no, flags |
| `page-abbrev` | p. and pp. with or without the point | yes |
| `latin-abbrev` | e.g., i.e., cf. with or without points | yes |
| `ibid-form` | ibid with or without the point | yes |
| `percent` | per cent, percent or % | between the two words |
| `date-order` | 12 March 1651 or March 12, 1651 | yes |
| `century` | seventeenth century or 17th century | yes |

The profile is a file you can read: `inputs/config/<journal>.yml`. For each
rule it gives the count of each variant, the count per sample, three
examples of each, and a `decision`. A decision is written only when one
variant has at least 80 per cent of at least five hits. Otherwise it is
left empty with the reason, and that rule is not checked until you fill it
in. You can overrule any decision by editing the file.

With `--citations`, a model (Gemini 3.8 Flash through OpenRouter) reads the
samples whole and returns the journal's citation conventions in its own
words, with example citations copied from the articles. Every example is
then searched for in the sample text. One that does not occur there word
for word is recorded as not found and is never used.

## Step 2: the review

`journal check` writes `review.csv` and `report.html` in a run folder
under `outputs/out/`. Every row has the place, the text as it stands, the
proposed text, the rule, and a status: `proposed`, or `flag` where the
tool points and proposes nothing.

What it leaves alone, so that your sources stay as their authors wrote
them:

- Spelling, dashes, dates, centuries and per cent are checked in the body
  only. Notes and the bibliography hold titles, which are quoted matter.
- In the body, a hit inside quotation marks or in italics is skipped and
  counted. The count is in the report.
- A paragraph in a block-quotation style is skipped whole.

With `--citations`, the model restyles the footnotes after the journal's
verified examples. All the notes are sent together, in order and whole,
because a shortened later citation depends on the notes before it. Each
restyled note is a `citation-form` row, and each is compared with your
original word by word:

- a word in the proposal that is in none of your notes is named on the
  row, in capitals, and those rows are listed first;
- a page range that is no longer a range is named;
- a cross-reference to a note that is not earlier is named;
- words taken from an earlier note (as a short form needs) are listed.

## Steps 3 and 4: decide, then apply

Nothing is applied until it is decided. `journal decide` records your
decision with your name and the time, on every proposal of a rule or on
single rows by id; you can also write `accepted` or `rejected` in the
status column of `review.csv` yourself. The report is rebuilt each time.

`journal apply` writes the accepted rows into a copy and a `diff.html`
showing each changed paragraph. A change is made inside the runs that
hold the text, so italics and other formatting around it stay. The copy is
then read back: every paragraph must read exactly as the original plus
the accepted changes, and every other paragraph exactly as before. If
not, no copy is kept. Where an accepted restyle of a whole note overlaps a
smaller accepted change in the same note, the restyle is applied and the
smaller one is reported as refused.

## What was run and checked

All on synthetic files (`inputs/fixtures/`): a short invented draft in
American spelling with four Chicago-style notes, and three invented
"journal articles" in a British, OSCOLA-like style. These show that the
commands do what they say. They are not evidence about any real journal
or draft.

- Profile: 12 of 15 rules decided; 3 left empty for too few hits. The
  committed example is `inputs/config/synth-synthetic-review.yml`.
- Citation examples: 13 returned, 13 found word for word in the samples.
  Cost $0.004.
- Check: 24 findings, of which 4 are restyled notes. Four spelling hits
  were left alone inside a quotation or an italic title. Cost of the
  restyle call, $0.001.
- Apply: 19 rows accepted, 16 written, 3 refused because the restyle of
  the whole note was applied in their place. The copy read back as
  expected, and the two italic titles in the notes were still italic.
- Eleven tests in `tests/test_style_journal.py`, none of which calls a
  model.

Two things the live runs showed:

- The model's first restyle of note 3 turned the article's page range
  `123-124` into `123, 124`, a first page and a pinpoint. A second run
  gave `123, 123–4`. The journal's examples do have that form, but your
  note gave no pinpoint. This is the kind of row to reject: the form is
  right and the content is the model's guess. The check for lost ranges
  was added because of the first of these; it does not catch the second.
- Left to itself the model spent 30,717 thinking tokens on four notes
  ($0.117). Thinking is now set low for both calls, which brought the same
  call to 162 output tokens.

Not yet run: on a real journal's PDFs, or on a real draft.

## Limits

- The profile reads a PDF as plain text. It cannot see italics, and it
  cannot tell an article's body from its notes, so spelling counts in the
  samples include titles in the notes. The examples in the profile show
  what was counted.
- A scanned PDF with no text layer is refused with a message.
- The rules read English. German or Latin passages in your body text are
  protected only if they are in italics or quotation marks.
- Straight quotation marks (`"`) are not handled; the rules work on
  curly marks.
- An apostrophe after a plural inside single quotation marks (the judges’)
  can be mistaken for the closing mark. Rows where that could have happened
  say so.
- A restyled note changes text only. If the journal italicises differently
  from your draft, that is yours to fix; the report cannot see it.
- A note of several paragraphs is flagged, not edited.
- Moving between footnote citations and author-date citations in the text
  is not attempted. The report gives the counts of each in the samples and
  in your draft so that you can see if that is the situation.
- A long manuscript's notes go to the model in one request. If that
  exceeds the model's limit the error is reported and no citation rows are
  written; run it a chapter at a time.

# Markdown — Intro & Cheatsheet

> **In one line:** Markdown lets you write formatted text using a few plain
> symbols. This page explains the idea for a total beginner, then gives you a
> one-screen reference for the symbols themselves.

## What Markdown is (start here)

You already know what a *formatted* document looks like: headings, **bold** words,
bullet lists, links. In Word or Google Docs you create that formatting by
**clicking buttons** in a toolbar.

Markdown is the same result with a different method: instead of clicking a button,
you **type a small symbol** and the text becomes formatted when it's displayed.

For example, you type this:

```
# Welcome
This is **important**.
- first point
- second point
```

…and when it's shown, it looks like:

> **Welcome** (as a large heading)
> This is **important**.
> • first point
> • second point

Three things that surprise beginners — and are the whole point:

1. **A Markdown file is just plain text.** It opens on any computer, in any era,
   and never gets corrupted. There is no hidden formatting.
2. **It's readable even without rendering.** Even before the symbols turn into
   formatting, `# Welcome` and `- first point` are perfectly understandable.
3. **You don't have to memorize it.** You can ask Claude to write Markdown for
   you. The goal of this page is just to help you *recognize* the symbols so
   `#` and `*` don't throw you.

This is why nearly everything Claude reads and writes — including every doc in
this glossary and your [CLAUDE.md](claude-md.md) file — is Markdown.

## The cheatsheet

Left column: what you **type**. Right column: what you **get**.

### Headings

| You type | You get |
|---|---|
| `# Heading 1` | Biggest heading |
| `## Heading 2` | Section heading |
| `### Heading 3` | Sub-section heading |

> Put a space after the `#`, and a blank line before the heading.

### Emphasis

| You type | You get |
|---|---|
| `**bold**` | **bold** |
| `*italic*` | *italic* |
| `***bold italic***` | ***bold italic*** |
| `~~strikethrough~~` | ~~strikethrough~~ |

### Lists

```
- Bullet item
- Another bullet
  - Indented sub-bullet (two spaces)

1. Numbered item
2. Next item
```

> For bullets you can use `-`, `*`, or `+` — pick one and stay consistent.
> For numbered lists the actual numbers don't matter; `1.` on every line still
> renders 1, 2, 3.

### Links and images

| You type | You get |
|---|---|
| `[Bok Center](https://bokcenter.harvard.edu)` | A clickable link → [Bok Center](https://bokcenter.harvard.edu) |
| `![Alt text](cat.png)` | An embedded image (the `!` is the only difference) |

### Code

Inline: wrap text in single backticks — `` `like this` `` renders as `like this`.

Block: fence it with three backticks. You can name the language for coloring:

````
```python
print("hello")
```
````

### Quotes and dividers

```
> This is a blockquote — good for callouts and notes.

---
```

A line of `---` on its own becomes a horizontal divider.

### Tables

```
| Term     | Meaning            |
|----------|--------------------|
| Markdown | Plain-text format  |
| Prompt   | What you send      |
```

The `|` separates columns; the `---` row marks the header. Spacing doesn't have
to be perfect — it just needs the pipes.

### Two everyday gotchas

- **Blank lines matter.** Put a blank line between paragraphs, before lists, and
  before headings, or things run together.
- **A single line break is usually ignored.** To force a new line within a
  paragraph, end the line with two spaces, or just leave a blank line.

## Why it matters in this workshop

Almost everything you create and read in [Claude Code](claude-code.md) is
Markdown. You won't write much of it by hand — but recognizing the symbols means
"oh, that's just formatting," not confusion.

## See also

- [Markdown](markdown.md) — the short glossary definition
- [CLAUDE.md](claude-md.md) · [SKILL.md](skill-md.md) — Markdown files you'll meet
- [Artifact](artifact.md) — other things Claude can produce

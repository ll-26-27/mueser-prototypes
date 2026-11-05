# CLAUDE.md

> **In one line:** `CLAUDE.md` is a plain-text notes file you keep in a project
> folder; Claude Code reads it first, so it starts every conversation already
> knowing the basics.

## In plain terms

Remember the *Memento* problem: each conversation is a fresh "day," and Claude only
knows what's written on the notes in front of it. `CLAUDE.md` is the note you leave
*for next time* — pinned to the front of the folder.

When [Claude Code](claude-code.md) opens a folder, it reads the `CLAUDE.md` there
before doing anything else. So instead of re-explaining your project every session,
you write it down once: what this folder is, who it's for, how you like things done,
what to avoid.

A teaching-materials example might say: "This folder is readings for a freshman
seminar. Keep summaries under 200 words. Don't change the `originals/` folder." From
then on, Claude starts every conversation already knowing that.

It's just a Markdown file (see the forthcoming *Markdown* entry) — readable text,
no code. You can open and edit it like any document.

## Why it matters in this workshop

It's [context engineering](context-engineering.md) made concrete and durable: the
standing part of the briefing, written once instead of retyped every time. This
repo itself has a `CLAUDE.md` — a real example to show participants.

## See also

- [Context](context.md) — why a "notes for next time" file is necessary
- [Context Engineering](context-engineering.md) — the practice this serves
- [SKILL.md](skill-md.md) — instructions for a *task*, vs. notes for a *project*
- [Claude Code](claude-code.md) — what reads this file

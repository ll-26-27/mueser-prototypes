# Compact

> **In one line:** Compact is a command (`/compact`) that squeezes a long
> conversation down to a summary and continues in a fresh thread — so a filling
> context window doesn't quietly degrade Claude's work.

## In plain terms

A conversation can only get so long before it hits the edge of the
[context window](context-window.md), and well before that, a cluttered window
starts to drag answers down ([context rot](context-rot.md)). **Compact** is the
deliberate version of the *Memento* "summarize the day" move: it crushes the
conversation so far into a summary and starts a new thread carrying that summary —
alongside the [system prompt](system-prompt.md) and [memory](memory.md), which are
always there.

The workshop's framing matters here: this is not magic. Compact is just a
[Markdown](markdown.md) instruction telling Claude *how* to summarize a long
conversation. Because it's only text, it can be customized — you can write your own
version that summarizes work the way your field or project actually needs.

It's a [slash command](skill-md.md): you type `/compact` mid-conversation rather
than waiting to run out of room. (Forking or branching a conversation is a related
escape hatch — covered later with Claude Code.)

## Why it matters in this workshop

It's the first concrete, you-can-type-this-now tool for managing the context story
instead of just understanding it — and the cleanest proof that even Claude's
"smart" features are, underneath, just text instructions.

## See also

- [Context Window](context-window.md) — the limit Compact works around
- [Context Rot](context-rot.md) — why you compact *before* you must
- [Memory](memory.md) — the other thing carried into the fresh thread
- [SKILL.md](skill-md.md) — how a command like this is just an editable instruction

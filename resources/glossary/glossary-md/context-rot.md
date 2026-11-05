# Context Rot

> **In one line:** Context rot is the way Claude's answers get worse when the
> [context window](context-window.md) fills up with stale, irrelevant, or
> contradictory material.

## In plain terms

More context is not always better. As a conversation gets long and cluttered —
abandoned tangents, an early draft you've since rejected, three contradictory sets
of instructions — Claude has a harder time telling what *currently* matters. The
quality of its answers can quietly degrade. That drift is **context rot**.

A desk analogy: a clear desk with the one document you need is better than a desk
buried under every draft from the past hour. The buried-desk state is context rot.

Signs you may be seeing it:

- Claude reverts to an instruction you already corrected.
- It blends two different tasks together.
- Replies get vaguer or more generic the longer you go.

The usual fixes are simple: start a fresh conversation for a new task, restate what
matters now, or remove the clutter rather than piling more on top.

## Why it matters in this workshop

It's the counter-intuitive half of [context engineering](context-engineering.md):
the goal isn't to give Claude *everything*, it's to give it the *right* things and
keep the rest out. Naming this failure mode helps participants diagnose "why did it
suddenly get worse?"

## See also

- [Context Window](context-window.md) — the space that fills up
- [Context](context.md) — what's in that space
- [Context Engineering](context-engineering.md) — preventing the rot on purpose

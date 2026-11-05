# Context Window

> **In one line:** The context window is the fixed amount of text Claude can hold in
> view at one time. When it's full, something has to give.

## In plain terms

[Context](context.md) is what Claude can see; the **context window** is *how much*
of it fits. It's measured in "tokens" (roughly, chunks of words), and the limit is
large but real — think of it as a very big, but finite, desk.

Continuing the *Memento* analogy: each conversation is one "day," and the context
window is how many notes can be spread across the desk at once for that day. Every
message you send and every reply Claude gives takes up some of the desk. Things that
go on the desk early — Claude's [memory](claude-md.md), the workshop's setup notes —
are there from the start; the rest fills up as you talk.

What this means in practice:

- Long conversations gradually fill the window. Very long ones can push earlier
  details out of view.
- Pasting in a huge document uses a lot of the window at once.
- A fuller window isn't automatically better — see [Context Rot](context-rot.md).

You don't need to count tokens. You just need the instinct: *space is limited, so
spend it on what matters.*

## Why it matters in this workshop

It's the reason [context engineering](context-engineering.md) is a skill and not an
afterthought. If the window were infinite, you could dump everything in; because
it's finite, *choosing* is the work.

## See also

- [Context](context.md) — what fills the window
- [Context Rot](context-rot.md) — why a full window can hurt
- [Context Engineering](context-engineering.md) — using the space well

# Prompt Chaining

> **In one line:** Prompt chaining is breaking one big request into a sequence of
> smaller prompts, where each step's output feeds into the next.

## In plain terms

Instead of asking Claude to do everything in a single prompt — "read this paper,
summarize it, pull the citations, draft a critique" — you stage it. Prompt 1 pulls
the citations; prompt 2 takes those and drafts the summary; prompt 3 takes the
summary and writes the critique. Each step is small, focused, and checkable.

An analogy: rather than handing a colleague a sprawling brief and hoping the end
product is right, you ask for an outline first, review it, then ask for the draft.
The intermediate steps give you visibility — and a place to course-correct — before
the final output is locked in.

This matters for two reasons:

- **Quality.** Smaller, well-scoped prompts produce sharper results than an
  all-in-one prompt that asks for too much at once.
- **Control.** You can inspect each step, fix what looks off, and re-run the chain
  without redoing everything.

You'll often do this informally inside a single chat ("good — now using that,
draft the…"), or formally in a recipe where each step is its own [prompt](prompt.md)
file. When Claude chains the steps *itself* — deciding what to do next based on
what just happened — you've crossed into [agent](agent.md) territory.

## Why it matters in this workshop

It's the bridge from one-off chats to repeatable workflows. The recipes you'll see
later are essentially prompt chains: a sequence of prompts assembled to produce a
specific kind of artifact reliably.

## See also

- [Prompt](prompt.md) — the building block being chained
- [Context](context.md) — each step's output enters the next step's context
- [Agent](agent.md) — when Claude chains the steps itself instead of you doing it
- [Agentic System](agentic-systems.md) — the bigger arrangement around chained work

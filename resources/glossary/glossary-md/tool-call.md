# Tool Call

> **In one line:** A tool call is when Claude, instead of just writing an answer,
> *does something* — runs code, reads a file, fetches a page — and uses the result.

## In plain terms

A plain [LLM](llm.md) only predicts text. That alone can't reliably multiply large
numbers or know what's in your folder. **Tool calls** are how Claude steps outside
pure text prediction: it can reach for a tool, get a real result, and continue with
that result in hand.

Two kinds you'll see early in the workshop:

1. **Doing something exactly** — e.g. writing and running a snippet of code to do
   arithmetic. The earlier multiplication failure disappears, because now it's
   *computing*, not *guessing*.
2. **Grounding in real material** — e.g. opening the actual reading or spreadsheet
   so the answer is based on *your* document, not a plausible-sounding average.

You usually don't invoke tools yourself; Claude decides a task needs one and you see
it happen ("reading file…", "running…"). The idea to hold onto: **Claude can act,
not just talk — and acting is what makes it accurate and grounded.**

This is also the foundation of an [agent](agent.md): an agent is largely Claude
choosing and chaining tool calls toward a goal. When *you* stage the steps instead
of Claude, the same idea shows up as [prompt chaining](prompt-chaining.md) — each
prompt can include the results of an earlier tool call.

## Why it matters in this workshop

Tools let Claude read source files and compute results you can inspect.
Check that it used the right inputs and that its code does what you intended.

## See also

- [LLM](llm.md) — what tools compensate for
- [Agent](agent.md) — tool calls chained toward a goal
- [Context](context.md) — tool results come back *into* context
- [Prompt Chaining](prompt-chaining.md) — staging tool results across steps

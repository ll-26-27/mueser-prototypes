# Context

> **In one line:** Context is everything Claude can "see" at this moment — your
> messages, its replies, any files or notes in front of it. Every answer is built
> only from this.

## In plain terms

Claude has no memory of you between conversations unless you give it one. Each reply
is generated *only* from what's currently in front of it. That "what's in front of
it" is the **context**.

The workshop's running analogy is the film *Memento*: the main character can't form
new long-term memories, so he survives by writing notes to himself. Each new
conversation with Claude is a fresh "day" for that character. It knows only what's
written on the notes you've handed it *so far*: your prompts, its own previous
replies in this conversation, plus things like its [memory](claude-md.md) and any
files you've shown it.

The practical consequences:

- If something isn't in the context, Claude doesn't know it — even if you told it
  yesterday, or it's "obvious."
- If something *unhelpful* is in the context, it can drag the answer down (see
  [Context Rot](context-rot.md)).
- So the highest-leverage skill is choosing what goes in — [Context
  Engineering](context-engineering.md).

## Why it matters in this workshop

Almost every "why did Claude do that?" moment traces back to context: something was
missing, or something junk was present. Get this idea and the rest of the workshop
clicks into place.

## See also

- [Context Window](context-window.md) — the limited space context lives in
- [Context Rot](context-rot.md) — what happens as it fills with clutter
- [Context Engineering](context-engineering.md) — deliberately curating it

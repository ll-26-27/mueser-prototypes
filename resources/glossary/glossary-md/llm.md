# Large Language Model (LLM)

> **In one line:** A large language model is the kind of system Claude is — at its
> core, it predicts the next bit of text, one piece at a time, based on patterns
> learned from an enormous amount of writing.

## In plain terms

"LLM" stands for **large language model**. Strip away the jargon and the core
mechanic is surprisingly humble: given the text so far, the model predicts what
[token](token.md) (roughly, the next chunk of a word) is most likely to come next —
then does it again, and again, building up a reply.

It learned those predictions from a vast amount of text — loosely, "the average of
the internet." That has two consequences worth feeling in your bones early:

- **It's astonishingly fluent**, because fluent text is what it learned to
  continue.
- **It can be confidently wrong**, because "what sounds likely" is not the same as
  "what is true." The classic demo: ask for a long multiplication and it often gets
  it wrong — not from stupidity, but because it's *predicting* an answer rather than
  *calculating* one. (Have it write and run code instead, and it's exact — a
  preview of why code matters in this series.)

This is why [context](context.md) is everything: a next-text predictor is only as
good as the text you put in front of it.

## Why it matters in this workshop

Understanding "it predicts, it doesn't look up or calculate" explains both Claude's
brilliance and its failure modes — and motivates everything we do with code and
context engineering to compensate.

## See also

- [Token](token.md) — the "chunks" it predicts
- [Context](context.md) — what its prediction is based on

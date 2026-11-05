# Hallucination

> **In one line:** A hallucination is when Claude states something false with
> complete confidence — fluent, plausible, and wrong — because it is predicting
> likely text, not looking facts up.

## In plain terms

Because a [large language model](llm.md) works by continuing patterns in
[text](token.md) rather than retrieving stored facts, it will sometimes produce an
answer that *sounds* right and *is* wrong — and it won't sound any less sure when it
does. The workshop showed two clean examples:

- **Big-number multiplication.** Ask it to multiply two seven-digit numbers and it
  gets the first few digits and the digit-count right, but the middle wrong — it's
  pattern-matching toward a plausible-looking number, not calculating.
- **The scene that doesn't exist.** Ask for a close reading of a passage that isn't
  real and it will confidently say so — or, given a slightly different prompt,
  confidently analyze something fabricated — until you paste in the actual text.

The fix in both cases is the same move: give it the right tool or the right
material. "Try it again with Python" turns the math right; supplying the real
passage turns the reading right. Hallucination isn't random noise — it's what
prediction looks like when the model is asked for something it can't pattern-match
its way to.

## Why it matters in this workshop

Match the operation to the task: use [code](tool-call.md) for arithmetic,
source text for quotation, and retrieved [context](context.md) for specific
factual claims. Save the result and the check so the next step can use both.

## See also

- [Large Language Model (LLM)](llm.md) — why it predicts instead of looking up
- [Context](context.md) — supplying the right material is the main fix
- [Tool Call](tool-call.md) — letting it use Python/search instead of guessing
- [Model](model.md) — stronger models hallucinate less, not never

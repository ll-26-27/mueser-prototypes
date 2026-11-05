# Token / Tokenization

> **In one line:** A token is a small chunk of text — often a word or part of a word
> — and tokenization is the act of slicing text into those chunks. It's the unit
> Claude actually reads and writes in.

## In plain terms

Claude doesn't process text letter by letter or exactly word by word. It breaks text
into **tokens**: pieces that are usually a short word or a fragment of a longer one.
"Teaching" might be one token; "Bok Center" might be three. Splitting text this way
is called **tokenization**.

Two reasons a beginner should care:

- **It explains some weird failures.** Because the model sees chunks, not letters,
  tasks like "count the r's in *strawberry*" or reversing a word can trip it up —
  it's not looking at letters the way you are.
- **It's the unit the [context window](context-window.md) is measured in.** When we
  say the window holds a large but finite amount, the count is in tokens. A rough
  feel: a token is about ¾ of a word, so a page of text is several hundred tokens.

You never have to count tokens yourself. The takeaway is just the mental model:
*Claude reads in chunks, and those chunks are what fill the limited window.*

## Why it matters in this workshop

It demystifies a class of "why can't it do something that simple?" moments, and it
gives [context window](context-window.md) and [context rot](context-rot.md) a
concrete unit instead of a hand-wave.

## See also

- [LLM](llm.md) — the predictor that works in tokens
- [Context Window](context-window.md) — measured in tokens

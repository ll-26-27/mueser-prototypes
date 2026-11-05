# Glossary — Index

**Purpose:** plain-language definitions of every term, concept, and tool that will be
new to workshop participants. Each entry is one short Markdown doc. Write for an
**absolute beginner**: introduce the term, define it in a sentence, give an analogy,
say why it matters here.

## How to use this

- Entries are grouped by concept below, but each is a standalone doc you can link to
  from the workshop materials.
- When a segment introduces a term for the first time, link to its glossary entry
  rather than re-explaining it.
- Every entry follows the same shape: a one-line definition callout, an **In plain
  terms** explanation with an analogy, **Why it matters in this workshop**, and
  **See also** cross-links.

## The basics — who and what

| Term | One-line gist |
|---|---|
| [Claude](claude.md) | The AI assistant you're talking to. |
| [Anthropic](anthropic.md) | The company that makes Claude. |
| [Claude Code](claude-code.md) | A version of Claude that can work with the files on your computer. |
| [Claude Cowork](claude-cowork.md) | Desktop-app mode where Claude reads and changes files in a folder. |
| [Project](project.md) | A saved workspace that bundles related chats and (in Cowork) a folder. |
| [Model (Opus / Sonnet / Haiku)](model.md) | Which version of Claude is doing the thinking — depth vs. speed. |
| [API](api.md) | Using Claude from software instead of a chat window (foreshadowing). |

## How Claude "thinks"

| Term | One-line gist |
|---|---|
| [Large Language Model (LLM)](llm.md) | What Claude is: a next-text predictor. |
| [Token / Tokenization](token.md) | The chunks of text Claude reads and writes in. |
| [Tool Call](tool-call.md) | When Claude *does* something (runs code, reads a file) instead of just talking. |
| [Hallucination](hallucination.md) | A confident, fluent answer that is simply wrong. |
| [Agent](agent.md) | Claude pursuing a goal over multiple steps. |
| [Agentic System](agentic-systems.md) | One or more agents organized to do work together — including subagents and pipelines. |
| [Harness](harness.md) | The program around Claude that runs the loop and its tools. |

## How Claude remembers (the context story)

Read these as a chain — each builds on the last.

| Term | One-line gist |
|---|---|
| [Context](context.md) | Everything Claude can "see" right now — the basis for every reply. |
| [Context Window](context-window.md) | The fixed amount of context Claude can hold at once. |
| [Context Rot](context-rot.md) | How answers degrade as the window fills with clutter. |
| [Context Engineering](context-engineering.md) | Deliberately choosing what goes into the context. |
| [Memory](memory.md) | Optional saved notes re-read at the start of new conversations. |
| [Compact](compact.md) | A command that summarizes a long chat so it can continue fresh. |

## Talking to Claude

| Term | One-line gist |
|---|---|
| [Prompt](prompt.md) | What you send to Claude. |
| [System Prompt](system-prompt.md) | Background instructions Claude has before you start typing. |
| [Prompt Chaining](prompt-chaining.md) | Breaking one big task into a sequence of smaller, staged prompts. |

## Files, formats, and outputs

| Term | One-line gist |
|---|---|
| [Markdown](markdown.md) | Plain text where simple symbols become formatting. |
| [Markdown — Intro & Cheatsheet](markdown-cheatsheet.md) | Beginner intro plus a one-screen syntax reference. |
| [HTML](html.md) | A web-page format Claude Code can output — visual structure and interaction, not just text. |
| [CLAUDE.md](claude-md.md) | A notes file Claude reads first, so it knows your project. |
| [SKILL.md](skill-md.md) | A reusable instruction packet for a specific task. |
| [Artifact](artifact.md) | A finished thing Claude produces — a doc, chart, or web page. |

## Using Claude safely at Harvard

| Term | One-line gist |
|---|---|
| [Data Classification](data-classification.md) | The temporary HUIT plan is a bridge — nothing above Harvard Level 2 until the Anthropic Enterprise agreement is in place. |

## Suggested teaching order

If introducing these in sequence rather than by lookup:

1. [Claude](claude.md) → [Anthropic](anthropic.md) → [Markdown](markdown.md)
2. [LLM](llm.md) → [Token](token.md) → [Hallucination](hallucination.md) →
   [Context](context.md) → [Context Window](context-window.md) →
   [Context Rot](context-rot.md) → [Compact](compact.md) →
   [Context Engineering](context-engineering.md)
3. [Prompt](prompt.md) → [System Prompt](system-prompt.md) →
   [Prompt Chaining](prompt-chaining.md) → [Memory](memory.md) →
   [Data Classification](data-classification.md)
4. [Artifact](artifact.md) → [HTML](html.md) → [Tool Call](tool-call.md) →
   [Claude Cowork](claude-cowork.md) → [Project](project.md) →
   [Claude Code](claude-code.md) → [CLAUDE.md](claude-md.md) →
   [SKILL.md](skill-md.md)
5. [Agent](agent.md) → [Agentic System](agentic-systems.md) →
   [Harness](harness.md) → [Model](model.md) → [API](api.md)
   *(forward-looking, for later in the series)*

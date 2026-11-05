# Agentic Systems

> **In one line:** An agentic system is the whole arrangement around one or more
> [agents](agent.md) — what tools they have, how they're organized, how they hand
> work to each other.

## In plain terms

A single [agent](agent.md) is Claude pursuing a goal across several steps. An
**agentic system** is the bigger picture: maybe one agent that spawns smaller
"subagents" for focused jobs (one to search, one to summarize, one to check);
maybe several agents coordinating; maybe a single agent given a carefully chosen
set of tools and instructions. The term covers the *setup* as much as any one
Claude inside it.

An analogy: a single agent is a researcher working through a task on their own.
An agentic system is the whole research group — who does what, who hands off to
whom, what tools each person has. The intelligence is still in the individual
workers; the system is how they're organized.

Two patterns you'll meet later in the series:

- **Subagents.** A main Claude spawns smaller, focused Claudes for narrow jobs
  (read these files, search this question) and pulls their results back. This
  keeps the main thread's [context](context.md) clean.
- **Pipelines.** A sequence of agents — or [prompt chains](prompt-chaining.md) —
  where each stage refines the previous one's output.

For a beginner, the term mostly signals *direction*: as you go further in the
series, you stop thinking of "Claude" as one assistant and start designing little
systems of them.

## Why it matters in this workshop

It frames where the recipes and later sessions are heading. You won't build a
multi-agent system on day one, but you'll start to see why your workflow gets
cleaner when work is split across focused pieces rather than crammed into one
chat.

## See also

- [Agent](agent.md) — the building block of any agentic system
- [Harness](harness.md) — the program that runs the agent loop
- [Prompt Chaining](prompt-chaining.md) — chains of prompts, the simpler cousin
- [API](api.md) — how agentic systems are built programmatically

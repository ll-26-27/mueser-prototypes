# Agent

> **In one line:** An agent is Claude working toward a goal over multiple steps —
> deciding what to do, doing it ([tool calls](tool-call.md)), checking the result,
> and continuing — instead of answering in a single reply.

## In plain terms

A normal exchange is one round: you ask, Claude answers. An **agent** is Claude
given a goal and the room to take several steps to reach it: read this, then change
that, then check it worked, then move on — looping until the job is done.

An analogy: the difference between asking a colleague a question (one answer) and
handing them a task to go complete (they'll take many small actions on their own and
come back when it's done). [Claude Code](claude-code.md) working through a folder is
acting as an agent.

What makes this possible is the combination you've already met:

- [Tool calls](tool-call.md) — so it can actually *do* each step.
- [Context](context.md) — so each step's result informs the next.

For beginners the word matters less than the shift in expectation: Claude isn't only
a question-answerer; it can carry out a multi-step task. Everything later in the
series — research workflows, building small apps, [agentic systems](agentic-systems.md)
that compose several agents — is this idea scaled up.

A subtle distinction worth holding: in [prompt chaining](prompt-chaining.md), *you*
decide the next step; in an agent, *Claude* decides. The line between them isn't
always sharp.

## Why it matters in this workshop

It frames where the series is heading and reframes [Claude Code](claude-code.md):
not "chat that can touch files," but "an assistant that can carry out a piece of
work." The skill of steering it well is, again, context engineering.

## See also

- [Tool Call](tool-call.md) — the steps an agent takes
- [Harness](harness.md) — the program that runs the agent loop
- [Claude Code](claude-code.md) — an agent you'll actually use
- [Agentic System](agentic-systems.md) — multiple agents organized together
- [Prompt Chaining](prompt-chaining.md) — the human-driven cousin

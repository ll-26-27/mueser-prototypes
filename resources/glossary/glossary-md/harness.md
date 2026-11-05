# Harness

> **In one line:** The harness is the program around Claude that actually runs the
> loop — feeding it context, carrying out its [tool calls](tool-call.md), and
> passing results back — turning a text predictor into something that gets work
> done.

## In plain terms

Claude itself only takes text in and produces text out. By itself it can't open a
file or run code. The **harness** is the surrounding software that makes the rest
happen: it assembles what goes into the [context](context.md), notices when Claude
asks to use a tool, performs that action, and hands the result back so Claude can
continue.

An analogy: Claude is the engine; the harness is the rest of the car — wheels,
pedals, dashboard. The engine provides the intelligence, but you only get anywhere
because the harness connects it to the road.

[Claude Code](claude-code.md) is, in effect, a harness: it's why the same Claude
that just chats on the web can, here, read your folder and make changes. Different
harnesses give the same underlying Claude different abilities.

This is a more advanced term — beginners mainly need it to make sense of a sentence
like "Claude Code is a harness." The point: **what Claude can *do* depends as much
on the harness around it as on the model itself.**

## Why it matters in this workshop

It explains why "Claude" feels different on the web vs. in Claude Code — same model,
different harness — and sets up later parts of the series where the harness is
configured deliberately.

## See also

- [Tool Call](tool-call.md) — what the harness carries out
- [Agent](agent.md) — the loop the harness runs
- [Claude Code](claude-code.md) — the harness you'll use here

# Getting Started with Claude.ai

A walk-through for using Claude's browser interface on the HUIT-provided plan, configuring the key settings, and trying one of the activities from the workshop (the interactive population pyramid).

---

## 1. Confirm you're on the HUIT plan

Go to **[claude.ai](https://claude.ai)** and sign in. Check the **bottom-left corner** next to your name for the HUIT-plan indicator (e.g. **"HUIT Early Access"**). If you don't see it, you're on a different account — use the activation link from the pre-workshop HUIT email to switch over. Let us know if the link no longer works.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UN3QS7K/screenshot_2026-05-14_at_3.42.14___pm.png?pub_secret=a18a56f681)

> **Data sensitivity.** The HUIT-provided plan is temporary, bridging us until Harvard's full Enterprise agreement with Anthropic is in place. Until then, treat it like any other unmanaged cloud tool: public materials, your own notes, and the workshop sample files are fine, but **do not paste student work, grades, research data, or anything above Harvard Level 2 data** into chats. Once the Enterprise agreement lands you'll be able to use it for Level 3 data; we'll let you know when that switches over.

---

## 2. Tour of the interface



Once you're signed in, you'll land in a fresh chat. A quick map of what you're looking at:

- **Sidebar (left).** Your past chats. If you only see icons, click the small toggle in the top-left to expand the sidebar.
- **New chat (top-left).** Starts a fresh conversation. Every new chat is a clean slate — Claude doesn't remember the previous chat unless memory is on (more below).
- **Search.** Once you have a few weeks of chats, the search bar near the top of the sidebar becomes essential.
- **Hover on a chat** in the sidebar to get a three-dot menu: **star**, **rename**, **delete**, **move to a project**.
- **Incognito chat.** Top of the chat window — useful for a one-off conversation you don't want saved to history or fed into memory.
- **Projects (sidebar).** Long-running workspaces with their own shared instructions and uploaded files. We'll touch projects more on the Cowork side.
- **Your name (bottom-left)** → **Settings** is where the important toggles live. We'll go there in step 4.

### Send a first message

Type a sanity-check prompt — something where you know the answer, e.g. *"What is the capital of Canada?"* — and hit send. If you get a sensible response, your account is wired up correctly.

---

## 3. Models, and switching between them

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4UKAJU9F/screenshot_2026-05-19_at_9.29.35___am.png?pub_secret=100780b34a)

At the bottom of the chat window, just below the message box, you'll see a model picker. The main three you'll encounter:

| Model | Use when |
|---|---|
| **Opus 4.7** | Hard tasks: long analysis, careful reasoning, complex code, multi-step writing. Most expensive in credits. |
| **Sonnet 4.6** | The everyday default. Fast, capable, good for most chats. |
| **Haiku 4.5** | Quickest and cheapest. Good for simple lookups, formatting tasks, or chatty back-and-forth. |

A useful habit: start in Sonnet, and bump up to Opus when you hit a wall (long reasoning, dense source material, code that has to be right). Your account has finite credits per period.

You can switch the model mid-conversation — it applies to your next message.

---

## 4. Settings: turning on memory (optional)

Without memory turned on, each new chat is a fresh start: Claude remembers nothing from previous conversations — like the protagonist in *Memento*, every chat is its own self-contained day. What Claude can see during a chat is the **context window**: the system prompt, any saved memory entries, and the back-and-forth as it accumulates. Turning memory on is what lets information carry from one chat to the next, which is why it's worth understanding before you do.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B5M672GSU/animation.gif?pub_secret=8377dacf99)

Click your **name (bottom-left)** → **Settings** → **Capabilities**.

Look for **"Generate memory from chat history."**

**What this does:** at the end of each day, Claude writes a short summary of what you talked about and saves it as plain text. Future chats can read that text, so over time Claude builds up a working picture of who you are, what you work on, and how you like things done.

**What it is:** a text file that gets prepended to your conversations. You can read it, edit individual entries, and delete it. There's no hidden state beyond that.

**Trade-off.** Memory makes Claude more useful over weeks of use, but it does retain notes about you. Until the Harvard Enterprise agreement is in place, only turn it on if you're comfortable with that, and don't discuss sensitive data in memory-enabled chats. You can toggle it off and clear stored memories from the same settings page at any time.

If you've been using ChatGPT and have memories there you'd like to bring over, scroll down to **"Start import."** It's a copy-paste migration — the prompt it gives you is what you run on the other service to export your memories as text.

---

## 5. The plus (+) button: attaching context
![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4LKXDY3V/animation_3.gif?pub_secret=625e28a642)

Next to the message box is a **+** button. From there you can:

- **Add files or photos.** PDFs, Word docs, CSVs, images, screenshots. Claude reads the contents directly.
- **Web search.** Lets Claude look things up. Use this for anything that happened recently or anything you want a citation for — Claude's training data has a cutoff, so without web search it's working from memory.
- **Add to a project.** Drops this chat into one of your project workspaces.

---

## 6. Worked example: build an interactive population pyramid
This activity demonstrates **artifacts** — interactive web tools Claude builds inside the chat by writing and running code.

You'll need the file `wpp2024_population_country.csv` from the workshop materials folder (`claude-cowork-20260518/population-data/`).

1. Click **New chat**. Confirm you're on **Opus 4.7** (this one benefits from the stronger model).
2. Click the **+** button → **Add files or photos** → navigate to the CSV and attach it.
3. In the message box, type:
   > Can you create an interactive population pyramid as an artifact from the attached CSV data? Please compare Nigeria and Japan.
4. Send. Claude will think for a moment, then render an **artifact panel** on the right side of the screen with a live, interactive chart.

If the chart isn't quite what you wanted, say so in the next message — for example: *"Move youth to the bottom, elderly to the top,"* or *"Show males and females on opposite sides of a single axis."* Claude will rewrite the artifact in place.

### How this is different from an image-generation model

In the workshop we contrasted this with what Midjourney produced when asked for the same comparison. The results were striking — pretty, vaguely chart-shaped artwork — but they weren't population pyramids. There were no real bars tied to real ages and real population counts; just an image that gestured at the idea of a chart about populations. An image model produces pixels that resemble similar images it has seen; it has no representation of Nigeria's actual age distribution, only of what a chart about it tends to look like.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B42LNK00P/process-black_comparison_of_population_pyramids_for_nigeria_a_87465a7f-14fb-41a8-b3ff-6d10fe4c698f_3.png?pub_secret=7c907539d5)

What Claude does with an artifact is structurally different. Given the CSV and the request, it writes a small program that reads the data and renders the chart, then runs that program inside the chat. The bars correspond to the real numbers in the file. You can interact with the result, change parameters, and ask Claude to revise it — because the output is code, not a picture.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4C6G2F7D/screenshot_2026-05-18_at_11.09.07___am.png?pub_secret=a6482e7fc7)

This is the broader point about Claude's tool use (running code here; web search and file reading in other situations): the tools let Claude produce outputs that are grounded in something verifiable, rather than predictions of what a plausible answer would look like. 

The basic loop — **context in → operation → output** — is the same one you'll use whether you're making a visualization, drafting a rubric, or organizing files.

---

## 7. Habits worth building early

- **One topic per chat.** When you switch tasks, start a new chat. Long unfocused chats accumulate clutter and Claude starts losing the thread (this is called "context rot" — there's a paper in your workshop folder if you're curious).
- **Tell Claude what good looks like.** Instead of *"summarize this paper,"* try *"summarize this paper in three bullets aimed at a sophomore who hasn't taken the prerequisite."* The more specific the target, the better the output.
- **Iterate, don't restart.** If the first answer is 70% right, reply with what to change rather than opening a new chat.
- **Web search on by default for current events.** Without it Claude is guessing at anything past its training cutoff.

---

## 8. Where to next

The browser is where you'll do most of your one-off chats, quick lookups, and artifact-building. When you want Claude to work across a folder of files on your own computer — renaming, reorganizing, summarizing across many documents, generating multiple linked outputs — use the desktop app and Cowork. The guide for that is the second document.

The interface updates frequently, so exact button placement may shift. The concepts — chats, projects, memory, attachments, artifacts, models — are stable.

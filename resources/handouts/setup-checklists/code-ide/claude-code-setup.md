
# Getting Started with Claude Code

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4Z7E9QA1/screenshot_2026-05-20_at_10.03.42___am.png?pub_secret=7a1c812771)

A walk-through for installing **Claude Code** on your own computer, opening the workshop repository in a code editor, and understanding how it relates to claude.ai and Cowork.

This is one task: a setup that takes 15–25 minutes and involves a little troubleshooting — but it's a *one-time* setup. Once Claude Code is installed, it stays installed and works from then on.

This guide covers the **concepts** and the **shape** of the setup. The exact, copy-pasteable commands — with a fix for every common snag — live in two companion files beside this one: `claude-code-mac-setup.md` and `claude-code-windows-setup.md`. Keep whichever one matches your machine open alongside this guide; there's also a one-page printable checklist for each under `checklists/`.

---

## How Claude Code fits with claude.ai and Cowork

Two surfaces come before this one. **claude.ai** in the browser is a conversation, plus files you upload, plus artifacts that live inside the chat. **Cowork** in the desktop app is the same conversation, but pointed at a folder on your computer, so Claude can read and — with permission — change real files.

Claude Code is the third door onto the same Claude models. Two things make it different:

- **It runs in a code editor and a terminal.** You'll work in VS Code, with the files of a project on one side and a conversation with Claude on the other. The terminal — the text-only way of moving around your computer — is where Claude Code is installed and launched.
- **You can see what it's doing.** With Cowork, a lot stays out of sight: you ask, files change, but *how* it happened stays hidden behind a friendly interface. Claude Code is the opposite. Every file it reads, every command it runs, and every line of code it writes is visible in the editor in front of you.

That second point is the heart of it. A question that always comes up: if Claude is working through a large dataset, how do you know it did it right — isn't it just a black box? Claude Code is the answer to that. Because the work happens as visible, readable code, you can check each step, give Claude precise constraints on *how* to do the job, and even ask it to write detailed logs of what it did. You're not trusting a black box; you're reading the receipts.

The trade Claude Code asks you to make: Claude Code takes more effort to set up and gives you a terminal instead of a tidy chat box. In return you can watch and verify every step, work across far more files at once, and build operations you can run again. The setup pain is paid once.

---

## The shape of the work: inputs → operations → outputs

Before the repo will make sense, one simple mental model. It isn't an industry term of art; it's just a way to orient yourself. Any project you do with AI tends to have three kinds of thing:

- **Inputs** — the raw material you start with. The Shakespeare texts. The CSV files. The recipe photos. The past exams.
- **Operations** (also called tools, commands, or processes) — whatever moves you from inputs to outputs. Often this is just a prompt saved as a text file; sometimes it's a script.
- **Outputs** — the thing you make. The close reading. The interactive website. The makeup exam.

The whole workshop repo is organized this way. Open `02-your-project/` and you'll find three folders: `inputs/`, `operations/`, and `outputs/`.

Real projects aren't always a clean left-to-right line. Everything still happens inside the **context window** — the system prompt, memory, your files, and the running conversation, all stacked together. So steps can chain together: the output of one operation becomes the input to the next. You might analyze some data (operation 1), then use that analysis as part of the context for writing a report (operation 2). This three-part pattern isn't a rigid assembly line — it's just a way to keep the pieces straight as they stack up.

---

## 1. Before you start

- **A paid Claude account.** Pro, Max, Team, or Enterprise — the free plan does not include Claude Code. Your HUIT workshop account qualifies.
- **15–25 minutes**, most of it spent waiting on downloads. Expect a little troubleshooting along the way. That's normal, and it's exactly why this part of the workshop is run in person with the whole team on hand.

> **Data sensitivity.** Claude Code can read every file in a folder, change those files, and run commands on your computer — more reach into your machine than either of the other two tools. Until Harvard's Enterprise agreement with Anthropic is in place, treat it the same way: public materials and the workshop sample files are fine, but **do not point Claude Code at — or run it inside — folders containing student work, grades, or research data above Harvard Level 2.** The grading and course-building workflows shown later in this guide are exactly what Claude Code is *for* once the data agreement lands; we'll let you know when that switches over.

---

## 2. One-time setup: install Claude Code

The full step-by-step is in [`claude-code-mac-setup.md` (Mac)](claude-code-mac-setup.md) or [`claude-code-windows-setup.md` (Windows)](claude-code-windows-setup.md). **Follow that guide for the exact commands.** This section explains what each step is *for*, so the commands aren't just magic you paste.

Mac users work in the **Terminal** app; Windows users work in **PowerShell**. The two paths are equivalent — the same seven steps, just with slightly different commands.

1. **Get a package manager.** A package manager installs applications from the terminal — like an app store you drive with text. Macs need **Homebrew** (`brew`) installed once; Windows 11 already ships with **winget**. Confirm yours works before going further.
2. **Install the core tools** — Git, Node, VS Code, and Python — one command each. Git is the slow one; let it finish. Git is the tool that copies the workshop repo onto your computer; VS Code is the editor you'll live in. **When all four finish, fully quit the terminal and open a fresh window** — a terminal that was already open won't notice newly installed programs, but a fresh window will.
3. **Install Claude Code itself.** One command runs the official installer (`curl -fsSL https://claude.ai/install.sh | bash` on Mac; `irm https://claude.ai/install.ps1 | iex` on Windows). Reopen the terminal, then run `claude --version` to confirm it's there.
4. **Clone the workshop repo.** The workshop materials live on **GitHub** — think of GitHub as the Google Docs version of a folder of files: a shared copy in the cloud rather than only on one computer. A **repository** ("repo") is just a folder structure. *Cloning* copies the repo down onto your machine. The setup guide creates a `Development` folder and clones `eng298ai-20261103` into it.
5. **Open the project in VS Code** with `code .` from inside the cloned folder. If VS Code asks whether you trust the authors of the folder, choose **Yes**.
6. **Log in to Claude.** Open the terminal that lives inside VS Code itself — use the menu **Terminal → New Terminal** — then type `claude`, press Enter, and follow the prompts. A browser window opens for you to sign in with your paid account.


![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4Y507R2Q/screenrecording2026-05-19at11.40.12am-ezgif.com-video-to-gif-converter.gif?pub_secret=ebaed0b723)

**(Optional) Add the VS Code extension.** This puts Claude in its own panel next to your files, where it clearly marks every change it makes to a file and lets you attach a file by typing `@` and picking it from a list. Open the Extensions panel, search for **Claude Code**, and install the one published by **Anthropic** — check the publisher, since there are similarly-named imitations.

**The one snag that explains most setup problems:** if a command "isn't recognized" right after you installed the thing, the terminal you have open simply hasn't noticed it yet. Quit the terminal completely, open a fresh window, and try again — the oldest tech-support trick there is, and here it genuinely is the fix. Both setup guides have a troubleshooting section for everything else.

---

## 3. Tour of the VS Code window

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B507FPL30/animation_10.gif?pub_secret=486dc52e5a)

VS Code is a code editor — a program for opening, viewing, and editing the files in a project. (You may hear it called an "IDE"; that's just the technical name for the same kind of program.) It has a lot of panels doing different jobs, so the first time you open it, it can look busy. The layout you want, left to right:

- **Explorer (left).** The list of files and folders in the repo you copied down. If you see something else instead, click the **Explorer** icon — it's at the top of the narrow strip of icons running down the far-left edge of the window. Folders have a small arrow beside them; click the arrow to open or close the folder.
- **Editor (middle).** Click any file in the Explorer and its contents open here. This is where you'll *see* what Claude does — the changes it makes to files show up right here.
- **Claude (right).** Your conversation with Claude. You can close any panel with its **X** and reopen Claude by clicking its icon, or open a file to bring the editor back.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B506L82VC/animation_8.gif?pub_secret=53a60bba98)

The end state looks simple: three columns — your files, the file you've selected, and Claude. It's worth remembering that "simple" sits on top of everything you installed in Section 2. That's the whole point — a lot of tooling underneath, a calm three-panel window on top.

NOTE: there are a couple of different ways you can open VS code on your computer. You can open it through terminal (Mac) or your shell (PC). You can also open it like you would any other app on your computer and then manually import a folder. See below for an example.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B548HRT5X/side_by_side_comparison.gif?pub_secret=aa791ef625)

---

## 4. How Claude sees your files

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B5WHF2N1E/animation_9.gif?pub_secret=b007687f71)

In the browser, you paste information *in* and copy results *out* by hand. In Claude Code, that mostly disappears: **whatever file you have open, Claude can automatically see.**

Click a file in the Explorer — say `context/course-readings/syllabus.md` — and ask Claude *"what does this file contain?"* It already has the file, because you have it selected. You'll see the filename appear at the bottom of the Claude panel, confirming what Claude can see.

When you want to hand Claude a specific file, type `@` in the Claude panel: a list of the project's files appears, and you type a few letters of the name to narrow it down, then pick the one you want. For a file outside the current project, paste in its full location instead (Mac: hold Option and right-click the file in Finder → *Copy as Pathname*; Windows: hold Shift and right-click → *Copy as path*).

Try it now: click any file in the Explorer and ask Claude what it is.

NOTE: When you create or add a new file inside VS Code, it automatically generates that actual file on your computer's hard drive in real time. Because of this, it's best practice to keep your project organized inside a dedicated "Development" folder so you always know exactly where to find your files outside of the app.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4VUX9LQK/screenshot_2026-05-20_at_9.32.18___am.png?pub_secret=d5ef6b8bc8)

---

## 5. The workshop repo

The repository follows the inputs → operations → outputs structure:

- **`02-your-project/`** — your workspace, with folders for source material,
  saved prompts and scripts, and results.
- **`context/`** — shared course readings and Learning Lab AI materials.
- **`01-use-cases/`** — humanities examples in progress; currently a placeholder.
- **`resources/`** — the glossary, handouts, and these setup guides.

### Project instructions: the CLAUDE.md file

A project can carry a `CLAUDE.md` file in its main folder. This is Claude Code's version of Cowork's custom instructions: a plain-text file describing what the project is, how you'd like Claude to work in it, and any rules to follow. Claude reads it automatically whenever you work in that folder. When you find yourself giving Claude the same guidance over and over — how you like files named, what tone to write in, an "always ask before deleting" rule — write it into a `CLAUDE.md` so you don't have to keep repeating it.

---

## 6. Worked example: start your own project

The goal isn't to finish a project. It's to leave with the tool installed and a clear idea of what you'd point it at. `02-your-project/` is there for exactly that.

1. **Rename it.** Right-click `02-your-project` in the Explorer and choose **Rename** (or select it and press Enter). Give it a name that means something to you — a course, a research task, a recurring chore.
2. **Put something in `inputs/`.** Drag a file in from Finder/Explorer, or create a new file and paste text into it. Anything textual works — a syllabus, a draft email, lecture notes, an exported document. In the workshop, one faculty member started a course-redesign project simply by pasting in the text of a relevant email.
3. **Write the operation.** Create a text file in `operations/` that describes, in plain sentences, what you want done. Name the input files, describe the result you want, and say how you will check it. Numbers at the front of filenames (`01-`, `02-`) can keep multi-step operations in order.
4. **Ask Claude to run it.** In the Claude panel, point it at your input and your operation, and have it write the result to `outputs/`.
5. **Iterate.** As with artifacts in the browser — if the first result is 70% right, tell Claude what to change rather than starting over.

Optionally, add a short `CLAUDE.md` in the project's main folder once you know how you want Claude to behave in it.

---

## 7. What this unlocks

Two examples shown in the workshop, both built by Becca:

- **Grading support.** 
    - Inputs: a folder of roughly a hundred anonymized exam answers, plus the exam, the solutions, and any rubric. 
    - Operations: one prompt that drafts a grading rubric, and a second that generates grading instructions. 
    - Output: a per-student grading report you can read side by side with the original answer. It handled hard-to-read handwriting capably — in one case correctly recognizing a crossed-out attempt, then awarding full credit for an answer left in factorial rather than the rubric's "choose" notation, because it understood the two are equivalent. The same speed made in-class short writing assignments feasible: scan a stack of handwritten responses, get quick check / check-plus / check-minus feedback, assign work that would otherwise have been too onerous to grade.
- **Building an online course.** 
    - Inputs: recorded course videos, a Canvas export, problem sets, and a syllabus. 
    - Operations: transcribe every video, build a topic index of each transcript, work through the course's problems. 
    - Output: a learning sequence on the university's learning-management system — a lecture clip, a quiz built from a question that had been asked live in class, and a brand-new interactive simulation that Claude built in about ten minutes, just from a plain-language description of what it should do, to help students build intuition.

These are also the clearest illustration of the point from the top of this guide about being able to check Claude's work. You don't hand Claude a dataset and hope. You give it precise instructions, you read the code it writes, you can ask it for a step-by-step record of what it did — and as you go you'll notice the mistakes it tends to make and the preferences you have. Save those into a `CLAUDE.md`, and the next run goes better. That's what "seeing under the hood" buys you.

*(As in Section 1: workflows over real student work, like the grading example, wait until Harvard's Enterprise data agreement is in place.)*

---

## 8. Habits and gotchas

- **A "command not recognized" error is the most common setup snag.** When it happens right after you installed something, the terminal you have open just hasn't noticed the new program. Quit the terminal fully and open a fresh window.
- **Check what changed.** When Claude edits files, the changes show up in the editor — glance at them before moving on. Being able to see the work is the whole advantage of Claude Code; use it.
- **One project per folder.** Point each project at the smallest folder that holds what it needs, the way the workshop projects are set up.
- **Start a new conversation when you switch tasks.** Leftover conversation from the last task ("context rot") quietly misleads Claude. Typing `/context` shows what's currently filling the context window; `/compact` shrinks a long conversation into a summary so you can keep going.
- **Back up before big changes.** Before any task that renames or deletes a lot of files, make a copy of the folder first.
- **The setup is one-time.** Errors during install are expected, and the team has seen them all; the troubleshooting sections of the two setup guides cover the common ones.
- **Type `/exit`** to close Claude Code when you're done in the terminal.

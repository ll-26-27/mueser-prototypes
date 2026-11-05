# Getting Started with Claude Cowork

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4WLJUM2Q/screenshot_2026-05-19_at_9.59.14___am.png?pub_secret=47b786c9a7)

A walk-through for opening **Cowork** in the Claude desktop app, setting up projects that give Claude access to folders on your own computer, and running three concrete projects end-to-end:

- **Project A** — point Cowork at a folder of recipe photos and have it rename, transcribe, and build a small website from them.
- **Project B** — point Cowork at a course schedule and syllabus and have it reshuffle the term when a guest lecturer needs to change dates.
- **Project C** — point Cowork at your old midterms and have it draft candidate makeup-exam questions of similar difficulty.

All three use sample materials from the workshop folder (`claude-cowork-20260518/`).

---

## How Cowork is different from claude.ai in the browser

In the browser, you have a conversation with Claude. You type a message, sometimes attach a file, and Claude replies — sometimes with an artifact like the population pyramid that lives inside the chat window. If you want the result on your computer, you copy or download it.

Cowork is more like handing Claude a folder on your machine and letting it work inside that folder. Claude can read every file in it, edit them, rename them, and create new ones. The changes save directly to the folder, the same way they would if you edited the files yourself.

A few practical differences:

- **How much it handles at once.** A browser chat usually deals with one or two attached files. Cowork can work across dozens or hundreds of files in a single chat inside a project.
- **Where the outputs live.** Artifacts in the browser stay in the chat. Files Cowork creates or edits sit on your computer, in the folder you pointed it at.
- **What it can do.** The browser produces text and in-chat visualizations. Cowork also changes things on your computer — renaming files, editing documents, creating new ones.

---

## 1. Confirm you're on the HUIT plan and open Cowork

Open the Claude desktop app and check the **bottom-left corner** of the window for the HUIT-plan indicator (e.g. **"HUIT Early Access"**). If you don't see it, sign out and sign back in using the activation link from the pre-workshop HUIT email.

> **Data sensitivity.** Cowork reads, edits, and creates files on your actual computer. Until the Harvard Enterprise agreement with Anthropic is finalized, **do not point Cowork at folders containing student work, grades, or research data above Harvard Level 2.** The recipe photos and the publicly-distributed midterm practice materials are fine; your live gradebook is not. We'll let you know when that changes.

Click the **Cowork** tab (along the top or in the sidebar, depending on your version).

A few things to notice that differ from the web chat:

- A panel showing your **projects** and **tasks** (more on this in Section 2).
- The option to dock work to whole **folders** on your computer, not just attached files.
- A **Code** view. Don't click into that yet — stay on the chat side for now.

---

## 2. Projects and tasks

Two terms to know in Claude:

- A **project** is a persistent, dedicated workspace that groups files, custom instructions, and chat histories. Projects are the unit you'll work in throughout this guide — each of the three workflows below is its own project, docked to its own folder.
- A **task** is an individual automated action, process, or routine that Claude executes within or across projects.

The Cowork UI uses **New task** as the button label for starting a fresh chat thread inside a project; once you're in a project, those tasks accumulate as the project's history. To keep terms clear, this guide uses *project* for the workspace and *task* or *step* for individual conversation threads inside it.

### Set up your first project (Project A)

We'll create Project A now and use it as the demo. The same steps work for B and C.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4QAT9EQM/recording.gif?pub_secret=5214a74094)

1. From the workshop materials (`claude-cowork-20260518/`), copy or move the **`recipe-photos`** folder somewhere you can find it — your Desktop is fine.
2. In Cowork, click **New task** (or your version's equivalent), then click **"work in a project"** and choose to create a new project. Name it `recipe-photos` and attach the `recipe-photos` folder as its docked folder. On Mac you can drag the folder in; otherwise use the folder-attach button.
3. The first time you grant folder access, your operating system will prompt you to confirm. Approve it.

A sanity-check prompt:

> *Can you list the files in this folder?*

You should get back a list of the eight or so recipe images.

> **What folder access actually means.** Tasks inside this project can read every file in the docked folder, change file names, edit text files, create new files, and delete files (Claude will usually ask first, but not always). They **cannot** see anything outside that folder. Keep each project scoped to a single folder of work.

---

## 3. Pointing Claude at a specific file in the project's folder

You can refer to any file inside your project's docked folder by name in the chat — *"open `2024 midterm_2 v2.docx`"* usually works fine. When a filename is ambiguous, deeply nested, or has unusual characters, it's more reliable to paste the **full file path** instead. Two ways to copy one — use whichever fits your workflow:

**Mac**

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4LDY1VGB/screenshot_2026-05-19_at_9.31.49___am.png?pub_secret=f7978a2d2c)

- **Keyboard shortcut:** Select the file in Finder, then press `Option + Command + C`.
- **Right-click menu:** Right-click (or `Control`-click) the file in Finder, then hold `Option` — the menu item changes to *Copy "[filename]" as Pathname*.

**Windows**

- **Keyboard shortcut:** Hold `Shift`, then right-click the file in File Explorer → *Copy as path*.
- **Address bar:** Click the address bar at the top of File Explorer — it switches from the breadcrumb view to a copyable full path.

---

## 4. Project A — Organize a folder (the recipe-photos example)

A low-stakes workflow to see Cowork operate across many files at once. Your `recipe-photos` project is already set up from Section 2 — we can complete these three steps inside it.

### Step 1 — Rename the messy files

> *These files have unhelpful names like `scan0005.jpg` and `20130811-164637.jpg`. Please look at each image, figure out what recipe it is, and rename it to something descriptive and consistent (kebab-case, like `peanut-butter-fudge.jpg`).*

Cowork will open each image — including handwritten recipe cards — and rename them. You can watch the file names change in your Finder/Explorer window as it works.

### Step 2 — Transcribe each recipe to text

> *For each renamed image, create a `.md` file next to it with the same base name, containing: (1) a one-sentence description of what the recipe is, and (2) a clean transcription of the recipe text.*

Now you have one Markdown file per image, sitting beside the photos.

### Step 3 — Build a little website out of them

> *Create an `index.html` and one `.html` page per recipe in this folder. Each recipe page should display the photo and the transcribed text. The index should link to all of them, with thumbnails. Style it simply — clean, readable, no frameworks.*

When it finishes, open `index.html` in your browser. You now have a small static site you can share, host, or keep as a local resource.

The same **inputs → operations → outputs** pattern transfers to other workflows:

- A folder of photos of the **blackboard at the end of each class**, plus a short audio reflection recorded on the walk back to your office → Cowork transcribes the audio and the boards into a running teaching diary.
- A folder of **scans of student minute papers** (once Harvard's data agreement is live) → a summary of what students are confused about this week.
- A folder of **PDFs of recent papers in your field** → a small interlinked review site with one-page summaries.

---

## 5. Project B — Reshuffle a course schedule around a visiting lecturer

This is the scenario Marlon walked through with Pia's Science & Cooking materials in the workshop: a guest lecturer can no longer make their scheduled date, and the term's schedule needs reshuffling without breaking the topical arc of the course. Cowork is well-suited for this because it can hold the schedule and the syllabus in context at once and propose a coherent set of swaps.

We'll use the **science-and-cooking** folder from the workshop materials (`claude-cowork-20260518/science-and-cooking/`), which includes `GENED1104_Schedule.md` and `GENED1104_Syllabus.md`. Swap in your own course materials if you'd prefer.

### Step 1 — Create the project

Create a new project (per Section 2), name it `science-and-cooking`, and dock it to the `claude-cowork-20260518/science-and-cooking/` folder. First confirm Cowork can see things:

> *Can you list the files in this folder and briefly describe what each one is?*

You should see it identify the schedule and the syllabus (and the `Midterm-2-Practice-Materials` subfolder, which we'll come back to in Project C).

### Step 2 — Have it read the existing structure

> *Read both `GENED1104_Schedule.md` and `GENED1104_Syllabus.md`. Summarize, in a single document, the topical arc of the course, which week covers which topic, where the guest lecturers fall, and any dependencies between weeks (e.g. content that builds on a prerequisite week). Save this as `course-structure-notes.md` in the folder.*

Spot-check the summary against the original files before relying on Claude's read of the structure.

### Step 3 — Ask for a reshuffle

> *Joanne Chang is scheduled to guest-lecture on T 9/23 (Phase Transitions) but can no longer make that date — she needs to come on T 9/30 instead. Please propose a revised schedule that:
> - moves Joanne's session to T 9/30
> - finds a feasible new slot for Nok Suntaranon, who was originally on T 9/30
> - preserves the topical arc of the course (no week's content shifted before its prerequisites)
> - flags any constraints I should double-check with the other lecturers or with the lab schedule
>
> Save the revised schedule as `GENED1104_Schedule_revised.md`, and a short change-log explaining each move as `schedule-changes.md`.*

### Step 4 — Iterate

The first draft will surface tensions you may not have considered — *"this swap also moves the lab session, is that OK?"* or *"the new slot conflicts with midterm review."* Reply in the same chat to refine:

- *"The midterm review session has to stay on T 10/7."*
- *"Nok's session needs a guest-speaker slot, not a regular lecture slot."*
- *"What if Joanne came in the slot the week before her original date instead — does that work better?"*

Cowork will update both files in place.

The same pattern works for any structured document with embedded constraints — lab rotations, office-hour schedules, comp exam reading lists, reading assignments tied to specific weeks.

---

## 6. Project C — Draft candidate makeup-exam questions

This is the workflow Becca described in the workshop: a folder of old midterms with answer keys, and a recurring need to produce fresh-but-equivalent makeup exams. With the whole problem bank in context, Cowork can draft new questions of similar difficulty on the same topics.

We'll use the **Midterm-2-Practice-Materials** folder from the workshop materials (`claude-cowork-20260518/science-and-cooking/Midterm-2-Practice-Materials/`). If you have your own past exams you'd rather use, swap them in — keeping the data-sensitivity guidance in mind. These particular workshop files are publicly distributed practice materials.

### Step 1 — Create the project

Create a new project (per Section 2), name it `midterm-2-makeup`, and dock it to the `Midterm-2-Practice-Materials` subfolder. Scoping the project narrowly to just the exam materials — rather than the parent `science-and-cooking` folder — keeps Cowork focused on the problem bank. First confirm:

> *Can you list the files in this folder and tell me, for each one, whether it appears to be an exam, a key, or supporting material?*

You should see it correctly identify the 2022/2023/2024 midterms, their corresponding keys, the equation sheet, and the practice problems.

### Step 2 — Have it read the problem bank

> *Read through all of the past midterms and their answer keys. Then summarize, in a single document, the topics covered across these exams, the typical question formats (short-answer, calculation, free-response, etc.), and roughly how difficulty has varied year-to-year. Save this as `topic-coverage-notes.md` in the folder.*

This step is doing two things: confirming Cowork has actually parsed the PDFs and Word docs correctly, and producing a reference document you can sanity-check before relying on its judgment for new questions.

**Read what it produces.** Spot-check a few of the claims against the actual exams. If it got something wrong (mis-identified a topic, hallucinated a question type), correct it in the chat — that correction goes into the context for the next step.

### Step 3 — Generate candidate makeup questions

> *I need to write a makeup midterm 2 for students who missed the regular one. Please draft 8 candidate new questions that:
> - cover the same topics as the past midterms, in roughly the same proportions
> - match the typical difficulty of midterm-2 questions (not the practice-problem level, which is easier)
> - are clearly different from the questions on the 2022, 2023, and 2024 exams — not close paraphrases
> - include a full worked answer key for each
>
> Save the questions in `makeup-candidate-questions.md` and the answer key in `makeup-candidate-key.md`, both in this folder.*

A few minutes later you'll have two new files in the folder, ready to review.

### Step 4 — Iterate

The first batch will likely be partially usable. Reply in the same chat with what you want changed:

- *"Question 3 is too close to 2024 Q5 — please replace it."*
- *"I need two more calculation questions and one fewer conceptual."*
- *"The difficulty on questions 6–8 is too high relative to the originals. Aim for the level of the 2022 exam."*
- *"For each question, also tell me which past exam question it's most similar to in topic, so I can verify coverage."*

Cowork will edit the files in place. Open them in any editor (or keep them open in Preview/Word) and refresh as it works.

The same pattern works for:

- **Quiz question banks** — generate variants of a problem at multiple difficulty levels.
- **Rubric drafting** — feed it an assignment prompt and a few sample student responses, and ask for a draft rubric.
- **Reading questions** — feed it a paper and ask for discussion questions targeted at a specific learning objective.

---

## 7. Project-level instructions

Beyond its docked folder, a project can hold **custom instructions** that apply to every task inside it. Useful when you find yourself giving Cowork the same guidance over and over — *"always cite the equation sheet,"* *"prefer Markdown over Word,"* *"don't use em-dashes."*

In Cowork, click on **Projects** and click on the project you want to edit. On the upper right corner, you'll see a panel labeled **Instructions** that you can edit. Add a short list of preferences. From then on, any new task inside that project inherits them.

![alt text](https://files.slack.com/files-pri/T0HTW3H0V-F0B4VJHJVKK/projectinstructions.gif?pub_secret=010b37c542)

Custom instructions are also why you might start a *second* task inside an existing project rather than spinning up something new: a long thread drifting into context rot, or a different angle on the same materials, can be picked up fresh in the same project without redoing setup.

Good things to put in custom instructions:

- Your name, role, and the audience you usually write for ("undergraduates in an intro chem class").
- Conventions for file naming, formatting, citation style.
- Things you've corrected Cowork on more than twice.
- "Always ask before deleting files" is a good safety rule.

---

## 8. Habits and gotchas

- **One folder per project.** Scope each project to the smallest folder that contains what it needs.
- **Read the diff.** When Cowork edits or renames files, glance at what changed before you move on. Renames and edits are easy to undo immediately, harder to untangle after a week.
- **Back up before bulk operations.** Before any task that renames or deletes many files, duplicate the folder.
- **Long tasks drift.** If a single task has been running for an hour and Cowork starts forgetting things from the start, that's context rot. Start a fresh task inside the same project and summarize where you left off — the docked folder and custom instructions carry over automatically.

---

## 9. Where to next

Cowork is for getting Claude to act on files on your computer through a graphical interface. The next step up — covered in tomorrow's session — is **Claude Code**, driven from the terminal. It's faster, scales further, and handles cases where you want to apply the same operation across many folders, or work with things that don't sit nicely as files (logs, databases, web pages).

The desktop app and Cowork will carry you a long way before you need that. Come back to this guide the first time you have a real folder of your own work to run through.

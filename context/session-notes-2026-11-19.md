# Notes from our session, 19 November

Nov 19, 2026 · Madeleine Woods

Ben, here are the notes from today, in the order of your questions. In a few places I answered too quickly or too simply, so I have marked those as clarifications.

## What to do next

1. Make a GitHub account, then ask Claude to clone `https://github.com/ll-26-27/mueser-prototypes` into a new folder. Keep your older downloaded copy beside it for now.
2. In the folder where you edit the book, ask Claude: "Set up git here, and commit before and after each session with a message saying what changed." Keep making your own copy of the manuscript as well.
3. For footnotes, citations and transcription, set effort to high. When you want it to ask you questions, use plan mode or write "ask me before you decide".
4. I will send you the OpenRouter key separately. It is not in the repository.
5. Leave the orchestrator and the terminal until you want them. Everything on this page works in the desktop app you already use.

## Versions and backups

Git is the right safeguard for your "what if it wrecks my files" question, but I made it sound automatic and it is not.

**Clarification.** I said git is constantly watching the folder. It saves a snapshot only when someone commits, and only of files it has been told to track. Anything changed between two commits has no earlier version to return to.

- **Commit often.** Ask Claude to commit at the start and end of each session. Each commit is a point you can go back to.
- **Check what is tracked.** In our repository the `inputs` folders for the style and notes projects are deliberately left out of git, so that a manuscript never lands on public GitHub. Git does not protect files in those folders.
- **Word files.** Git keeps whole earlier versions of a `.docx`, so you can go back to yesterday's file. It cannot undo one change inside the file and keep the rest (which is why we work in markdown).
- **Undoing something from two days ago.** This works when there are commits: Claude reads the history, finds the change and shows what else depends on it. A new chat does not remember the old chat, so the commit messages are what make this possible.
- **Branches.** Before an experiment, ask for a new branch named for the idea. The main version stays untouched until you decide to keep the experiment.
- **GitHub.** Pushing to GitHub puts a copy off your machine. For the book, use a private repository.

Your habit of copying the whole folder before experimenting was sound. Keep doing it for the manuscript until the commit routine is in place.

## Skills and scripts

A skill is a folder holding a file of written instructions, plus any scripts and reference files those instructions point to. Because it is a folder of files, you can copy it into a repository, share it and version it. That answers your export question.

- **Global or project.** Yours currently sit at the global level, so they apply everywhere. A skill can also live inside one project and differ there.
- **Skill versus script.** A skill's instructions pass through the model, so the result is probabilistic. A script is code that does the same thing every time.
- **The usual shape.** A prompt, then scripts doing the exact work, then a prompt that reads what the scripts did and checks it.
- **For footnotes.** Use scripts for anything with an exact rule: quote marks, italics for a fixed list of terms, flagging every note that does not match the pattern into a log. Use the model for judgment: page number or year, whether a cited work is missing from the bibliography.

**Clarification on length.** I said a skill should be about 200 lines. That figure is the guidance for a project's standing instruction file. For a skill, the main file should stay under about 500 lines, with detail moved into reference files it reads when needed. Your 600-line skill is a little long, but not as illegal as I thought. The split Claude proposed (mechanics, notes, bibliography) is a reasonable way to bring it down.

When you ask it to streamline, let it reorganise structure and code, and tell it not to reword your instructions. Then ask to see the skill text and read it. A summary of your rules is an interpretation of them.

On a book you admire as a model for citation style: give it the PDF with a short note on what you like about it, and ask it to interview you before it writes any rules. Finishing the bibliography in Chicago first and converting afterwards is the right order.

## Keys, OpenRouter and DeepL

A key is a password that identifies your account to a paid service each time a script calls it.

- **Where the limits live.** When you described the limits as coded into the key, I agreed too quickly. The key only says who you are. The quota and billing sit with the provider, on the account behind the key.
- **OpenRouter.** One account and one key that reach many models. The repository uses it for the vision models that read the pages and for the translation in the reading room. That is why Claude keeps asking you for it.
- **Where the key goes.** In a file called `.env` in the repository folder. That file never goes to GitHub.
- **Who pays.** Our R&D budget. OpenRouter is not a Harvard-contracted service, so it suits published and public sources. For anything sensitive I will get you a Harvard key.
- **Free local tools.** Tesseract, Kraken and Whisper run on your own machine at no cost. I made local tools sound uniformly weak. Quality depends on the tool and the size of model you download, and the larger ones are good.

**DeepL.** I skipped past this. OpenRouter does not include DeepL, so the OpenRouter key will not unblock it. Using DeepL would mean a small script that calls DeepL with your own key. I do not yet know why Claude reported it as blocked on the Harvard account. Send me the exact message and I will find out.

## Zotero, Scrivener and MCP

The reverse Zotero is doable. Scrivener is a different case from the one I described.

- **Zotero.** It has an interface that both reads and writes, using a key from your zotero.org account settings. The workflow: compare the full citations in the manuscript with the library entries, list the proposed corrections, you approve the list, then it writes them back. Back up the library before the first run.
- **Scrivener (clarification).** I grouped it with Zotero and said it has developer tools and keys. It has neither (womp womp I just chcked). A Scrivener project is a folder of text files with an index file. Claude can *read* that folder. Writing into it can damage the project, so do that only on a copy, with Scrivener closed. The safer route is to have Claude propose the new arrangement and move the items yourself.

**MCP (clarification).** I described an MCP as a server that hands a model documentation for a service. An MCP server gives Claude a set of actions for a service, such as searching a library or updating an entry, and carries each action out. BBBUUUUTTTTTT…. some run on the company's servers and *some* run on your own machine. If you ever get a local MCP, just make sure you keep it checking for updates (for instance, you make your own MCP for a company that has failed to do so).

You asked whether an MCP sets rules your AI has to follow, and I said no. BUT as a reminder, if you are using the MCP, in practice it will: Claude, when wired to an MCP, can do only what the server offers and what your account allows. But you can also use the MCP to nab documentation and then go rogue.

## Models and effort

There are two settings: which model, and how much effort it spends on each reply.

- **Models.** In Claude the order is Haiku, Sonnet, Opus, Fable, rising in capability and in how fast they use your allowance. I use the largest for planning and for the final check, and a mid-sized one for the work between.
- **Two models side by side.** I run Claude and Codex on the same folder and have each review the other. I said benchmarks show Claude is better at humanistic work and Codex at building. That is my own experience, not a benchmark result.

**Effort (clarification).** I told you to keep effort low so that it asks more questions, and agreed when you put it as "high only when the repository has the answers". Effort is how much the model “thinks" before it replies. Now, sometime this is more recursive, but higher can also make the model more careful and slower.

- For footnotes, citations and early modern German, use high, when you want to “set it up” and walk away, use high.
- To get questions, use plan mode, or write "interview me first" or "ask me before you decide" in the prompt or set to low.

## Context windows, long jobs and orchestrators

Starting a fresh chat for each task is a good habit, and the continuity belongs in files, not in the chat.

- **What carries over.** The standing instructions file in the folder (`CLAUDE.md`), your skills, and the git history. Open a session with "read CLAUDE.md and the last few commits" and it knows where you were.
- **Long image jobs.** I did not answer this, but I see it was question in the transcript. A long run over many page images should not be one chat reading every image. It should be a script that sends one page per call and saves each result to disk, which is how the repository works. The chat never fills up, and a run that stops can resume. Ask for it in those words: "write a script that processes one page per call and saves each result".
- **Orchestrator.** One main session plans the job, hands pieces to sub-agents that each have their own context window, and collects the results. Its two jobs are splitting the work and logging: every prompt it wrote and every output, saved in folders, in plain English you can read.
- **Where it runs.** Sub-agents work in the desktop app, too. But the terminal with cmux lets you watch several sessions at once (which I prefer for visibility.
- **Hooks.** Small scripts the app runs at fixed moments, such as after a file is written or a turn ends. They are the dependable way to force a log entry. This is a later step.
- **Loops.** A check-and-fix cycle: at the point where the work narrows to a choice, a second model reviews it and reports its concerns to you.

## Checking its work

The routine is: plan, read the plan, run, read the log.

- **Plan first.** Ask for a plan document before any work. Edit it, then let it run.
- **Ask for a chart.** "Show me the flow as a Mermaid chart" gives a diagram of what feeds what. It is easier to check than a long list of what it did.
- **Your wording stays yours.** After any change to a skill, ask to see the text and read it.
- **Citations.** I said I have high confidence in it for finding how something like the 1202 decretal is cited. It is good at gathering how and where a text is cited. It can also produce a plausible citation that does not exist. Each one needs opening and checking against the source before it goes in a footnote. The footnotes brief in the repository carries the rule that a short form is never guessed.
- **Testing your tools.** I did not answer this. The repository has tests: ask Claude to "run the tests and tell me what failed". For your own tools, keep three to five sample inputs whose correct outputs you have checked by hand, and ask it to rerun and compare them after any change.

**Is the time worth it?** You asked this and I gave you encouragement where you wanted an answer. A working rule: build a tool for what recurs across every chapter or every article, and do one-off fixes by hand. Once the rules sit in a file with commits behind them, the hours are worth it.

## The repository

Everything is in one public repository, [mueser-prototypes](https://github.com/ll-26-27/mueser-prototypes), pushed today. Open `index.html` at the top level for the home page linking all four projects.

| Project | Folder under `01-use-cases` | State today |
| --- | --- | --- |
| Reading room | `transcription/04-reading-room` | Built. Switch between transcription, translation and both; flag a line with a question; copy a passage with its citation. |
| Timeline | `timeline/01-thinkers-and-events` | Built after we met. 8,781 nodes drawn from Wikidata by written rules, each cited and linked out, and 170 proposed connections for you to accept or reject. |
| Style: CV, journal house style, handouts, footnotes | `style` | CV and journal house style: built today. You add a CV entry as a line of text and it is written into a copy with the neighbouring entry's formatting. For a submission, you give it three or more recent articles from the journal; it lists where your draft differs and writes only the changes you accept into a copy. Both have run on synthetic test files only, not yet on a real CV or draft. Handouts and footnotes: written briefs. |
| Notes apparatus | `notes/01-notes-apparatus` | Written brief only. |

- The translation in the reading room comes from a low-cost Gemini model through OpenRouter. The model can be changed.
- Copying a passage without the original line breaks, which you asked for, is not built yet.
- The timeline would not load when we met. It was still pulling entries.
- The `maps` folder is the earlier place-mapping work.

These are prototypes for you to take apart and change. To start any of them, open the folder in Claude and ask it to read the README and start the page.

## What I owe you

- [ ] The OpenRouter key, sent separately.
- [ ] Why DeepL is reported as blocked, once you send me the message Claude gave.
- [ ] Copy without line breaks in the reading room.
- [ ] A first run of the CV tool and the journal-style tool on your own files. Both are now built, with guides in `style/02-cv` and `style/04-journal-style`. Send me your CV as a Word file, and a draft with three recent articles from the journal you have in mind, or run them yourself.
- [ ] A walk-through of the terminal and cmux, if and when you want one.

You mentioned being in on Tuesday 24 November. Dani can set the time if that works. For quick questions, email me directly!

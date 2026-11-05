# What You Can Make with Desktop AI Apps — A Gallery

*A gallery of faculty projects, ordered from familiar text toward unfamiliar code.*

**How to read this.** A review of what faculty are building, arranged on one axis. It begins in the writing you already command and descends toward forms that did not exist two years ago. Each row is a genre of output: quick examples first, then one project unpacked — situation, inputs, operations, outputs, and the interface suited to it (Chat / Desktop / Code). The loop is constant — inputs, operations, outputs. Only the medium changes. Begin where you are fluent. Descend.

## 1. Structured Text & Documents — *most familiar*

Generating finished products in genres you already know.

**Examples:** an email to a chair proposing a new course · an NSF/NIH grant Specific Aims page from a project description · a committee report from raw meeting notes · a letter of recommendation from a CV and a prompt · a conference abstract from a draft paper · a syllabus skeleton from a reading list.

**Unpacked: meeting notes → a clean report for the dean**
- **Situation:** you left a faculty meeting with messy notes and need a structured report by tomorrow.
- **Inputs:** `meeting-notes.md` — your raw bullet points.
- **Operations:** one prompt: "Turn these notes into a report with a summary, decisions made, and action items with owners and dates."
- **Outputs:** `report.md`, or a polished `.docx` on request.
- **Best fit:** Chat or Desktop; Code if repeated monthly.

## 2. Reference Pages (Static HTML) — *intro to code*

Your first step into code: one file, opens in any browser, no setup.

**Examples:** a searchable glossary of course terms · a one-page syllabus website · a printable command/reference dashboard · an illustrated lecture handout · a course-policy FAQ page.

**Unpacked: a glossary your students can search and copy from**
- **Situation:** you want one page holding every key term in your course, searchable, that works offline.
- **Inputs:** `glossary.md` — terms and definitions.
- **Operations:** "Build a single-file HTML page with a search box and click-to-copy, styled for comfortable reading."
- **Outputs:** `glossary.html` — one file you can email or host anywhere.
- **Best fit:** Code or Desktop.

## 3. Web Apps (Next.js) — *more complex*

Multi-page, deployable sites with real interactivity.

**Examples:** a course website with interactive concept demos · a reading-response collection app · an interactive timeline of a period or movement · a "build your own X" student exercise.

**Unpacked: course site for GENED 1049 *East Asian Cinema***
- **Situation:** you want a site that pairs a cinematography glossary with interactive demos built on the films you actually teach.
- **Inputs:** syllabus, *Rashomon* stills, glossary text.
- **Operations:** scaffold a Next.js app, build parametric demo components, deploy to Vercel.
- **Outputs:** a live site (e.g. `gened-1049.vercel.app`) you share by link.
- **Best fit:** Code.

## 4. Bots & Connected Tools (MCP, Slack) — *not covered today*

An AI assistant wired to live data and other services.

**Examples:** an assistant connected to a library catalogue for live literature search · an art-history lecture pulling live images from a museum's own records · a Slack bot that answers from your course materials · an oral-exam practice bot · an assistant connected to your Google Drive.

**Worth knowing: AI assistants can be wired to live services**

Every row above works on files you already have. This one is different: the assistant reaches *out* — to a catalogue, a database, an institutional system — and works with whatever it finds there. The plumbing may use **MCP** or a provider-specific connector, and access has to be deliberately set up and granted before the assistant can use it.

We are not setting one up today. Worth knowing the category exists — and worth knowing that connecting an AI assistant to a live service is a real grant of access to that account, not a setting you flip casually.

## 5. Data Visualizations (d3, three.js) — *even more complex*

Turning a corpus or dataset into something you can see and manipulate.

**Examples:** a 2D semantic-embedding map of a text corpus · an interactive chart of course-evaluation trends · a 3D model of a molecule, artifact, or building · a network graph of citations or characters · an animated explainer for a hard concept.

**Unpacked: Calvino's *Six Memos*, by the numbers**
- **Situation:** you want students to see literary qualities as a measurable space — and plot their own prose against it.
- **Inputs:** the five memos as text; definitions for each measure.
- **Operations:** deterministic text analysis + a 2D embedding map + a live draft composer, charts drawn in d3.
- **Outputs:** a live page where pasted prose appears in every chart in real time.
- **Best fit:** Code.

## 6. Agentic Pipelines & Systems — *most complex*

Many tools orchestrated at scale: subagents, connected data, automation.

**Examples:** a make-up exam generator that interviews you between drafts · a reproducible coding pipeline for interview transcripts · close-reading a whole corpus with parallel subagents · an automated weekly research digest (scheduled).

**Unpacked: a make-up exam that is genuinely equivalent, not a reshuffle**
- **Situation:** a student misses the final. You need a replacement that tests the same things at the same difficulty, and you do not have a week.
- **Inputs:** the original exam, as LaTeX and PDF.
- **Operations:** a skill runs a multi-round flow — read the exam, interview you on what each question is really testing, draft two or three candidates per slot, revise on your feedback, then assemble the chosen ones in the original's format.
- **Outputs:** a candidate bank you chose from, plus the finished make-up exam as LaTeX.
- **Best fit:** Code (multi-round, stateful).

## ?. Unknown ??? — *beyond the map*

One day, a sort of Gesamtkunstwerk. Past the bottom: potentially new mediums, or new combinations of the rows above — text, application, visualization, sound, physical space in one project — buildable as the remaining technical barriers come down. Too early to catalogue.

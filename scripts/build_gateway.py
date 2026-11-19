"""Build the static project gateway. No model calls, research runs, or logs are changed.

Run: python3 scripts/build_gateway.py
Shared presentation lives in assets/gateway.{css,js}; Mermaid is vendored for offline use.
"""
from html import escape
from pathlib import Path
import os
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
TIMELINE_READY = (ROOT / '01-use-cases/timeline/01-thinkers-and-events/outputs/index.html').exists()
PROJECTS = [
    ('transcription', 'Reading room', 'Read a source closely.', 'Scans, German transcriptions and English translations, with a place to settle doubts and copy citations.', 'Working example', 'ready'),
    ('timeline', 'Timeline', 'See ideas in their time.', 'Thinkers, works, events and concepts, connected to their sources and open to your interpretation.', 'Working example' if TIMELINE_READY else 'In development', 'ready' if TIMELINE_READY else 'progress'),
    ('style', 'Style & documents', 'Keep the shape of your writing.', 'A CV you can extend and a draft you can bring to a journal’s house style, with every change yours to accept. Handouts and footnotes are planned.', 'Two tools working', 'progress'),
    ('notes', 'Notes apparatus', 'Bring the loose pieces together.', 'Email, voice notes, highlights and references, gathered by project without losing where they came from.', 'Planned', ''),
]


def url(target, page):
    return os.path.relpath(ROOT / target, (ROOT / page).parent).replace(os.sep, '/')


def anchor(text, target, page, cls=''):
    return f'<a class="{cls}" href="{escape(url(target, page), quote=True)}">{escape(text)}</a>'


def status(text, cls=''):
    return f'<span class="status {cls}">{escape(text)}</span>'


def page(title, path, body, current='Projects'):
    nav = ''.join(f'<a href="{url(dest, path)}"'+(' aria-current="page"' if name == current else '')+f'>{name}</a>' for name, dest in [('Projects','index.html'),('How it works','how-it-works.html'),('Methods','experiments.html')])
    diagram_script = f'<script defer src="{url("assets/vendor/mermaid.min.js",path)}"></script>' if 'class="mermaid"' in body else ''
    document=f'''<!doctype html>
<html lang="en" data-gateway="true"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Ben’s workspace</title><link rel="stylesheet" href="{url('assets/gateway.css',path)}">
{diagram_script}<script defer src="{url('assets/gateway.js',path)}"></script></head>
<body><a class="skip" href="#main">Skip to content</a><div class="shell"><header class="site-head">
<a class="brand" href="{url('index.html',path)}">Ben’s workspace<small>Research &amp; teaching</small></a><nav aria-label="Main navigation">{nav}</nav></header>
<main id="main">{body}</main><footer class="footer"><span>Bok Center Learning Lab · Research prototypes</span><span>{anchor('Project roadmap','context/roadmap.md',path)} · {anchor('Repository guide','README.md',path)}</span></footer></div></body></html>'''
    out=ROOT/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(document,encoding='utf-8')
    print(path)


def diagram(title, source, steps, caption, ident='workflow'):
    if source.startswith('flowchart LR'):
        source = re.sub(r'\["([^"]+)"\]', lambda m: '["' + '<br/>'.join(textwrap.wrap(m[1], width=22, break_long_words=False)) + '"]', source)
    return f'''<section class="diagram-section"><h2>{title}</h2><p>{caption}</p>
<div class="diagram-box" id="{ident}" aria-label="{escape(title)}"><button class="close-diagram" type="button">Close diagram</button><pre class="mermaid">{escape(source)}</pre></div>
<div class="diagram-tools"><span>Workflow diagram · available offline</span><button type="button" data-expand="{ident}">Enlarge diagram ↗</button></div>
<ol class="plain-steps">{''.join('<li>'+s+'</li>' for s in steps)}</ol>
<details><summary>View the diagram’s Mermaid source</summary><pre><code>{escape(source)}</code></pre></details></section>'''


def overview_header(path, title, intro, state, cls='', actions=''):
    return f'<div class="hero section-hero"><p class="breadcrumb">{anchor("Projects","index.html",path)} / {escape(title)}</p>{status(state,cls)}<h1>{title}</h1><p class="lead">{intro}</p>{actions}</div>'


def resources(path, items, heading='Go further'):
    return '<section class="section-line"><h2>'+heading+'</h2><ul class="link-list">'+''.join('<li>'+anchor(label,target,path)+f'<small>{description}</small></li>' for label,target,description in items)+'</ul></section>'


NOTES = [('context/session-notes-2026-11-19.md', 'session-notes-2026-11-19.html')]


def inline(text):
    """Markdown inside a line: code, links, bold, italic. The text is escaped first."""
    text = escape(text.replace('&#32;', '').replace('****', ''), quote=False)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'\*([^*]+?)(\s*)\*', r'<em>\1</em>\2', text).strip()


def markdown(lines):
    """The subset the session notes use: headings, paragraphs, lists, task lists and one kind of table."""
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith('## '):
            title = line[3:].strip()
            out.append(f'<h2 id="{re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")}">{inline(title)}</h2>')
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            head, body = rows[0], rows[2:]
            out.append('<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table></div>')
        elif re.match(r'\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'\d+\. ', lines[i]):
                items.append(inline(re.sub(r'^\d+\. ', '', lines[i])))
                i += 1
            out.append('<ol>' + ''.join(f'<li>{x}</li>' for x in items) + '</ol>')
        elif line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(lines[i][2:])
                i += 1
            if all(x.startswith('[ ] ') or x.startswith('[x] ') for x in items):
                out.append('<ul class="todo">' + ''.join(f'<li class="{"done" if x.startswith("[x]") else "open"}">{inline(x[4:])}</li>' for x in items) + '</ul>')
            else:
                out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>')
        else:
            out.append(f'<p>{inline(line)}</p>')
            i += 1
    return '\n'.join(out)


def note_page(source, path):
    """A note kept as Markdown under context/, shown whole as a page: first line the title, second the date and author."""
    lines = (ROOT / source).read_text(encoding='utf-8').splitlines()
    title = lines[0].lstrip('# ').strip()
    rest = [x for x in lines[1:]]
    while rest and not rest[0].strip():
        rest.pop(0)
    byline = rest.pop(0).replace('@', '')
    heads = [x[3:].strip() for x in rest if x.startswith('## ')]
    toc = '<nav class="note-toc" aria-label="On this page">' + ''.join(f'<a href="#{re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")}">{inline(h)}</a>' for h in heads) + '</nav>'
    body = f'<div class="hero section-hero"><p class="breadcrumb">{anchor("Projects","index.html",path)} / Session notes</p><p class="eyebrow">{escape(byline)}</p><h1>{inline(title)}</h1></div>{toc}<article class="prose">{markdown(rest)}</article>'
    page(title, path, body, current='')
    return title


def build():
    notes=[(note_page(src,dest),dest) for src,dest in NOTES]
    path='index.html'
    latest=''.join(f'<a class="start-here" href="{url(dest,path)}"><span>Start here</span><b>{escape(title)} →</b><small>What to do next, the clarifications, where each project stands, and what is still owed.</small></a>' for title,dest in notes)
    cards=''.join(f'''<article class="project-card"><div class="card-meta"><span class="number">0{i}</span>{status(state,cls)}</div>
<h2>{anchor(name,f'01-use-cases/{slug}/index.html',path)}</h2><p><strong>{tag}</strong> {description}</p>{anchor('Explore '+name+' →',f'01-use-cases/{slug}/index.html',path,'text-link')}</article>''' for i,(slug,name,tag,description,state,cls) in enumerate(PROJECTS,1))
    page('Projects',path,latest+f'''<div class="hero"><p class="eyebrow">Four projects · one local workspace</p><h1>Your research workspace.</h1><p class="lead">Read sources, explore connections, prepare documents, and bring your notes together. Choose a project to see what it does and where to begin.</p></div>
<div class="project-grid" aria-label="Projects">{cards}</div>
<section class="bridge"><div><h2>{anchor('How the pieces fit together →','how-it-works.html',path)}</h2><p>Your desktop AI app, your project folder, the models, and the pages you review. A map of what happens where.</p></div><div class="steps" aria-label="Instruct, work, review"><span><b>01 / Instruct</b>Desktop app</span><i aria-hidden="true">→</i><span><b>02 / Work</b>Your folder</span><i aria-hidden="true">→</i><span><b>03 / Review</b>These pages</span></div></section>'''+resources(path,[('Maps & places','01-use-cases/maps/index.html','Earlier experiments connecting historical sources to geography.'),('Methods & experiments','experiments.html','The full pipelines, comparisons, results and evidence behind this work.')],'Around the projects'))

    path='how-it-works.html'
    source='''flowchart TB
  You["You: a task and your material"] --> App
  subgraph Local["On your computer"]
    App["Desktop AI app / coding agent"] -->|"runs tools"| Tools["Project scripts"]
    Folder["Your project folder"] <-->|"read inputs / write new outputs"| Tools
    Tools --> Pages["Browser pages and documents"]
    Pages -->|"your decisions"| Log["Local review log"]
    end
  App <-. "conversation + tool requests" .-> Assistant["The desktop app's model"]
  Tools <-. "task inputs + model results" .-> API["Task models via OpenRouter"]'''
    body=overview_header(path,'How it works','The desktop app is where you ask for work. Your folder holds the material and the results. These pages are where you inspect what happened.','A shared working model')
    body+=diagram('One folder, several ways to work',source,[
        'Give the desktop app a task and access to the relevant project folder. Its coding agent can run the project’s scripts; the same commands can also be run in a terminal.',
        'Scripts read source files, do local processing, and call a model or reference service only at the steps that need one. Results are written into the project folder.',
        'Open the resulting page or document. Review doubtful readings, proposed connections or suggested changes.',
        'For the implemented review pages, a local server saves actions to the log. Applying decisions or rebuilding produces the next output.'
    ],'The desktop app operates the project tools. Those tools read your folder and produce pages or documents to review. Model calls are shown outside the local workspace.')
    body+='''<div class="two-col"><section><h2>Two kinds of model work</h2><p><strong>The app’s model</strong> interprets your request and helps operate the tools. It receives the conversation and whatever file context the desktop app supplies.</p><p><strong>The scripts’ task models</strong> perform specific passes, such as transcription or translation. Those calls use the repository’s API configuration and keep their prompts and replies with the run evidence.</p></section><section><h2>Local files, explicit calls</h2><p>Keeping a project in a local folder does not mean every model runs locally. Context sent by a desktop app or an API step goes to the model service configured for that step.</p><p>Opening a generated page does not itself run the transcription or translation models. The timeline can load linked portraits online; maps can request online map tiles.</p></section></div>
<section class="two-col"><div><h2>A folder you can inspect</h2><p>Each project keeps the material, the operations and the outputs together. Runs record how a result was produced; the review log records your decisions.</p></div><pre class="folder">project/
  inputs/       source files and settings
  operations/   commands for each step
  outputs/      pages, documents and run folders
    log…        review decisions, by project</pre></section>
<div class="note"><strong>Saving from a page.</strong> Start that project’s local server to save review actions to disk. When opened directly as a file, a review page keeps work in the browser and offers an export to import into the project. A static website cannot write directly into your folder.</div>'''
    body+=resources(path,[(name,f'01-use-cases/{slug}/index.html',tag) for slug,name,tag,*_ in PROJECTS],'Follow one project')
    page('How it works',path,body,'How it works')

    path='01-use-cases/transcription/index.html'
    body=overview_header(path,'Reading room','Read an old German source beside its scan and translation. Inspect disagreements, settle passages and take a quotation with its citation.','Working example','ready','<div class="actions">'+anchor('Open the reading room →','01-use-cases/transcription/04-reading-room/outputs/index.html',path,'button primary')+anchor('How the workspace works','how-it-works.html',path,'button')+'</div>')
    body+='''<div class="two-col"><section><h2>What you bring</h2><p>Page scans or photographs, plus the title, author, date and archive details needed to cite them. The current example uses three historical pages: print, handwriting and Antiqua type.</p></section><section><h2>What you get</h2><p>A scan beside a starting transcription and English translation; marked disagreements; a record of your choices; and passages you can copy with citations.</p></section></div>'''
    body+=diagram('From a scan to a reading you can cite','''flowchart LR
  A["Scans + source details"] --> B["OCR engines + vision models"]
  B --> C["Compare readings; mark disagreements"]
  C --> D["Align text to the scan"]
  D --> E["Models propose translations"]
  E --> F["You review in the reading room"]
  F --> G["Log decisions; apply to a new build"]''',[
        'The desktop agent or a terminal runs the reading pipeline on your scans. Multiple readers supply alternatives; agreement provides a starting point, not a guarantee of correctness.',
        'The page brings the scan, text, translation and evidence together. You decide the passages that need judgment.',
        'The local server logs your actions. Applying decisions writes a new build, keeping the original diplomatic reading alongside it.'
    ],'The working example is built. Bringing in your own scans still uses the project commands; there is no upload-and-process button yet.')
    body+=resources(path,[('Reading room guide','01-use-cases/transcription/04-reading-room/README.md','What was run, what was checked, and how to use your own pages.'),('Compare print readers','01-use-cases/transcription/01-fraktur-print-bakeoff/outputs/index.html','Alternative readings, accuracy, time and cost.'),('Compare handwriting readers','01-use-cases/transcription/02-kurrent-handwriting/outputs/index.html','Where readers agree and where difficult handwriting defeats them.'),('Layout & hybrid reading','01-use-cases/transcription/03-layout-and-hybrid/outputs/layout.html','How text is aligned to regions and lines on the scan.')])
    page('Reading room',path,body)

    path='01-use-cases/timeline/index.html'
    live=ROOT/'01-use-cases/timeline/01-thinkers-and-events/outputs/index.html'
    action='<div class="actions">'+anchor('Open the timeline →','01-use-cases/timeline/01-thinkers-and-events/outputs/index.html',path,'button primary')+'</div>' if live.exists() else ''
    body=overview_header(path,'Timeline','Explore thinkers, works, events and concepts together. Follow the connections, inspect their sources, and add your own interpretations.','Working example' if TIMELINE_READY else 'In development','ready' if TIMELINE_READY else 'progress',action)
    if not live.exists():body+='<p class="note">The viewer and pipeline are implemented and tested with synthetic data. The first real-data page is still being assembled; this overview is available while that run finishes.</p>'
    body+='''<div class="two-col"><section><h2>What goes in</h2><p>A written rule for the people, works, events and concepts to include. Wikidata supplies records and identifiers; encyclopedia metadata and Wikipedia extracts provide references and context.</p></section><section><h2>What you get</h2><p>A timeline and connection map, with links and citations. Recorded relationships, model proposals and connections you add remain distinguishable.</p></section></div>'''
    body+=diagram('From reference records to a reviewed connection','''flowchart LR
  A["Written collection rules"] --> B["Wikidata records"]
  B --> C["Reference links + attributed extracts"]
  C --> D["Model proposes connections"]
  D --> E["Database + timeline page"]
  E --> F["You inspect, accept, reject or add"]
  F --> G["Local log; rebuild the view"]''',[
        'The desktop agent or a terminal collects records under the written rules and caches the service replies.',
        'A task model proposes connections from the supplied extracts. Its quoted evidence is checked against the text; proposals still need a reader’s judgment.',
        'You explore and decide in the browser. The local server saves decisions and notes for the next build.'
    ],'A model’s proposed connection is shown as a proposal. A recorded connection retains its source property; your own connections carry your name.')
    body+=resources(path,[('Timeline design and scope','01-use-cases/timeline/README.md','The node types, layers, sources and relationship to the original mock-up.'),('Pipeline commands','01-use-cases/timeline/01-thinkers-and-events/operations/README.md','The collection, source, model, database and page-building steps.')])
    page('Timeline',path,body)

    path='01-use-cases/style/index.html'
    body=overview_header(path,'Style & documents','Make recurring document work easier while keeping your own form: the handout, the CV, the article and its notes.','Two tools working','progress')
    body+='<p class="note">The CV tool and the journal-style tool work and have been run on synthetic documents only. The next step is to run each on one of yours. Handouts and the footnote checker are scoped, not built.</p><div class="subprojects">'
    for title,desc,target,built in [('CV','Add an entry as a line of text. It is written into a copy as a duplicate of the neighbouring entry’s paragraph, so indents, tab stops and fonts stay yours. Working; run on a synthetic CV.','02-cv',True),('Journal house style','Give it a few recent articles from the journal. It counts the journal’s conventions, lists where your draft differs, and writes the changes you accept into a copy. Working; run on synthetic files.','04-journal-style',True),('Handouts','Infer a house style from existing examples, apply it without changing the words, and update course details for a new term. Planned.','01-handouts',False),('Footnotes & bibliography','Find inconsistent citations and unmatched short forms. Review proposed fixes before applying them to a copy. Planned.','03-footnotes',False)]:
        body+=f'<article><h2>{title}</h2><p>{desc}</p>'+anchor('Read the guide →' if built else 'Read the brief →',f'01-use-cases/style/{target}/'+('README.md' if built else 'HANDOFF.md'),path)+'</article>'
    body+='</div><div class="two-col"><section><h2>What you bring</h2><p>Your current CV as a Word file. For a submission, your draft as a Word file and three or more recent articles from the journal. For the planned tools, three to five handouts and a chapter or manuscript.</p></section><section><h2>What comes back</h2><p>A new copy of the document plus a report of what changed and what was refused. Your original file is never written to.</p></section></div>'
    body+=diagram('A document, a rule, a reviewable change','''flowchart LR
  A["Your documents + examples"] --> B["Desktop agent runs document tools"]
  B --> C["Extract structure and check rules"]
  C -. "citations only" .-> M["Optional model proposal"]
  C --> D["Report of changes and questions"]
  M --> D
  D --> E["You review"]
  E --> F["Apply to a copy; compare text and layout"]''',[
        'Start with the actual document and its reference examples or written style rules.',
        'Formatting and explicit checks run in code. A model is optional, for restyling citations after a journal’s examples; each of its answers is a proposal, with any word it added named.',
        'Review the report, then write an updated copy and inspect the differences.'
    ],'The CV and journal-style tools follow this workflow now; the desktop app can run their commands for you. These pages do not edit a Word document themselves.')
    body+=resources(path,[(name,f'01-use-cases/style/{slug}/README.md',desc) for name,slug,desc in [('CV guide','02-cv','Adding an entry, what the report says, what was checked.'),('Journal style guide','04-journal-style','The fifteen conventions, the review, and what the model pass is checked against.'),('Handouts guide','01-handouts','House style, course details and the inputs needed.'),('Footnotes guide','03-footnotes','Bibliography matching, explicit rules and unresolved questions.')]])
    page('Style & documents',path,body)

    path='01-use-cases/notes/index.html'
    body=overview_header(path,'Notes apparatus','Gather the fragments of research in one place, then find them again by project, theme, person or time.','Planned')
    body+='<p class="note">The workflow is scoped. Importers, the database and the reviewer page still need to be built and tried with your material.</p>'
    body+='''<div class="two-col"><section><h2>What you bring</h2><p>Email exports, a few voice notes, text or Word notes, PDF highlights and reference-manager exports. Start with your project list and the themes you already use.</p></section><section><h2>What comes back</h2><p>A local collection with each item’s source intact, suggestions for project and theme tags, a review queue, and a digest for each project.</p></section></div>'''
    body+=diagram('From scattered notes to a project collection','''flowchart LR
  A["Email / voice / files / highlights"] --> B["Import; keep the original"]
  B --> C["Local notes database"]
  C -. "eligible items only" .-> D["Optional model: propose tags and connections"]
  C --> E["Browser review page"]
  D --> E
  E --> F["You accept or revise"]
  F --> G["Local decision log"]
  G --> H["Apply; export project digests"]''',[
        'Import copies of the source material into the local project; preserve the original and its origin.',
        'The planned enrichment step proposes tags and connections. Items marked private are excluded from that model step.',
        'Review the suggestions, record decisions, and export the accepted collection by project.'
    ],'Planned workflow. A note may belong to more than one project; that should not create competing copies of the source.')
    body+=resources(path,[('Notes guide','01-use-cases/notes/README.md','The local-first structure and material needed to begin.'),('Implementation brief','01-use-cases/notes/01-notes-apparatus/HANDOFF.md','Import formats, review behavior and the proposed database.')])
    page('Notes apparatus',path,body)

    path='01-use-cases/maps/index.html'
    body=overview_header(path,'Maps & places','Earlier experiments in taking place names from historical sources and putting them on a map, with the evidence for each match.','Working examples','ready')
    body+=resources(path,[('Places from a route','01-use-cases/maps/01-places-to-map/outputs/index.html','Compare gazetteer candidates for the names on a historical route.'),('From page to map','01-use-cases/maps/03-from-page-to-map/outputs/index.html','Follow a mapped name back to its transcription, page and line.'),('Historical names around Breslau','01-use-cases/maps/04-from-map-data/outputs/index.html','Explore place records and name changes through time.'),('Historical map overlays','01-use-cases/maps/02-historical-map-overlay/README.md','What was checked and how a suitable map could be georeferenced.')],'Open an experiment')
    body+=diagram('From a name to a place','''flowchart LR
  A["Text or a list of places"] --> B["Extract and verify names"]
  B --> C["Look up gazetteer candidates"]
  C --> D["Apply a written matching rule"]
  D --> E["You review unresolved matches"]
  E --> F["Map + source references"]''',[
        'Start with a list, structured place data or names extracted from a transcription.',
        'Gazetteer lookups supply candidate places. Written rules accept clear matches; ambiguous names remain for review.',
        'The map keeps the chosen candidate, the reason and the source reference together.'
    ],'These experiments support the wider research workspace; they are kept alongside the four current projects.')
    page('Maps & places',path,body)


if __name__=='__main__':
    build()

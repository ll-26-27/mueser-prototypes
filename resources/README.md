# Resources

Reference material, readable independently of the use cases.

- [`accounts.md`](accounts.md): every external service this repository can
  call, its free tier, where to sign up with the Learning Lab account, which
  paid tier is worth it, and which `.env` variable each key goes in.
- [`glossary/`](glossary/): thirty terms (*token*, *context window*,
  *agent*, *skill*, *data classification* …), as Markdown source and as a
  browsable HTML page (`glossary/glossary-html/index.html`).
- [`handouts/`](handouts/): the Learning Lab's workshop handouts, the same
  set used in the desktop-app workshop: AI surfaces, "It's all text", the
  project plan (`inputs/` → `operations/` → `outputs/`), Markdown, the
  terminal, Claude Code commands, security concerns, what you can make, and
  setup checklists for the terminal, VS Code and the desktop apps.

The handouts are HTML and PDF; rebuild a PDF with
`~/.claude/skills/handout-house-style/scripts/html2pdf.sh handouts/<name>/<name>.html`
if that skill is installed.

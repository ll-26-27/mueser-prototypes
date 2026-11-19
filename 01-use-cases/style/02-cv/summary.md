# CV: summary

**Purpose.** Add entries to Ben's CV without changing its page size,
margins, indentation or tab stops, and tell him when a change grows the
page count rather than quietly fitting it.

**Workflow.** `extract` writes the CV as data with a format fingerprint
per entry and a geometry report. Ben adds entries in `cv.yml`. `render`
edits a copy: each new entry is a deep copy of a sibling paragraph's XML
with its run text replaced, inserted in date order; nothing else is
touched. `check` converts before and after to PDF and reports page count,
lines per section and the first page that differs, stopping if the count
grew.

**Findings.** None yet: scoped 5 November 2026, moved into this
repository 19 November 2026, not built. First in the group's build order.

**Limits.** A section with no existing entry has no sibling to clone;
such entries are reported, not invented. Page counts need LibreOffice,
not installed on the build machine as of 5 November. The repository is
public, so `cv.yml` (the CV as data) is committed only if Ben agrees.

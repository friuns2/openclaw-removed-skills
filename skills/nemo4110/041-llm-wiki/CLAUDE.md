# LLM-Wiki Work Protocol

> This is the core protocol file for llm-wiki. As an Agent, you MUST follow this protocol to maintain the knowledge base.
> **Before performing any task, you MUST read and understand `SKILL.md` to learn the machine-readable specification, available functions, entry points, and dependencies.**

## Design Philosophy

- **LLM as programmer, Wiki as codebase**
- **User is responsible for**: Placing materials, asking good questions, judging significance
- **You are responsible for**: Summarizing, cross-referencing, indexing, logging, all the tedious work
- **Accumulation over retrieval**: Every interaction should leave lasting value

## Directory Structure

```text
llm-wiki/
├── sources/          # Raw materials (user-managed + tool-fetched; Agent is FORBIDDEN from writing any LLM-generated content)
│   └── README.md     # Material management guide
├── wiki/             # Generated knowledge pages (Agent-managed)
│   ├── index.md      # Entry index
│   └── *.md          # Topic pages
├── assets/           # Templates and configuration
│   ├── page_template.md
│   └── ingest_rules.md
├── scripts/          # Auxiliary scripts (optional)
├── src/              # CLI implementation (optional)
├── log.md            # Timeline log (append-only)
├── CLAUDE.md         # This file (user-facing protocol)
├── AGENTS.md         # Agent implementation guide
└── SKILL.md          # Machine-readable skill specification (ALL Agents MUST read)
```

## Core Workflows

### 1. Ingest

**Trigger** (satisfies either condition):

1. **File already exists in `sources/`**: User has placed material in `sources/` and explicitly requests `/wiki-ingest <path>`
2. **User provided a fetchable URL/DOI**: User gives a network address; Agent MUST first use network tools to fetch into `sources/`, then execute ingest

**Pre-check**:
- If user only provided title, author, or description but no URL/DOI, and no file is in `sources/` → Agent should **proactively use web search tools** (WebSearch, WebFetch, etc.) to find open-access versions, present search results to user for confirmation, then download after confirmation; if search yields nothing, mark as `[[Pending: SourceName]]` and inform user
- If user provided a URL but fetching failed (404, paywall, anti-bot) → **do NOT fabricate content to fill `sources/`**, mark as `[[Pending: SourceName]]` and record failure reason in `log.md`

**Steps**:

1. **Read** material content
2. **Extract** key insights
3. **Identify** affected wiki pages (create new or update existing)
4. **Update** pages: Merge new information while preserving existing structure
5. **Dynamic linking** (NEW): After creating new pages, proactively discover relations with existing pages and perform bidirectional updates
   - Run `wiki link --source <new_page> --mode light` to discover related pages
   - For high-confidence relations (score >= 0.5):
     a. Read existing page content, analyze the relationship between old and new knowledge
     b. Choose merge strategy: `link_only` (add link only) / `append_related` (related pages) / `append_section` (append section)
     c. Run `wiki link --source <new_page> --target <existing_page> --strategy <strategy>` to generate changes
     d. Review diff, confirm before applying; high-risk modifications require user confirmation
   - For batch ingest (>=2 sources): Complete all new page creations first, then run `wiki relink --since <earliest_date> --mode deep`
6. **Maintain** cross-references: `[[PageName]]` format. All internal links appearing in new pages must have corresponding **stub pages** created synchronously (at least one-sentence definition + standard frontmatter) if the target page does not exist.
7. **Record** in `log.md`:

   ```markdown
   ## [2026-04-10] ingest | Material name
   - New pages: [[PageA]], [[PageB]]
   - Updated pages: [[PageC]]
   - Relation updates: [[PageD]] (added comparison with PageA)
   - Key insight: One-sentence summary
   ```

8. **Update** `wiki/index.md`

**Rules**:

- One concept per page
- Page names use PascalCase (e.g. `Transformer.md`)
- Use `[[links]]` to establish associations; do not duplicate content
- **Dynamic linking first**: After creating new pages, prefer using CLI tools to discover relations rather than guessing from memory
- **Bidirectional update safety**: When backward-updating existing pages, append only, never replace; must generate diff for review; automatic backup to `wiki/.backups/` before modification
- **Batch linking**: When ingesting >=2 sources in one batch, use `wiki relink --since <date> --mode deep` for global linking

### 2. Query

**Trigger**: User asks `/wiki-query <question>` or directly asks a question involving the knowledge base

**Steps**:

1. **Read** `wiki/index.md` to locate relevant pages
2. **Read** relevant wiki page content
3. **Synthesize** answer with citations: `[[PageName]]`
4. **Judge**: Is this answer worth archiving?
   - If it is a new insight → Create new page or append to existing page
   - If it is a frequently asked question → Update the FAQ section of `wiki/index.md`

### 3. Lint (Health Check)

**Trigger**: `/wiki-lint` or periodic execution

**Checklist**:

- [ ] **Orphan pages**: Pages not referenced by any other page
- [ ] **Dead links**: `[[Non-existent page]]`
- [ ] **Stale pages**: Not updated in 90 days
- [ ] **Contradictory statements**: Same concept defined differently across pages
- [ ] **TODO items**: `TODO` markers not processed

**Output**: Markdown report with fix suggestions

## Page Format Specification

### Frontmatter (Required)

```yaml
---
created: 2026-04-10
updated: 2026-04-10
sources:
  - "sources/paper.pdf"
  - "sources/notes.md"
tags:
  - "AI/ML"
  - "Architecture"
status: "active"  # active | draft | archived
---
```

### Page Structure

```markdown
# Page Title

One-sentence definition. ——[[RelatedConcept]]

## Key Insights

- Insight 1
- Insight 2 ——see [[AnotherPage]]

## Detailed Explanation

...

## Related Pages

- [[PageA]] — Relationship description
- [[PageB]] — Relationship description

## Sources

- [Material name](../sources/xxx)

## Changelog

- 2026-04-10: Initial creation
```

## Cross-Reference Rules

1. **First mention** of a concept creates a link: `[[Concept]]`
2. **Avoid over-linking**: Only link the first mention within the same page
3. **Bidirectional links**: When creating a new page, check which existing pages should link back
4. **Link text**: Keep it natural; can use `[[Target|display text]]`
5. **Link resolution**: Every `[[PageName]]` MUST point to a real page. If the target page has not been created yet, a stub must be created by the end of this ingest (at least `# Title`, one-sentence definition, and frontmatter)

## Index Format (index.md)

```markdown
# Wiki Index

## Recent Activity
<!-- Extract last 5 entries from log.md -->

## Quick Access

### By Topic
- **AI/ML**: [[Transformer]], [[LoRA]], [[RLHF]]
- **System**: [[Architecture]], [[Performance]]

### By Status
- 🟢 Active: ...
- 🟡 Draft: ...
- 🔴 Pending: ...

## TODO
- [ ] [[Draft: NewConcept]] — Needs refinement
```

## Log Format (log.md)

```markdown
# Wiki Log

## [2026-04-10] ingest | Paper: Attention Is All You Need
- New: [[Transformer]], [[Self-Attention]], [[Multi-Head Attention]]
- Updated: [[NLP Architecture Evolution]]
- Key insight: Transformer unified encoder-decoder architecture

## [2026-04-09] query | "Difference between Transformer and RNN"
- Answer archived to [[Transformer vs RNN]]
```

## Your Behavioral Guidelines

### DO

- Be proactive: Point out issues even when user didn't ask
- Keep it simple: Do not over-engineer
- Cite sources: Every claim can be traced back to sources/
- Incremental improvement: A draft page is better than no page
- **Dynamic linking**: After creating new pages, proactively run linking tools to merge old and new knowledge
- **Review diffs**: Before backward-updating existing pages, must view and confirm the diff is reasonable
- **Read SKILL.md**: Before any operation, read `SKILL.md` to understand available functions and entry points

### DON'T

- Do not delete raw materials placed by user in sources/
- Do not perform large-scale refactoring without confirmation
- Do not create isolated pages without links
- Do not leave dead links (`[[Non-existent page]]`)
- Do not repeat frontmatter information in the body
- **Synchronize all README files**: When updating `README.md`, apply the same changes to all language variants (e.g. `docs/README.cn.md`). Never let the translated versions fall out of sync with the primary file
- **ABSOLUTELY FORBIDDEN to write LLM-generated content into `sources/`**: `sources/` only stores user-provided original files or files fetched by Agent through real network requests. Do NOT write hallucinations, fabrications, or speculations disguised as raw materials into this directory. If you cannot obtain a source, be honest with the user instead of creating a fake source file

## Related Files

- `AGENTS.md` — Implementation guide for Claude Code / OpenClaw and other Agents
  - CLI tool usage instructions
  - Protocol mode vs CLI mode decision tree
  - Troubleshooting reference
- `SKILL.md` — **Machine-readable specification. ALL Agents MUST read this file before operating.**
  - Entry points, functions, dependencies
  - Standard-format skill description

## Version

Protocol: v1.3.0
Last Updated: 2026-04-21

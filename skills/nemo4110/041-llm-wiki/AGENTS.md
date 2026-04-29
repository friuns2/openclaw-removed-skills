# Agent Implementation Guide

> This document guides Claude Code, OpenClaw, and other AI Agents on how to use llm-wiki.
> **All Agents operating in this project directory MUST read and understand `SKILL.md` before performing any task.**

## Mandatory Pre-Flight Checklist

Before executing any wiki-related task, every Agent MUST:

1. **Read `SKILL.md`** — Understand the machine-readable specification, entry points, functions, and dependencies.
2. **Read `CLAUDE.md`** — Understand the core protocol and behavioral rules.
3. **Verify available tools** — Check whether CLI tools are available; if not, fall back to protocol mode (direct file operations).
4. **Respect `sources/` integrity** — Never write LLM-generated content into `sources/`.

Failure to follow the above may result in corrupted knowledge base, fabricated sources, or broken cross-references.

---

## Sources Directory Write Rules

> The integrity of `sources/` is the foundation of the entire knowledge base. Once raw materials are polluted, all derived wiki content loses credibility.

### Two Allowed Cases for Writing to `sources/`

| Case | Condition | Action |
|------|-----------|--------|
| A | User manually placed a file | Read-only, do not modify |
| B | User provided a URL/DOI and the file is not yet in `sources/` | Use network tools to fetch, verify non-empty and correct format, then write |

### Absolute Prohibitions

- **NEVER** save LLM-generated text, summaries, or speculative content as `.md`, `.txt`, or any format into `sources/`
- **NEVER** claim "downloaded" and create files without actually executing a network request
- **NEVER** "fall back" to generated content when fetching fails

### Standard Network Fetch Template

**Direct download (PDF, text files)**:

```bash
# Check if URL is reachable
curl -I -L "https://example.com/paper.pdf"

# Download to sources/
curl -L -o "sources/YYYY-MM-DD-description.pdf" "https://example.com/paper.pdf"

# Verify file is non-empty
ls -la "sources/YYYY-MM-DD-description.pdf"
```

**Rendered web pages (tech blogs, dynamic content)**:

Use Playwright tools to fetch page content:

```bash
# Use playwright to get rendered page
playwright screenshot --full-page "https://tech.blog.example.com/article" "sources/temp-screenshot.png"
```

Or use a Python script to get text:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://tech.blog.example.com/article")
    text = page.inner_text("article")  # or appropriate selector
    with open("sources/YYYY-MM-DD-description.md", "w", encoding="utf-8") as f:
        f.write(text)
    browser.close()
```

**DOI resolution**:

```bash
# DOI usually redirects to publisher pages; paywalls may apply
curl -L -o "sources/paper.html" "https://doi.org/10.xxxx/xxxxx"

# Prefer open-access versions like arXiv
curl -L -o "sources/paper.pdf" "https://arxiv.org/pdf/xxxxx.pdf"
```

### Fetch Failure Handling Flow

```
Fetch attempt
    |
    +-- Success → Verify file non-empty → Write to sources/ → Continue ingest
    |
    +-- Failure (404/403/paywall/anti-bot)
          |
          +--> Do NOT create any file in sources/
          +--> Create or update [[Pending: SourceName]] stub page in wiki/
          +--> Record failure reason in log.md
          +--> Reply to user explaining the situation and request assistance
```

### Correct vs Incorrect Examples

**Incorrect** (absolutely forbidden):

```
User: Please ingest these papers [provides 5 titles, no URLs]

Agent: (Did not execute any curl/playwright call)
      Directly creates sources/paper-1.md with LLM-generated "summary"
      Then creates wiki pages based on fabricated content
```

**Correct** (no URL, Agent proactively searches):

```
User: Please ingest these papers [provides 5 titles, no URLs]

Agent: Uses WebSearch to find open-access versions for each title
      → Found arXiv link for paper 1, author homepage PDF for paper 2
      Replies to user: "I found the following possible sources, please confirm:
      1. Paper Title 1 → https://arxiv.org/pdf/xxxx.pdf
      2. Paper Title 2 → https://author-page.edu/paper2.pdf
      I will download and ingest after your confirmation."
      (User confirms → Execute curl download → Continue ingest)
```

**Correct** (URL provided):

```
User: Please ingest https://arxiv.org/pdf/2401.xxxxx.pdf

Agent: Execute curl -L -o "sources/2026-04-20-paper.pdf" "https://arxiv.org/pdf/2401.xxxxx.pdf"
      Verify file size > 0
      Read PDF content
      Continue normal ingest flow
```

**Correct** (fetch failed):

```
User: Please ingest https://example.com/paywalled-paper.pdf

Agent: Execute curl -I "https://example.com/paywalled-paper.pdf"
      → Returns 403 Forbidden
      Do NOT create sources/ file
      Create wiki/Pending-Paywalled-Paper.md (stub, marked as pending)
      Record in log.md: "[Date] pending | Paywall prevented fetching xxx"
      Reply to user: "This paper requires paid access; I cannot fetch it automatically.
      Please download manually and place in sources/, or provide an open-access link."
```

---

## File Type Processing Strategy

> **Key principle**: Different file types require different reading strategies; avoid using the Read tool directly on binary files.

### Decision Tree

```
File Type Recognition
    |
    +-- Text files (.md, .txt, .json, .yaml, .py, .js, etc.)
    |     +--> Use Read tool directly
    |
    +-- PDF files (.pdf)
    |     +-- Check dependency: is PyMuPDF (pymupdf) installed?
    |     |     +-- Yes -> Use Python script to read
    |     |     +-- No  -> Install dependency first, then read
    |     +--> Process via scripts/read_pdf.py or Python code
    |
    +-- Image files (.png, .jpg, .jpeg, .gif, etc.)
    |     +--> Use Read tool (vision model supported)
    |
    +-- Office documents (.docx, .xlsx, .pptx)
    |     +--> Requires python-docx / openpyxl, etc.
    |
    +-- Other binary formats
          +--> Find or create corresponding Python processing script
```

### PDF File Processing Detailed Flow

**Step 1: Check dependency**

```bash
# Check if PyMuPDF is installed
python -c "import fitz; print(fitz.__doc__[:30])"
```

If it fails, install first:

```bash
pip install pymupdf>=1.25.0
```

**Step 2: Read PDF content**

**Method A: Use existing script**

```bash
# Read all pages
python scripts/read_pdf.py sources/paper.pdf

# Read specific page range
python scripts/read_pdf.py sources/paper.pdf 1-10
```

**Method B: Use Python code (Recommended: PyMuPDF)**

```python
import fitz  # PyMuPDF

doc = fitz.open("sources/paper.pdf")
for page in doc:
    print(page.get_text())
doc.close()
```

**Fallback: pdfplumber (table extraction)**

If PyMuPDF performs poorly on complex tables, fall back to `pdfplumber` (note: install secure version >= 0.11.8 to fix CVE-2025-64512):

```python
import pdfplumber

with pdfplumber.open("sources/paper.pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```

**OCR last resort**

For scanned PDFs or when all above methods fail, use `pdf2image` + `pytesseract` for OCR.

**PDF extraction quality fallback**

If pdfplumber produces garbled text (especially with Chinese, special fonts, or complex academic layouts), try these alternatives:

**Method C: Use PyMuPDF (fitz)**

PyMuPDF is typically more reliable for CJK fonts and complex PDF text extraction:

```bash
# Install
pip install pymupdf
```

```python
import fitz  # PyMuPDF

doc = fitz.open("sources/paper.pdf")
for page in doc:
    print(page.get_text())
```

**Method D: Convert to images then OCR (last resort)**

For scanned PDFs or when all above methods fail, use `pdf2image` + `pytesseract` for OCR — slower but more robust.

### Text File Processing

Use Read tool directly:

```python
# Directly read Markdown, text, code files
Read("sources/notes.md")
Read("sources/config.yaml")
Read("sources/script.py")
```

### Image File Processing

Read tool supports vision models:

```python
# Read tool can process images and return visual content
Read("sources/diagram.png")
Read("sources/screenshot.jpg")
```

### Dependency Management

**Dependency file location**: `src/requirements.txt`

**Included dependencies**:
- `click>=8.0.0` - CLI framework
- `pyyaml>=6.0` - YAML parsing
- `pymupdf>=1.25.0` - PDF processing (PyMuPDF, supports CJK fonts and complex layouts)

**Fallback dependencies** (only when PyMuPDF table extraction is poor):
- `pdfplumber>=0.11.8` - PDF table extraction (secure version required for CVE-2025-64512)
- `pdfminer.six>=20251107` - PDF underlying library

**Installation commands**:

```bash
# Using conda (recommended)
conda activate llm-wiki
pip install -r src/requirements.txt

# Using pip
pip install -r src/requirements.txt

# Using uv (if you have it)
uv pip install -r src/requirements.txt
```

---

## Two Work Modes

### Mode A: Protocol Mode (Recommended)

**Applicable scenario**: User uses natural language commands, e.g. "Please ingest material", "Query wiki"

**Your behavior**:
1. Read `CLAUDE.md` to understand the protocol
2. Read `SKILL.md` to understand available functions, entry points, and dependencies
3. **Select the correct reading strategy based on file type** (see "File Type Processing Strategy" above)
4. Operate files directly (read, write, edit)
5. Follow Ingest/Query/Lint workflow
   - **Must create stub pages during Ingest**: Any `[[Concept]]` first appearing in a new page must have a corresponding stub created synchronously (at least frontmatter + one-sentence definition) if the target page does not exist
   - **Bidirectional link check**: After updating existing pages, check if new pages should link back

**Not needed**: Invoke any CLI commands

### Mode B: CLI Mode

**Applicable scenario**: User explicitly requests command-line tools, or scripting operations are needed

**Your behavior**:
1. Check CLI availability: `python -m src.llm_wiki --help`
2. Use corresponding commands to assist execution

---

## CLI Tool Reference

### Check Dependencies and Virtual Environment

The project may already have a virtual environment; check first:

```bash
# Check if virtual environment exists in project directory
ls -la .venv/  # or venv/

# If yes, use virtual environment's Python
.venv/Scripts/python -m src.llm_wiki --help  # Windows
.venv/bin/python -m src.llm_wiki --help      # Linux/macOS
```

### Check CLI Availability

```bash
# Using virtual environment Python (preferred)
.venv/Scripts/python -c "from src.llm_wiki.core import WikiManager; print('OK')"

# Or using system Python
python -c "from src.llm_wiki.core import WikiManager; print('OK')"

# Command-line entry point
# python -m src.llm_wiki --help
```

### Available Commands

```bash
# View wiki status
python -m src.llm_wiki status

# Health check
python -m src.llm_wiki lint

# View all command help
python -m src.llm_wiki --help
```

| Command | Purpose | Note |
|---------|---------|------|
| `status` | View wiki overview | Page count, recent activity |
| `lint` | Health check | Orphan pages, dead links, etc. |
| `ingest <path>` | Ingest material (auxiliary) | Only preview; actual processing requires protocol mode |
| `query <text>` | Query wiki (auxiliary) | Only lists pages; actual query requires protocol mode |

**Note**: `ingest` and `query` require LLM processing; CLI only provides auxiliary functions. Actual content processing is recommended via **protocol mode** direct file operations.

### CLI Auxiliary Workflow Example

```bash
# Use virtual environment (recommended)
PY=".venv/Scripts/python"  # Windows
PY=".venv/bin/python"      # Linux/macOS

# 1. Check wiki status first
$PY -m src.llm_wiki status

# 2. Run lint to check for issues
$PY -m src.llm_wiki lint

# 3. User requests ingesting new material; you (Agent) process directly:
#    - Read sources/new-paper.pdf
#    - Extract insights
#    - Update pages under wiki/
#    - Append log.md
```

---

## Decision Tree

```
User Input
    |
    +-- Natural language ("ingest sources", "query wiki")
    |     +--> Protocol mode: operate files directly
    |
    +-- Explicit CLI ("run wiki lint", "check status")
    |     +--> CLI mode: execute commands and explain output
    |
    +-- Scripting needs ("batch process", "automation")
          +--> CLI mode: generate / execute scripts
```

---

## Important Principles

1. **Default to protocol mode**: Most users expect natural language interaction
2. **CLI is supplementary**: For status viewing, batch operations, script integration
3. **Do not assume CLI is installed**: User may not have installed dependencies; prefer pure file operations
4. **Be transparent**: If using CLI, tell the user what you are doing
5. **Synchronize all README files**: When updating `README.md`, apply the same changes to all language variants (e.g. `docs/README.cn.md`). Never let the translated versions fall out of sync with the primary file

---

## Example Conversations

### Scenario 1: Natural Language Command

```
User: Please ingest sources/paper.pdf

You (Protocol mode):
1. Read sources/paper.pdf
2. Extract key insights
3. Create wiki/Attention-Mechanism.md (with [[Self-Attention]], [[Transformer]], etc. links)
4. Check dead links: Create wiki/Self-Attention.md and wiki/Transformer.md stub pages
5. Update wiki/index.md
6. Append log.md

Reply: Ingested paper.pdf, created [[Attention Mechanism]] page, and synchronously created stub pages for [[Self-Attention]], [[Transformer]], etc...
```

### Scenario 2: Explicit CLI Request

```
User: Run wiki lint to see if there are any issues

You (CLI mode):
1. Execute: python -m src.llm_wiki lint
2. Analyze output
3. Explain issues and provide fix suggestions

Reply: Found 3 orphan pages: [[PageA]], [[PageB]]...
```

### Scenario 3: Using Virtual Environment

```
User: Check wiki status

You: Found .venv/ directory in the project; using virtual environment
    .venv/Scripts/python -c "from src.llm_wiki.core import ..."
    → Successfully retrieved information

Reply: Wiki currently has 15 pages; recent activity was...
```

### Scenario 4: Using conda Environment

```
User: Check wiki status

You: Detected CONDA_PREFIX environment variable; using conda environment
    $CONDA_PREFIX/bin/python -c "from src.llm_wiki.core import ..."
    → Successfully retrieved information

Reply: Wiki currently has 15 pages; recent activity was...
(Using conda environment: llm-wiki)
```

### Scenario 5: CLI Dependencies Not Installed (Protocol Mode Fallback)

```
User: Run wiki lint

You: Attempted execution
    .venv/Scripts/python -c "from src.llm_wiki.core import WikiManager"
    → Failed (ModuleNotFoundError: .venv does not exist or dependencies not installed)

You: Switched to protocol mode; reading files directly
    - Read wiki/ to count pages
    - Read log.md to get recent activity
    - Manually executed lint logic

Reply: Wiki currently has 15 pages; found 3 orphan pages: [[PageA]]...
(Note: CLI dependencies not installed; I retrieved this information by reading files directly)
```

---

## Bidirectional Update Implementation Guide

> This section guides Agents on how to perform dynamic linking and bidirectional updates during ingest.
> **Before using any `link` or `relink` CLI commands, you MUST have read `SKILL.md` to understand the function signatures, inputs, and workflow.**

### Why Bidirectional Updates Are Needed

Traditional ingest only creates new pages; existing pages do not automatically reflect new knowledge. Bidirectional updates let the knowledge base **self-improve** over time:
- New paper improves an old method → old page automatically gets "Latest Progress" section
- New work contrasts with old work → both pages add comparison links
- New work depends on old concept → old concept page gets backlinked

### Linking Workflow

```
Finish new page creation
    |
    v
+----------------------------------+
| 1. Run: wiki link --source PAGE  |  <-- CLI discovers relations
|         --mode light             |
+----------------------------------+
    |
    v
+----------------------------------+
| 2. Agent reviews relation report |  <-- LLM judges relevance
|    Only process score >= 0.5     |
+----------------------------------+
    |
    v
+----------------------------------+
| 3. For each high-confidence rel: |
|    a. Read existing page         |
|    b. Analyze old vs new         |
|    c. Choose merge strategy      |
|    d. Run: wiki link --target    |
|    e. Review diff, then apply    |
+----------------------------------+
    |
    v
Update log.md, record operations
```

### Merge Strategy Decision Tree

```
Relation between new page and existing page
    |
    +-- Same field, different work
    |     +--> link_only (add to "Related Pages")
    |
    +-- New work extends/improves old method
    |     +--> append_section (add "Latest Progress")
    |
    +-- New work contrasts with old work
    |     +--> append_section (add "Comparison with xxx")
    |     +--> append_related (bidirectional links)
    |
    +-- New work corrects old concept
    |     +--> update_concept (update definition, use with care)
    |     +--> append_section (add "Concept Evolution")
    |
    +-- New work heavily depends on old concept
          +--> append_related (add backlink to old page)
```

### CLI Command Reference

**Discover relations (light mode):**
```bash
python -m src.llm_wiki link --source "Bid2X" --mode light
```
Output: Markdown relation report with related pages, score, relation type, suggested action

**Discover relations (deep mode, with embedding):**
```bash
python -m src.llm_wiki link --source "Bid2X" --mode deep --max-related 10
```

**Execute specific merge (with diff review):**
```bash
# Preview
python -m src.llm_wiki link --source "Bid2X" --target "RTBAgent" \
    --strategy append_related --dry-run

# Apply
python -m src.llm_wiki link --source "Bid2X" --target "RTBAgent" \
    --strategy append_related
```

**Batch global linking:**
```bash
# Global deep linking for pages added in the last 7 days
python -m src.llm_wiki relink --mode deep --dry-run

# Specify date range
python -m src.llm_wiki relink --since 2026-04-20 --mode deep
```

### Agent Implementation Pattern (Protocol Mode)

**Scenario: User requests ingesting sources/new-paper.pdf**

```
Agent:
1. Read sources/new-paper.pdf
2. Extract insights, create wiki/NewMethod.md
3. Check dead links, create stub pages
4. Run CLI (if virtual environment available):
   .venv/Scripts/python -m src.llm_wiki link --source "NewMethod" --mode light
   → Get relation report
5. For score >= 0.5 relations, e.g. [[OldMethod]]:
   a. Read wiki/OldMethod.md
   b. LLM analysis: "NewMethod is an improvement over OldMethod, extending xxx capabilities"
   c. Decision: Use append_section strategy, append "Relationship with NewMethod"
   d. Run CLI to generate diff:
      .venv/Scripts/python -m src.llm_wiki link \
        --source "NewMethod" --target "OldMethod" \
        --strategy append_section --dry-run
   e. Review diff, confirm it is reasonable
   f. Apply modification (remove --dry-run)
6. Update log.md, record new pages and relation updates
7. Update wiki/index.md
```

### Safety Rules

1. **Always --dry-run first**: Generate diff for review before applying
2. **Append only, never replace**: `append_related` and `append_section` are safe strategies
3. **Use update_concept with caution**: Only when new information genuinely corrects an old definition
4. **Limit batch updates**: Single source should trigger no more than 5 backward updates
5. **Automatic backups**: CLI tools automatically back up to `wiki/.backups/`; rollback available

### Troubleshooting

| Problem | Solution |
|---------|----------|
| `wiki link` errors: page not found | Confirm page has been created; check title spelling |
| Diff is unreasonable | Do not apply; manually edit the page instead |
| False positive relation to unrelated page | Ignore (score usually < 0.3); do not execute merge |
| Strategy not in allowed list | Check config.yaml `linking.deep_mode.strategies_allowed` |
| Backup directory too large | Manually clean old backups in `wiki/.backups/` |

---

## Technical Details

### CLI Entry Points

- **Module**: `src.llm_wiki`
- **Main file**: `src/llm_wiki/commands.py`
- **Core logic**: `src/llm_wiki/core.py`

### Auxiliary Scripts

Project includes auxiliary scripts (`scripts/`):
- `scripts/wiki-status.sh` — Quick wiki status view
- `scripts/wiki-lint.sh` — Run health check
- `scripts/init-wiki.sh` — Initialize new project

### Dependencies and Virtual Environment

Dependency file: `src/requirements.txt`
- `click` - Command line framework
- `pyyaml` - YAML parsing

#### Check Dependencies (including virtual environment detection)

```python
import importlib.util
from pathlib import Path
import subprocess
import sys

# 1. Detect virtual environment (uv/venv or conda)
venv_paths = [
    Path(".venv"),           # uv / modern tools
    Path("venv"),            # traditional
]
# Detect conda environment
conda_env = Path(os.environ.get("CONDA_PREFIX", ""))
if conda_env.exists():
    venv_python = conda_env / "python.exe" if sys.platform == "win32" else conda_env / "bin" / "python"
else:
    for venv in venv_paths:
venv_python = None
for venv in venv_paths:
    if venv.exists():
        venv_python = venv / "Scripts" / "python.exe" if sys.platform == "win32" else venv / "bin" / "python"
        break

# Decision path
if venv_python and check_dep("src.llm_wiki", venv_python):
    print(f"Using virtual environment: {venv_python}")
    python_cmd = str(venv_python)
elif check_dep("src.llm_wiki"):
    print("Using system Python")
    python_cmd = "python"
else:
    print("Dependencies not installed; using protocol mode")

# 2. Check if dependency is available
def check_dep(module_name, python_path=None):
    py = python_path or sys.executable
    result = subprocess.run([py, "-c", f"import {module_name}"], capture_output=True)
    return result.returncode == 0
```

### Relationship with CLAUDE.md

- `CLAUDE.md`: Defines **user-visible** working protocol
- `AGENTS.md`: Defines **Agent-internal** implementation strategy
- `SKILL.md`: Machine-readable specification that **ALL Agents MUST read** before operating

They are not contradictory: Protocol mode implements the semantics of CLAUDE.md; CLI mode provides additional tooling capabilities.

---

*Agent Guide Version: 1.3.0*
*Last Updated: 2026-04-21*

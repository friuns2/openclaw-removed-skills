---
name: google-stitch-workflow
version: 1.4.2
description: Use when working with Google Stitch through a disciplined MCP-first workflow. Prefer this skill for project inspection, controlled screen generation and editing, prompt structuring, and failure recovery.
---

# Google Stitch Workflow

Use Google Stitch primarily as a design exploration and screen-iteration system.
For greenfield apps, once a screen direction is accepted and exportable code is available in the active environment, use the generated HTML/CSS as the translation base rather than recreating the design from screenshots by hand.

This skill separates three concerns that are often conflated:

- verified MCP capabilities in the current environment
- browser-only Stitch product features
- optional local workflow conventions that improve traceability

Use this skill when the task involves one or more of:

- inspecting Stitch projects and screens before making changes
- generating a new screen from a text prompt
- refining an existing generated screen with small, controlled edits
- organizing a multi-screen redesign effort without losing revision history
- converting vague design requests into structured prompts

Do not assume the browser UI, the public product marketing, and the MCP surface expose the same operations.

## When to use this skill

Use this skill when the task involves one or more of:

- inspecting Stitch projects and screens before making changes
- generating a new screen from a text prompt
- refining an existing generated screen with small, controlled edits
- organizing a multi-screen redesign effort without losing revision history
- converting vague design requests into structured prompts

Do not assume the browser UI, the public product marketing, and the MCP surface expose the same operations.

Do not use Stitch as the primary path when the real task is:

- implementing production UI code directly
- making deterministic pixel-perfect edits to an existing coded screen
- redesigning an app without reliable reference screens or screenshots
- planning an entire product in one step without screen-level iteration
- evaluating engineering feasibility without a prior visual direction

## When not to use this skill

Do not use Stitch as the primary path when the real task is:

- implementing production UI code directly
- making deterministic pixel-perfect edits to an existing coded screen
- redesigning an app without reliable reference screens or screenshots
- planning an entire product in one step without screen-level iteration
- evaluating engineering feasibility without a prior visual direction

Important nuance:

- for an existing coded app, Stitch is usually best as a design reference and iteration surface
- for a new app with no established implementation, accepted Stitch exports can be the fastest way to seed the first real UI structure

## Quick operating rules

- **rewrite before acting** — before any `generate`, `edit`, or `variants` call, rewrite the user request into a stronger design prompt or a tighter edit intent
- **inspect before editing** — always inspect the project and target screen first; verify whether the screen is actually generated content (if `htmlCode` exists, it's more likely editable)
- **pick the operation class first** — decide whether this pass is `generate`, `edit`, or `variants`; do not blur exploration, refinement, and branching in one move
- **work one screen at a time** — one short generation followed by controlled edits; keep one screen as the unit of iteration
- **keep prompts short, explicit, and preservation-oriented** — start with the smallest prompt that can produce a useful screen
- **review the visual result before the next major step** — review screenshots or visual artifacts immediately after each generate/edit; ask the user to choose using a human description, not an opaque screen ID
- **move to code only after one direction is clearly accepted** — confirm the visually reviewed canonical screen before export or translation; move to code only after the screen family is coherent
- **stop repeating failing payloads** — do not brute-force retries with the same parameters
- **act as creative director** — Stitch is the designer, you provide the direction
- **define what must NOT change** — the single most important iteration rule: tell Stitch what to keep, not just what to change
- **hub-first for multi-screen projects** — generate a hub screen first, derive all other screens via edit, never fresh generate siblings
- **report state after every pass** — after each generate/edit/variants step, report the project id, screen id, artifact location if any, a short design judgment, and the next recommended move
- **treat wrapper enhancements as optional** — not part of the Stitch MCP contract

## Complete process order

This is the recommended sequence from blank canvas to accepted design:

1. **Empathy** → Who is the user? What should they feel?
2. **Creative direction** → Concrete vocabulary, metaphors, not abstract words
3. **Prompt with direction** → Describe what the site *is* and how it *feels*
4. **Design system** → Set color hierarchy, font hierarchy, corner radius in DESIGN.md
5. **Layout** → Use variants (Explore level) with scoped layout prompts
6. **Copywriting** → Generate real copy matching the creative brief
7. **Iterate** → One screen at a time, scoped refinements
8. **Export/code** → Only after the direction is clearly accepted

**Before step 1, create a feature matrix.** Map which features appear on which screen. Only start generating once the coverage is clear — this makes every generate/edit call a deliberate execution step, not a discovery. Three focused screens you've thought through beat ten screens you discover issues with during generation.

At the start of each pass, choose one operation class on purpose:

- `generate` for a new canonical screen
- `edit` for a focused improvement to an existing screen
- `variants` for controlled branching from a base direction

Skip steps and you'll iterate more later. Follow them and each step builds on the last.

---

## Creative Direction

### Creative direction framework

The single biggest lever for better Stitch results is **direction before description**. A generic prompt gives a generic screen. A directed prompt gives something you can actually iterate on.

#### 1. Start with empathy

Before touching color, typography, or layout, answer two questions:

- Who is the user?
- What should they feel when they arrive?

Everything else flows from these answers.

#### 2. Replace abstract words with concrete vocabulary

Bad: "make it look high-end", "patriotic", "sporty", "modern"  
Good: "architectural limestone", "neoclassical", "ink on paper", "clay of an old track"

Concrete aesthetic words give Stitch something to build from. Abstract words give you the same generic output as everyone else.

**Tip:** Use an LLM (Gemini works well) to help craft prompts with specific design concepts and aesthetic descriptions. Feed it your empathy answers and ask it to return design vocabulary you wouldn't have thought of.

#### 3. Use metaphors to find layouts

When stuck on layout, ask: "If my site were a physical object, what would it be?"

- A coffee table book → lookbook editorial layout with full-page imagery
- A newspaper → dense typographic grid
- A luxury travel magazine → large headings over cinematic photography

This bridges the gap between "I know what I want" and "I don't know what to prompt."

### Design system as DNA

Stitch auto-generates a design system for every project. Treat it as the DNA of your design, not decoration. It covers colors, fonts, components, and — critically — a structured creative brief.

#### DESIGN.md

Stitch generates a **DESIGN.md** tab covering creative direction, color hierarchy with roles, typography rationale, elevation, components, and dos/don'ts. This is what drives the design system.

Treat `DESIGN.md` as a two-layer artifact:

- a token layer with the concrete values the system depends on
- a prose layer with the reasoning for what those values are supposed to do

Keep those two layers aligned. If the rationale and the token values drift apart, the design system stops being reliable for both Stitch and coding agents.

Think of tokens as **named design decisions**, not loose variables. `primary` is not just a hex slot; it is the role for the main ink of the product. `body-main` is not just a size; it is the role for default reading copy. The current value fills that role, but the role is the durable part.

**What you can do with DESIGN.md:**

- edit it directly in Stitch to course-correct
- have an LLM generate an improved one
- copy it to new projects for consistency (paste it into a new prompt and Stitch builds from it)
- copy it into your coding agent (VS Code, Cursor, etc.) as a rule set that maintains design consistency when translating Stitch output to real code

**DESIGN.md portability pattern:**

1. Generate a design in Stitch and let it create the DESIGN.md
2. Review and refine the DESIGN.md inside Stitch
3. Copy the DESIGN.md content
4. Paste it into your coding agent's context (system prompt, rules file, or inline)
5. Use it as the style authority when translating Stitch exports to production code

This bridges the gap between Stitch's design environment and your coding environment, ensuring the coding agent respects the same typography, color hierarchy, spacing rules, and component decisions.

This is the single most portable artifact in your Stitch workflow. Invest time in getting it right.

**Creating a custom DESIGN.md outside Stitch:**

1. Write a minimal design-system brief first: visual posture, intended mood, main user job, and 3-5 things the UI must not resemble.
2. Turn that brief into a compact `DESIGN.md` with:
   - YAML front matter for the durable tokens: color roles, typography, radius, spacing, and only the stable component rules
   - markdown sections for the why: overview, colors, typography, layout, components, and do's/don'ts
3. Keep the token layer concrete. Keep the prose layer directional. Do not mix them.
4. Define the baseline role anchors clearly:
   - `primary` for the main ink and core text emphasis
   - `neutral` for the canvas and emotionally neutral surfaces
5. In component rules, prefer references to roles over hardcoded raw values. A button should usually point at `primary`, `tertiary`, `on-primary`, or another named role instead of embedding a literal color directly.
6. Keep the Components section conservative. Encode the stable reusable rules, not every temporary visual exception.
7. In Stitch: Design Systems → Create New → paste the finished `DESIGN.md` → Save
8. Stitch visualizes the design system immediately — colors, fonts, spacing all rendered
9. Generate screens using this custom design system as the base

This pattern is useful when you've already brainstormed design direction with a coding agent and want to transfer that direction into Stitch.

If the copied `DESIGN.md` will become a real project artifact outside Stitch,
validate it before treating it as authoritative:

```bash
npx @google/design.md lint DESIGN.md
npx @google/design.md diff DESIGN-before.md DESIGN-after.md
```

Use `lint` as part of the normal edit loop, not just as a final gate: read the current design system, make the change, lint it, fix the findings, then re-check. Use `diff` before and after meaningful revisions to catch token drift or accidental regressions in the design system itself.

**Importing from an existing website:**

Beyond pasting a URL for style hints in a prompt, you can import a website's design as a formal design.md file via the design systems panel: provide the URL and Stitch crawls the site, extracting style and typography into a structured design system. This gives you an editable, portable design foundation rather than a one-off style hint.

#### Color hierarchy (not just a palette)

Colors have jobs based on visual weight and importance. Reach for the role first, then the value that currently fills it. That keeps the design system semantic instead of turning it into a bag of swatches.

`Primary` and `neutral` are the anchor roles. In practice, `primary` usually carries the reading ink and strong emphasis, while `neutral` carries the background and surface system.

Colors have jobs based on visual weight and importance:

| Role | Usage | Visual weight |
|------|-------|---------------|
| **Neutral** | 80-90% of the canvas — the background | Lightest |
| **Primary** | Headings, body text, core content | Dark, high contrast |
| **Secondary** | Subdued support text | Softer than primary |
| **Tertiary** | Accent, CTAs, hover states | Loudest, but used the least |

The tertiary color is third in volume but first in visual pull. Choose it deliberately.

#### Font hierarchy

Stitch sets up three font slots: headline, body, and label.

Opinionated guidance:
- Choose fonts that match your creative direction, not just "what looks nice"
- **Space Grotesk is great for labels and timestamps. It does not belong in headlines.** (Stitch will put it there — override it.)
- A font like Public Sans works for both headline and body when you want official-but-approachable
- Match the font personality to the emotional goal

#### Corner radius as a design decision

Corner radius is not neutral — it communicates:
- **More rounded** → friendly, approachable, casual
- **Sharp edges** → editorial, serious, stationary-like

Decide based on the feeling you want, not a default.

---

## Prompting & Generation

### App vs Web toggle

Before generating, switch between **App** (mobile/narrow) and **Web** (wide/horizontal) in the Stitch UI. This fundamentally changes the output — Stitch composes a proper layout rather than stretching a design. Don't forget this toggle when switching between mobile and desktop targets.

### Model selection & thinking mode

Stitch offers multiple generation modes. Pick based on where you are in the process:

| Mode | When to use |
|------|------------|
| **Gemini Flash** (`GEMINI_3_FLASH`) | Fast exploratory passes, iterating on direction |
| **Gemini Pro** (`GEMINI_3_PRO`) | Complex multi-screen dashboards, when quality matters more than latency |
| **Redesign** | You have a screenshot or existing site to work from |
| **ID8** | You only have a vague problem statement; Stitch helps you construct a plan |
| **Live** | Real-time conversational editing; changes appear as you chat (voice-based, AI sees your screen) |

**Thinking mode:** Stitch 2.0 exposes a **Thinking** toggle alongside model selection. Thinking mode takes a few seconds longer but follows complex instructions significantly better than fast mode. Use it when:
- the prompt specifies detailed section-by-section layout
- the design has complex multi-region composition
- you need the output to match a specific structure, not just a general vibe

**Tip:** For complex apps with many screens, use Pro + Thinking for the first generation then Flash for quick iterations.

### Component isolation

Stitch's strongest tendency is to generate **full application layouts** — sidebar, header, navigation, content — even when you only asked for a button. To counteract this, include this incantation when generating individual components:

> "Design a single standalone UI component — do NOT generate a full application screen or layout. Show it isolated on a neutral background, like a component in a design system."

Also add: "Make sure all text is fully visible — do not truncate any labels or text with ellipsis."

This produces dramatically better results for component work.

### First prompt: don't start blank

A common pattern from other AI design tools is to start with a blank page and build the design system manually first. **This does not work well in Stitch.** Starting with "build me a blank page with no design system" produces noticeably worse results than letting Stitch generate its own design system from a descriptive initial prompt.

Instead, include your theme and color choices directly in the first prompt:

> "Build me a crypto dashboard with purple as the primary color in dark mode"

Stitch generates the design system (primary/secondary/tertiary/neutral colors, fonts, components) alongside the first screen. You can adjust everything afterward, but you get a much stronger starting point than starting from nothing.

**Also:** mobile designs currently tend to be higher quality than web. If output quality matters more than platform, consider generating mobile first.

### Prompt construction: incremental enrichment

Don't write the final prompt in one shot. Build it up:

1. Start with the app description (1-2 sentences)
2. List the specific screens by name (e.g., "mission overview, trajectory, weather, mission log, system status")
3. Add core functionality per screen
4. Set the vibe with concrete adjectives
5. Optionally: use another AI tool (Gemini works well) to iteratively refine the prompt before pasting into Stitch — this produces significantly better results than writing the prompt directly in Stitch

Simple prompts work for simple apps. Complex dashboards benefit from upfront enrichment.

### PRD + reference image pattern

The most reliable way to get a strong first generation is to combine a **PRD** (Product Requirements Document) with a **reference screenshot**:

1. Find a design you like on the web
2. Capture a full-page screenshot (use a browser extension like GoFullPage — wait for all animations/lazy loads to finish first)
3. Paste the screenshot into ChatGPT or Gemini with a prompt like: *"I want to reference the design in the attached image to create a detailed PRD for a [type of app]. Include design principles, layout system, typography, color palette, components, and page structure."*
4. Review and tweak the generated PRD
5. In Stitch: paste the PRD + attach the reference image together as your first prompt

This produces significantly better results than typing a design description from scratch. The PRD gives Stitch structural guidance (layout system, component hierarchy, color roles) while the reference image anchors the visual direction.

**Tip:** The PRD doesn't need to be long. Even a bullet-point outline covering layout, typography, and color intent is better than a vague one-liner. Stitch will generate its own design system from the PRD, so focus on *what* and *why*, not on exact pixel values.

### Prompt structure template

Every good Stitch prompt has four layers. Omit one and Stitch fills the gap with generic defaults — that's where "AI slop" comes from:

1. **Context** — who and what: industry, audience, app reference ("Like Linear's dashboard")
2. **Structure** — layout and components: sidebar navigation, card grid, hero section, KPI cards with sparklines
3. **Aesthetic** — visual tone using precise keywords (see style keyword table below)
4. **Constraints** — device, format, what must NOT change

### Style keyword reference

Stitch relies on precise design vocabulary. Use these keywords deliberately:

| Keyword | What Stitch generates |
|---------|---------------------|
| `minimal` / `clean` | Lots of whitespace, restrained palette, simple geometry |
| `editorial` / `magazine-style` | Large typography, dramatic whitespace, museum-curatorial feel |
| `brutalist` / `neobrutalist` | Thick black borders, clashing colors, hard shadows, monospaced type |
| `glassmorphism` | Frosted translucent cards over colorful backgrounds, blur effects |
| `dark mode` | Dark backgrounds with light text, often paired with accent colors |
| `premium` / `luxury` | Restrained palette, serif typography, generous spacing |
| `playful` / `consumer` | Rounded shapes, bright colors, friendly illustrations |
| `vintage` | Texture, paper grain, serif type, aged feel |
| `retro` | Modern homage to past era (80s synthwave, pixel art, neon) |

**Vintage ≠ retro.** Vintage gives you a 19th-century cookbook. Retro gives you 80s neon. Be specific.

**Color directions:** monochromatic, neutral with accent, vibrant on dark, pastel, muted/earthy — or specific: "indigo accent", "emerald green", "warm amber"

### Section-by-section prompt pattern

For best results with complex layouts, structure the prompt as:

1. **Context line** — device and app type: "A mobile dashboard for a crypto tracking app"
2. **Aesthetic line** — visual direction: "dark mode aesthetics with neon purple and green accents"
3. **Section-by-section layout** — each section gets its own sentence: "Top section shows total portfolio value, below that a graph showing a 7-day trend"

Example (web): "A modern clean landing page for a SaaS productivity tool called Flowstate. Wide hero section with a headline 'focus faster' subtext and primary blue CTA button. Below, a three-column feature grid with icons, minimalist aesthetics with lots of white space."

This pattern works better than listing features without spatial context.

### Adjective-driven mood language

Stitch relies on **adjectives to identify mood** rather than exact structural descriptions. "Warm, inviting, premium" works better than "rounded corners, 16px padding, serif font." When prompting, prefer mood and intent language first, then add structure afterward.

### URL-based style extraction

Two approaches, depending on depth:

**Quick (paste in prompt):** Paste an existing website URL into Stitch's prompt area. Stitch extracts the color scheme, typography, and general visual vibe as a starting point. This avoids reinventing a design language that already exists.

**Structured (import as design.md):** Via the design systems panel, provide a URL and Stitch crawls the site, extracting style and typography into a structured design system file. This gives you an editable, portable design foundation rather than a one-off style hint.

### Wireframe-to-design from photos

Upload a photo of a paper sketch and use this prompt pattern:

> "Turn this wireframe into a [fidelity level] [platform] [screen type], [aesthetic direction]"

Example: "Turn this wireframe into a high fidelity iOS login screen, clean white background." Stitch converts scribbles into proper UI elements.

**Use Pro + Thinking for wireframe uploads.** Flash produces noticeably weaker results with sketch/wireframe inputs — the output tends to look flat and generic. Pro + Thinking interprets spatial relationships from drawings significantly better.

Expect variable quality from hand-drawn input. Results depend heavily on sketch clarity and prompt specificity. The impressive examples on social media often come from clean, well-structured sketches combined with detailed prompts.

---

## Iteration & Refinement

### Continue suggestions

After generating a screen, Stitch suggests one-click follow-up edits (e.g., "Add a buy/sell button for quick trades"). Check these before writing your own follow-up prompt — they're often useful and faster than crafting a custom edit.

### Variants

Variants let you generate multiple takes on a design and scope the exploration.

**Creativity levels:**

| Level | Behavior | When to use |
|-------|----------|-------------|
| **Refine** | Small tweaks, close to original | Polishing an accepted direction |
| **Explore** | Balanced creativity — the sweet spot | Finding layout and imagery options |
| **Reimagine** ("YOLO" in Stitch UI) | Wild reinterpretation | Breaking out of a rut, early exploration |

**Scoping:** Scope variants to specific aspects: **layout**, **color scheme**, **images**, **text**, or **font**. This prevents unwanted changes in areas you've already accepted.

**Best practices:**

1. Generate 3-5 variants (adjustable count in the UI)
2. **Expect artistic flops** — not every variant will be usable. This is normal.
3. **Expect complete failures** — some variants may produce blank, broken, or empty results. Don't analyze failures; just regenerate.
4. Don't pick one winner — pick elements from multiple screens and compose
5. Everything in Stitch is a component; you can mix and match across variants
6. Use scoped prompts to refine specific aspects without breaking what works
7. Use the **custom instructions** field in the variant dialog for specific guidance

Note: `generate_variants` through MCP may still have reliability limitations (see capability boundaries). Variants are most reliable through the browser UI.

### Annotate: visual targeted editing

The **Annotate** feature lets you drag-select a region of a generated screen and describe changes for just that area. This is a visual alternative to text-based element targeting — useful when you can see what needs to change but don't want to re-describe the full context.

Best for: layout tweaks in a specific section, repositioning elements, adjusting spacing in one area without affecting the rest.

### Direct inline editing

You don't always need the prompt box. Click any element on a generated screen to:

- **Edit text directly** — click and type, no regeneration needed
- **Use AI on a specific element** — targeted changes without affecting the whole screen

This is the fastest path for small copy changes, label fixes, or tweaking a single button. Use it before reaching for a full prompt-based edit.

### Quick style adjustments

Select a screen → **Edit → Edit Theme** to open a right panel with color and corner radius controls. Faster than re-prompting for small style changes. You can also right-click any screen for quick access to editing features and keyboard shortcuts.

### Multi-screen hub-first pattern

For multi-screen projects, the critical rule: **generate a hub screen first, then derive all other screens via edit — never fresh generate siblings.**

Why: `generate` invents everything from scratch (layout, colors, spacing, typography). `edit` takes the source screen as the visual basis and changes only what you describe. Navigation, typography, and color palette stay consistent.

Recommended flow:
1. Generate the hub screen → review carefully
2. All further screens of the same concept → `edit` from the hub
3. Max 1-2 changes per edit prompt — too many changes = unpredictable results
4. Even elements you did NOT mention can change in an edit. Fewer changes = more stable output.

During the concept phase, 3-4 consistent core screens are enough. Full screen coverage only after the concept is approved.

### Screen review loop

After each generate or edit, categorize issues systematically:

| Category | Examples | Action |
|----------|----------|--------|
| **Stitch-fixable** | Missing section, wrong layout order, major color error, wrong navigation | Edit prompt (max 1-2 changes) |
| **Post-export fix** | Exact pixel spacing, icon details, typography fine-tuning, persistent content hallucinations | Note it, move on |

**Decision tree:**
- Stitch didn't fix it after 2 edits → note as post-export fix, move on
- Detail work (shadows, exact radii, pixel spacing) → directly note as post-export fix, don't waste edit budget
- Structural issue (section missing, navigation wrong) → Stitch edit

The user decides which tool to use for post-export fixes (Figma, code, etc.). Do not prescribe a tool.

### Sequential wizard / multi-step pattern

Generate each step individually, using the previous step as base:

> "Use the existing Step 2 screen as the base. The following elements must stay exactly identical: [header, sidebar, progress indicator, page title]. Change ONLY these elements: [form content, step number, CTA label]."

Without explicit constraints, Stitch will change headers, titles, and layout between steps.

### Copywriting as a design step

Generic placeholder text makes even a beautiful layout feel like a template. Real copy makes the design feel real.

**When:** After the creative direction and design system are stable, but **before** the final design pass. Copy is not a finishing touch — it's a structural element.

**How:**

1. Use an LLM or agent skill with your DESIGN.md as context
2. Include the app description, community aspects, and emotional goals
3. Get multiple options for headlines, subheadlines, CTAs
4. Review and revise before feeding back into Stitch
5. Paste the copy into a variant prompt scoped to text content

The copy should match the creative brief. If your direction is "prestigious journal," the copy should sound like one.

### Multi-page expansion

After generating a page with navigation (sidenav, tab bar, etc.), rapidly scaffold the rest of the app:

> "Build me a page for each of the items in the left hand navigation"

Stitch generates all sub-pages in one shot, carrying the design system forward. Some pages may introduce inconsistencies (e.g., a top nav on one page when the rest use a sidenav) — expect minor cleanup.

**Brand consistency:** When adding pages, you don't need to re-specify the brand or design language. A minimal prompt like "design a second page for pricing" is enough — Stitch carries the color scheme, typography, and brand name forward.

### Mobile-from-web conversion

After designing a web/desktop screen, use **Generate → "build a mobile app version"** to have Stitch adapt the layout for mobile. This produces a separate mobile screen based on the same design system.

Expect some inconsistencies (chart types, minor layout differences) — treat it as a starting point, not a pixel-perfect responsive version.

### Sketch-to-design workflow

Upload a sketch or wireframe in the Stitch Web UI, then tell the agent:

> "I uploaded a sketch called [title]. Edit it to [desired changes]."

The agent finds the screen by title via `list_screens` and applies edits via the API.

Use Pro + Thinking for sketch/wireframe uploads — Flash produces noticeably weaker results with drawn inputs.

### Live mode: voice-driven design exploration

Stitch's **Live mode** lets you talk to the AI in real-time while it sees your screen. It can suggest design changes, adjust layouts, and generate new versions — all through conversation.

Good for:
- quick exploratory direction changes ("make the text more luminous")
- getting the AI's opinion on readability or layout issues
- hands-free iteration when you're reacting visually

Not good for:
- precise, scoped edits (use text prompts or direct inline editing instead)
- complex multi-step instructions (the AI may drift)

**Rule of thumb:** Live mode is for creative exploration. Text prompts are for precise control. Direct editing is for surgical changes.

### Redesign as style guide, not copy

Stitch 2.0's redesign feature does **not** replicate the source screenshot. It uses it as a **style guide**: pulling patterns, component placement, and design language, then applying them to your original content.

**Tip:** Use a full-page screenshot tool (e.g., GoFullPage) instead of capturing section-by-section. One full-page reference gives Stitch the complete design context in a single shot.

### Cross-device preview

Before exporting, click the **Preview** button to see your design on phone, tablet, and desktop form factors. This catches responsive issues early. Make this a mandatory step before any export to AI Studio or code translation.

### Cross-device preview

Before exporting, click the **Preview** button to see your design on phone, tablet, and desktop form factors. This catches responsive issues early. Make this a mandatory step before any export to AI Studio or code translation.

### Heat map (attention audit)

Select a generated screen → **Generate → Predicted Heat Map** to see where users' eyes will land first. Use this as a quality gate: if key elements (CTAs, primary info) aren't in high-attention zones, iterate before moving to code.

Heuristic: "If your buy button isn't glowing on the heat map, fix the design before you code it."

**Known issue:** The heat map may generate for the wrong page or create a new page instead of analyzing the selected one. Verify which screen it actually analyzed before trusting the results.

### Prototype mode tips

After generating pages, select 2+ screens and click **Prototype** to get an interactive click-through:

- Stitch auto-connects screens based on navigation elements
- Turn on **hotspots** to see clickable areas
- Switch between mobile/tablet/desktop to verify responsive behavior
- Select a specific element → "Change with AI" for targeted edits (e.g., add animation) without regenerating the whole screen
- Edit text directly on elements without re-generation
- **"Imagine a new screen"** suggests new pages based on your existing design context
- After adding new screens manually, use **connect to screen** to wire up navigation

This is a browser-only feature but invaluable for validating user flow before coding.

---

## Export & Code Translation

### Export paths

| Export path | Direction | Best for |
|------------|-----------|----------|
| **Google AI Studio** | One-way push | Simple apps (1-2 pages), quick prototyping |
| **MCP connection** | Bidirectional | Ongoing projects, multi-page apps, iterative development |
| **Download zip** | One-time | Offline work, custom build pipelines |
| **Copy code** | One-time | Quick paste into existing project |
| **Figma** | One-time | Design handoff to designers |
| **Project brief** | One-time | Requirements document for stakeholders |

### AI Studio pipeline

The simplest end-to-end path for getting a working website from a Stitch design:

1. **Design in Stitch** — finalize the direction, verify via cross-device preview
2. **Export → Build with AI Studio** — Stitch automatically uploads images, a markdown file, and a prompt. No manual copying needed.
3. **Press Build** in AI Studio — generates a functional website matching the design
4. **Verify** — check mobile/desktop views in AI Studio, test interactions
5. **Publish** — create a cloud project (may require billing), get a live URL
6. **Customize** — set up custom domain if needed

This is the "Vibe Design → Vibe Coding" pipeline: zero manual design, zero manual coding.

**AI Studio as a faster iteration surface:** Once you export to AI Studio, it becomes faster than Stitch itself for refinements:
- Changes typically take **30-60 seconds** vs. **2+ minutes** in Stitch
- **Screenshot-anchored editing**: paste a screenshot of the specific section to change, describe the edit. The image pins context so the AI knows exactly what to modify.
- AI Studio preserves your full HTML/CSS, so every edit updates the actual code

**Practical flow:** Design direction in Stitch → export to AI Studio → refine details there → publish or copy code.

**AI Studio export gotchas:**
- **Select all screens before exporting.** By default, AI Studio may only receive the active screen.
- **Export page-by-page for complex apps.** Sending 5+ complex screens at once can overload AI Studio (12+ minute builds with missing content).
- AI Studio export is **one-way**. Changes in Stitch after export don't sync back.

### Bidirectional MCP workflow

MCP creates a two-way connection between Stitch and your coding agent:

1. In Stitch: Export → Set up MCP → Choose your tool → Create API key
2. In coding agent: Add MCP server → Search "Stitch" → Install → Paste API key
3. Available tools: create/list/get projects, get/generate screens, pull design files, sync updates
4. **Key benefit:** edit in Stitch → pull changes in coding agent → edit code → push back. No re-export needed.

Recommended hybrid flow for larger projects:
1. Design in Stitch
2. Initial export to AI Studio for the first working prototype
3. Push to GitHub
4. Open in coding agent (Antigravity, Claude Code, Cursor)
5. Connect MCP for ongoing bidirectional iteration

### Figma export

Export to Figma: **Export → Figma → Convert → Copy frame → Paste in Figma.** The resulting auto layout is usable — better than most AI design tool exports — though some elements may be hidden or not fully responsive. Good enough for design handoff and developer inspection.

### Review gate before code translation

Do not port a Stitch output into code until these conditions are true:

- required elements are still present
- the primary user task is clearer than before
- mobile density and hierarchy are acceptable
- the screen fits the rest of the project direction
- the design can be implemented coherently in the current application architecture

If the answer is not clearly yes, keep iterating in Stitch.

For greenfield translation from exported Stitch code, also check:

- the exported code represents the accepted direction, not an older candidate
- the layout system is coherent enough to preserve rather than rewrite immediately
- the token layer can be mapped into the target project's theme system
- there is a plan to replace placeholders and hardcoded demo content with real data
- the team will translate deliberately instead of pasting large exports blindly
- all required npm dependencies are installed before integration
- hardcoded colors/sizes have been replaced with project theme tokens

### Design system file injection

When the SDK doesn't support `design_system_id` in generate/edit calls, use this workaround: load a design system markdown file and append its content to the prompt. This carries design tokens (colors, typography, spacing rules) into each generation without relying on Stitch's built-in design system panel.

### Dependency check during integration

When integrating Stitch output into a codebase, check whether the generated code uses libraries not yet installed (e.g. `recharts`, `framer-motion`, `lucide-react`). Run `npm install <pkg>` before integration to prevent build failures.

Also check whether the generated code uses hardcoded colors or sizes that conflict with the project's existing theme — replace them with CSS variables or design tokens before saving.

### Architecture-aware component placement

When integrating components, respect the project's architecture:
- Standard: `src/components/<ComponentName>.tsx`
- Hexagonal/modular: `src/modules/<domain>/components/<ComponentName>.tsx`
- Feature-based: `src/features/<feature>/components/<ComponentName>.tsx`

Don't blindly place everything in `src/components/` — detect the project's convention first.

### Shadcn UI integration

For converting Stitch designs into production-quality component apps:

1. Set up the **Shadcn MCP** before building (provides tool calls for component operations)
2. Install Google's **Shadcn UI skill** — a detailed guide for converting Stitch output to Shadcn components
3. Add instructions to your agent's config so Stitch MCP output automatically flows through the Shadcn skill
4. Specify additional registries for premium components (e.g., glassmorphism, motion primitives)
5. Workflow: specify the Stitch project name → agent fetches the project → loads Shadcn skill → implements with MCP tool calls + registries

This produces interactive, production-ready apps from Stitch designs in one shot rather than static HTML.

---

## Autonomous Agent Pipeline

Google provides three skills for agent-connected Stitch workflows:

1. **Enhanced Prompt skill** — transforms vague prompts into Stitch-optimized prompts using adjective-based mood language and Stitch-specific keywords
2. **Stitch Loop skill** — autonomous iterative building using Chrome DevTools; maintains prompt tracking across stages
3. **React Component skill** — converts Stitch's monolithic HTML export into modular React components with validation scripts

**Recommended pipeline order for coding agents:**

1. Enhanced Prompt → convert your vague prompt into a Stitch-specific one
2. Stitch Loop → build the design via MCP (generates design system first, then actual design)
3. React Component skill → break the monolithic export into modular components

Add these steps to your coding agent's config file (e.g., Claude.md) so the pipeline runs automatically when you request a new screen.

---

## MCP API Reference

### Capability boundaries

**Verified MCP capabilities** (default safe surface):

- `list_projects`
- `get_project`
- `list_screens`
- `get_screen`
- `create_project`
- `generate_screen_from_text`
- `edit_screens`

**Known weak or unverified areas** — treat as unstable until revalidated:

- `generate_variants` — reliable through browser UI (see Variants section), less predictable via MCP
- screenshot-driven redesign through MCP
- prototype creation through MCP
- browser-style canvas operations beyond basic project and screen inspection

**Browser-only product features** — do not infer MCP can perform these:

- image or screenshot redesign
- prototype-oriented workflows
- broader canvas interactions
- newer browser-facing product features

### Parameter discipline

The MCP surface is parameter-sensitive. Incorrect casing or identifier shape can produce generic invalid-argument failures.

**`deviceType`:** Use uppercase enum values when explicitly setting a device: `"MOBILE"`, `"DESKTOP"`. If uncertain, omit the parameter instead of guessing.

**`modelId`:** Use only verified model identifiers for direct MCP calls. Known working values: `"GEMINI_3_FLASH"`, `"GEMINI_3_PRO"`. If a local wrapper maps model names differently, treat that as wrapper-specific behavior, not a direct MCP guarantee.

**`selectedScreenIds`:** For `edit_screens`, pass bare screen IDs rather than full resource names.

Example:

```json
{
  "projectId": "15190935684505273965",
  "selectedScreenIds": ["69b3228b6c5f4b9f9efceea4b6a30168"],
  "deviceType": "MOBILE",
  "prompt": "Make the primary button darker and add a small secondary text link below it."
}
```

### Failure handling

**`Request contains an invalid argument.`** — Check in this order:

1. `deviceType` casing
2. `modelId` spelling
3. `selectedScreenIds` shape
4. whether the screen is genuinely editable generated output
5. whether the prompt is trying to change too much at once

Long-running operations may still complete even when the client appears to fail. Re-check `list_screens`, inspect any likely new screens, and avoid blind re-submission.

**Generation or edit timeout:** `generate_screen_from_text` can take 2-10 minutes. The API may drop the TCP connection after ~60 seconds even though the generation continues server-side. The client sees a failure, but the screen may appear in the project moments later.

Safe reconciliation pattern:

1. do not immediately resend the same request
2. re-check `list_screens`
3. inspect whether a new screen appeared
4. retry only if no result landed
5. if retrying, use exponential backoff — don't brute-force with identical parameters

**Incomplete or lagging screen lists:** `list_screens` may lag behind a successful operation. If the originating call indicated success, re-check before retrying. Do not assume immediate list lag means failure.

**HTTP-level errors:**

| Error | Likely cause | Action |
|-------|-------------|--------|
| `401 Unauthorized` | Token/API key expired | Refresh auth, retry once |
| `400 Bad Request` | Invalid payload or vague prompt | Check parameters, refine prompt |
| `429 Too Many Requests` | Rate limit | Wait 60s, retry with backoff |

---

## Workflows

### Workflow A: inspect before editing

Before any edit:

- inspect the project
- inspect the target screen
- verify whether the screen is actually generated content

Practical heuristic:

- if `htmlCode` exists, the screen is more likely to be safely editable
- if the target is only an uploaded image or reference asset, do not assume `edit_screens` will behave well

### Workflow B: generate first, then refine

For new directions:

1. create or choose the right project
2. generate a first screen with the minimum safe parameter set
3. review output quality
4. move to small edits rather than repeating large generation prompts

Default safe starting point: `projectId` + a short, structured prompt. Then add `deviceType` or `modelId` only when there is a reason.

### Workflow B2: greenfield app bootstrap from Stitch exports

Use this when the product is new enough that there is no meaningful coded UI to preserve yet.

1. generate the canonical screen family in Stitch first
2. get explicit acceptance on the direction before broad implementation
3. if code or HTML export is available in the active environment, download it
4. read the export completely before rewriting anything
5. translate the exported structure into the target stack instead of eyeballing screenshots
6. keep the layout system, spacing logic, token choices, and section structure where they are sound
7. replace hardcoded content and brittle markup gradually, not all at once
8. add the real app concerns after translation: data flow, typing, state, accessibility, dark mode, tests

Use this path especially when:

- the app is being built from scratch
- Stitch generated a strong screen family quickly
- the main value is the concrete composition, hierarchy, and token choices
- recreating the same layout manually would be slower and less faithful

Do not treat the export as production-ready final code. Treat it as a high-fidelity implementation seed.

### Workflow C: full-app redesign

For an existing product redesign:

1. create a dedicated Stitch project
2. define the main screen families
3. generate one canonical screen per family
4. refine those canonical screens with preservation-first prompts
5. only then add alternate states and edge cases
6. move to code after the family set is coherent

This is slower than opportunistic one-off generation, but it reduces design drift.

### Workflow D: reference-driven redesign

When redesigning a real app:

- gather reliable reference captures first
- work one screen family at a time
- name the relevant reference images explicitly in the prompt
- treat those references as the source of truth for current structure

Good pattern:

```text
Use the uploaded real app references in this project.
The relevant images are named today_top.png, today_day_actions.png, and today_meals_mid.png.
Those images show what exists now.
Keep the real structure and improve only hierarchy, spacing, and polish.
Do not invent new sections.
```

### Workflow E: visual review before further iteration

Use this when the session already has multiple candidate screens or when the next edit would otherwise be ambiguous.

1. use `list_screens` to find the likely targets
2. use `get_screen` to inspect candidate screens
3. when a screenshot or visual artifact is available, review it before the next major edit
4. ask the user to choose using a human description of the screen, not only an opaque ID
5. continue only after the canonical target is clear

### Workflow F: decide whether to stay in Stitch or move to code

Stay in Stitch when:

- the information architecture is still drifting
- the visual hierarchy is still weak
- multiple screen directions are still being explored
- the user is reacting to screenshots rather than implementation details

Move to code when:

- one canonical screen direction is accepted
- the required elements are stable
- the remaining work is implementation fidelity rather than design exploration
- the screen can be implemented coherently in the target stack

For greenfield work, prefer this move-to-code order:

1. generate mobile and desktop canonical screens separately when both matter
2. accept the visual direction
3. export or download the generated code artifact when available
4. translate that artifact into the real stack
5. only then start screen-by-screen product hardening

---

## Appendix

### Naming guidance for larger projects

If the project will contain many screens, use stable ordered titles from the start.

Recommended pattern:

- `01 Onboarding - Welcome`
- `02 Onboarding - Personal Info`
- `10 Today - Main`
- `20 Progress - Overview`
- `30 History - Browse`
- `40 Settings - Profile`

This improves canvas scanning and reduces later cleanup.

### What a good Stitch pass should produce

A successful pass should leave the session with:

- one clearly identified target project
- one clearly identified canonical screen or small set of candidate screens
- the exact prompt or edit intent that produced the result
- a short judgment on whether the result is accepted, rejected, or needs another small iteration

After each generate/edit/variants, report to the user:
- the project and screen IDs
- the output location (if artifacts were saved)
- a short design assessment
- the recommended next step

If those artifacts are missing, slow down and re-establish state before continuing.

### Not recommended

- copying browser-product claims into MCP instructions without revalidation
- starting with a "blank page, no design system" prompt
- skipping the empathy step and jumping straight to colors and layouts
- using Space Grotesk for headlines (labels and timestamps only)
- treating copywriting as a final polish step instead of a structural design element
- picking one variant winner instead of composing from multiple variant elements
- using design boards or mood boards as substitutes for real app screens in a product redesign
- attempting to redesign a whole app from memory in a single prompt
- exporting 5+ complex pages to AI Studio all at once (causes overloading and missing content)
- forgetting to select all screens before exporting to AI Studio
- moving into implementation code before the design family is coherent
- trusting the heat map output without verifying which screen it actually analyzed
- rebuilding an accepted greenfield Stitch design from screenshots when a usable export already exists
- using exact structural descriptions instead of mood adjectives in prompts
- taking section-by-section screenshots for redesign — use full-page captures instead
- uploading a screenshot and asking Stitch to add something to it — Stitch regenerates the entire screen, losing consistency. Instead: generate the addition in isolation, integrate elsewhere (Figma or code)
- using multiple screens in one prompt — produces broken theming, incomplete outputs, errors. One prompt = one screen or one component
- using Reimagine/NanoBanana for small changes — it redesigns everything. Use for full overhauls only
- trusting generated content blindly — Stitch invents copy, subtexts, badges, status labels that weren't requested
- long prompts over 5000 characters — Stitch truncates or omits elements. Keep focused, iterate instead
- letting design drift across edits — after 3+ edits in a session, add: "Use the existing design system established in this project. Do not create new styles."

### Google screenshot URL size parameters

Stitch returns screenshot URLs on `lh3.googleusercontent.com`. Append these suffixes to control resolution:

| Suffix | Result |
|--------|--------|
| `=w780` | Full mobile design width (good default) |
| `=w1440` | Full desktop design width |
| `=s2000` | Max 2000px on longest side |
| (no suffix) | Thumbnail only (~168px wide) |

### Optional local workflow enhancements

If you want aliases, execution artifacts, derivation history, or last-active-screen state, use [`references/local-workflow-conventions.md`](./references/local-workflow-conventions.md).

These are useful for traceability, but they are optional and not part of the Stitch MCP contract.

### References

- Prompt reference: [`references/prompt-structuring.md`](./references/prompt-structuring.md)
- Visual review and artifacts: [`references/visual-review-and-artifacts.md`](./references/visual-review-and-artifacts.md)
- Redesign prompt patterns: [`references/redesign-prompt-patterns.md`](./references/redesign-prompt-patterns.md)
- Local workflow conventions: [`references/local-workflow-conventions.md`](./references/local-workflow-conventions.md)
- Style keywords: see the Style keyword reference table in the Prompting & Generation section

Keep the main skill focused on operating rules. Use the prompt reference only when the request needs prompt shaping or prompt repair.

# Changelog

## 1.4.2

- Expands the `DESIGN.md` guidance to treat tokens as named design roles/decisions rather than loose variables.
- Clarifies the two-layer `DESIGN.md` model: concrete token values plus prose rationale that must stay aligned.
- Adds stronger guidance for baseline role anchors (`primary`, `neutral`), role-referenced component rules, and using lint/diff as a normal validation loop.
- Makes the top-level Stitch workflow stricter: rewrite prompts before action, choose `generate` vs `edit` vs `variants` explicitly, and report state after every pass.
- Adds a maintainer-facing `publish/RELEASE_RULES.md` so future sessions can follow the same ClawHub release policy without relying on prior chat context.

## 1.4.1

- Refines the `DESIGN.md` guidance so custom design-system creation starts from a brief and a compact token-plus-rationale artifact instead of pointing to another repo.
- Tightens mood-language guidance to keep the public bundle self-contained and free of external skill references.

## 1.3.0

- Major expansion: creative direction framework, design system as DNA, and complete process order.
- Prompt patterns: incremental enrichment, section-by-section, PRD+reference image, mood adjectives.
- Design system guidance: color hierarchy (neutral/primary/secondary/tertiary), font hierarchy, corner radius, DESIGN.md portability and URL-based import.
- Model selection table (Flash/Pro/Redesign/Live/ID8) with use-case guidance.
- App vs web toggle, thinking mode, and continue-suggestion patterns.
- Iteration: variants (refine/explore/reimagine), inline editing, annotate, heat map attention audit.
- Multi-page expansion with navigation-aware prompting and brand consistency.
- Export strategy: AI Studio (faster iteration), Figma, Stitch→AI Studio→Publish pipeline, mobile-from-web conversion.
- Autonomous agent pipeline: MCP bidirectional workflow, Shadcn UI integration, custom design.md generation.
- Wireframe/sketch upload guidance (use Pro+Thinking, variable quality from hand-drawn input).
- Cross-device preview as mandatory verification step before export.
- Consolidated and reorganized into logical phases.

## 1.2.0

- Adds a greenfield-app workflow: when Stitch direction is accepted and exportable code is available, use the generated HTML/CSS as the translation base instead of recreating layouts from screenshots.
- Clarifies the split between existing-app redesign work and new-app bootstrap work so Stitch is not treated with one rigid rule in both cases.

## 1.1.0

- Improves the public bundle landing experience with a clearer README and quick-start guidance.
- Tightens the main skill with quick operating rules and clearer boundaries for when Stitch should and should not be used.
- Adds clearer guidance for deciding when to stay in Stitch and when to move to implementation code.
- Moves optional local workflow conventions into a dedicated reference so the main skill stays more scannable.
- Adds supporting references for visual review, redesign prompt patterns, and local workflow conventions.
- Makes publishing instructions clone-path-neutral instead of tied to one local machine path.

## 1.0.0

- Initial public bundle for Stitch operational guidance.
- Separates verified MCP capabilities from browser-only features.
- Adds concise workflows for inspection, generation, refinement, and redesign.
- Introduces optional local workflow conventions: screen aliases, execution artifacts, operation history, and last-active-screen state.
- Extracts prompt guidance into a focused supporting reference.
- Adds explicit MIT licensing and publication-oriented bundle documentation.

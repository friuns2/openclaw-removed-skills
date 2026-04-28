# CLAUDE.md

## Keep SKILL.md and AGENTS.md in sync

`SKILL.md` (Claude Code) and `AGENTS.md` (other agent runtimes) are parallel entry points for the same skill and must stay in sync in content and structure. Any substantive change to one must be mirrored in the other in the same commit — including the frontmatter/description, opening "Two APIs" paragraph, Quick Start, Key Rules, Core Patterns, Reference Documentation list, and CLI Commands. Format differences are fine (e.g., SKILL.md has YAML frontmatter, AGENTS.md has a `<!-- version: -->` comment), but the meaning, ordering, and coverage must match. If a section exists in one file, it should exist in the other unless there's an explicit reason it doesn't apply.

## Version bumping

Only bump the skill version **once, at the very end** of a change — after all edits are finalized and the user has confirmed they're done. Do not bump mid-change, do not bump after each individual edit, and do not bump speculatively. If the user is still iterating, hold off.

When bumping at the end, update all four places in the same commit:

1. `CHANGELOG.md` — add a new version entry at the top with a summary of changes
2. `SKILL.md` — update the `version:` field in the frontmatter metadata
3. `AGENTS.md` — update the `<!-- version: x.x.x -->` comment
4. `.claude-plugin/plugin.json` — update the `"version"` field

## SDK version and Last verified go together

Every reference file under `references/` and every entry in `.github/scripts/sources.yaml` has a paired `SDK version:` / `sdk_version:` and `Last verified:` / `last_verified:` field. These must always move together: if you bump one, bump the other in the same commit. Bumping only the SDK version leaves a lie in the date field — the record claims someone verified against a newer SDK on an older date, which is worse than not bumping at all.

Apply this rule whenever:

- You update a reference file's `SDK version:` header after a PyPI release
- You edit a reference file's content to reflect new/changed docs
- You change any URL in that file's `Source:` list (or its entry in `sources.yaml`)

In all three cases, set `Last verified:` to today's date in the same edit, and mirror the same date to the corresponding `last_verified:` field in `sources.yaml`. The `README.md` illustrative example header should also be kept current.

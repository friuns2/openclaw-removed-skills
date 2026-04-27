# Host Profiles

## Goal

Separate the generic core from host-specific integration assumptions.

`memory-governor` should be understood as:

- a generic memory-governance core
- plus one or more host profiles

## Profile: Generic

Use this when the host does not already provide OpenClaw-style files.

Characteristics:

- no assumption of `AGENTS.md`
- no assumption of `workspace/memory/`
- adapters may point anywhere the host considers valid
- fallback should start from templates in `assets/fallbacks/`

Recommended starting point:

- copy fallback templates from `assets/fallbacks/`
- define a local adapter map
- add `memory-governor-host.toml` if you want machine-readable host checks
- optionally add a host-level “memory governance” note in whatever root document the host uses

See also:

- `../examples/generic-host/README.md`

## Profile: OpenClaw

Use this when the host already follows the OpenClaw workspace shape.

Typical mappings:

- `long_term_memory` -> `MEMORY.md`
- `daily_memory` -> `memory/YYYY-MM-DD.md`
- `reusable_lessons` -> `~/self-improving/...` if installed, otherwise `workspace/memory/reusable-lessons.md`
- `proactive_state` -> `~/proactivity/memory.md` + `~/proactivity/session-state.md` if installed, otherwise `workspace/memory/proactive-state.md`
- `working_buffer` -> `~/proactivity/memory/working-buffer.md` if installed, otherwise `workspace/memory/working-buffer.md`
- `system_rules` -> `AGENTS.md` / `SOUL.md`
- `tool_rules` -> `TOOLS.md`

Current note:

- OpenClaw reference profile can now declare these mappings in `memory-governor-host.toml`
- existing external adapters such as `~/proactivity/...` may still be legacy human-readable files rather than schema-frontmatter targets
- installing the skill into OpenClaw should not silently rewrite `AGENTS.md` or other skills; package-external integration should remain explicit
- if OpenClaw Dreaming is enabled, treat it as an optional consolidation engine for `daily_memory -> long_term_memory`, not as a new target class or a replacement for `learning_candidates`

## Selection Rule

If you are packaging this skill for others, do not present the OpenClaw profile as the generic default.

Instead:

1. describe the generic core first
2. list host profiles separately
3. present OpenClaw as the reference profile, not the universal assumption

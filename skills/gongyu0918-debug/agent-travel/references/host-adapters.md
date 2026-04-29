# Host Adapters

Use this file when a host needs a minimal adapter policy for `agent-travel`.

## OpenClaw

- Treat `agent-travel` as a quiet-window skill.
- Prefer heartbeat, task-end, failure-recovery, or explicit user commands.
- Keep search tools `public-only` by default.
- Read the isolated suggestion channel only when the next task matches the fingerprint and TTL.

## Hermes

- Treat `agent-travel` as a progressive-disclosure skill.
- Do not load large reference files unless the skill is invoked.
- Prefer small-scope micro-travel by default.
- Keep all stored hints advisory-only.

## OpenAI / Codex-style hosts

- Keep manual invocation available for operators who want to run a one-off travel pass.
- Keep automatic model invocation disabled unless the host has an explicit quiet-window scheduler around it.
- Prefer the same `public-only`, advisory-only, next-relevant-turn flow used by the other adapters.

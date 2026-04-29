# Suggestion Contract

`agent-travel` writes hints into a dedicated advisory channel. The channel must stay clearly separate from core instructions, persona files, and permanent memory.

## Preferred Storage

Use this file path when the host can read a repo-local advisory file:

`./.agents/agent-travel/suggestions.md`

Store lightweight run state here when the host supports repo-local state:

`./.agents/agent-travel/state.json`

If the host supports only a single context file, embed the same block inline under exact markers.

## Required Markers

```md
<!-- agent-travel:suggestions:start -->
...
<!-- agent-travel:suggestions:end -->
```

## Canonical Shape

```md
<!-- agent-travel:suggestions:start -->
# agent-travel suggestions
generated_at: 2026-04-20T03:00:00+08:00
expires_at: 2026-04-27T03:00:00+08:00
search_mode: low
tool_preference: public-only
source_scope: primary+secondary
thread_scope: active_conversation_only
problem_fingerprint: host|subsystem|symptom|version
advisory_only: true
trigger_reason: heartbeat
visibility: silent_until_relevant
fingerprint_hash: h64:2b55f2f02031d480801fd20ab8ce6bea1dd16f5ff5e95f5ff4de73452f6ca1c7
reuse_gate: min_4_of_5_axes_and_ttl_valid

## suggestion-1
title: Refresh the skill snapshot after edits
applies_when: The host changed SKILL.md and the new content is still missing.
hint: Start a fresh session or restart the host before assuming the edit failed.
confidence: medium
manual_check: Confirm the host rescanned the skill directory and the file timestamp changed.
solves_point: The current thread is blocked on whether the host has reloaded the edited skill.
new_idea: Treat stale skill behavior as a host reload problem and verify the scan path before changing the skill again.
fit_reason: This fits when the user already edited the skill locally and needs a fast low-risk check before more changes.
match_reasoning:
- host: matched the same skill-host reload surface
- version: matched the same host build family where scan timing matters
- symptom: matched stale behavior after a local edit
- desired_next_outcome: matched a low-risk reload check before more edits
version_scope: Any host build where skill reload still depends on filesystem scan timing.
do_not_apply_when: Skip this hint when the host has already confirmed a fresh reload and the symptom now points to skill logic instead of cache staleness.
evidence:
- primary_official_discussion: https://example.com/maintainer-thread
- secondary_community: https://example.com/community-thread
<!-- agent-travel:suggestions:end -->
```

The fields above `## suggestion-1` belong to the top-level envelope. The fields under each `## suggestion-n` heading belong to that suggestion item only.

Optional fields such as `trigger_reason`, `visibility`, `fingerprint_hash`, and `reuse_gate` should not break older hosts. Hosts that do not understand them should preserve them when possible and ignore them otherwise. Older hosts may still emit an earlier mode field that mirrors `search_mode`.

Timestamps must include an explicit timezone offset. `problem_fingerprint` should contain at least 4 non-empty segments, and `fingerprint_hash` should be formatted as `h64:<64 lowercase hex chars>`. Each suggestion needs at least one `primary` evidence item, one additional non-`primary` cross-validation evidence item, and one additional independent evidence source. The current standardized `reuse_gate` value is `min_4_of_5_axes_and_ttl_valid`.

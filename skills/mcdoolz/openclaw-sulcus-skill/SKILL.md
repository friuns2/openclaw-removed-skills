---
name: openclaw-sulcus-skill
description: "Equip your agent with Sulcus — thermodynamic memory with a knowledge graph. Full SIU pipeline: SIVU (quality gate) → SICU (classifier) → SILU (entity extraction) → SIRU (adaptive recall). Apache AGE knowledge graph. Multi-signal recall with learned scoring weights. Interaction-based decay. Reactive triggers."
author: "Digital Forge Studios"
version: "2.5.0"
metadata:
  openclaw:
    requires:
      plugins: [openclaw-sulcus]
    credentials:
      serverUrl:
        description: "Sulcus server URL (e.g., https://api.sulcus.ca). Required for cloud mode. Leave empty for local-only."
        required: false
      apiKey:
        description: "Sulcus API key. Same key is used for memory storage, recall, and BGE-small-en-v1.5 embeddings. Get one at sulcus.ca. Required for cloud mode."
        required: false
    environment:
      SULCUS_SERVER_URL:
        description: "Mapped from config.serverUrl. Not required for local-only mode."
        required: false
      SULCUS_API_KEY:
        description: "Mapped from config.apiKey. Not required for local-only mode."
        required: false
      OPENCLAW_WORKSPACE:
        description: "OpenClaw workspace path. Used by opt-in history import. Defaults to ~/.openclaw/workspace."
        required: false
    dataFlows:
      - direction: local-only
        condition: "When serverUrl is NOT configured"
        destination: "~/.sulcus/data/ (local embedded PostgreSQL)"
        data: "Memory text, embeddings, search queries"
      - direction: outbound
        condition: "When serverUrl IS configured"
        destination: "Configured Sulcus server"
        data: "Memory text, metadata, search queries, session events, embedding requests"
        auth: "apiKey"
---

# Sulcus Memory Skill

Sulcus is a cognitive memory system for AI agents — not a simple key-value store. Every memory is automatically scored, classified, graph-linked, and subject to thermodynamic decay. The system learns what matters and keeps it accessible.

## Prerequisites

**Required plugin:** `openclaw-sulcus` (install via `openclaw plugin install openclaw-sulcus`)

**Two operating modes:**
- **Local-only (no credentials needed):** All memory stays in `~/.sulcus/data/`. Zero network calls. Requires native dylibs (`libsulcus_store`, `libsulcus_vectors`) or WASM fallback.
- **Cloud mode (requires serverUrl + apiKey):** Memories are stored on and recalled from the configured Sulcus server. Embedding (BGE-small-en-v1.5) uses the same `apiKey` — no separate credentials. Get a key at [sulcus.ca](https://sulcus.ca).

**No additional databases or infrastructure needed by the agent.** PostgreSQL, pgvector, and Apache AGE run server-side (managed by the Sulcus server). The plugin communicates via REST API.

## What Sulcus Is

- **Thermodynamic memory** — memories have heat that decays over time and interaction patterns. High-utility memories stay hot; irrelevant ones cool and disappear.
- **Apache AGE knowledge graph** — temporal graph over all stored memories. Entities and relationships are extracted automatically. Graph queries reveal connections across time.
- **SIU v2 pipeline** — every `memory_store` fires: SIVU (utility scoring) → SICU (type classification) → SILU (entity extraction) → AGE graph update → trigger evaluation.
- **Curator (sleep cycle)** — background process that reclassifies, consolidates, summarizes, and re-vectorizes memories. No manual cleanup needed.
- **Reactive triggers** — rules that fire automatically on memory events. Useful for auto-pinning important facts, notifying on key recalls, or chaining memory actions.
- **Temporal-aware search** — natural language time references ("yesterday", "last week", "3 days ago") are auto-detected and used to boost temporally relevant results.
- **SILU output evaluation** — recursive LM supervisor that checks LLM outputs against stored memories for contradictions, preference drift, and hallucination risk.

## Memory Lifecycle

### Storing

```
memory_store(content, memory_type)
  → SIVU scores utility (0–1)
  → SICU classifies type (if not specified)
  → SILU extracts entities and relationships
  → AGE graph node created/updated
  → Triggers evaluated (on_store)
  → Memory persisted with heat, confidence, provenance
```

### Recalling

```
memory_recall(query, limit)
  → Semantic embedding search (pgvector)
  → Base score = similarity × sim_weight + heat × heat_weight
  → Keyword overlap boost (exact word matches)
  → Temporal proximity boost (time-referenced queries)
  → Namespace ownership boost (agent's own memories preferred)
  → Recall-boost applied (heat += boost_delta)
  → Triggers evaluated (on_recall)
  → Graph context available alongside results
```

### Automatic Context Injection (v5.5.0+)

The plugin automatically injects relevant memories into every turn via `before_prompt_build` using a **multi-signal recall pipeline**:

```
User sends message
  → Signal 1: Semantic Search (query against memory embeddings)
  → Signal 2: Hot Context (top 5 highest-heat memories, no query needed)
  → Signal 3: Entity Context (graph neighbors of entities mentioned in message)
  → Signal 4: Profile (user preferences + facts, periodic refresh)
  → Dedup by memory ID across all signals
  → Composite Scoring: Similarity (40%) + Heat (30%) + Recency (20%) + Source Boost (10%)
  → Token Budget Assembly: top-scored memories packed into budget limit
  → Injected via prependContext (agent sees enriched context every turn)
```

This replaces manual `memory_recall` for context loading. The agent doesn't need to search — the memory layer surfaces what matters automatically.

### Cache-Friendly Injection (v5.5.1+)

The context block is designed to maximize LLM prompt cache hit rates:

- **Stable confidence bands** — memories tagged `[high]`/`[mid]`/`[low]` instead of volatile exact percentages (`[47%]`). Prevents cache-busting from minor score drift between turns.
- **No relative timestamps** — timestamps like "3h ago" change every hour and bust the cache. Removed from injected context.
- **Deterministic sort** — memories with similar scores sorted by stable node ID. Same set of memories always renders in the same byte order.
- **5-minute recall TTL** — within an active session, the same context block is reused for 5 minutes instead of re-querying Sulcus on every turn. Reduces API calls and ensures byte-identical injection.

These optimizations are critical for cost control on Anthropic models, where prompt caching uses prefix matching. A single changed byte invalidates the entire cache and triggers an expensive cache-write.

### Session Lifecycle (v4.3.0+)

- **session_start** — logs session open
- **session_end** — runs SIVU auto-capture for final memory extraction
- **before_reset** — extracts memories before `/reset` wipes context (last chance to save)

## Memory Types — Choose Carefully

Decay rates differ significantly. Wrong type = memory disappears too fast or lingers too long.

| Type | Decay | Use For |
|---|---|---|
| `episodic` | Fast | Events, sessions, one-off observations |
| `semantic` | Slow | Concepts, relationships, domain knowledge |
| `preference` | Slower | User preferences, opinions, style choices |
| `fact` | Slow | Stable factual knowledge, ground truth |
| `procedural` | Slowest | How-tos, processes, workflows, playbooks |

**Best practices:**
- Store user preferences as `preference` — they survive long and surface reliably
- Store how-tos and processes as `procedural` — these should never decay quickly
- Store facts as `fact` — stable, slow decay, always available
- Use `episodic` for events and session context — fast decay is correct here
- Use `semantic` for domain concepts and relationships

## Interaction-Based Decay

Sulcus supports 3 decay modes (configured server-side):

- **Time-only** — classic: memory cools based on wall-clock time since last access
- **Interaction-only** — memories decay per agent interaction, not time; great for high-frequency agents
- **Hybrid** (default) — combination of both; high-utility memories (high SIVU score) resist decay

The Hybrid mode is the right default. High-utility memories (`procedural`, `fact`, high-SIVU) decay slowly. Low-utility noise (`episodic`, low-SIVU) cools quickly and gets consolidated.

## Temporal Search (v2.6.0+)

Search queries with temporal references are automatically enhanced. The server parses natural language time expressions and boosts memories from the matching time window.

**Supported references:** yesterday, today, last week, this week, last month, this month, last monday/friday/etc., N days ago, explicit YYYY-MM-DD dates.

**How it works:**
- "What happened yesterday?" → memories from yesterday get 30% similarity boost
- "Sulcus work from last week" → memories from last week boosted
- "Deploy the server" → no temporal reference, pure semantic search (unchanged)

**Explicit time params** (for programmatic use):
```
memory_recall(query="deployment issues", time_from="2026-04-01T00:00:00Z", time_to="2026-04-07T23:59:59Z")
```

Temporal search is **additive** — it boosts, not filters. If the best match is from months ago, it still appears. But recent relevant memories rank higher.

The `provenance` field in search results includes `temporal_window` when a time reference was detected:
```json
"temporal_window": {
  "reference": "yesterday",
  "start": "2026-04-08T00:00:00+00:00",
  "end": "2026-04-08T23:59:59+00:00"
}
```

## SILU Output Evaluation (v5.2.0+)

The SILU (Sulcus Intelligence Learning Unit) can act as a recursive language model supervisor — evaluating LLM outputs against stored memories for semantic alignment.

**What it checks:**
- **Contradictions** — output directly contradicts stored memories
- **Preference drift** — output ignores or reverses known user preferences
- **Stale references** — output references outdated information superseded by newer memories
- **Hallucination risk** — output makes specific claims that conflict with stored facts

**Per-agent toggle (off by default):**
```
PATCH /api/v1/settings/siu/:namespace
{ "silu_output_evaluation": true }
```

**OpenClaw plugin hook:** Enable in plugin config:
```json
{
  "hooks": {
    "llm_output_evaluation": { "enabled": true }
  }
}
```

When enabled, every LLM response is evaluated fire-and-forget. Misalignment findings are automatically stored as episodic memories for the agent to learn from.

**Response format:**
```json
{
  "alignment": {
    "score": 0.72,
    "status": "misaligned",
    "issues": [
      { "type": "contradiction", "description": "Output says use TypeScript, memory says user prefers Python" }
    ],
    "corrections": [
      { "original": "Use TypeScript for scripting", "suggested": "Use Python for scripting (user preference)" }
    ]
  },
  "meta": { "memories_checked": 5, "evaluation_ms": 340, "model": "gpt-5.4-nano" }
}
```

## SIRU — Sulcusian Intelligence Recall Unit (v5.8.0)

SIRU is the recall optimization layer. It learns which memories are most useful for a given query by analyzing accumulated recall sessions, then replaces the default heuristic scoring with **per-tenant/namespace learned weights**.

### How SIRU Works

1. **Data Collection (automatic)** — Every recall (context injection) is logged to the server:
   - Query text, entity hints extracted from the query
   - Memory IDs selected, their composite scores, and which signal found them
   - Token budget vs actual usage, candidate counts per signal
   - Optional explicit feedback (“helpful” / “unhelpful” / “partial”)

2. **Training** — When ≥20 recall sessions have accumulated, trigger training:
   ```
   POST /api/v2/siu/retrain { "model": "siru", "namespace": "optional" }
   ```
   SIRU analyzes:
   - Sessions with explicit feedback (gold signal) — which sources dominated in helpful vs unhelpful recalls
   - Recall frequency patterns (implicit signal) — memories recalled often across sessions
   - Source diversity — sources that contribute more unique memories get boosted

3. **Adaptive Scoring** — The plugin fetches learned weights every 30 minutes and uses them in composite scoring:
   - `similarity_weight` (default 0.40) — semantic similarity signal
   - `heat_weight` (default 0.30) — thermodynamic heat signal
   - `recency_weight` (default 0.20) — time since last update
   - `source_boost_semantic` (default 0.00) — boost for semantic search results
   - `source_boost_hot` (default 0.05) — boost for hot-context results
   - `source_boost_entity` (default 0.10) — boost for graph entity neighbors
   - `source_boost_profile` (default 0.15) — boost for profile (preferences + facts)

4. **Fallback** — If no trained weights exist or the server is unreachable, heuristic defaults are used. Zero disruption.

### SIRU Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/agent/recall-log` | POST | Log a recall session (plugin → server, automatic) |
| `/api/v1/agent/recall-feedback` | POST | Submit explicit feedback on recall quality |
| `/api/v1/agent/recall-weights` | GET | Get current scoring weights (learned or default) |
| `/api/v2/siu/retrain` | POST | Trigger SIRU training (`model=siru`) |

### SIRU Feedback

Agents can provide explicit feedback on recall quality to accelerate SIRU learning:
```
POST /api/v1/agent/recall-feedback
{ "session_id": 42, "signal": "helpful" }
```
Valid signals: `helpful`, `unhelpful`, `partial`. Sessions with feedback are weighted more heavily during training than implicit frequency signals.

No action needed from the agent for basic operation — session logging is fire-and-forget, and learned weights are fetched automatically.

## Trigger System

Triggers fire automatically on server-side memory events. You can evaluate them explicitly with `evaluate_triggers`.

**Events:**
- `on_store` — fires when a memory is stored
- `on_recall` — fires when a memory is recalled
- `on_boost` — fires when a memory's heat is boosted
- `on_decay` — fires when a memory cools below a threshold

**Actions:**
- `notify` — emit a notification event to the agent
- `boost` — raise heat on matching memories
- `pin` — prevent a memory from decaying
- `tag` — add a tag to a memory
- `deprecate` — mark a memory as superseded
- `webhook` — call an external URL with memory context
- `chain` — trigger another trigger

## Curator (Sleep Cycle)

The curator is a background process that runs independently of agent activity:

- **Reclassifies** memories where SICU confidence is low
- **Consolidates** near-duplicate memories (merges or deprecates)
- **Summarizes** clusters of episodic memories into semantic nodes
- **Re-vectorizes** memories whose embeddings are stale
- **Resolves conflicts** detected by the conflict detection system (v2.3.0+)

You don't need to trigger the curator — it runs on a schedule. Use `consolidate` to manually initiate a consolidation pass when needed.

## Confidence Levels (v2.3.0+)

Every memory carries a confidence level:

- `observed` (default) — directly observed fact or event
- `inferred` — derived from other memories or reasoning
- `asserted` — explicitly stated by user or system

The conflict detection system flags memory pairs with high similarity but contradictory content. Use `memory_status` to inspect open conflicts.

## Tool Reference

| Tool | What It Does |
|---|---|
| `memory_store` | Store a memory. SIU pipeline fires automatically. |
| `memory_recall` | Semantic search with relevance weighting. |
| `memory_status` | Backend status, hot nodes, decay mode, curator state, open conflicts. |
| `memory_delete` | Delete by ID. Optional SIVU training to reject similar content. |
| `consolidate` | Merge and prune cold memories below a heat threshold. |
| `export_markdown` | Export all namespace memories as Markdown. |
| `import_markdown` | Import memories from a Markdown document. |
| `evaluate_triggers` | Evaluate reactive triggers against an event + context. |
| `evaluate_output` | (MCP) Evaluate LLM output against memory for semantic alignment. |
| `trigger_feedback` | Submit feedback to improve trigger accuracy (SITU scoring). |
| `memory_share` | Share a memory with another agent's namespace (disabled by default, opt-in). |
| `memory_cross_recall` | Search another agent's memories for cross-agent context (disabled by default, opt-in). |

## Cross-Agent Memory (v5.0.0+)

Agents can share context through namespace bridging:

- **`memory_share`** — stores a memory in another agent's namespace with `[Shared by {source}]` prefix
- **`memory_cross_recall`** — queries another agent's memories
- **`sharedNamespaces`** config — automatically includes context from configured namespaces in every turn

Both tools are **disabled by default**. Enable in plugin config:
```json
{
  "tools": {
    "memory_share": { "enabled": true },
    "memory_cross_recall": { "enabled": true }
  },
  "sharedNamespaces": ["agent-b", "agent-c"]
}
```

## Usage Patterns

### Start of session
Context is injected automatically via `before_prompt_build` (v5.5.0+). No manual recall needed on session start — the multi-signal recall pipeline surfaces your most important memories every turn.

For explicit search when you need specific context:
```
memory_recall(query="[current task or project]", limit=5)
```

### Capturing preferences
```
memory_store(content="User prefers TypeScript strict mode", memory_type="preference")
```

### Capturing a process
```
memory_store(content="Deploy process: build → test → tag → push → notify #releases", memory_type="procedural")
```

### After compaction/reset
The plugin auto-captures a session summary on compaction (`captureOnCompaction=true`) and reset (`captureOnReset=true`). These fire automatically — no manual action needed.

### Periodic cleanup
```
consolidate(min_heat=0.1)
```
Run occasionally to merge near-duplicates and prune cold noise.

## Plugin Configuration

Key config fields in `openclaw.json` → `plugins.entries.sulcus.config`:

| Field | Type | Default | Description |
|---|---|---|---|
| `serverUrl` | string | — | Sulcus server URL (e.g., `https://api.sulcus.ca`) |
| `apiKey` | string | — | API key from [sulcus.ca](https://sulcus.ca) |
| `agentId` | string | — | Agent identifier |
| `namespace` | string | — | Memory namespace (usually same as agentId) |
| `autoRecall` | boolean | `false` | Enable automatic multi-signal context injection via `before_prompt_build`. Opt-in. |
| `tokenBudget` | number | `500` | Max tokens for injected context block. Keep this compact for cache efficiency. |
| `autoCapture` | boolean | `false` | Enable SIVU auto-capture on `agent_end`, `session_end`, `before_reset`. Opt-in. |
| `importHistory` | boolean | `false` | One-time import of OpenClaw workspace files (MEMORY.md, daily notes) into Sulcus. Opt-in. |
| `maxRecallResults` | number | `5` | Max memories per search |
| `captureOnCompaction` | boolean | `true` | Mine pre-compaction transcripts for memories (only fires if `autoCapture` is true) |
| `captureOnReset` | boolean | `true` | Extract memories before `/reset` wipes context (only fires if `autoCapture` is true) |
| `hooks.llm_output_evaluation.enabled` | boolean | `false` | Enable SILU output evaluation on every LLM response |

**⚠️ Critical: `hooks.allowPromptInjection` must be `true`** for `before_prompt_build` to inject context. Without it, the memory layer is silent.

### Minimal working config (local-only, no network):
```json
{
  "plugins": {
    "entries": {
      "openclaw-sulcus": {
        "enabled": true,
        "config": {
          "agentId": "your-agent",
          "namespace": "your-agent"
        }
      }
    }
  }
}
```

### Cloud mode config:
```json
{
  "plugins": {
    "entries": {
      "openclaw-sulcus": {
        "enabled": true,
        "hooks": { "allowPromptInjection": true },
        "config": {
          "serverUrl": "https://api.sulcus.ca",
          "apiKey": "YOUR_API_KEY",
          "agentId": "your-agent",
          "namespace": "your-agent",
          "autoRecall": true,
          "autoCapture": true
        }
      }
    }
  }
}
```

**Note:** `autoRecall` and `autoCapture` are `false` by default — the above explicitly enables them for cloud mode. Without `serverUrl`/`apiKey`, the plugin runs local-only with zero network calls.

## Server Recall Tuning (v2.6.0+)

These fields are tuned server-side via `PATCH /api/v1/settings/thermo`:

| Field | Default | Effect |
|---|---|---|
| `recall.similarity_weight` | 0.7 | Weight for semantic similarity |
| `recall.heat_weight` | 0.3 | Weight for memory heat |
| `recall.keyword_weight` | 0.15 | Boost for exact word matches |
| `recall.temporal_max_boost` | 0.4 | Max boost for time-referenced queries |
| `recall.temporal_decay_days` | 7.0 | Days over which temporal boost decays |
| `recall.namespace_boost` | 0.1 | Boost for agent's own namespace memories |

## Troubleshooting

- **Plugin not responding** — ensure `openclaw-sulcus` is installed and enabled in `~/.openclaw/openclaw.json`. Run `openclaw gateway restart` after config changes.
- **No context injection** — check that `hooks.allowPromptInjection: true` is set. Without it, `before_prompt_build` can't inject.
- **No cloud sync** — `serverUrl` and `apiKey` required. Get a key at [sulcus.ca](https://sulcus.ca). Without them, plugin runs local-only.
- **Local mode** — `sulcus-local` binary manages embedded PostgreSQL. Check `memory_status` to confirm backend mode.
- **Memories not persisting** — verify namespace matches across sessions (`agentId` / `namespace` in config).
- **Memories decaying too fast** — check decay mode via `memory_status`. Switch to `Hybrid` mode server-side, or use `procedural`/`fact` types for long-lived knowledge.
- **Conflicts detected** — use `memory_status` to inspect. The curator will attempt auto-resolution; use `memory_delete` + `memory_store` to manually resolve.
- **Agent knocked offline after plugin update** — ensure the plugin version matches the server version. v5.5.0 plugin requires server v2.6.0+ for hot-context and entity-context. Falls back gracefully on older servers but with reduced functionality.
- **High LLM cache-write costs** — if cache hit rate is below 50%, upgrade to v5.5.1. Earlier versions inject volatile relevance percentages and timestamps that bust the prompt cache on every turn. v5.5.1 uses stable confidence bands and a recall TTL to keep the injected block byte-identical across turns.
- **Recall seems stale within a session** — the 5-minute recall TTL means the same context is reused within a session. If you need fresh recall after a significant topic change, wait for TTL expiry or use explicit `memory_recall` tool calls.

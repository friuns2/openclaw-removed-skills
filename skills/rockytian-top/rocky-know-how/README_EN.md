# rocky-know-how v3.4.8

**Experience & Knowledge Auto-Learning System for OpenClaw Agents**

> Enable AI Agents to learn from failures and automatically record successes, forming a complete experience closed-loop.

[![Version](https://img.shields.io/badge/version-3.4.8-blue)]()
[![Models Tested](https://img.shields.io/badge/models_tested-deepseek_v4%20%7C%20glm_5.1%20%7C%20minimax_m2.7-green)]()
[![Code Lines](https://img.shields.io/badge/code-4632_lines-orange)]()

---

## Overview

rocky-know-how is a **fully automatic experience learning system** designed for OpenClaw Agents. Through 4-event Hook integration, it achieves a complete closed-loop: automatic experience extraction from conversations → LLM intelligent judgment → triple-layer storage management.

**Key Features:**
- Full Auto-Closed-Loop — Auto-extract on compaction → LLM judge → write experience, zero manual intervention
- LLM Dual-Judgment — First judges if worth saving, then decides create vs append
- Triple-Layer Storage — HOT (always loaded) / WARM (on-demand) / COLD (archive)
- 5-Layer Security — Regex injection prevention, path traversal filtering, concurrent write lock, dedup promotion, degradation fallback
- Multi-Provider — Supports deepseek / glm / minimax / stepfun (including OAuth)
- 3-Model Verified — deepseek-v4, glm-5.1, minimax-m2.7 all passed forward & reverse testing

---

## Quick Start

### Install

```bash
git clone https://gitee.com/rocky_tian/skill.git
cd skill/rocky-know-how
bash scripts/install.sh
```

### Core Commands

```bash
# Search experiences
bash scripts/search.sh "keyword"

# Write experience
bash scripts/record.sh "problem" "pitfall" "solution" "prevention" "tag1,tag2" "area"

# View all
bash scripts/search.sh --all

# Statistics dashboard
bash scripts/stats.sh
```

---

## Architecture

### 4-Event Driven

| Event | Trigger | Function |
|-------|---------|----------|
| `agent:bootstrap` | Agent startup | Inject experience reminder into systemPrompt |
| `before_compaction` | Before compression | Extract task/tools/errors → save to pending/ |
| `after_compaction` | After compression | Core: LLM dual-judge → draft → write → archive |
| `before_reset` | Before session reset | Fallback save pending context |

### Triple-Layer Storage

```
~/.openclaw/.learnings/
├── experiences.md    ← Main data (v1 compatible)
├── memory.md         ← HOT layer (≤100 lines, always loaded)
├── domains/          ← WARM layer (by area: infra, code, global...)
├── projects/         ← WARM layer (by project)
├── archive/          ← COLD layer (90+ days)
├── drafts/           ← Auto-generated drafts (LLM judged)
└── pending/          ← Session context (before processing)
```

---

## Safety & Security

| Mechanism | Implementation |
|-----------|---------------|
| Regex injection prevention | `escape_grep()` sed escaping |
| Path traversal filtering | `replace(/[^a-zA-Z0-9_-]/g, '')` |
| Concurrent write lock | `.write_lock/` directory atomic lock |
| Tag dedup promotion | record.sh dedup + promote.sh ≥3x/7days threshold |
| Graceful degradation | LLM → keyword → write, triple fallback chain |

---

## Code Statistics

| Module | Lines |
|--------|------:|
| handler.js (Core Hook) | 1,110 |
| 17 Scripts | 3,522 |
| **Total** | **4,632** |

---

## Verified Testing

### Models Tested

| Model | Provider | Forward Test | Reverse Test | Status |
|-------|----------|:------------:|:------------:|:------:|
| deepseek-v4 | deepseek (api-key) | ✅ Pass | ✅ 144/150 | Verified |
| glm-5.1 | zai (api-key) | ✅ Pass | ✅ 146/150 | Verified |
| MiniMax-M2.7-highspeed | minimax-portal (OAuth) | ✅ Pass | ✅ 146/150 | Verified |

---

## Key Advantages

1. **Zero-config auto-learning** — Hook events automatically capture experience, no manual trigger needed
2. **LLM dual-judgment** — First judges if worth saving, then decides create vs append
3. **Triple degradation** — LLM → keyword → write, never loses data
4. **Multi-provider** — Supports OpenAI, Anthropic, OAuth providers (zai/stepfun/minimax)
5. **Production proven** — 45+ real experiences, 2.6MB data, stable operation
6. **Safety first** — 5 security mechanisms (regex injection, path traversal, write lock, etc.)

---

## Repositories

- **Gitee**: https://gitee.com/rocky_tian/skill
- **GitHub**: https://github.com/rocky-tian/skill
- **ClawHub**: https://clawhub.ai/skills/rocky-know-how

---

_Version: 3.4.8 | Tested: 2026-04-25 | License: MIT_

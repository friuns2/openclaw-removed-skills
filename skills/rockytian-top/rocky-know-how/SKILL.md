---
name: rocky-know-how
slug: rocky-know-how
version: 3.4.8
homepage: https://clawhub.ai/skills/rocky-know-how
description: "Learning knowledge skill v3.4.8 — vector search with bge-large-zh-v1.5, auto-fallback to keyword search, preprocessing for numbers/English/spell-correction. Tested & verified: deepseek-v4, glm-5.1, minimax-m2.7."

metadata: {"openclaw":{"emoji":"📚","requires":{"bins":["bash"]},"os":["darwin","linux"]}}
---

# rocky-know-how v3.4.8

**Experience & Knowledge Auto-Learning System for OpenClaw Agents**

> 让 AI Agent 从失败中学习，在成功后自动记录，形成经验闭环。

---

## 🎯 When to Use / 适用场景

| Scenario 场景 | Action 操作 |
|---------------|-------------|
| Failed 2+ times 失败≥2次 | `bash scripts/search.sh "关键词"` |
| Solved after failures 解决后 | `bash scripts/record.sh "问题" "踩坑" "方案" "预防" "tags" "area"` |
| Auto on compaction 压缩时 | **before_compaction driven** — pending → LLM extract → write experiences.md |
| Auto on reset 重置时 | **Fully automatic** — Hook saves pending context |
| Tag used 3x/7days 晋升 | `bash scripts/promote.sh` |
| Tag unused 30days 降级 | `bash scripts/demote.sh` |

---

## 🏗️ Architecture / 架构

### Triple-Layer Storage / 三层存储

```
~/.openclaw/.learnings/
├── experiences.md    ← Main data (v1 compatible, all experiences)
├── memory.md         ← HOT layer (≤100 lines, always loaded)
├── domains/          ← WARM layer (by area: infra, code, wx...)
│   ├── infra.md
│   ├── code.md
│   └── global.md
├── projects/         ← WARM layer (by project)
├── archive/          ← COLD layer (90+ days)
├── drafts/           ← Auto-generated drafts (LLM judged)
├── pending/          ← Session context (before processing)
└── corrections.md    ← Correction log (auto-dedup)
```

### Event-Driven Integration / 事件驱动

| Event 事件 | Trigger 触发 | Function 功能 |
|-----------|-------------|---------------|
| `agent:bootstrap` | Agent startup 启动 | Inject experience reminder into systemPrompt + process old drafts |
| `before_compaction` | Before compaction (auto) | **Core: save pending → LLM extract → write experiences.md → auto-review** |
| `before_reset` | Before session reset 重置前 | Save context as pending (fallback) |

> ✅ **v3.1.1**: `before_compaction` hook now properly triggers experience recording (LLM extract + write). `memoryFlush` still used for memory/*.md files.

---

## 🔄 Experience Recording Flow / 经验记录流程

### before_compaction-Driven (Core) / before_compaction 驱动（核心）

> **v3.1.1**: Hook triggers synchronously during compaction, before `compact()` executes.

```
before_compaction hook fires
    │
    ▼
① Save session context 保存上下文
    └─ handler.js → pending/*.json
    │
    ▼
② Extract & write 提取并写入
    ├─ processPendingItem() → LLM judgment
    └─ experiences.md written
    │
    ▼
③ Auto-review  auto-review.sh
    ├─ Similar experience detection
    └─ Tag → TOOLS.md promotion check
    │
    ▼
Compaction continues (compact() executes)
```

### bootstrap (Startup) / 启动时

```
agent:bootstrap triggers
    ├─ Load domains/*.md → inject experience reminder into systemPrompt
    └─ Check drafts/ → process old drafts (fallback)
```

### before_reset (Fallback) / 重置兜底

```
/reset or /new triggers
    └─ handler.js saves context → pending/*.json
```

---

## 🛡️ Safety & Security / 安全机制

| Mechanism 机制 | Implementation 实现 |
|---------------|-------------------|
| Regex injection prevention 正则注入防护 | `escape_grep()` sed escaping |
| Path traversal filtering 路径穿越过滤 | `replace(/[^a-zA-Z0-9_-]/g, '')` |
| Concurrent write lock 并发写锁 | `.write_lock/` directory atomic lock |
| Tag dedup promotion Tag去重晋升 | record.sh dedup + promote.sh threshold |
| Graceful degradation 降级容错 | LLM → keyword → write fallback chain |

---

## 📊 Scripts Reference / 脚本说明

| Script 脚本 | Lines 行数 | Function 功能 |
|------------|:----------:|--------------|
| handler.js | 1,110 | Core hook handler (4 events, LLM integration) |
| search.sh | 539 | Search experiences (keyword / preview / all) |
| record.sh | 476 | Write new experience (with dedup & lock) |
| demote.sh | 371 | Demote HOT tags to WARM |
| compact.sh | 348 | Compress layers when exceeding limits |
| clean.sh | 247 | Remove test/invalid entries |
| vectors.sh | 232 | Vector search via LM Studio embeddings |
| promote.sh | 185 | Promote WARM tags to HOT (≥3x/7days) |
| import.sh | 172 | Import experiences from other sources |
| archive.sh | 167 | Archive old experiences to COLD |
| install.sh | 161 | Install skill to workspace |
| stats.sh | 153 | Show statistics dashboard |
| auto-review.sh | 136 | Auto-review pending drafts |
| append-record.sh | 100 | Append solution to existing experience |
| summarize-drafts.sh | 80 | Summarize and process drafts |
| update-record.sh | 77 | Update existing experience |
| common.sh | 41 | Shared utility functions |
| uninstall.sh | 37 | Remove skill |
| **Total 共计** | **4,632** | |

---

## ✅ Verified Testing / 测试验证

### Models Tested / 已测试模型

| Model 模型 | Provider | Forward Test 正向 | Reverse Test 逆向 | Status |
|-----------|----------|:-----------------:|:-----------------:|:------:|
| deepseek-v4 | deepseek (api-key) | ✅ Pass | ✅ Pass (144/150) | Verified |
| glm-5.1 | zai (api-key) | ✅ Pass | ✅ Pass (146/150) | Verified |
| MiniMax-M2.7-highspeed | minimax-portal (OAuth) | ✅ Pass | ✅ Pass (146/150) | Verified |

### Test Coverage / 测试覆盖

| Test 测试 | Result 结果 |
|----------|:----------:|
| agent:bootstrap → systemPrompt injection | ✅ 12→952 chars |
| before_compaction → pending + LLM write | ✅ pending → LLM → experiences.md → auto-review |
| memoryFlush → memory/*.md write | ✅ Still used for memory file writing |
| before_reset → fallback save | ✅ pending saved |
| record.sh write + search | ✅ Write & find |
| auto-review.sh process draft | ✅ Draft → archive |
| compact.sh dry-run | ✅ All layers healthy |
| promote.sh tag promotion | ✅ Threshold check |
| stats.sh dashboard | ✅ Full panel |
| 5 safety mechanisms | ✅ All present |

---

## 🚀 Installation / 安装

### 1. Install Skill / 安装技能

```bash
# Clone
git clone https://gitee.com/rocky_tian/skill.git
cd skill/rocky-know-how

# Install
bash scripts/install.sh

# Verify
bash scripts/stats.sh
```

### 2. Configure memoryFlush / 配置 memoryFlush（重要）

> **This config is for memory/*.md file writing only (v3.1.1).**
> Experience recording is now handled by `before_compaction` hook.

Add the following to your `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "memoryFlush": {
          "enabled": true,
          "softThresholdTokens": 8000,
          "prompt": "会话即将压缩。请按以下流程处理经验，再写记忆：\n\n【第一步：处理旧草稿】\n检查 ~/.openclaw/.learnings/drafts/ 目录是否有旧草稿：\n  - 旧草稿 + 当前对话没提到同问题 → 说明已解决 → 调 record.sh 转正式经验\n  - 旧草稿 + 当前对话还在处理同问题 → 保留草稿不动\n\n【第二步：提取新经验】\n扫描当前对话，遇到以下情况值得记录：\n  - 同一问题失败≥2次后解决\n  - 踩坑后找到正确方案\n  - 发现重要配置/命令/技巧\n判断逻辑：\n  - 无旧草稿 + 第1轮就搞定 → 直接 record.sh 写正式经验\n  - 同问题有旧草稿（多轮调试）→ 写/更新草稿到 drafts/\n  - 没有值得记录的 → 跳过\n\n【第三步：写记忆文件】\n将重要记忆追加到 memory/YYYY-MM-DD.md（已有则追加，不覆盖）\n\n完成后回复 NO_REPLY。\n\nrecord.sh 用法：bash ~/.openclaw/skills/rocky-know-how/scripts/record.sh \"问题\" \"踩坑过程\" \"正确方案\" \"预防措施\" \"tag1,tag2\" \"领域\"",
          "systemPrompt": "会话即将压缩。按顺序处理：旧草稿→新经验→记忆文件。经验优先，记忆精简。"
        }
      }
    }
  }
}
```

**Why `softThresholdTokens: 8000`?**

OpenClaw default is 4000, but experience recording (judge + record.sh + memory write) needs ~3000-5500 tokens. 8000 provides enough headroom.

**Why not use default 4000?**

4000 tokens is too tight. If there are old drafts to process or the memory content is long, it may exceed the budget and cause the flush to fail.

### 3. Configure Hooks / 配置 Hook

```bash
# Add hook config to openclaw.json (under hooks.internal.entries)
# install.sh does this automatically
```

Hooks needed:
- `agent:bootstrap` → handler (inject experience reminder)
- `before_reset` → handler (fallback save)

---

## 📈 Key Advantages / 核心优势

1. **before_compaction-driven auto-learning** — Experience recording triggered before every compaction
2. **LLM dual-judgment** — First judges if worth saving, then decides create vs append
3. **Triple degradation** — LLM → keyword → write, never loses data
4. **Multi-provider** — Supports OpenAI, Anthropic, OAuth providers (zai/stepfun/minimax)
5. **Production proven** — 45+ real experiences, 2.6MB data, stable operation
6. **Safety first** — 5 security mechanisms (regex injection, path traversal, write lock, etc.)

---

_Version: 3.4.8 | Tested: 2026-04-25 | License: MIT_

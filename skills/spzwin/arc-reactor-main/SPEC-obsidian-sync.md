# SPEC: Obsidian Sync 集成规范

> **版本**: v1.0  
> **状态**: 设计规范  
> **目标**: 将 Obsidian 同步功能无缝嵌入 ARC Reactor SKILL.md 主流程

---

## 1. 背景与设计目标

### 现状
- ARC Reactor 的 **4连击** (source → entity → index → log) 已完善，输出落地在本地 `arc-reactor-doc/` Wiki
- `references/dispatchers/obsidian.md` 定义了 Obsidian 同步调度逻辑，但**未集成**到 SKILL.md 主流程
- 用户需要在报告生成后手动同步到 Obsidian，流程割裂

### 设计目标
1. **透明集成**：Obsidian 同步作为 Display Layer 之后的附加动作，对主流程无侵入
2. **可选控制**：通过 `AUTO_SYNC=false` 完全关闭，不影响任何主流程
3. **异步非阻塞**：同步失败不阻塞用户，不影响 Display Layer 输出
4. **Display Layer 纯净**：≤200字原则不受影响，同步状态用超链接替代文字堆砌

---

## 2. 集成点设计

### 2.1 在 SKILL.md 中的插入位置

在 SKILL.md 的 **Display Layer** 小节之后、**Channel 自适应输出** 之前，插入新小节：

```
## 🔄 Obsidian 同步层（可选后处理）

触发时机：Display Layer 输出完成后，作为独立附加动作异步执行
前置条件：OBSIDIAN_VAULT_PATH 已配置且有效
```

### 2.2 完整流程顺序

```
用户输入
  ↓
[4连击 Ingest]  (source → entity → index → log)
  ↓
[Display Layer] ≤200字，用户可见
  ↓
[Obsidian Sync] ← 附加动作，异步，不阻塞
  ↓
返回结果给 Orchestrator
```

**关键决策**：Obsidian 同步**不是第5步**，而是 Display Layer 之后的独立后处理动作。

理由：
- 4连击 是知识库写入的原子操作，职责单一
- Obsidian 同步是**消费**已生成的报告，不是生产知识
- Display Layer 必须在同步之前完成（否则会因同步失败而延迟用户可见输出）

---

## 3. 同步触发时机

### 3.1 触发条件（同时满足）

| 条件 | 说明 |
|------|------|
| `OBSIDIAN_VAULT_PATH` 已配置 | 未配置时跳过，不询问 |
| `AUTO_SYNC` != `false` | 默认为 `true`，用户可关闭 |
| 本次 Ingest 产生了 source 文件 | 无 source 时不同步（避免空操作） |

### 3.2 触发时机点

在 Display Layer 输出完成**之后**，作为独立步骤执行：

```python
# 伪代码
def after_display_layer(report_path):
    if not AUTO_SYNC or AUTO_SYNC == "false":
        return  # 完全跳过

    if not OBSIDIAN_VAULT_PATH:
        return  # 未配置，跳过

    # 异步后台执行，不阻塞主流程
    async_task = spawn(sync_to_obsidian, report_path)
```

### 3.3 同步文件选择

同步时按以下优先级选择要复制的文件：

1. **source 文件**（本次 Ingest 的原始报告）：`arc-reactor-doc/wiki/sources/{date}/{topic}.md`
2. **不存在时**：使用 index.md 中本次相关的摘要行

---

## 4. 配置方式

### 4.1 环境变量（推荐）

```bash
# .env 或 openclaw.json
OBSIDIAN_VAULT_PATH=~/Library/Mobile Documents/iCloud~md~obsidian/Documents/
OBSIDIAN_TARGET_DIR=github分享/AI调研/{date}/
AUTO_SYNC=true
```

### 4.2 SKILL.md 中的引导流程（新增）

在 SKILL.md 的**铁律**之后、**Display Layer** 之前，插入 Obsidian 配置引导：

```
### Obsidian 同步配置（首次使用引导）

若 OBSIDIAN_VAULT_PATH 未设置，Agent 应主动引导：

1. 询问用户 Obsidian 根目录路径
2. 将路径写入 .env（OBSIDIAN_VAULT_PATH）
3. 执行自检脚本（见 obsidian.md 第3节）
4. 确认后告知用户已开启自动同步
```

### 4.3 配置校验逻辑

```python
def validate_obsidian_config():
    vault = os.path.expanduser(OBSIDIAN_VAULT_PATH)
    if not os.path.isdir(vault):
        return False, "Obsidian 库路径不存在"

    test_path = os.path.join(vault, '.arc-sync-test')
    try:
        with open(test_path, 'w') as f:
            f.write('ping')
        os.remove(test_path)
        return True, "OK"
    except:
        return False, "无写入权限"
```

---

## 5. Display Layer 输出规范

### 5.1 原则

- Display Layer **永远独立**于 Obsidian 同步状态
- 同步成功/失败**不在 Display Layer 文字中体现**
- 用户通过超链接或附加标记感知 Obsidian 状态

### 5.2 Display Layer 输出模板

**场景A：同步成功（Display Layer 不变）**

```
报告已完成 ✅

· [[Claude-Code]]: Anthropic 系统级 AI 编程助手
· [[SWE-bench]]: 软件工程评测基准
· [[Devin]]: Cognition AI 的自主编程智能体

📁 已在 Obsidian 同步 → [打开 Obsidian](obsidian://open?vault=Documents)
```

**场景B：同步失败（Display Layer 仍显示成功）**

```
报告已完成 ✅

· [[Claude-Code]]: Anthropic 系统级 AI 编程助手
· [[SWE-bench]]: 软件工程评测基准

⚠️ Obsidian 同步暂不可用（后台重试中）
📁 报告已保存在本地 arc-reactor-doc/wiki/sources/
```

### 5.3 字数控制

Display Layer 核心文字（不含链接）≤180字，剩余空间留给同步状态标记。

| 场景 | 核心字数 | 状态标记字数 | 总计 |
|------|----------|--------------|------|
| 同步成功 | ~150字 | ~25字 | ≤200字 |
| 同步失败 | ~150字 | ~40字 | ≤200字 |
| 未配置同步 | ~190字 | 0 | ≤200字 |

### 5.4 同步状态附录标记

在源报告文件末尾追加（不影响 Display Layer）：

```markdown
---
同步状态: ✅ Obsidian (时间: 2026-04-09 14:30)
---
```

或失败时：

```markdown
---
同步状态: ⚠️ Obsidian 失败 (原因: 路径无写入权限)
重试次数: 1/3
---
```

---

## 6. 错误处理策略

| 错误类型 | 处理方式 |
|----------|----------|
| `OBSIDIAN_VAULT_PATH` 未配置 | 跳过，不询问（按需引导） |
| 库路径不存在 | Display Layer 显示警告，超链接变为"配置 Obsidian" |
| 写入权限不足 | 重试1次，失败后记录到 log.md，跳过 |
| 网络问题（iCloud不同步） | 后台重试3次（间隔5分钟），Display Layer 无感知 |
| 目标目录创建失败 | 记录错误，不阻塞，Display Layer 无感知 |

**重试策略**：使用指数退避，最多3次，异步执行。

---

## 7. 实现方案

### 7.1 新增 SKILL.md 片段

在 SKILL.md Display Layer 小节**之后**插入：

```markdown
## 🔄 Obsidian 同步层（可选后处理）

**触发时机**：Display Layer 输出完成后，异步执行  
**前置条件**：`OBSIDIAN_VAULT_PATH` 已配置且 `AUTO_SYNC != false`

### 配置变量
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OBSIDIAN_VAULT_PATH` | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` | Obsidian 仓库根路径 |
| `OBSIDIAN_TARGET_DIR` | `github分享/AI调研/{date}/` | 目标子目录，`{date}` 自动替换 |
| `AUTO_SYNC` | `true` | 是否自动同步 |

### 执行流程
1. **校验配置**：`validate_obsidian_config()` 返回失败则跳过
2. **复制报告**：将本次 source 文件复制到 `{vault}/{target_dir}/{topic}.md`
3. **追加状态**：在源文件末尾追加 `同步状态: ✅ Obsidian (时间: ...)`
4. **Display Layer**：Display Layer 永远先于同步完成，用户无感知等待

### 铁律
- 同步失败**不阻塞** Display Layer 输出
- 同步失败**不重写** Display Layer 内容
- `AUTO_SYNC=false` 时完全不执行任何 Obsidian 相关代码
```

### 7.2 archive-manager.py 扩展

新增 `--sync-obsidian` 命令：

```bash
python3 scripts/archive-manager.py \
  --sync-obsidian \
  --source arc-reactor-doc/wiki/sources/2026-04-09/claude-code.md \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --target "github分享/AI调研/{date}/" \
  --async
```

返回 JSON 回执：
```json
{
  "status": "success",
  "action": "obsidian_sync",
  "source": "...",
  "destination": "...",
  "obsidian_vault": "~/Library/.../Documents/",
  "sync_time": "2026-04-09 14:30:05",
  "message": "Obsidian sync complete."
}
```

### 7.3 Orchestrator 任务注入更新

Spawn 任务时，在 Display Layer 完成后追加：

```bash
# Obsidian 同步（如果已配置且 AUTO_SYNC != false）
python3 scripts/archive-manager.py \
  --sync-obsidian \
  --source "arc-reactor-doc/wiki/sources/{date}/{topic}.md" \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --target "$OBSIDIAN_TARGET_DIR" \
  --async
```

---

## 8. 测试用例

### TC-1：完整同步流程
```
前置条件：AUTO_SYNC=true, OBSIDIAN_VAULT_PATH 有效
步骤：
  1. 执行 Ingest（4连击）
  2. 观察 Display Layer 输出
  3. 检查 Obsidian 目标目录是否有文件
预期：Display Layer 先显示，Obsidian 同步异步完成
```

### TC-2：同步失败不影响主流程
```
前置条件：AUTO_SYNC=true, OBSIDIAN_VAULT_PATH 指向不存在路径
步骤：
  1. 执行 Ingest（4连击）
  2. 观察 Display Layer 输出
预期：Display Layer 正常显示成功，Obsidian 失败有日志但不展示给用户
```

### TC-3：AUTO_SYNC=false 完全关闭
```
前置条件：AUTO_SYNC=false
步骤：
  1. 执行 Ingest（4连击）
  2. 检查是否有任何 Obsidian 相关日志或文件操作
预期：无任何 Obsidian 操作，Display Layer 正常
```

### TC-4：Display Layer 字数验证
```
前置条件：标准 Ingest 输出
步骤：
  1. 捕获 Display Layer 输出
  2. 统计字符数（含状态标记）
预期：≤200字
```

### TC-5：OBSIDIAN_VAULT_PATH 未配置时按需引导
```
前置条件：OBSIDIAN_VAULT_PATH 为空，用户首次提及 Obsidian
步骤：
  1. 用户说"帮我搜 xxx，结果存到 Obsidian"
预期：Agent 主动询问 Obsidian 路径，完成配置引导
```

---

## 9. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `SKILL.md` | 修改 | 在 Display Layer 后插入 Obsidian 同步小节 |
| `scripts/archive-manager.py` | 修改 | 新增 `--sync-obsidian` 命令 |
| `references/dispatchers/obsidian.md` | 保持 | 现有调度器保持不变，作为参考 |

---

## 10. 关键设计决策记录

| 决策 | 理由 |
|------|------|
| 同步不是第5步 | 4连击是知识生产原子操作，Obsidian 是消费动作，时机不同 |
| Display Layer 不感知同步状态 | 保持≤200字原则，同步是后处理细节 |
| 失败不阻塞 | Obsidian 是锦上添花，不能因为 iCloud 问题影响核心体验 |
| 异步执行 | 用户不需要等待 iCloud 同步完成才能看到结果 |
| 配置通过环境变量 | 与现有 .env 体系一致，无需新配置接口 |

---

*本规范为设计文档，实现请同步更新 SKILL.md 和 archive-manager.py*

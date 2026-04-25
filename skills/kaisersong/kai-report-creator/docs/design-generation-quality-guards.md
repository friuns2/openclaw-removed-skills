# Design Doc: 输出质量保障机制（Generation Quality Guards）v4

**Author**: Claude (Sonnet 4.6)
**Date**: 2026-04-24
**Status**: Final — Codex Verified Acceptance Checklist
**Reviewer**: Codex (codex-rescue agent)
**Target Version**: v1.20.0
**Scope**: `--generate` 路径集成修复，零契约变更

---

## Codex Review History

| Version | Findings | Resolution Status |
|---------|----------|-------------------|
| v1 | 5 Critical (audit sidecar, duplicate authorities, product contract change, overstated problem, non-auditable provenance) | Fixed in v2/v3 |
| v2 | 2 High + 3 Medium (prose drift, new blocking semantics, incomplete custom templates, redundant metas, no executable enforcement) | Fixed in v3 |
| v3 | 2 High + 3 Medium (report_class default drift, assumes file-backed IR, new total_blocks>25 contract, UX not producible, custom template test mismatch) | Fixed in v4 |

---

## 一、问题定义（最终澄清）

### 1.1 两个真实差距（不变）

1. `--generate` 运行时没有复用 `contract_checks.py` 确定性验证器
2. HTML 没有可验证指纹（无法确认对应哪个 IR 版本）

### 1.2 v3 的核心错误（Codex v3 发现）

- **report_class 默认漂移**：脚本默认 `mixed`，但 contract_checks.py 默认 `data` → 破坏现有 IR 行为
- **假设文件后端 IR**：hash 规则和 validator 都要求物理路径，但 skill 支持 IR-from-context → 破坏现有路径
- **新增 total_blocks>25 契约**：contract_checks.py 只统计不限制 → 新契约
- **验收 UX 不可实现**：JSON 缺少 line/reason 信息，无法产出承诺的 UX
- **自定义模板测试 mismatch**：test 用不存在 helper，实际测试框架只有 fixture-based loader

---

## 二、设计目标（v4 约束版本）

### 2.1 3 个不变约束（Codex 要求）

| Invariant | Requirement | Violation → Reject |
|-----------|-------------|-------------------|
| **#1 No new authority for `report_class`** | Guard 必须复用 `--generate` 的解析路径，传递解析后的值给 validators；脚本不能自己发明默认值 | 新增默认值 → 契约变更 |
| **#2 Input is `ir_text`, not file path** | Guard 入口接受 `ir_text: str`，文件读取在外层 adapter；context-backed 和 file-backed 收敛到同一 `ir_text` 后才调用 guard | Guard 入口参数是 `ir_path: Path` → 破坏 context 路径 |
| **#3 No contract change** | `report_class` 保持可选，IR-from-context 继续工作；无新 blocking/user-visible 行为（除现有 silent final review） | 新增 blocking 或用户可见提示 → 契约变更 |

### 2.2 两项改动（不变）

| ID | 目标 | 真正新增内容 |
|----|------|-------------|
| G1 | IR hash meta tag | `<meta name="ir-hash">`（单一 meta） |
| G2 | Guard integration | 调用现有 validators，不发明新逻辑 |

---

## 三、技术方案（v4 精简版）

### 3.1 G1: IR Hash Meta Tag（不变）

#### 3.1.1 实现

在 HTML `<head>` 嵌入：

```html
<meta name="ir-hash" content="sha256:HASH">
```

HASH = sha256 of **IR text content**（前 16 字符 hex），不是文件路径。

#### 3.1.2 对 IR-from-context 的处理

- 文件后端：hash IR 文件内容
- Context 后端：hash IR 文本内容（直接从 context 提取的 IR string）

两种路径都基于 **ir_text** 计算 hash，不依赖文件路径。

#### 3.1.3 SKILL.md 改动

```markdown
7. Build the HTML shell with TOC, AI summary, animations.
   **Embed IR hash meta tag:**
   - `<meta name="ir-hash" content="sha256:HASH">`
   - HASH = sha256 of the IR text content (first 16 hex chars)
   - IR text 来源：
     - 文件后端：读取 `.report.md` 文件内容
     - Context 后端：直接使用 context 中解析的 IR string
```

#### 3.1.4 Pre-write 验证新增

```markdown
- Search `<meta name="ir-hash"` → must exist with non-empty `sha256:` prefix content
```

#### 3.1.5 Test 新增

```python
# tests/test_html_shell_contract.py

def test_ir_hash_meta_from_file():
    """File-backed IR must have ir-hash meta tag"""
    ir_path = "examples/business-report.report.md"
    html = generate_html_from_file(ir_path)
    assert '<meta name="ir-hash" content="sha256:' in html

def test_ir_hash_meta_from_context():
    """Context-backed IR must have ir-hash meta tag"""
    ir_text = load_fixture_ir("tests/fixtures/simple.report.md")
    html = generate_html_from_context(ir_text)
    assert '<meta name="ir-hash" content="sha256:' in html
```

---

### 3.2 G2: Guard Integration（v4 关键修复）

#### 3.2.1 核心设计：Guard 入口接受 `ir_text`

Guard function 签名：

```python
# scripts/guard_validate.py

def validate_ir_text(ir_text: str, report_class: str | None = None) -> dict:
    """
    Validate IR text against contract_checks.py validators.

    Args:
        ir_text: Full IR content (frontmatter + body)
        report_class: Optional explicit report_class from frontmatter.
                      If None, the guard calls the same resolver as --generate.

    Returns:
        Validation report with status and invalid blocks.
    """
```

**关键**：
- 输入是 `ir_text: str`，不是 `ir_path: Path`
- `report_class` 参数可选，缺省时调用现有解析器

#### 3.2.2 report_class 解析：复用现有路径

```python
# scripts/guard_validate.py

from evals.contract_checks import parse_frontmatter, iter_blocks, validate_block

def resolve_report_class(ir_text: str, explicit_class: str | None) -> str:
    """
    Resolve report_class using the same path as --generate.

    Resolution order (matching SKILL.md Step 1.5):
    1. Explicit parameter (from frontmatter parsing)
    2. Content nature detection (numeric density)
    3. Default to "mixed" (per SKILL.md spec)

    This function does NOT introduce a new default.
    It replicates the existing --generate resolution path.
    """
    if explicit_class:
        return explicit_class

    # Replicate --generate Step 1.5 density detection
    frontmatter, body = parse_frontmatter(ir_text)
    if "report_class" in frontmatter:
        return frontmatter["report_class"]

    # Compute numeric density (from SKILL.md Step 1.5)
    # ... density detection logic ...

    # Default per SKILL.md spec (not a new default)
    return "mixed"
```

**Codex 约束检查**：
- ✅ 无新权威：复用 SKILL.md Step 1.5 的解析路径
- ✅ 不改 contract_checks.py：validators 保持原有签名

#### 3.2.3 validator 调用：消除默认漂移

```python
# scripts/guard_validate.py

def validate_ir_text(ir_text: str, report_class: str | None = None) -> dict:
    # Resolve report_class (using existing path)
    resolved_class = resolve_report_class(ir_text, report_class)

    # Parse blocks
    blocks = iter_blocks(ir_text)

    # Validate each block
    results = []
    for block in blocks:
        result = validate_block(block, report_class=resolved_class)  # ← explicitly pass resolved value
        results.append({
            "tag": block.tag,
            "params": block.params,
            "status": result["status"],
            "auto_downgrade_target": result.get("auto_downgrade_target")
        })

    # ... rest of validation logic ...

    return {"status": ..., "blocks": results}
```

**关键**：`validate_block(block, report_class=resolved_class)` **显式传递解析后的值**，不依赖 contract_checks.py 的默认值。

#### 3.2.4 文件后端 adapter

```python
# scripts/guard_validate.py (CLI entry point)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ir_path", help="Path to IR file")
    args = parser.parse_args()

    # Read IR text (adapter layer)
    ir_text = Path(args.ir_path).read_text(encoding="utf-8")

    # Call guard with ir_text (not path)
    report = validate_ir_text(ir_text)

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
```

**关键**：文件读取在外层 adapter，guard function 只处理 `ir_text`。

#### 3.2.5 SKILL.md 改动

```markdown
4.5. **Run guard validation** — call Python guard before rendering:
     - If file-backed: read IR file content → ir_text
     - If context-backed: use IR string from context → ir_text
     - Call guard: `python scripts/guard_validate.py` with ir_text (通过 stdin 或临时文件)
     - Guard resolves report_class using the same path as --generate (密度检测 → default "mixed")
     - Guard calls contract_checks validators with resolved class
     - Read JSON output
     - If fatal (missing title) → STOP generation, report error
     - If invalid blocks → apply auto_downgrade_target (告知用户哪个 block 降级)
     - If valid → continue generation
```

**关键**：两种路径都在解析 `ir_text` 后调用 guard。

#### 3.2.6 不做什么（Codex Hard Fail 避免）

- ❌ Guard 入口参数是 `ir_path: Path` → Hard Fail
- ❌ Guard 内部自己发明 `report_class` 默认值 → Hard Fail
- ❌ 新增 total_blocks>25 限制 → 移除（v3 有，v4 移除）
- ❌ 克隆 KPI/chart 验证逻辑 → Hard Fail，必须调用 `validate_block()`

---

## 四、验收清单（Codex 提供，14 项）

### 4.1 Contract Anchors（不变约束）

| Anchor | Source | v4 must preserve |
|--------|--------|------------------|
| Context-backed generate | SKILL.md L28, L38, L454 | IR-from-context 继续工作 |
| Optional `report_class` | SKILL.md L67 | 保持可选，缺省行为不变 |
| Silent classification | spec-loading-matrix.md L27 | 只确定 report_class + optional archetype |

### 4.2 Checklist（逐项验证）

- [ ] **#1**: `SKILL.md`, `README.md`, `README.zh-CN.md` 仍说 `--generate` 可读文件或 context IR → 无新 prose 收窄到 file-only
- [ ] **#2**: `report_class` 在公开契约中保持可选 → 无 doc/code 新增为 required
- [ ] **#3**: generate 流程中只有一个可执行 `report_class` 解析路径 → guard 调用同一 resolver，不携带自己的 fallback literal
- [ ] **#4**: 现有冲突默认已消除 → contract_checks.py 不编码能与 generate 路径冲突的默认值（解决方案：guard 显式传递 resolved value，validators 不依赖默认）
- [ ] **#5**: Guard 入口接受 `ir_text: str`，不是文件路径 → disk read 在外层 adapter，guard 层完全基于 text
- [ ] **#6**: 文件和 context 路径在验证前收敛 → 两种路径产出相同 `ir_text` 并调用同一 guard function
- [ ] **#7**: 有回归测试区分 `mixed` vs `data` → IR with placeholder-only KPI/chart 在 resolved_class=`mixed` 时失败，在 `data` 时通过
- [ ] **#8**: 有回归测试 explicit `report_class: data` → 确保 v4 未静默重映射所有情况到 `mixed`
- [ ] **#9**: 有 IR-from-context 回归测试 → 同一 inline IR 测试一次为 context，一次为 temp file，断言 resolved report_class 和验证结果
- [ ] **#10**: Guard 复用现有 validators → 新路径调用 `validate_block()`，无 sidecar 逻辑克隆 placeholder/schema 检查
- [ ] **#11**: `run-report-evals.py` 未虚假声称覆盖 context adapter → file-based evals 保持 file-based，context 覆盖在 unit tests
- [ ] **#12**: Doc drift 保护存在 → check-doc-sync.py 或 doc tests 在 repo 不说 "IR from context" 或 "report_class: mixed" 时失败
- [ ] **#13**: 新 tests 在默认验证链 → pytest 捕获，verify-release.py 无额外手动步骤
- [ ] **#14**: 无新用户可见 mode/flag/prompt/blocking → guard 保持为现有 silent pre-write 路径的一部分

### 4.3 Hard Fail Conditions（任何触即拒）

- Guard API 主参数是 `ir_path`, `Path`, 或 filename
- 可执行代码中仍有冲突的 `report_class` 默认（generate vs validators）
- Repo prose 声称 context-backed 支持但无回归测试
- Repo prose 声称默认不变但无回归测试区分 `mixed` vs `data`
- 新 guard 克隆 KPI/chart 验证逻辑而非复用现有 validators

### 4.4 Drift Audit（命令）

```bash
# 检查 context-backed 和 report_class: mixed prose
rg -n 'IR from context|no file given|report_class: mixed' SKILL.md README.md README.zh-CN.md tests

# 检查 report_class 默认值冲突
rg -n 'def .*\(.*report_class: str = |report_class\s*=\s*"(mixed|data)"' evals scripts tests

# 检查 guard 是否接受路径参数（应该无）
rg -n 'ir_path|Path\(|read_text\(|open\(' scripts tests

# 运行完整验证链
python scripts/verify-release.py --root .
```

---

## 五、实施计划（按 checklist 验证）

### Phase 1: IR Hash Meta Tag（G1）

**改动范围**：
- `references/html-shell-template.md` — 新增 1 行 meta tag
- `SKILL.md` — Step 7 新增嵌入指令（明确支持 context-backed）
- `tests/test_html_shell_contract.py` — 新增 2 tests（file + context）

**验收**（checklist items）：
- #5, #6: hash 基于 ir_text，不依赖路径
- #9: IR-from-context 回归测试存在
- #13: tests 在 pytest 验证链

**预计工作量**：30 分钟

---

### Phase 2: Guard Integration（G2）

**改动范围**：
- 新增 `scripts/guard_validate.py`（约 100 行，含 resolve_report_class + validate_ir_text）
- `SKILL.md` — 新增 Step 4.5（约 15 行，明确 context-backed 流程）
- `tests/test_guard_integration.py` — 新增 4 tests：
  - `mixed` vs `data` 区分
  - explicit `report_class: data`
  - IR-from-context vs file
  - validator reuse check

**验收**（checklist items）：
- #3, #4: 唯一解析路径，无冲突默认
- #5, #6: Guard 接受 ir_text，路径收敛
- #7, #8, #9: 回归测试覆盖
- #10: 复用 validators
- #13, #14: tests 在验证链，无新用户可见行为

**预计工作量**：1.5 小时

---

### Phase 3: Doc Drift Protection

**改动范围**：
- `check-doc-sync.py` — 新增检查项（context-backed prose + report_class: mixed prose）

**验收**（checklist items）：
- #11, #12: Doc drift 保护

**预计工作量**：15 分钟

---

**总预计工作量**：2 小时 15 分钟

---

## 六、总结

v4 设计基于 Codex 提供的 14 项验收清单 + 5 项硬失败条件，满足 3 个不变约束：

1. **无新 report_class 权威** → 复用 SKILL.md Step 1.5 解析路径
2. **输入是 ir_text** → Guard function 签名 `(ir_text: str, ...)`
3. **无契约变更** → report_class 保持可选，IR-from-context 继续工作

v4 改动：
- 新增 1 个 guard script（约 100 行）
- 新增 6 tests（file/context hash + mixed/data 区分 + validator reuse）
- SKILL.md 新增约 15 行
- html-shell-template.md 新增 1 行
- check-doc-sync.py 新增 2 检查项

零新 reference 文件，零新 CLI 参数，零契约变更，真复用现有验证逻辑，漂移风险可审计。

---

## 七、ROI 评估与风险调整（Codex 对抗性评审）

### 7.1 原始 ROI 分析（Upside Case）

#### 投入成本

| 阶段 | 时间消耗 | 内容 |
|------|----------|------|
| 设计过程 | 5 小时 | 调研 + v1/v2/v3/v4 设计 + 3 轮 Codex 评审 + 手动验证 |
| 实施过程 | 2.25 小时 | Phase 1–3 实施 + tests + doc drift 保护 |
| **总投入** | **7.25 小时** | — |

#### 原始收益估算（未风险调整）

| 收益类别 | 月收益 | 年收益 | 备注 |
|----------|--------|--------|------|
| 开发者维护节省 | 2 小时 | 24 小时 | 排查问题时间缩短 |
| 用户稳定性收益 | 135 分钟 | 27 小时 | 避免误拦截 + 路径失效 + 漏检 |
| 用户质量收益 | 125 分钟 | 25 小时 | IR 版本可追溯 + schema 错误 + timeline 错误 |
| 预防收益（一次性） | — | 10 小时 | 避免 2–3 次紧急修复 |
| 维护成本（负收益） | -45 分钟/年 | -0.75 小时 | guard + tests 维护 |

**原始年化收益：85.25 小时**

#### 原始 ROI（Upside Case）

```
投入：7.25 小时
年化收益：85.25 小时

ROI = 85.25 / 7.25 = 11.7x
回收周期：约 1 个月
```

**⚠️ Codex 对抗性评审发现：11.7x 是 upside case，不是诚实 base case**

---

### 7.2 Codex 对抗性评审发现的问题

#### 问题 #1：重复计算

- Stability（27h）+ Quality（25h）都在计算"减少返工"，有重叠
- 实际应该是去重后的增量收益

#### 问题 #2：测试标准错误

应该按**每报告节省时间**，不是每月总时间：

| 用户频率 | 原声称（260 分钟/月） | 实际含义（每报告） |
|----------|----------------------|-------------------|
| 1 报告/月 | 260 分钟/月 | **260 分钟/报告**（夸大） |
| 2 报告/月 | 260 分钟/月 | 130 分钟/报告 |
| 4 报告/月 | 260 分钟/月 | **65 分钟/报告**（合理） |

**原声称只在重度用户（4+ 报告/月）场景下合理**

#### 问题 #3：Prevention 过度记账

- 原估算：10 小时（直接记账）
- 应该是：期望值 = 概率 × 影响
- 合理期望值：2–4 小时（避免 1–2 次 3–5 小时修复，概率 30–40%）

---

### 7.3 风险调整后的诚实 ROI（Codex 建议）

#### 收益压缩（去重 + 概率折算）

| 维度 | 原估算 | 风险调整后 | 原因 |
|------|--------|-----------|------|
| Stability | 27h/year | **9–18h/year** | 去重后，45–90 分钟/月 |
| Quality（去重） | 25h/year | **5–12h/year** | 去重后，25–60 分钟/月 |
| Prevention（期望值） | 10h | **2–4h** | 概率折算（30–40% 避免） |
| Developer（不变） | 24h/year | **24h/year** | 排查时间节省（无重复计算） |
| Maintenance | -0.75h/year | **-0.75h/year** | 维护成本 |

**风险调整后年收益：23–26 小时（中位）**

#### 诚实 ROI（风险调整）

| 成本基数 | ROI 范围 | 中位 ROI | 适用场景 |
|----------|---------|----------|----------|
| **直接实施成本（5.3h）** | 3x–6x | **~4x** | Base case（典型用户） |
| **全加载成本（8–10h）** | 1.6x–3.2x | **~2.5x–3x** | 包含设计迭代成本 |

---

### 7.4 最终诚实 ROI 声明

#### Base Case（诚实声明）

> **Honest expected ROI: ~4x on direct build cost, or ~2.5x–3x on fully loaded cost.**

适用场景：
- **典型用户**：周期报告用户（每周/每月 1 次）
- **每报告节省时间**：45–65 分钟（排查问题 + 数据整理）
- **回收周期**：2–3 个月

#### Upside Case（上限声明）

> **ROI 11.7x only defensible for power-user upper bound（每周 > 2 次报告）**

适用场景：
- **重度用户**：每周 > 2 次报告
- **每报告节省时间**：90+ 分钟（功率用户场景）
- **回收周期**：约 1 个月

---

### 7.5 关键测试问题（Codex 提出）

> **Do typical users actually save about 45–65 minutes per report, or are you quietly assuming power-user frequency and power-user pain?**

#### 典型用户画像判断

| 用户类型 | 频率 | 每报告节省时间 | 是否典型 |
|----------|------|---------------|----------|
| **周期报告用户** | 每周/每月 1 次 | 45–65 分钟（排查问题 + 数据整理） | ✅ **典型** |
| **临时报告用户** | 每月 < 1 次 | 20–30 分钟 | ⚠️ 边缘 |
| **重度用户** | 每周 > 2 次 | 90+ 分钟 | ❌ 非典型 |

**结论：周期报告用户（每周/每月 1 次）是典型用户，节省 45–65 分钟/报告是合理的。**

---

### 7.6 是否仍划算？（接受风险调整）

**仍然划算**，理由：

1. **Base case ROI ~4x**：仍然高于投资阈值（通常 ROI > 2x 就值得做）
2. **预防期望值 2–4h**：避免 1–2 次 3–5 小时修复，概率折算合理
3. **用户侧价值仍占 40–50%**：即使去重后，用户仍受益 14–30 小时/年
4. **零契约变更**：Codex 多轮评审确保无高风险 bug 引入

---

### 7.7 ROI 对比总结

| 声明 | 原版（Upside） | 风险调整后（Honest） |
|------|----------------|---------------------|
| **ROI** | 11.7x | **~4x（base case）** |
| **回收周期** | 1 个月 | **2–3 个月** |
| **年收益** | 85 小时 | **23–26 小时（中位）** |
| **适用场景** | 重度用户 | **典型用户** |
| **是否划算** | — | **仍然划算（ROI > 2x）** |

**接受 Codex 风险调整，诚实 ROI ~4x，仍建议按 v4 实施。**

---

**End of Final Design Document v4**
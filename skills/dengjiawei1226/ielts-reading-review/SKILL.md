---
name: ielts-reading-review
description: "IELTS Reading passage review, scoring, and progress tracking skill. Generates structured review data (JSON) and professional HTML/PDF review notes locally — no server required. Supports batch import of legacy reviews with auto-discovery of review folders. Trigger phrases: 雅思复盘, 帮我复盘阅读, IELTS reading review, 分析错题, 阅读错题分析, 成绩单, 打分, 统计, 进步趋势, 批量导入历史复盘, 历史笔记转 JSON, 把文件夹里的复盘都生成 JSON, 扫一下我电脑里的复盘, 帮我找出所有历史笔记, 自动发现复盘, score, band, progress, batch import, auto scan."
---

# IELTS Reading Review Skill

## Purpose

帮用户把雅思阅读做题结果变成结构化复盘笔记（HTML + PDF）和结构化数据（JSON），追踪分数进步趋势。

## Architecture (v3.2 — Offline + Web Hand-off)

**Skill 纯离线执行**——所有错题分析、文件生成都在本地完成，不发起任何网络请求。

产出物：
1. **复盘 HTML** — 专业排版的复盘笔记，双击浏览器打开
2. **复盘 PDF** — 从 HTML 生成的 PDF 文件，便于存档和分享
3. **结构化 JSON** — 成绩、错题、词汇、同义替换的全量数据（v3.0 schema）

产出物与 Web 端（tuyaya.online）的对接方式详见下方 **Step 6: Apply to Web**。

## When to Activate

- 用户发做题截图/答案，提到"复盘""错题分析""阅读复盘"
- 用户问成绩、分数、进步趋势
- 用户要生成复盘笔记或 PDF

## Workflow

### Step 1: Collect Input

确保以下信息齐全（缺什么问什么）：

- **来源**：哪本书、哪套题、哪篇（如剑5 Test1 Passage2）
- **原文**或答题上下文
- **正确答案**
- **用户答案**及错题
- **🔴 用时（MUST ASK）**：做题用时（格式 `MM:SS`，如 `28:01`）。**必问项**，不能标"可选"——Web 端进步趋势图依赖此字段。用户若没计时，明确询问"这套大概做了多久"让其估算，别直接跳过
- **可选**：翻译、自我反思

### Step 1b: Screenshot Wrong Answer Protocol (CRITICAL)

**用户发答题截图时必须执行 3 步**：

1. **逐题读截图标记**：每题是红色（错）还是绿色（对），不能跳题，不能用自己的判断代替截图标记
2. **先报错题清单等确认**：输出"根据截图，错题为 QX/QY/QZ（共N道），请确认"，**确认后才能写分析**
3. **截图标记是唯一真相**：截图 vs 自己判断冲突时，信截图

**禁止**：跳过确认直接写分析、用 answer comparison 覆盖截图标记。

### Step 2: Generate Review HTML

基于 `assets/review-template.html` 模板，使用 `references/` 下的规范生成完整复盘 HTML 文件。

**🔴 文件命名强制规范（MUST FOLLOW）**：

文件名格式：`剑{book}-Test{test}-Passage{passage}-{titleCN}复盘.html`

- `{titleCN}` **必须与 JSON 里的 `source.titleCN` 字段完全一致**（同一个字符串，一字不差）
- **必须以"复盘"两字结尾**（不是"积累"、不是直接 `.html`）
- **禁止**：空格、下划线、英文连字符中混中文
- 示例：
  - ✅ `剑5-Test1-Passage2-鲸鱼感官复盘.html`
  - ✅ `剑6-Test4-Passage2-识字女性与育儿复盘.html`
  - ❌ `剑4-Test3-Passage2-火山专题积累.html`（缺"复盘"两字）
  - ❌ `剑6-Test4-Passage2-识字女性育儿复盘.html`（和 title 里"与"字不一致）

**命名一致性自检（生成前必做）**：
1. 决定 `titleCN` 后，HTML 文件名、JSON 文件名、JSON 内 `source.titleCN` 三者必须用**完全相同**的中文串
2. 生成完成后，自查输出"`{文件名}` 和 `source.titleCN='{titleCN}'` 一致 ✅"
3. 如果篇目已在 `site/answer-key.json` 里存在，直接复用其 `title` 字段作为 `titleCN`，**不要自创新表述**（避免和已有文件/数据库漂移）

遵循 `references/review-style-guide.md` 的设计规范（V2 紫色渐变主题、Lucide 图标、卡片布局）。

### Step 3: Generate Review Data JSON

在生成 HTML 的同时，输出一份结构化 JSON 文件，供后续导入 Web 系统：

**输出文件命名规则**：`剑X-TestX-PassageX-中文主题复盘.json`

> 命名必须与 Step 2 的 HTML 文件名**主干完全一致**（只差后缀），否则会触发 Web 端路径错乱。

示例：
- HTML: `剑5-Test1-Passage2-鲸鱼感官复盘.html`
- JSON: `剑5-Test1-Passage2-鲸鱼感官复盘.json`
- `source.titleCN`: `"鲸鱼感官"`

> **命名说明**：文件名使用中文标题（`source.titleCN`），方便用户在文件管理器中一眼识别内容。Web 端导入时通过 JSON 内的 `source.book/test/passage` 识别篇目，不依赖文件名。

**🔴 timing 字段必须填充**：
- `minutes`：数值型分钟（支持小数，如 `28.0` / `35.4`）
- `formatted`：`"MM:SS"` 字符串（如 `"28:01"`）
- MM:SS → minutes 换算：`分钟 + 秒/60`，保留 1 位小数
- 用户实在给不出用时，才能置 `null`，但必须在回复里提醒"缺用时，进步图将缺一个点"

```json
{
  "version": "3.0.0",
  "generatedAt": "2026-04-20T23:00:00.000Z",
  "source": {
    "book": 5,
    "test": 1,
    "passage": 2,
    "title": "English Title",
    "titleCN": "中文标题"
  },
  "score": {
    "correct": 9,
    "total": 13,
    "band": "5.0",
    "breakdown": {
      "fillBlank": { "correct": 4, "total": 6 },
      "tfng": { "correct": 3, "total": 4 },
      "matching": { "correct": 2, "total": 3 }
    }
  },
  "timing": {
    "minutes": 25,
    "formatted": "25:00"
  },
  "date": "2026-04-20",
  "wrongQuestions": [
    {
      "q": 3,
      "type": "tfng",
      "myAnswer": "TRUE",
      "correctAnswer": "NOT GIVEN",
      "errorCategory": "ng-false-confusion",
      "analysis": "错因分析文字",
      "lesson": "教训一句话"
    }
  ],
  "synonyms": [
    {
      "original": "原文表达",
      "replacement": "题目表达",
      "meaning": "中文释义",
      "questionRef": "Q3"
    }
  ],
  "vocabulary": [
    {
      "word": "exemplify",
      "phonetic": "/ɪɡˈzemplɪfaɪ/",
      "pos": "v.",
      "definition": "举例说明",
      "ieltsFreq": 3,
      "source": "538 #42",
      "appearance": "剑4T3P1"
    }
  ],
  "problems": [
    {
      "type": "同义替换识别失败",
      "detail": "具体表现",
      "questions": "Q3, Q7",
      "improvement": "改进方法"
    }
  ]
}
```

### Step 4: Generate PDF (Optional)

如果用户需要 PDF：

```bash
node scripts/generate-pdf.js 剑X-TestX-PassageX-主题复盘.html
```

需要 puppeteer-core + 本地 Chrome。PDF 输出到同目录。

### Step 5: Update Memory

复盘完成后更新 working memory：新增的错误模式、词汇、成绩数据。

### Step 6: Apply to Web (User-Initiated)

复盘生成完成后，**输出以下引导**：

---

📤 **复盘文件已生成！**

| 文件 | 用途 |
|------|------|
| `剑X-TestX-PassageX-主题复盘.html` | 双击打开即可阅读，可打印 |
| `剑X-TestX-PassageX-主题复盘.json` | 导入到 Web 端同步成绩 |

**一键同步到 Web 端** 👉 [点此上传 JSON](https://tuyaya.online/ielts/submit.html?mode=json)

上传页面会自动从 JSON 中识别出篇目信息（如「剑5 Test1 Passage2 · 鲸鱼感官」），确认后点击「导入」即可。

> 💡 JSON 文件在你当前的工作目录中，文件名如 `剑5-Test1-Passage2-鲸鱼感官复盘.json`

---

#### 其他同步方式

**方式 B：Skill 伴侣脚本**（私有部署场景）

如果有 `ielts-server-sync` skill（个人专用），可命令行批量上传：

```bash
# 单文件上传
node ~/.workbuddy/skills/ielts-server-sync/scripts/upload.js 剑5-T1-P2.json

# 批量上传目录
node ~/.workbuddy/skills/ielts-server-sync/scripts/upload.js --batch ./reviews/
```

**方式 C：纯离线**

直接双击 `.html` 文件即可阅读 / 打印，不依赖任何服务器。

**重要**：Skill 本身 **不执行任何网络请求**。所有上传操作由用户主动发起，数据隐私可控。

## Batch Import Mode (v3.2 — Legacy Review Folder → JSON)

**触发场景**：用户说"帮我把 XX 目录下的历史复盘都转成 JSON"、"批量导入我以前的复盘笔记"、"扫一下我电脑里的复盘"、"帮我找出所有历史笔记"等。

此模式下 Buddy 自主循环，**无需用户自己找路径、无需一篇篇喂**。

### Step B0: Auto-Discovery（🔍 推荐默认起点）

**不要开口就问用户"复盘文件夹在哪？"**——先自动扫常见位置：

```bash
node ~/.workbuddy/skills/ielts-reading-review/scripts/scan-legacy-reviews.js --auto
```

脚本会扫描以下位置并按命中数推荐：
- 当前工作目录 (cwd)
- `~/Documents`、`~/Documents/个人`、`~/Documents/个人/WorkBuddy`
- `~/Desktop`、`~/Downloads`
- `~/Library/Mobile Documents/com~apple~CloudDocs`（iCloud）
- `~/WorkBuddy`、`~/WorkBuddy/Claw`

输出 `discoveries`（去重后的真实命中目录，命中数多的子目录优先）和 `recommended`（首选目录）。

**把发现结果呈现给用户**：

```
我扫了你电脑常见位置，找到你的复盘应该在这里：

🎯 推荐：/Users/xxx/Documents/个人/WorkBuddy/雅思学习（60 个候选文件）
   样例：剑6-Test3-Passage3-抗衰老药物复盘.html / 剑4-Test1-听力Part2-河滨工业村复盘.html …

其他候选：
  - /Users/xxx/Downloads（4 个）

要用推荐目录还是选其他的？
```

用户点头后进入 Step B1 做精扫。**只有当自动发现完全找不到候选（discoveries 为空）时**，才问用户要具体路径。

### Step B1: Scan the Folder

调用扫描脚本生成候选清单：

```bash
# 默认只扫顶层
node ~/.workbuddy/skills/ielts-reading-review/scripts/scan-legacy-reviews.js <目录> --out=/tmp/ielts-scan.json

# 需要递归子目录
node ~/.workbuddy/skills/ielts-reading-review/scripts/scan-legacy-reviews.js <目录> --deep --out=/tmp/ielts-scan.json
```

输出 JSON 结构（groups 按篇目聚合）：

```json
{
  "totalFiles": 18,
  "identifiedPassages": 6,
  "groups": [
    {
      "passage": "C5-T1-P2",
      "fileCount": 3,
      "files": [
        { "path": "...", "ext": ".html", "hints": { "book": 5, "test": 1, "passage": 2, "title": "鲸鱼感官" } },
        { "path": "...", "ext": ".md" },
        { "path": "...", "ext": ".png" }
      ]
    },
    { "passage": "__unknown__", "files": [...] }
  ]
}
```

### Step B2: Show Plan & Confirm

读取 scan 结果后，**必须先给用户一份执行计划**，不要直接开干：

```
扫描完成，找到 18 个候选文件，识别出 6 篇复盘：

✅ 可识别：
  1. 剑5-T1-P2 · 鲸鱼感官（HTML + MD + 截图，共 3 个文件）
  2. 剑5-T1-P3 · 儿童认知（HTML）
  3. 剑6-T2-P1 · ...
  ...

⚠️ 无法识别篇目（需你人工分配）：
  - notes-2026-03-15.md
  - 错题整理.docx

我将逐篇处理可识别的 6 篇，每篇生成一个 JSON。预计 10-15 分钟。
确认开始？
```

用户点头后才进入 Step B3。

### Step B3: Loop — Generate JSON for Each Passage

**逐篇循环**，每次处理一组：

1. 读取该组所有文件内容（HTML 提纯文字、MD 直读、图片用视觉 OCR）
2. 从内容中提取：原文/正确答案/用户答案/错题/时长/日期
3. **关键兜底**：
   - 内容里找不到"正确答案" → 查 `site/answer-key.json`（本地答案库，401 题全覆盖）
   - 找不到用户答案 → 标注 `score.correct = null` 让用户后续补
   - 错题列表不清晰 → 只生成基础成绩单 JSON，`wrongQuestions: []`
4. 按 v3.0 schema 生成 JSON，文件名 `剑X-TestX-PassageX-中文主题复盘.json`
5. 写入用户指定的输出目录（默认 `./batch-output/`）
6. 输出一行进度：`✅ [3/6] 剑5-T1-P3 · 儿童认知 → 剑5-Test1-Passage3-儿童认知复盘.json`

### Step B4: Summary Report

全部完成后输出总结：

```
批量导入完成！

✅ 成功：5 篇（已生成 5 个 JSON 到 ./batch-output/）
⚠️ 部分数据缺失：1 篇（剑6-T2-P1 找不到用户答案，score.correct 置空）
❌ 跳过：0 篇

下一步：
👉 打开 https://tuyaya.online/ielts/submit.html?mode=json
👉 把 ./batch-output/ 里所有 JSON 拖进去，一键导入
```

### Batch Mode Rules (MUST FOLLOW)

1. **永远先 scan + confirm，绝不跳过计划确认**
2. **每篇独立处理，失败不阻塞下一篇**（捕获异常，记录到 skip 列表）
3. **绝不编造数据**：用户答案缺失就置 null 或空数组，不要瞎填
4. **同义替换/词汇/错因分析是可选项**：老笔记里没有就不生成，不要硬凑
5. **答案库优先**：正确答案一律从 `site/answer-key.json` 核对，笔记里的可能是老婆写错的
6. **产物隔离**：批量输出统一放 `./batch-output/`，不污染用户工作目录

## Error Analysis Rules

### TRUE / FALSE / NOT GIVEN 三步法

1. **找话题** — 文章有没有讨论题目中的对象？→ 没讨论 = **NOT GIVEN**
2. **找立场** — 讨论了的话，是同意还是矛盾？→ **TRUE** / **FALSE**
3. **验证** — "如果选 TRUE/FALSE，能指出原文哪句话吗？" 指不出来 → 大概率 **NOT GIVEN**

关键区分：
- FALSE 需要**直接矛盾证据**，"没提到"= NG 不是 FALSE
- 概括性表达覆盖题目对象 = 算讨论过，不是 NG
- `however + adj` = `no matter how`（让步），不是因果

### Fill-in-the-blank

- 答案不能重复题干已有的词
- 填完必须通读：语法/词性/语义/字数 四项检查
- `such as ___` → 必须填具体例子
- `the ___ of X` → 必须填能和 "of X" 搭配的名词

### Common Pitfalls

- **过度推理**：只看作者明确写了什么，不推导
- **被绝对词吓到**：all/never 不一定错，看原文证据
- **人名观点混淆**：先在文中标注每个人说了什么
- **邻近干扰词**：从定位句提取答案，不要被旁边的句子污染

## Error Categories

参见 `references/error-taxonomy.md`，共 12 类错误分类。JSON 中 `errorCategory` 字段使用以下 ID：

| ID | 错误类型 |
|----|---------|
| `synonym-failure` | 同义替换识别失败 |
| `ng-false-confusion` | NOT GIVEN / FALSE 混淆 |
| `over-inference` | 过度推理 |
| `stem-repetition` | 填空重复题干词 |
| `grammar-mismatch` | 语法/让步句理解错 |
| `incomplete-option` | 选项不完全匹配 |
| `vocab-gap` | 词汇缺口 |
| `carelessness` | 粗心/时间压力 |
| `word-form-error` | 填空词形/词性错 |
| `scope-confusion` | 跨代/范围混淆 |
| `category-reasoning` | 类别推理误判 |
| `adjacent-distractor` | 邻近干扰词 |

## Style Guidelines

- 简洁直接，不废话
- 错题分析直说问题，不糖衣炮弹
- 中文为主，英语术语保留原文

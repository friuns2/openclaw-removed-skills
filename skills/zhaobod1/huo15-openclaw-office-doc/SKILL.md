---
name: huo15-openclaw-office-doc
displayName: 火一五文档技能
description: 【青岛火一五信息科技有限公司】企业级 Word & PDF 文档生成 v7.5。39 类规范覆盖企业全场景：合同细分 7 类（劳动 / 服务 / 技术开发 / 销售 / 采购 / 保密NDA / 合作）+ HR / Sales / PR / PM / Ops / Tech / Legal / Reporting 各类文体。三条路径：Word 直出、原生 PDF 直出、Word→PDF。templates/ 下 22 份可拷贝改写的 markdown 范本。每种规范按真实场景决定是否带【内部】banner / 元数据表 / 版本史 / 审批 / TOC，CLI 可覆盖。触发词：写word、写文档、写PDF、写合同、写劳动合同、写服务合同、写技术开发合同、写销售合同、写采购合同、写NDA、写保密协议、写战略合作协议、写方案、写报告、写需求文档、写PRD、写BP、写用户手册、写培训手册、写招投标书、写演讲稿、写研究报告、写验收单、写立项书、写SOP、写公司制度、写公函、写简历、写CV、写报价单、写新闻稿、写复盘、写测试报告、写故障报告、写postmortem、写任命书、写应急预案、写在职证明、写风险评估、写项目计划书、写项目结项报告、写API文档、写部署文档、写runbook、写备忘录、写MOU、Word转PDF。
version: 7.6.1
aliases:
  - 火一五文档技能
  - 文档生成
  - Word生成
  - PDF生成
  - 多规范文档
dependencies:
  python-packages:
    - python-docx
    - reportlab
    - pygments  # 可选；装了即代码块语法高亮
---

# 火一五文档技能 v7.5

> 企业级 Word & 原生 PDF 文档生成 — 青岛火一五信息科技有限公司

**愿景：** 加速企业向全场景人工智能机器人转变
**理念：** 打破信息孤岛，用一套系统驱动企业增长

---

## 一、v7.5 关键变化（合同细分 7 类 + 配套范本）

> 用户反馈："合同帮我再细分"。

通用"合同"在 ToB 场景下太粗 — 一份合同应不应该带 试用期 / 知识产权 / 退换货 /
保密期限 / 收益分配 等条款，取决于具体合同子类。v7.5 把合同细分为 7 类：

| 子类 | 触发关键词 | 适用场景 | 范本 |
|------|-----------|---------|------|
| **劳动合同** | 劳动合同 / 雇佣合同 / 用工合同 / 实习合同 | HR 招聘入职 | [templates/劳动合同.md](templates/劳动合同.md) |
| **服务合同** | 服务合同 / 技术服务 / 咨询 / 维保 / SaaS / 运维 | 长期服务 | [templates/服务合同.md](templates/服务合同.md) |
| **技术开发合同** | 软件开发 / 委托开发 / 定制开发 / 开发合同 | 一次性开发 | [templates/技术开发合同.md](templates/技术开发合同.md) |
| **销售合同** | 销售合同 / 货物销售 / 软件许可 / 经销 | 售方角度 | [templates/销售合同.md](templates/销售合同.md) |
| **采购合同** | 采购合同 / 物资采购 / 设备采购 / 框架采购协议 | 购方角度 | [templates/采购合同.md](templates/采购合同.md) |
| **保密协议** | 保密协议 / NDA / 信息保密 / 双向保密 | 保密信息保护 | [templates/保密协议.md](templates/保密协议.md) |
| **合作协议** | 战略合作协议 / 联营协议 / 联合开发协议 | 有约束力合作 | [templates/合作协议.md](templates/合作协议.md) |

通用"合同"作为兜底保留 — 输入命中"合同"但没匹配到具体子类时使用。

视觉上 7 个合同子类共享通用合同的版式（宋体 / 标准页边距 / 无文档壳 / 第一条 ~
第N条结构）；差异在 **正文结构** 与 **范本内容**。FORMAT_KEYWORDS 顺序保证子类
关键词在通用"合同"之前命中。

---

> 历史变更详见文末 §十 版本历史。

---

## 二、39 类文档规范（v7.5）

> 列含义：banner = 顶部右上 【内部】 红字；meta = 文档编号/版本/密级/日期 2 列表；
> 版本史 = 末尾"版本历史"表；审批 = 末尾"审批记录"表；TOC = 自动目录。
> 命中顺序由上至下；`auto` 命中后立即返回；`--doc-format <规范>` 强制覆盖。

| 规范 | 触发关键词 | banner | meta | 版本史 | 审批 | TOC |
|------|-----------|:------:|:----:|:------:|:----:|:---:|
| **个人简历** ⭐v7.4 | 简历 / resume / CV | ❌ | ❌ | ❌ | ❌ | ❌ |
| **报价单** ⭐v7.4 | 报价单 / 商务报价 / 报价书 / 询价回复 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **新闻稿** ⭐v7.4 | 新闻稿 / 媒体通稿 / 发布稿 / press release | ❌ | ❌ | ❌ | ❌ | ❌ |
| **复盘报告** ⭐v7.4 | 复盘 / 项目复盘 / 项目总结 / 月度复盘 | ❌ | ✅ | ✅ | ❌ | ✅ |
| **测试报告** ⭐v7.4 | 测试报告 / QA报告 / 验证报告 / 性能测试 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **故障报告** ⭐v7.4 | 故障报告 / 事故报告 / 故障复盘 / postmortem | ✅ | ✅ | ❌ | ❌ | ❌ |
| **任命书** ⭐v7.4 | 任命书 / 聘任书 / 委任书 / 任命决定 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **应急预案** ⭐v7.4 | 应急预案 / 应急响应预案 / 应急处置方案 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **在职证明** ⭐v7.4 | 在职证明 / 离职证明 / 工作证明 / 收入证明 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **风险评估报告** ⭐v7.4 | 风险评估 / 风险报告 / 安全评估 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **项目计划书** ⭐v7.4 | 项目计划书 / 项目执行计划 / 项目章程 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **项目结项报告** ⭐v7.4 | 结项报告 / 项目收尾报告 / 项目交付总结 | ❌ | ✅ | ✅ | ✅ | ✅ |
| **API文档** ⭐v7.4 | API文档 / 接口文档 / 接口规范 / openapi | ❌ | ✅ | ✅ | ❌ | ✅ |
| **部署文档** ⭐v7.4 | 部署文档 / 部署手册 / 上线手册 / runbook | ❌ | ✅ | ✅ | ❌ | ✅ |
| **备忘录** ⭐v7.4 | 备忘录 / MOU / 合作意向书 / 战略合作备忘录 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 验收单 ⭐v7.3 | 验收单 / 验收报告 / 交付确认书 / 项目验收 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 项目立项书 ⭐v7.3 | 立项申请 / 立项书 / 项目建议书 / 可行性研究报告 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 操作SOP ⭐v7.3 | SOP / 标准作业指导书 / 工艺文件 / 操作规程 | ❌ | ✅ | ✅ | ❌ | ✅ |
| 公司制度 ⭐v7.3 | 规章制度 / 管理办法 / 实施细则 / 管理细则 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 信函 ⭐v7.3 | 公函 / 商务函件 / 求职信 / 推荐信 / 邀请函 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 招投标书 | 招标书 / 投标书 / 投标文件 / 响应文件 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 商业计划书 | 商业计划书 / BP / 融资计划书 / 路演稿 | ❌ | ❌ | ✅ | ❌ | ✅ |
| 用户手册 | 用户手册 / 操作手册 / 使用说明 / Manual | ❌ | ❌ | ✅ | ❌ | ✅ |
| 培训手册 | 培训手册 / 培训教材 / 教学大纲 / 员工手册 | ❌ | ❌ | ✅ | ❌ | ✅ |
| 演讲稿 | 演讲稿 / 致辞稿 / 讲话稿 / 主题分享 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 研究报告 | 研究报告 / 学术论文 / 调研报告 / 白皮书 | ❌ | ✅ | ✅ | ❌ | ✅ |
| **劳动合同** ⭐v7.5 | 劳动合同 / 雇佣合同 / 用工合同 / 实习合同 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **服务合同** ⭐v7.5 | 服务合同 / 技术服务 / 咨询 / 维保 / SaaS 合同 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **技术开发合同** ⭐v7.5 | 软件开发合同 / 委托开发合同 / 定制开发 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **销售合同** ⭐v7.5 | 销售合同 / 货物销售 / 软件许可合同 / 经销 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **采购合同** ⭐v7.5 | 采购合同 / 物资采购 / 设备采购 / 框架采购 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **保密协议** ⭐v7.5 | 保密协议 / NDA / 信息保密 / 双向保密 | ❌ | ❌ | ❌ | ❌ | ❌ |
| **合作协议** ⭐v7.5 | 战略合作协议 / 联营协议 / 联合开发协议 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 合同（通用兜底）| 合同 / 协议 / 协议书 / 补充协议 | ❌ | ❌ | ❌ | ❌ | ❌ |
| 会议纪要 | 会议纪要 / 纪要 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 技术方案 | 技术方案 / 实施方案 / 解决方案 / 设计文档 / 架构设计 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 需求文档 | 需求规格 / SRS / PRD / 需求说明 / 需求文档 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 工作报告 | 工作报告 / 周报 / 月报 / 季报 / 年报 / 述职报告 | ❌ | ✅ | ❌ | ❌ | ❌ |
| 公文（默认）| 未命中其他关键词 | ✅ | ✅ | ✅ | ✅ | ❌ |

> 一行命令看全 17 种：`python3 scripts/create-word-doc.py --list-formats`。
> CLI 精细控制：`--with-version-history / --no-version-history /
> --with-approval / --no-approval /
> --with-classification-banner / --no-classification-banner /
> --with-doc-meta-table / --no-doc-meta-table /
> --with-title-block / --no-title-block`。

### 标题层级识别（每种规范独立）

每种规范都有自己的章节编号正则；同时支持标准 Markdown `# / ## / ### / ####`。例如：

| 规范 | 一级（chapter） | 二级（section） | 三级（article） |
|------|---------------|---------------|----------------|
| 公文 | 第X章/第X节 | 一、二、三、 | （一）（二） |
| 合同 | 第X章/第X条 | 一、二、 | — |
| 商业计划书 | 第X部分/一、二、 | 1.1 | 1.1.1 |
| 用户手册 | 第X章 | X. | X.X |
| 培训手册 | 模块X/单元X/第X课 | 一、二、 | X.X |
| 招投标书 | 第X章/篇/部分 | 一、二、 | （一）（二） |
| 研究报告 | 摘要/Abstract/引言/结论/参考文献/一、 | X. | X.X |

---

## 三、页眉 / 页脚规范

### 3.1 页眉

- **company**（默认）：LOGO + 公司名 + 文档编号 + 密级，**左对齐**
- **minimal**（合同 / 用户手册 / 演讲稿）：LOGO + 公司名，**左对齐**，不显示编号 / 密级
- **centered**（保留备选，当前无规范默认走此项）：仅公司名，居中
- 底部统一灰线 `#888888`

> v7.0 直接写 OOXML `<w:jc>` 并清 `<w:tabs>`，避免 WPS / 部分 Word 模板的样式继承覆盖。

### 3.2 页脚

- 所有规范统一为 `第 X 页 / 共 Y 页`，居中
- Word：`PAGE` / `NUMPAGES` 字段码（打开时自动计算）
- PDF：两遍渲染（NumberedCanvas）拿到真总页数

---

## 四、本地公司信息工作流

页眉的公司名、LOGO 按以下优先级解析：

1. **CLI 显式参数** `--company-name` / `--logo-path`
2. **本地缓存** `~/.huo15/company-info.json`
3. **Odoo `res.company`** 自动拉取（可用 `--no-odoo` 关闭）
4. **退出码 2 + 结构化 JSON** — 以上都拿不到时让 Claude 触发补录流程

### 4.1 标准流程（生成前）

```bash
python3 scripts/company-info.py check
#   exit 0 + 完整 JSON  → 直接生成
#   exit 2 + missing[]  → 进入补录
```

**补录流程**（Claude 执行）：

1. 先查 auto-memory 中的 `huo15_company_info.md` / `user_identity.md`
2. 仍缺失时用 `AskUserQuestion` 询问：公司全称、LOGO 路径、可选 slogan / 地址 / 电话 / 邮箱 / 官网
3. 写入：
   ```bash
   python3 scripts/company-info.py set \
     --company-name "<公司全称>" --logo-path "<LOGO绝对路径>"
   ```
4. 同步写入 memory（`huo15_company_info.md`）

---

## 五、命令行

```bash
# Word 直出
python3 scripts/create-word-doc.py --output 方案.docx \
  --title "技术方案：XXX系统" --content @/tmp/content.md \
  --doc-number "HG-FA-2026-001" --version "V1.0" --classification "内部" \
  --author "辉火云管家·贾维斯"

# 一览 39 种 preset：
python3 scripts/create-word-doc.py --list-formats

# 原生 PDF 直出（不依赖 LibreOffice / Office）：
python3 scripts/create-pdf-doc.py --output 方案.pdf \
  --title "技术方案：XXX系统" --content @/tmp/content.md \
  --doc-format 技术方案

# Word → PDF（保留版式）：
python3 scripts/word-to-pdf.py 方案.docx -o 方案.pdf
```

**关键 CLI 参数：**

- `--doc-format <规范>` — 39 类规范任选；省略走 `auto` 自动识别
- `--company-name / --logo-path` — 覆盖本地公司信息
- `--with-version-history / --no-version-history` — 版本历史表
- `--with-approval / --no-approval` — 审批记录表
- `--with-classification-banner / --no-classification-banner` — 顶部 【内部】红字
- `--with-doc-meta-table / --no-doc-meta-table` — 顶部元数据 2 列表
- `--with-title-block / --no-title-block` — 标题大字块

**何时用哪条路径**：只要 Word → 用 `create-word-doc.py`；只要 PDF →
`create-pdf-doc.py`（最快）；要 Word + PDF 版式一致 → 先 word，再
`word-to-pdf.py`。后端优先级 `libreoffice → docx2pdf → word_com` 自动回落。

字体：macOS 自带 Songti.ttc / STHeiti.ttc；Linux 推荐 Noto CJK；
Windows 可用 SimSun / SimHei。

---

## 六、Markdown 能力速查

| 元素 | 写法 | 说明 |
|------|------|------|
| 标题 | `#`~`######` | 也支持规范专属编号（一、 / 1. / 1.1 / 第X章） |
| 段落软换行 | 直接换行 | CJK ↔ CJK 不插入空格；ASCII 仍保留空格 |
| 段落硬换行 | 行尾 `  ` 或 `\` | 同段内强制换行 |
| 列表 | `- item` / `* item` / `1. item` | |
| 强调 | `**粗**` / `*斜*` / `` `inline code` `` | |
| 表格 | 标准 GFM | 缺前导 `|` / 转义 `\|` / 2 列起即可识别 |
| 代码块 | `` ``` ``...`` ``` `` | 等宽灰底；带语言标签 |
| 引用块 | `> ...` | 左侧橘色竖条 + 灰色段 |
| 分隔线 | `---` / `***` / `___` | |
| 元数据行 | `文档编号：XX | 版本：V1.0 | 密级：内部 | 日期：2026-04-27` | 自动两列表格 |
| 分页符 | `---PAGE---` / `\pagebreak` / `<!-- pagebreak -->` | 强制下一页 |
| 空内容 | — | 写"（无正文内容）"灰字占位 |

---

## 七、Python API

```python
# Word
from create_word_doc import create_word_doc
create_word_doc(
    output_path="文档.docx",
    title="技术方案：XXX系统",
    content=md_text,
    doc_number="HG-FA-2026-001",
    version="V1.0",
    classification="内部",
    author="辉火云管家·贾维斯",
    doc_format="auto",            # 12 类规范名 / 'auto'
)

# PDF
from create_pdf_doc import create_pdf_doc
create_pdf_doc(output_path="文档.pdf", title="...", content=md_text,
               doc_format="商业计划书")

# Word → PDF
from word_to_pdf import convert_to_pdf
ok, path = convert_to_pdf("方案.docx", "方案.pdf",
                          backend="auto", keep_fonts=True)
```

> 缺公司信息时三个入口都抛 `RuntimeError`，message 是结构化 JSON，Claude 据此触发补录。

---

## 八、触发词

通用：写 word / 写 PDF / 写文档 / 生成 word / 生成 PDF / 创建文档 / 导出文档 / Word 转 PDF。

39 类规范触发词由 §二 表格中"触发关键词"列定义。常用：写合同 / 写协议 /
写劳动合同 / 写服务合同 / 写技术开发合同 / 写销售合同 / 写采购合同 / 写 NDA /
写保密协议 / 写战略合作协议 / 写方案 / 写报告 / 写会议纪要 / 写需求文档 /
写 PRD / 写商业计划书 / 写 BP / 写用户手册 / 写培训手册 / 写招标书 / 写投标书 /
写演讲稿 / 写研究报告 / 写白皮书 / 写验收单 / 写立项书 / 写 SOP / 写公司制度 /
写公函 / 写邀请函 / 写简历 / 写 CV / 写报价单 / 写新闻稿 / 写复盘 / 写测试报告 /
写故障报告 / 写 postmortem / 写任命书 / 写应急预案 / 写在职证明 / 写风险评估 /
写项目计划书 / 写项目结项报告 / 写 API 文档 / 写部署文档 / 写 runbook / 写备忘录 /
写 MOU。

---

## 九、目录结构

```
scripts/
├── doc_core.py          # 共享核心：32 类预设 + Block AST 解析 + 内联 token
│                        # v7.4：再扩 15 类预设 + 关键词优先级调整
│                        # v7.3：FormatPreset 增 4 个文档壳开关
├── company-info.py      # 本地公司信息读写 + Odoo 回落
├── create-word-doc.py   # Word 渲染（python-docx + 强制 OOXML jc）
│                        # v7.3：_strip_markdown_emphasis + _maybe_dedupe_h1_title
├── create-pdf-doc.py    # 原生 PDF 渲染（reportlab + NumberedCanvas）
│                        # v7.3：与 Word 端文档壳逻辑保持一致
└── word-to-pdf.py       # Word → PDF 多后端转换

templates/               # v7.4：15 份可直接拷贝改写的 markdown 范本
├── 个人简历.md
├── 报价单.md
├── 新闻稿.md
├── 复盘报告.md
├── 测试报告.md
├── 故障报告.md
├── 任命书.md
├── 应急预案.md
├── 在职证明.md
├── 风险评估报告.md
├── 项目计划书.md
├── 项目结项报告.md
├── API文档.md
├── 部署文档.md
├── 备忘录.md
└── README.md
```

---

## 十一、未来路线（已调研、未实施）

| 功能 | 业界参考 | 优先级 | 复杂度 | 拟引入依赖 |
|------|---------|--------|-------|----------|
| LaTeX → OMML 公式管线 | markdocx / Pandoc | 中 | 中 | latex2mathml + XSLT |
| reference docx 模板继承 | Pandoc / Quarto | 中 | 中 | 仅模板文件 |
| Typst 第四条 PDF 路径（30× 速度） | typst.app + zh-kit | 中 | 中 | typst 二进制 |
| pandoc-crossref 风格交叉引用 `{#fig:xxx}` | pandoc-crossref | 中 | 中 | — |
| 水印 + AES 加密 | msoffcrypto-tool | 低 | 小 | msoffcrypto-tool |
| 修订追踪 / 批注 | docx-revisions | 低 | 大 | docx-revisions |
| docxtpl Jinja2 模板槽 | docxtpl | 低 | 小 | docxtpl |

> 任何一项触发刚需时再上；当前以稳定 + 中文友好 + 易维护为先。

---

## 十、版本历史

- **v7.6.1（当前）**：再修一类 KV 漏检测 — `站点名称 / WordPress 版本 / WooCommerce 版本 / 主题 / 完成日期 / 负责人` 这 6 行原本被 `_smart_join_paragraph` 合成单行（首行 `站点名称` 不在白名单 → 严格 KV 拒绝 → 落入 paragraph 路径）。修法：(a) `_is_known_metadata_key` 用词边界搜索取代严格起首匹配，`WordPress 版本` / `服务合同编号` 这类带前缀的 key 都能识别；(b) 新增 lenient 兜底 — 任意 ≥3 行连续 `Key:Value` 形式（form-only，不需 key 在白名单）自动归并为元数据块；(c) 白名单扩入 web/通用词：站点 / 站点名称 / 网站 / 网站名称 / 域名 / URL / 链接 / 名称 / 类目 / 品牌
- **v7.6.0**：解决用户截图复现的两类 bug —
  (1) **元数据表 TABLE 形式也能识别去重** — v7.5.2 只抓 KV `**Key：**` 形式；
      LLM 用 `| 文档编号 | xxx |` 的 markdown 表格写元数据时漏检测，导致和
      CLI 自动表叠加。v7.6 同时检测 `metadata` block 与 `table` block（首列 ≥2
      个 cell 命中文档编号 / 版本 / 密级 / 日期 / 作者等关键词）。
  (2) **TOC 占位符回填真目录** — 旧版"目录将在打开自动生成"灰字让用户误以为正文。
      v7.6 渲染期间收集所有 H1-H3，post-render 把缩进格式的标题列表写到 TOC
      字段缓存里。Word/WPS 打开前用户能看到完整目录（无页码）；打开后
      `updateFields=true` 触发刷新，替换为带页码的真目录。
  (3) **TOC 智能默认 + CLI 覆盖** — 旧版 preset 一旦 `table_of_contents=True`
      永远生成目录；很多 ≤ 3 章的短文档目录其实是噪音。v7.6 默认仅在 H1+H2 数
      ≥ 4 时生成 TOC；新增 `--with-toc / --no-toc` 显式覆盖。
  (4) **PDF outline level 跳跃 bug 修复** — reportlab 不允许 outline 从 -1 直接
      跳到 level 1+；之前章程类文档（H1 被 dedupe 后首个标题是 H2）会抛
      ValueError 导致 PDF 生成失败。v7.6 在 BaseDocTemplate 的 afterFlowable
      自动补齐缺失的中间 level（用空 anchor 占位）。
- **v7.5.2**：修三类视觉 bug — KV-style 元数据去重 / 短 TOC 占位 / 孤立 `**` 防御；公司制度 keyword 扩入"章程 / 议事规则 / 会议章程 / 员工守则 / 行为准则"
- **v7.5.0**：合同细分 7 类（劳动 / 服务 / 技术开发 / 销售 / 采购 / 保密 NDA / 合作），每类配 markdown 范本；通用"合同"保留作兜底
- **v7.4.0**：再扩 15 类（个人简历 / 任命书 / 在职证明 / 报价单 / 新闻稿 / 复盘报告 / 项目计划书 / 项目结项报告 / 测试报告 / 故障报告 / 应急预案 / 风险评估报告 / API 文档 / 部署文档 / 备忘录），全部配 markdown 范本，共 32 类
- **v7.3.0**：新增 5 类（验收单 / 项目立项书 / 操作 SOP / 公司制度 / 信函），共 17 类；`FormatPreset` 加 4 个文档壳开关（`show_classification_banner` / `show_doc_meta_table` / `show_title_block` / `dedupe_h1_title`），每种规范按真实场景设默认；修复 `**X**` 字面残留与 H1 与 --title 重复；新增 `--list-formats` 与文档壳 CLI 覆盖参数
- **v7.2.0**：合同页眉改为左对齐；`**Key：**` markdown 粗体元数据正确识别（合同编号 / 签订日期 / 验收日期 / 甲乙方 / 金额等 30+ 关键词扩入白名单）；连续多行 KV 自动归并为 2 列元数据表
- **v7.1.0**：CJK 段落属性 OOXML 直写、首行缩进字符化、Pygments 代码高亮、自动 TOC + 书签、PDF outline、文档核心属性、多行 Key:Value 元数据自动识别
- **v7.0.0**：解析器拆出 `doc_core.py` 共用；新增 `create-pdf-doc.py` 原生 PDF 直出；新增 6 类规范（商业计划书 / 用户手册 / 培训手册 / 招投标书 / 演讲稿 / 研究报告）；修复 CJK 软换行多余空格；硬换行支持；页眉强制左对齐；`word-to-pdf.py` 重写
- **v6.0.0**：Block AST 重写；页眉恒含 LOGO；页脚字段码；代码块 / 引用块
- **v5.3.0**：`company-info.py` 本地公司信息工具
- **v5.0.0**：多规范自动识别骨架

---

**技术支持：** 青岛火一五信息科技有限公司

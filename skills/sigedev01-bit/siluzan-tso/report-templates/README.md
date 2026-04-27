# 报告模板目录

本目录包含两类文件：

| 文件类型                | 用途                                            |
| ----------------------- | ----------------------------------------------- |
| `*.md`                  | 报告内容纲要：默认维度、可选维度、对应 CLI 命令 |
| `report-template*.html` | 视觉样式参考：排版/色彩/图表方案，不定义内容    |

> 冲突时以 `*.md` 的内容要求为准，样式文件仅影响排版。

---

## 内容纲要文件

| 文件                                 | 适用场景                                          |
| ------------------------------------ | ------------------------------------------------- |
| `google-period-report.md`            | Google 账户分析报告（周期/月度/诊断均用此模板）   |
| `google-account-diagnosis-report.md` | Google 账户深度诊断（健康度/转化/结构等）         |
| `google-ads-diagnosis.md`            | 与网页版《Google Ads 账户诊断报告》对齐的完整骨架 |
| `meta-period-report.md`              | Meta（Facebook）账户周期报告                      |
| `tiktok-period-report.md`            | TikTok 广告主周期报告                             |
| `bing-period-report.md`              | Bing（BingV2）分析报告                            |

---

## 样式参考文件

| 文件                            | 风格                  |
| ------------------------------- | --------------------- |
| `report-template.html`          | 商务/数据看板（默认） |
| `report-template-formal.html`   | 正式文件/对外         |
| `report-template-dark.html`     | 深色/投屏             |
| `report-template-onepager.html` | 单页摘要              |
| `report-template-mobile.html`   | 移动端                |
| `report-template-print.html`    | 打印归档              |
| `report-template-academic.html` | 学术/研究口吻         |

---

## 生成报告的规则

### 分析报告的维度确认

生成**分析报告**时：

1. 根据对应 `*.md` 的**默认维度**直接开始拉数（见各 `*.md` 首节）。
2. 同时向用户展示该文件里的**可选维度列表**，询问是否需要追加任何维度。
3. 用户追加的维度，补充拉数后追加到报告末尾。
4. 用户说「不用加」或不回复，只输出默认维度的内容。

### 禁止事项

- 不能使用 HTML 样式文件里的假数据填报告
- 不能凭印象写具体数字，所有数字来自 CLI 执行结果
- 某个维度的数据获取失败，在对应章节注明原因，不写推测内容

### 数据不可用时

在对应章节写：`[ 数据不可用：{原因} ]`，不做猜测。

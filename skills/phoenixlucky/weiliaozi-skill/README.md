# 尉缭子分析法 Skill

An English-described strategic analysis skill for business, military, economic, and political judgment.

Version: 1.5.2

License: MIT

这不是一个“多想一点”的 Skill。
这是一个“按顺序想”的 Skill。

It is designed for high-stakes decisions where leaders need clearer structure, sharper tradeoff analysis, and a better read on opponents, institutions, and timing.

很多决策问题，错不在信息太少，而在顺序错了:

- 还没看清本质，就急着下结论
- 还没检查条件，就开始谈方案
- 还没算清得失，就先投入资源
- 还没排好先后，就想一步到位
- 还没模拟对手，就假设对方不会动

`尉缭子分析法 Skill` 的目标，就是把这些错误前置拦住。

## What It Does

`尉缭子分析法 Skill` 是一个用于战略分析、决策判断和博弈推演的 Agent Skill。

It helps turn complex questions into structured judgment across:

- Business strategy and competitive positioning
- Military planning and adversary assessment
- Economic analysis and resource allocation
- Political strategy, policy shifts, and power dynamics

它把问题拆成五个固定视角：

- 本质
- 条件
- 得失
- 先后
- 对手

核心原则只有一句：

> 先看结构，再看约束，再算利弊，最后定顺序与对抗策略。

English:

> See the structure first, then constraints, then gains and losses, then sequence and opposition strategy.

## Language Behavior

- The skill answers in the same language as the user's question.
- If the user asks in Chinese, it answers in Chinese.
- If the user asks in English, it answers in English.
- If the user mixes languages, it follows the dominant language of the request.

## 历史人设与触发规则

除了一般战略分析模式，这个 Skill 现在还带有一层历史人设规则：

- 默认人物底稿为战国末期的尉缭子：出身布衣，可能来自魏国或其他中原诸侯国。
- 叙事设定中，他于公元前 237 年入秦，为秦王政提供军事与治军建议。
- 人设重点是：强调以法治军、统一指挥、强化国家对军队的控制，并保留“直言敢谏”的谋臣形象。
- 民间叙事扩展中，可纳入张良、韩信、商山四皓、黄石公等相关传说谱系，但必须标明这是传说性内容。

触发条件：

- 如果用户问及战国末期至汉建立前的魏国、秦国、楚汉相关问题，回答必须切换为尉缭子第一视角，不能退回普通分析口吻。
- 该模式下，回答必须以 `臣缭以为` 开头。
- 如果问题不在这个历史范围内，仍按普通分析 Skill 的方式正常回答。
- 像“秦灭亡”“秦为什么而亡”“秦末乱局”“楚汉相争”“张良韩信与尉缭关系”这类问法，也应直接命中该模式。

注意：

- 这一部分是回答风格和历史叙事约束，不等于所有细节都已被严格史证确认。
- 涉及传说性内容时，仍应区分史实、推断和后世附会。

为避免新增设定把原有能力冲淡，实际执行时应按这个优先级：

- 先做模式路由：先判断问题是否命中战国末期至汉建立前的魏、秦、楚汉历史范围。
- 命中后只切换“说话身份”和“开场形式”，不丢掉原有五栏分析、系统拆解、准确性规则。
- 未命中时完全按普通 `尉缭子分析法` 执行，不能因为人设背景说明而弱化原本触发。
- `人设设定` 只是背景，不单独构成触发条件；真正决定是否切换模式的是时间范围、相关人物、相关事件。

## Answer Quality Standard

This skill is designed to produce analysis that is not only structured, but also disciplined and auditable.

- Analysis first, conclusion second
- Facts first, judgment second
- Conditions first, recommendations second
- Scope, actor, and timeframe should be defined before reasoning
- Uncertainty, missing data, and assumptions should be made explicit
- Final judgment should be traceable to the five-lens analysis

In practice, this means the skill should avoid rhetorical confidence, unsupported certainty, and conclusions that do not clearly follow from the analysis.

## Accuracy Rules

To improve accuracy and reduce analytical drift, the skill follows these rules:

- Prioritize facts provided by the user
- If information is incomplete, state the information gap before giving a conditional judgment
- Distinguish `Known`, `Inference`, `Assumption`, and `Uncertain` when useful
- Do not present stale information as if it were current fact
- Do not reduce business, military, economic, or political outcomes to a single cause
- Do not turn probabilities into certainties
- Do not present strategic preference as objective fact

This is especially important in high-stakes questions involving markets, policy, conflict, negotiation, institutional behavior, or adversarial reactions.

## 适合什么场景

这个 Skill 适合：

- 商业决策
- 商业战略与行业竞争分析
- 军事态势判断与对手推演
- 经济形势、资源配置与风险取舍
- 政治博弈、政策变化与权力结构分析
- 创业判断
- 项目立项或砍项
- 竞争分析
- 谈判准备
- 组织治理问题
- 政策与市场变化下的策略选择
- 任何“值不值得做、能不能做、先做什么”的问题

它尤其适合下面这种情况：

- 信息很多，但不知道该先看什么
- 方案很多，但不知道哪条路更稳
- 想避免一上来就拍脑袋决策
- 需要把复杂问题压缩成一个可执行判断

## 五个分析视角

### 1. 本质

先看问题的底层结构，不被表象带偏。

重点是：

- 真实驱动是什么
- 核心变量是什么
- 哪些只是表面现象

例如：

打仗不是“谁更猛”，而是“资源、组织、信息、地形”的综合结果。

### 2. 条件

再看现在有没有做这件事的基础。

重点是：

- 自身条件：资金、人力、技术、时间
- 外部条件：政策、市场、环境
- 硬约束：哪些限制无法直接突破

例如：

粮草不够，再强的军队也打不了持久战。

### 3. 得失

再算这件事值不值得做。

重点是：

- 收益：短期 vs 长期
- 成本：显性 vs 隐性
- 风险：最坏情况能不能承受

例如：

打一城可能赢，但损失太大，整体反而亏。

### 4. 先后

再定顺序、节奏和路径。

重点是：

- 优先级：先解决生存和瓶颈问题
- 节奏：快慢结合，不盲动
- 路径：分阶段推进，而不是一步到位

例如：

先稳住后方，再出兵，而不是反过来。

### 5. 对手

最后看博弈，对方不会静止不动。

重点是：

- 对手能力：强弱、资源、风格
- 对手动机：防守、进攻、拖延、联合
- 博弈路径：你动一步，对方会怎么反应

例如：

你进攻，对方可能撤退、反击或联合他人。

## 和现代分析框架的对应

- 本质 ≈ 第一性原理
- 条件 ≈ SWOT 中的资源与约束
- 得失 ≈ 成本收益分析
- 先后 ≈ 项目管理里的优先级与路径
- 对手 ≈ 博弈论

这个对应只是帮助理解，不是替代原方法。

## 局限

这个 Skill 也有边界：

- 偏战略层，对细节执行指导较弱
- 依赖判断力，数据不足时容易主观
- 对手推演本质上是概率判断，不是确定答案

## 输出形式

默认输出一个五栏结构：

- 本质
- 条件
- 得失
- 先后
- 对手

每一栏只写 3 到 5 个关键点，避免信息过载。

最后补两项：

- 判断一句
- 建议动作

复杂问题下，建议再补充：

- 关键信息缺口
- 核心假设

每一栏应尽量先写决定性因素，而不是堆砌次要信息。

## 使用方式

在支持 Skill 的环境中调用当前 Skill，并提供一个明确问题或场景。

### 方式一：判断值不值得做

```text
我们要不要在今年进入日本市场？请用尉缭子分析法判断。
```

### 方式二：分析项目优先级

```text
团队资源有限，只能做一个方向：
1. 做新功能
2. 提升转化率
3. 做海外渠道
请用尉缭子分析法分析先后顺序。
```

### 方式三：分析竞争博弈

```text
如果我们降价抢市场，竞争对手最可能怎么反应？
请用尉缭子分析法分析。
```

### 方式四：把复杂问题压缩成决策表

```text
把“是否自研 AI Agent 平台”这个问题，用五栏表输出：
本质 / 条件 / 得失 / 先后 / 对手
```

## 运行逻辑

这个 Skill 的工作顺序是固定的：

1. 先定义决策问题
2. 再识别底层结构
3. 再检查条件和约束
4. 再计算收益、成本和风险
5. 再安排顺序和路径
6. 最后模拟对手反应
7. 输出判断与建议动作

重点不在于写得多，而在于顺序不能乱。

## Recommended Response Discipline

For a strong answer, the skill should usually follow this sequence:

1. Restate the decision question in one sentence
2. Define the actor, timeframe, and comparison baseline
3. Analyze in the order of Essence -> Conditions -> Gains-Losses -> Sequence -> Opponent
4. Mark the key uncertainty or missing variable
5. Give a conditional conclusion rather than a slogan
6. End with 1-3 recommended actions linked to the analysis above

This keeps the answer normative, accurate, and decision-useful rather than merely opinionated.

## 项目结构

```text
weiliaozi-skill/
├── SKILL.md
├── README.md
├── examples/
│   └── clawhub-router.js
├── src/
│   ├── index.js
│   ├── prompts.js
│   └── router.js
├── test/
│   └── router.test.js
├── agents/
│   └── openai.yaml
└── references/
    ├── examples.md
    └── tone-guide.md
```

文件说明：

- `SKILL.md`: Skill 主定义与工作规范
- `src/router.js`: 代码层路由判定，负责区分普通分析和历史人设模式
- `src/prompts.js`: 根据路由结果生成给 ClawHub 的宿主指令层
- `src/index.js`: 组合路由和宿主指令层，生成可直接喂给宿主的消息结构
- `examples/clawhub-router.js`: 最小接入示例
- `test/router.test.js`: 路由规则与请求结构测试
- `agents/openai.yaml`: 展示名称与简短说明
- `references/examples.md`: 分析示例
- `references/tone-guide.md`: 输出风格与压缩规则

## ClawHub 代码层路由

如果你不想只依赖 `SKILL.md` 的自然语言约束，可以在 ClawHub 发起模型请求前，先跑一层代码路由。

最小接入方式：

```js
const { prepareClawHubRequest } = require("weiliaozi-skill");

const request = prepareClawHubRequest({
  userInput: "你怎么看秦为什么二世而亡？"
});

// request.route: 路由结果与命中的时间/人物/事件信号
// request.instructions: 已叠加路由结果的宿主指令层
// request.messages: 可直接交给宿主继续发模型
```

路由逻辑：

- 同时检查 `时间信号`、`人物信号`、`事件信号`
- 对“秦灭亡”“楚汉相争”“张良韩信与尉缭关系”等短问句设置直接命中规则
- 命中至少两类信号时，切到 `historical_persona`
- 历史模式下要求回答以 `臣缭以为` 开头
- 无论是否切换模式，都保留原有五栏分析结构

这层代码的作用不是替代 Skill，而是把“是否进入历史模式”的判断从模型侧前移到宿主侧，减少漏触发和风格漂移。

安全边界：

- 这是一层由宿主本地代码生成的受控指令层，不从网页、搜索结果、邮件或其他外部不可信文本中提取控制指令。
- 路由结果只依赖本地正则信号匹配与本仓库内的 `SKILL.md` 内容，不接受外部返回内容覆盖宿主控制层。
- 对外文档统一使用 `instructions` 命名，不再展示旧版兼容字段名。

## 行动方案

这个 Skill 的推荐用法很简单：

1. 先写一个五栏表：本质 / 条件 / 得失 / 先后 / 对手
2. 每一栏只写 3 到 5 个关键点
3. 先填“条件”和“得失”，快速判断值不值得做
4. 再设计“先后”，拆成 3 步以内路径
5. 最后模拟“对手”，至少写出 2 种对方反应

## 更新与推送

如果你只是更新文案、示例或配置，推荐按下面的流程处理。

### 1. 查看当前变更

```bash
git status
```

### 2. 提交本次更新

```bash
git add README.md SKILL.md agents references package.json
git commit -m "docs: convert skill to weiliaozi analysis"
```

### 3. 推送到远端

如果仓库已经绑定远端：

```bash
git push origin main
```

### 4. 首次推送时

如果当前仓库还没有配置远端，先执行：

```bash
git remote add origin https://github.com/phoenixlucky/weiliaozi-skill.git
git branch -M main
git push -u origin main
```

如果当前远端还指向旧仓库，可以改成新库：

```bash
git remote set-url origin https://github.com/phoenixlucky/weiliaozi-skill.git
git push -u origin main
```

## 参考文件

- [SKILL.md](./SKILL.md)
- [CHANGELOG.md](./CHANGELOG.md)
- [references/examples.md](./references/examples.md)
- [references/tone-guide.md](./references/tone-guide.md)

## 变更日志

最新版本：`1.5.2`（2026-04-27）

- 移除 README 中容易被静态安全扫描误判的旧版兼容字段名展示。
- `prepareClawHubRequest()` 继续以 `instructions` 作为宿主接入的正式字段。
- 增加路由测试，覆盖 README 中承诺直接命中的历史短问句。

- 增加 `src/router.js`、`src/prompts.js`、`src/index.js`，提供可由 ClawHub 宿主在模型调用前执行的代码层路由。
- 增加 `prepareClawHubRequest()`，把路由结果、宿主指令层和消息结构组合成可直接接入的请求对象。
- 增加 `examples/clawhub-router.js` 示例，演示如何对“秦为什么二世而亡”这类问题先走历史路由，再进入技能正文。

- 修正英文历史模式的语言规则，不再固定继续用中文输出，而是默认跟随用户语言。
- 降低对外文档中的高敏感表述，统一将宿主侧覆盖说明写为 `instructions` / 宿主指令层。
- 增加安全边界说明，明确宿主控制层不接收外部不可信文本作为控制指令来源。

- 增加“模式路由与优先级”说明，明确先判断是否命中历史模式，再生成回答，避免新增人设描述稀释原有规则。
- 明确历史模式只是路由层：改变的是身份与开场，不得削弱既有五栏分析、准确性规则和系统拆解逻辑。
- 补充时间/人物/事件三类触发信号，并要求对短问句也直接命中，不再依赖模糊语感。

- 强化历史问答触发规则：凡命中战国末期至汉建立前的魏、秦、楚汉问题，必须使用尉缭子第一视角，不得退回普通口吻。
- 增加显式触发示例，覆盖“秦灭亡”“秦为什么二世而亡”“秦末乱局”“楚汉相争”等常见问法。

- 将“历史问答触发规则”从“战国末期至秦统一前”扩展为“战国末期至汉建立前”，覆盖秦末与楚汉相争叙事。
- 在人物设定中加入民间传说谱系：张良、韩信、商山四皓、黄石公等相关关联，但明确标注为传说性内容。
- 增加尉缭子人物底稿，包括布衣出身、可能来自魏或中原诸侯国、公元前 237 年入秦、为秦王政提供军政建议等设定。
- 明确这类设定属于风格与叙事约束，涉及传说内容时不得冒充严格史实。

- 新增“系统瓦解”视角，明确《尉缭子》的核心不是先打正面战，而是先用“钱 + 势 + 人心”削弱对手系统。
- 在“条件”中补入三项底线：稳定财力、情报体系、内部纪律。
- 在“先后”中固化低成本削弱顺序：`乱其谋 -> 削其力 -> 后再战`。
- 增加五步可执行抽象模型：识别关键节点、资源渗透、制造内耗、切断协同、低成本收尾。
- 增加安全约束，明确该技能用于分析与判断，不用于生成违法或有害的操作方案。

完整历史见 [CHANGELOG.md](./CHANGELOG.md)。

## 最后

这套方法的核心不是“多想”，而是“按顺序想”。

先别急着决策。
先把结构、约束、利弊、顺序和对手看清。

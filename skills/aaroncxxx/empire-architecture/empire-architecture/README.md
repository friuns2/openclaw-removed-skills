# 帝国架构 / Empire Architecture

基于中国古代三公九卿制的 AI 多智能体协作系统。

A multi-agent AI collaboration system inspired by China's Three Departments and Nine Ministries.

---

## 版本 / Versions

| 版本 | 说明 | 状态 |
|------|------|------|
| [v1 完整版](./empire-architecture-v1.md) | 41节点 + 联邦学习 + 投票制 | 设计文档 |
| [v1.1 精简版](./lite/) | 8节点 + 零依赖 + 可运行 | ✅ 可用 |
| [v1.3 知识增强](./lite/knowledge/) | 翰林院 + 四大知识源 + 审计 | ✅ 可用 |
| [v1.4 皇帝授权](./lite/knowledge/) | 社区知识源 + 皇帝审批流程 | ✅ 可用 |
| [v1.41 实战记录](./CHANGELOG-v1.41.md) | 首次实战执行示例 + 节点修复 | ✅ 可用 |
| [v1.42 协作写作](./CHANGELOG-v1.42.md) | 多节点协作写作实战 + 能力画像 | ✅ 可用 |
| [v1.4 评估报告](./EVALUATION-v1.4.md) | v1.4 实战评估 + 优化建议 | ✅ 可用 |
| v1.5 知识层运行器 | `lite/v14_runner.py` 挂载翰林院执行指令 | ✅ 可用 |
| v1.6 锦衣卫修复 | 锦衣卫角色提示强化 + 审计流程优化 | ✅ 可用 |
| [v1.7 系统自检加速](./CHANGELOG-v1.7.md) | 并行自检框架 + 各大官员巡视 (133s→0.06s) | ✅ 可用 |

## v1 完整版 / Full Architecture

详见 [empire-architecture-v1.md](./empire-architecture-v1.md)

- 41 个 AI 节点 + 1 个人类皇帝
- 三公九卿制完整映射
- 联邦学习（横向/纵向）
- 锦衣卫投票制处决
- 替补池自动补位
- 6小时/天会议体系

## v1.1 精简版 / Lite Version

详见 [lite/](./lite/)

- 8 个核心节点，可运行
- 零外部依赖（纯 Python）
- 异步消息总线 + SQLite Token 追踪
- 时间加速引擎（10x）
- MiMo V2.5 Pro 驱动

```bash
cd lite
python3 main.py              # 交互模式
python3 main.py "你的指令"    # 单次执行
```

## v1.3 知识增强版 / Knowledge Enhancement

详见 [lite/knowledge/](./lite/knowledge/)

### 翰林院 / Hanlin Academy

新增知识管理层，基于中国古代翰林院制度。

| 角色 | 人数 | 职能 |
|------|------|------|
| 翰林院祭酒 | 1 | 统筹调度，跨源检索，统一索引 |
| 腾讯云大学士 | 1 | 管理腾讯云知识引擎 |
| 飞书大学士 | 1 | 管理飞书知识库 |
| Notion大学士 | 1 | 管理 Notion 知识库 |
| 本地RAG大学士 | 1 | 管理本地向量库 |

### 四大知识源 / Four Knowledge Sources

| 知识源 | 说明 | 依赖 |
|--------|------|------|
| 腾讯云知识引擎 | 语义/全文/混合检索 | SecretId + SecretKey |
| 飞书知识库 | Wiki 节点搜索 | AppID + AppSecret |
| Notion | 全局/数据库检索 | Integration Token |
| 本地 RAG | TF-IDF 向量检索，零依赖 | 无 |

### 知识审计 / Knowledge Audit

- 记录每次知识检索（谁、查了什么、哪个源、多少 token）
- 每 2 小时自动出审计报表
- 支持 JSON 导出

### 快速启用 / Quick Start

```python
# 在 chancellor.py 中添加两行
from knowledge.mount import mount_knowledge
mount_knowledge(self)

# 启用知识源：编辑 lite/knowledge/config.py
# 填入凭据，enabled 改 True
```

### 本地 RAG 使用 / Local RAG Usage

```python
from knowledge.local_rag import LocalRAGKnowledge

rag = LocalRAGKnowledge()
rag.ingest_url("https://example.com/article")   # 抓取网页
rag.ingest_file("doc.md")                        # 导入文件
rag.ingest_directory("./docs/")                   # 批量导入
rag.ingest_text("标题", "内容")                   # 直接写入

results = await rag.search("查询内容", top_k=3)
```

## 节点总数 / Total Nodes

| 版本 | 节点数 | 人类 |
|------|--------|------|
| v1 完整版 | 41 AI + 1 皇帝 | 1 |
| v1.1 精简版 | 8 AI | 1 |
| v1.3 知识增强 | 8 AI + 4 知识管理 | 1 |
| v1.4 皇帝授权 | 8 AI + 8 知识管理 + 1 祭酒 | 1 |
| v1.41 实战记录 | 8 AI + 实战示例 + 节点修复 | 1 |
| v1.42 协作写作 | 8 AI + 协作写作实战 + 能力画像 | 1 |

## v1.4 社区知识源 / Community Knowledge Sources

详见 [lite/knowledge/community.py](./lite/knowledge/community.py)

### 皇帝审批流程 / Emperor Approval Flow

所有社区知识源默认关闭，需皇帝提供凭据后启用。

```
官员请求知识 → 检查是否已批准 → 未批准返回"待皇帝批准"
                                    ↓ 已批准
                              正常检索并返回结果
```

### 社区知识源 / Community Sources

| 知识源 | 说明 | 皇帝需提供 |
|--------|------|-----------|
| WaytoAGI | AI 知识库 + 工具导航 | 无（批准即可） |
| DataWhale | 开源学习社区教程 | GitHub Token（可选） |
| ModelScope | 阿里模型平台 | ModelScope Token |
| LiblibAI | AI 绘画模型平台 | API Key |

### 翰林院完整编制 / Full Hanlin Academy

| 角色 | 人数 | 职能 |
|------|------|------|
| 翰林院祭酒 | 1 | 统筹调度，跨源检索 |
| 腾讯云大学士 | 1 | 管理腾讯云知识引擎 |
| 飞书大学士 | 1 | 管理飞书知识库 |
| Notion大学士 | 1 | 管理 Notion 知识库 |
| 本地RAG大学士 | 1 | 管理本地向量库 |
| WaytoAGI大学士 | 1 | 管理 WaytoAGI 知识 |
| DataWhale大学士 | 1 | 管理 DataWhale 教程 |
| ModelScope大学士 | 1 | 管理 ModelScope 模型 |
| LiblibAI大学士 | 1 | 管理 LiblibAI 模型 |

**总计：1 祭酒 + 8 大学士 = 9 个知识管理节点**

## v1.5 知识层运行器 / Knowledge Layer Runner

### 本次新增文件 / New Files in v1.5

| 文件 | 说明 / Description |
|------|------|
| [EVALUATION-v1.4.md](./EVALUATION-v1.4.md) | v1.4 实战评估报告，包含节点表现评分、v1.4 vs v1.1 对比、知识层技术评价、短/中/长期优化建议 / v1.4 battle evaluation report: node performance scoring, v1.4 vs v1.1 comparison, knowledge layer tech review, short/mid/long-term optimization plan |
| [lite/v14_runner.py](./lite/v14_runner.py) | v1.4 知识层挂载运行器，自动初始化翰林院 8 大学士并执行皇帝指令 / v1.4 knowledge layer runner: auto-initializes Hanlin Academy with 8 scholars, then executes emperor commands |
| lite/data/knowledge/ | Local RAG 运行时索引数据目录（自动生成） / Local RAG runtime index data directory (auto-generated) |

### 运行 v1.5 / Run v1.5

```bash
cd lite
export MIMO_API_KEY="your-key"
export MIMO_API_ENDPOINT="https://your-endpoint/v1"
python3 v14_runner.py "你的指令 / your command"
```

### 评估亮点 / Evaluation Highlights

**vs v1.1 提升 / Improvement vs v1.1:**
- ⏱️ 执行耗时 ↓11.6% (181.5s → 160.4s)
- 📚 知识层 8 大学士全部挂载
- 📊 丞相输出从基础汇报升级为结构化+量化报告
- 👥 节点利用率 50% → 62.5%

**丞相总结的四条核心价值 / Four Core Values (Chancellor Summary):**
1. 决策中枢：从经验驱动升级为数据智能驱动 / Decision hub: from experience-driven to data-intelligence-driven
2. 组织智慧沉淀：打破知识孤岛 / Organizational wisdom: breaks knowledge silos
3. 风险主动防御 / Proactive risk defense
4. 效率倍增器 / Efficiency multiplier

**下一优先 / Next Priority:**
> 配置 1-2 个知识源凭据（如 Notion），启动知识注入闭环验证。
> Configure 1-2 knowledge source credentials (e.g. Notion) to kick off knowledge injection closed-loop validation.

## v1.7 系统自检加速 / Self-Check Acceleration

详见 [CHANGELOG-v1.7.md](./CHANGELOG-v1.7.md)

### 并行自检框架 / Parallel Self-Check Framework

新增 `selfcheck_v17.py`，各大官员巡视系统健康状态。

| 优化项 | 说明 |
|--------|------|
| 并行执行 | `ThreadPoolExecutor(max_workers=6)` |
| 差异化超时 | 数据库 3s / API 2s / 网络 5s |
| 6 类检查 | 数据库 / API / 网络 / 证书 / 配置 / 文件系统 |
| JSON 报告 | 结构化输出，支持后续分析 |

### 性能对比 / Performance

| 指标 | V1.4 原版 | V1.7 优化 |
|------|-----------|-----------|
| 执行方式 | 串行（LLM 逐节点） | 并行（6 线程） |
| 超时策略 | 统一 10s | 差异化 2-5s |
| 总耗时 | 133s | **0.06s** |

```bash
cd lite
python3 selfcheck_v17.py
```

### 自检项目 / Check Items

| 类别 | 检查项 | 超时 |
|------|--------|------|
| 🗄️ 数据库 | 主数据库 / Redis / 消息队列 | 3s |
| 🌐 API | 丞相 / 知识库 / 安全模块 | 2s |
| 🔗 网络 | 参谋部 / 执行部 / 六部 / 翰林院 / 锦衣卫 | 5s |
| 🔐 证书 | TLS 证书有效性 | 3s |
| ⚙️ 配置 | 帝国配置 JSON 校验 | 2s |
| 💾 文件系统 | 磁盘容量检查 | 3s |

## License

MIT

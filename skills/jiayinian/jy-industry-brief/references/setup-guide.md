# 行业速报 Skill 配置指南

## 必需配置

### 1. 安装 mcporter

```bash
# 通过 npm 全局安装
npm install -g mcporter

# 验证安装
mcporter --version
```

### 2. 获取 JY_API_KEY

向恒生聚源申请 JY_API_KEY，通过邮箱申请（首次配置需提供，配置一次即可）。

**申请邮箱**：datamap@gildata.com

**邮件标题**：数据地图 KEY 申请 -XX 公司 - 申请人姓名

**正文模板**：
- 姓名：
- 手机号：
- 公司/单位全称：
- 所属部门：
- 岗位：
- MCP_KEY 申请用途：
- Skill 申请列表：
- 是否需要 Skill 安装包：（是，邮件提供/否，自行下载）
- 其他补充说明（可选）：

### 3. 配置 MCP 服务

```bash
# 配置 jy-financedata-tool 服务（5 个核心工具）
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"

# 配置 jy-financedata-api 服务（252+ 工具）
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"

# 验证配置
mcporter list
```

**预期输出**：
```
jy-financedata-tool (5 tools)
jy-financedata-api (252+ tools)
2 healthy
```

### 4. 在 OpenClaw 中启用 mcporter

**编辑 openclaw.json**（路径：`C:\Users\你的用户名\.openclaw\openclaw.json`）：

```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": {
          "MCPORTER_CONFIG": "C:\\Users\\你的用户名\\config\\mcporter.json"
        }
      }
    }
  }
}
```

**重启 OpenClaw**：
```bash
openclaw gateway restart
```

---

## 可选配置

### 配置行业龙头股映射（推荐）

由于 MCP 工具主要基于股票代码，建议建立行业名称到代表性公司的映射：

**创建映射文件**（在工作空间）：
```markdown
# 行业 - 股票映射表

| 行业名称 | 代表性公司 | 股票代码 |
|----------|-----------|----------|
| 光子芯片 | 公司 A | 688000 |
| 光子芯片 | 公司 B | 688001 |
| 新能源汽车 | 比亚迪 | 002594 |
| 新能源汽车 | 宁德时代 | 300750 |
| 人工智能 | 科大讯飞 | 002230 |
| 半导体 | 中芯国际 | 688981 |
```

**使用方法**：
- 用户请求行业速报时，先查映射表
- 获取行业相关股票代码
- 调用 MCP 工具获取数据

---

## 使用示例

### 基本使用
```
生成光子芯片行业速报
```

### 指定行业
```
生成新能源汽车行业速报
```

### 输出格式
```
生成半导体行业速报，渲染成 HTML
生成医药行业速报，返回 PDF
```

---

## 常见问题

### Q1: mcporter list 显示服务未配置

**原因**：MCP 服务未正确配置

**解决**：
```bash
# 重新配置服务
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### Q2: 调用工具返回空数据

**原因**：该行业 24 小时内新闻较少或 MCP 未覆盖

**解决**：
- 尝试聚合多家相关公司数据
- 使用行业龙头股票代码查询
- 在报告中标注数据时间范围

### Q3: 投融资事件不足

**原因**：该行业 24 小时内投融资事件较少

**解决**：
- 放宽时间范围至过去一周
- 在报告中标注"过去 24 小时内投融资事件较少，以下为过去一周数据"
- 如确实没有，直接写"无"

### Q4: 行业名称无法识别

**原因**：行业名称太宽泛或太具体

**解决**：
- 使用标准行业分类名称
- 参考申万行业分类
- 或提供行业龙头公司名称

### Q5: JY_API_KEY 失效

**原因**：KEY 过期或被撤销

**解决**：重新向恒生聚源申请新的 KEY

### Q6: CorporateResearchViewpoints 调用失败

**原因**：错误地调用了 jy-financedata-tool.CorporateResearchViewpoints

**解决**：该工具在 jy-financedata-api 服务中，应使用：
```bash
mcporter call jy-financedata-api.CorporateResearchViewpoints query="行业名称"
```

---

## 最佳实践

### MCP 工具调用顺序

1. **优先调用 IndustryNewsFlash**（如可用）
   ```bash
   mcporter call jy-financedata-api.IndustryNewsFlash query="行业名称"
   ```

2. **补充调用 NewsPublicOpinionList**
   ```bash
   mcporter call jy-financedata-api.NewsPublicOpinionList query="相关股票代码"
   ```

3. **获取研究报告**
   ```bash
   mcporter call jy-financedata-tool.FinancialResearchReport query="行业名称 行业分析"
   ```

4. **获取研报观点**
   ```bash
   mcporter call jy-financedata-api.CorporateResearchViewpoints query="行业名称"
   ```

5. **自然语言查询**
   ```bash
   mcporter call jy-financedata-tool.FinQuery query="行业名称 最新政策 市场规模"
   ```

### 多公司数据聚合

对于行业层面信息，聚合多家相关公司数据：

```bash
# 示例：光子芯片行业（3 家代表公司）
mcporter call jy-financedata-api.NewsPublicOpinionList query="688000"
mcporter call jy-financedata-api.NewsPublicOpinionList query="688001"
mcporter call jy-financedata-api.NewsPublicOpinionList query="688002"
```

然后：
- 合并所有新闻舆情
- 去除重复新闻
- 按时间排序

### 数据验证

- **时效性验证**：检查新闻发布时间是否在 24 小时内
- **来源验证**：优先选择权威来源（公告、官方媒体）
- **去重处理**：同一事件多家媒体报道 → 选择最权威来源

---

## 性能优化

### 减少 MCP 调用次数

- 一次调用获取多条数据
- 避免重复调用同一工具
- 合理聚合多公司数据

### 提高数据质量

- 优先使用 IndustryNewsFlash（行业层面）
- 补充使用 NewsPublicOpinionList（公司层面）
- 使用 FinQuery 获取宏观数据

### 并发调用

多个独立的 MCP 工具调用可并发执行以提速：
```bash
# 可并发调用
mcporter call jy-financedata-api.IndustryNewsFlash query="行业名称" &
mcporter call jy-financedata-tool.FinancialResearchReport query="行业名称 行业分析" &
mcporter call jy-financedata-api.CorporateResearchViewpoints query="行业名称" &
mcporter call jy-financedata-tool.FinQuery query="行业名称 最新政策" &
wait
```

---

## 相关文档

- [SKILL.md](../SKILL.md) - 行业速报技能主文档
- [news-validation.md](news-validation.md) - 新闻核验清单
- [investment-validation.md](investment-validation.md) - 投融资核验规则
- [report-template.md](report-template.md) - 报告模板
- [html-template.md](html-template.md) - HTML 输出模板

---

**版本**：v1.0 | **更新**：2026-03-31 | **修正**：CorporateResearchViewpoints 服务分配

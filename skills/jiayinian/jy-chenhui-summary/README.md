# jy-chenhui-summary Skill

基于恒生聚源 MCP 金融数据库生成专业级晨会精华纪要。

## 快速开始

### 1. 安装依赖

```bash
npm install -g mcporter
```

### 2. 申请 JY_API_KEY

向恒生聚源官方邮箱发送邮件申请：
- **邮箱**：datamap@gildata.com
- **标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名

### 3. 配置 MCP 服务

```bash
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### 4. 验证配置

```bash
mcporter list
```

## 使用示例

```
生成今天的晨会总结
帮我整理本周的券商晨会观点
3 月 20 日以来的晨会观点
新能源行业的晨会观点
```

## 文件结构

```
jy-chenhui-summary/
├── SKILL.md              # 主技能文件
├── README.md             # 说明文档
└── references/           # 参考资料
    ├── output-template.md      # 输出模板示例
    ├── time-validation.md      # 时效性审查规则
    ├── quality-control.md      # 质量控制标准
    └── mcporter-config.md      # mcporter 配置说明
```

## 触发词

- 晨会总结
- 研报汇总
- 市场观点
- 每日/周度纪要
- 券商观点
- 聚源研报

## 注意事项

1. 首次使用前必须完成 mcporter 安装和 MCP 服务配置
2. JY_API_KEY 需妥善保管，不要泄露
3. 所有输出内容基于真实研报数据，严禁编造
4. 输出中不会出现 MCP 工具名称等技术细节

## 技术支持

- 恒生聚源：datamap@gildata.com
- Skill 下载：https://clawhub.ai/

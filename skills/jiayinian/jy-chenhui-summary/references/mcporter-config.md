# mcporter 配置详细说明

## 什么是 mcporter

mcporter 是一个 MCP（Model Context Protocol）客户端工具，用于连接和调用 MCP 服务。通过 mcporter，可以方便地访问恒生聚源等第三方数据服务。

## 完整配置流程

### 第一步：安装 mcporter

```bash
# 检查是否已安装
mcporter --version

# 如未安装，通过 npm 全局安装
npm install -g mcporter

# 验证安装成功
mcporter --version
```

**预期输出**：显示版本号，如 `mcporter v1.0.0`

### 第二步：申请 JY_API_KEY

**申请邮箱**：datamap@gildata.com

**邮件标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名

**正文模板**：
```
• 姓名：张三
• 手机号：13800138000
• 公司/单位全称：XX 证券股份有限公司
• 所属部门：研究所
• 岗位：分析师
• MCP_KEY 申请用途：晨会研报数据检索
• Skill 申请列表：jy-chenhui-summary
• 是否需要 Skill 安装包：否，自行下载
• 其他补充说明（可选）：
```

**处理时间**：通常 1-3 个工作日

**收到 KEY 后**：妥善保管，不要泄露给他人

### 第三步：配置 MCP 服务

```bash
# 配置 jy-financedata-tool 服务
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"

# 配置 jy-financedata-api 服务
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

**注意事项**：
- 将 `你的 JY_API_KEY` 替换为实际收到的 KEY
- URL 中的 token 参数必须正确
- 两个服务都需要配置

### 第四步：验证配置

```bash
# 列出所有已配置的服务
mcporter list
```

**预期输出**：
```
已配置的 MCP 服务：
- jy-financedata-tool (https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool)
- jy-financedata-api (https://api.gildata.com/mcp-servers/aidata-assistant-srv-api)
```

### 第五步：测试调用

```bash
# 测试调用工具
mcporter call jy-financedata-tool 研究报告数据 --args '{"query": "测试"}'
```

**预期**：返回 JSON 格式的响应数据

---

## 常见问题

### Q1: mcporter 安装失败

**可能原因**：
- Node.js 未安装或版本过低
- npm 权限问题

**解决方案**：
```bash
# 检查 Node.js 版本
node --version  # 建议 v16+

# 如使用 Linux/Mac，尝试加 sudo
sudo npm install -g mcporter

# 或使用 nvm 管理 Node.js 版本
nvm install 20
nvm use 20
npm install -g mcporter
```

### Q2: mcporter list 显示服务但调用失败

**可能原因**：
- JY_API_KEY 无效或过期
- 网络连接问题
- 服务端暂时不可用

**解决方案**：
1. 检查 KEY 是否正确（无多余空格）
2. 联系恒生聚源确认 KEY 状态
3. 检查网络连接

### Q3: 如何更新 JY_API_KEY

```bash
# 先删除旧配置
mcporter config remove jy-financedata-tool
mcporter config remove jy-financedata-api

# 重新配置新 KEY
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=新 KEY"
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=新 KEY"
```

### Q4: 如何查看配置详情

```bash
# 查看配置文件位置
mcporter config path

# 查看完整配置
mcporter config get
```

---

## 安全提示

1. **不要分享 JY_API_KEY**：KEY 与您的账户绑定，泄露可能导致滥用
2. **定期更新 KEY**：建议每 6 个月更新一次
3. **检查使用记录**：如发现异常调用，及时联系恒生聚源
4. **本地存储**：KEY 仅存储在本地配置文件中，不会上传

---

## 技术支持

- **恒生聚源官方邮箱**：datamap@gildata.com
- **Skill 下载**：https://clawhub.ai/
- **mcporter 文档**：https://github.com/openclaw/mcporter

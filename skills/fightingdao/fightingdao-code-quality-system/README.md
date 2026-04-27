# 代码质量分析系统

完整的代码质量分析解决方案，开箱即用。

## 一、快速开始

### 1. 安装技能

```bash
clawhub install code-quality-system
```

### 2. 让 AI 助手帮你初始化

```
请帮我初始化代码质量分析系统
```

AI 助手会自动：
1. 从 GitHub 克隆前后端代码
2. 检查环境（Node.js、PostgreSQL）
3. 安装依赖
4. 初始化数据库
5. 询问配置信息
6. 启动服务

### 3. 你只需要提供三个配置

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 代码仓库目录 | 所有项目已拉取完成的根目录 | `/Users/xxx/projects/` |
| Teams 配置 | Webhook 地址（含 token）和 secret | 在 Teams 群里创建机器人获取 |
| SMTP 配置 | 邮箱发送配置 | QQ邮箱、企业邮箱等 |

### 4. 访问系统

- 前端界面：http://localhost:5173
- 后端 API：http://localhost:3000/api/v1

---

## 二、环境要求

| 环境 | 版本 | 说明 |
|------|------|------|
| Node.js | ≥ 18.x | 推荐 20.x 或 22.x |
| PostgreSQL | ≥ 14.x | 推荐 16.x |
| Git | 任意版本 | 所有项目需提前 clone |

---

## 三、初始化详细步骤

### 3.1 克隆代码

```bash
cd ~/.openclaw/skills/code-quality-system

# 克隆后端代码
git clone https://github.com/FightingDao/code-quality-backend.git backend

# 克隆前端代码
git clone https://github.com/FightingDao/code-quality-frontend.git frontend
```

### 3.2 安装依赖

```bash
cd backend && npm install
cd ../frontend && npm install
```

### 3.3 配置数据库

1. 创建 PostgreSQL 数据库：
```bash
createdb code_quality
```

2. 创建后端环境变量文件 `backend/.env`：
```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/code_quality?schema=public"
PORT=3000
NODE_ENV=development
JWT_SECRET=your-secret-key
```

3. 初始化数据库：
```bash
cd backend
npx prisma generate
npx prisma migrate deploy
```

### 3.4 创建主配置文件

创建 `config.json`（放在技能目录或 workspace 目录）：
```json
{
  "codebaseDir": "/path/to/your/codebase",
  "teamId": "your-team-id",
  "apiBaseUrl": "http://localhost:3000/api/v1",
  "teams": {
    "webhookUrl": "https://your-teams-server.com/api/robot/send?access_token=xxx",
    "secret": "your-teams-secret",
    "botName": "质检君"
  },
  "smtp": {
    "host": "smtp.qq.com",
    "port": 465,
    "secure": true,
    "user": "your-email@qq.com",
    "pass": "your-auth-code",
    "fromName": "代码质量分析助手"
  },
  "emailRecipients": ["recipient@example.com"]
}
```

### 3.5 创建邮件配置文件（可选）

如需发送邮件周报，创建 `~/.openclaw/workspace/.email-config.json`：
```json
{
  "smtp": {
    "host": "smtp.qq.com",
    "port": 465,
    "user": "your-email@qq.com",
    "pass": "授权码"
  },
  "sender": {
    "email": "your-email@qq.com",
    "name": "代码质量分析系统"
  },
  "recipients": ["recipient1@example.com", "recipient2@example.com"]
}
```

### 3.6 创建前端环境变量

创建 `frontend/.env`：
```env
VITE_API_BASE_URL=http://localhost:3000/api/v1
```

### 3.7 启动服务

```bash
# 启动后端
cd backend && npm run start:dev

# 启动前端（新终端）
cd frontend && npm run dev
```

---

## 四、配置说明

### 4.1 Teams 配置获取方式

1. 在 Teams 群里添加"群预警机器人"
2. 开通"对话服务"
3. 复制 **Webhook 地址**（包含 access_token）和 **secret**

**Webhook 地址格式**：
```
https://your-teams-server.com/api/robot/send?access_token=xxxxxxxxx
```

### 4.2 SMTP 配置示例

**QQ邮箱**：
```json
{
  "host": "smtp.qq.com",
  "port": 465,
  "secure": true,
  "user": "your-qq@qq.com",
  "pass": "授权码（不是密码）"
}
```

**企业邮箱**：
```json
{
  "host": "smtp.exmail.qq.com",
  "port": 465,
  "secure": true,
  "user": "your-name@company.com",
  "pass": "邮箱密码"
}
```

### 4.3 团队 ID 获取

在前端界面"小组管理"页面可以查看团队 ID，或通过 API 获取：
```bash
curl http://localhost:3000/api/v1/teams
``

---

## 五、脚本使用说明

### 5.1 分析脚本

```bash
# 周维度分析（周期值为周四日期）
node scripts/analyze-code-v2.js 20260402

# 月维度分析（周期值为月份）
node scripts/analyze-code-v2.js 202603
```

### 5.2 同步脚本

```bash
# 同步分析数据到数据库
node scripts/sync-to-db.js 20260402
```

### 5.3 生成代码审查问题

```bash
# 在 backend 目录运行
cd backend
node ../scripts/generate-code-issues.js 20260402
```

### 5.4 发送邮件周报

```bash
# 在 backend 目录运行
cd backend
node ../scripts/notify-email.js 20260402
```

### 5.5 发送 Teams 消息

```bash
node scripts/notify-teams.js 20260402
```

---

## 六、技术栈

### 后端
- NestJS 10
- Prisma 5
- PostgreSQL 16

### 前端
- React 18
- TypeScript 5
- Vite 5
- Ant Design 5
- Zustand 4

---

## 七、代码仓库

- 后端：https://github.com/FightingDao/code-quality-backend.git
- 前端：https://github.com/FightingDao/code-quality-frontend.git

---

## 八、常见安装问题

### Q: Prisma migrate 失败？

A: 检查 PostgreSQL 是否运行，DATABASE_URL 是否正确：
```bash
psql postgresql://postgres:postgres@localhost:5432/code_quality
```

### Q: 前端启动报错？

A: 确保 Node.js 版本 ≥ 18：
```bash
node --version
```

### Q: 如何添加新项目？

A: 项目会自动识别。只要代码目录下有 `.git` 文件夹，就会被扫描到。

### Q: 如何添加团队成员？

A: 在前端界面的"小组管理"页面添加团队成员。**必须在分析前添加，否则提交不会被统计！**

---

## 九、联系支持

遇到问题？直接告诉 AI 助手：

```
代码质量分析系统启动失败，帮我看看
```

AI 助手会自动诊断并解决问题。
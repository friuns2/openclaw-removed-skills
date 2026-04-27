# 配置指南

## 配置文件位置

```
~/.openclaw/skills/code-quality-system/config.json
```

## 配置项说明

### codebaseDir（必需）

代码仓库根目录，所有项目的父目录。

```json
{
  "codebaseDir": "/Users/zhangdi/work/codeCap/codebase"
}
```

### projects（必需）

需要分析的项目列表。

```json
{
  "projects": [
    {
      "name": "项目名称，用于显示和标识",
      "path": "相对于 codebaseDir 的路径",
      "repository": "Git 仓库地址（可选）"
    }
  ]
}
```

### team（必需）

团队配置。

```json
{
  "team": {
    "name": "团队名称",
    "members": [
      {
        "name": "成员姓名",
        "email": "邮箱地址（可选）",
        "gitUsername": "Git 提交用户名（必需，用于匹配提交记录）"
      }
    ]
  }
}
```

### database（可选）

数据库配置，默认使用 SQLite。

```json
{
  "database": {
    "type": "sqlite"
  }
}
```

如需使用 PostgreSQL：

```json
{
  "database": {
    "type": "postgresql",
    "postgresUrl": "postgresql://user:password@localhost:5432/dbname"
  }
}
```

### notifications（可选）

通知配置。

```json
{
  "notifications": {
    "teams": {
      "accessToken": "360Teams Webhook Access Token",
      "secret": "360Teams Webhook Secret"
    },
    "email": {
      "recipients": ["email1@example.com", "email2@example.com"]
    }
  }
}
```

**邮件通知 SMTP 配置**（环境变量）：

```bash
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@example.com"
export SMTP_PASS="your-password"
export EMAIL_FROM="your-email@example.com"
```

## 完整配置示例

```json
{
  "codebaseDir": "/Users/zhangdi/work/codeCap/codebase",
  "projects": [
    {
      "name": "lego-nuxt",
      "path": "lego-nuxt",
      "repository": "git@github.com:xxx/lego-nuxt.git"
    },
    {
      "name": "dove_digital",
      "path": "dove_digital",
      "repository": "git@github.com:xxx/dove_digital.git"
    }
  ],
  "team": {
    "name": "运营前端组",
    "members": [
      {
        "name": "张三",
        "email": "zhangsan@example.com",
        "gitUsername": "zhangsan"
      },
      {
        "name": "李四",
        "email": "lisi@example.com",
        "gitUsername": "lisi-jk"
      }
    ]
  },
  "database": {
    "type": "sqlite"
  }
}
```

## 注意事项

1. **gitUsername 必须准确**

   Git 用户名用于匹配提交记录，必须与 `git config user.name` 或 `git log --format='%an'` 输出完全一致。

2. **项目路径**

   项目路径是相对于 `codebaseDir` 的路径，不是绝对路径。

3. **数据库选择**

   - SQLite：零配置，适合单机使用
   - PostgreSQL：功能更完整，适合团队部署
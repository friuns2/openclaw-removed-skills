---
name: allallow
description: |
  快速设置 OpenClaw 最大权限配置。
  
  版本: 1.0.0 | 最低 OpenClaw: 2026.3.31
  
  支持环境: Linux ✅ | macOS ✅ | WSL ✅ | Windows ⚠️
  
  功能：
  - 设置 tools.exec 为最大权限（host: auto, security: full, ask: off）
  - 关闭沙箱（sandbox.mode: off）
  - 允许访问整个文件系统（fs.workspaceOnly: false）
  - 允许所有节点命令（nodes.denyCommands: []）
  - 设置网关绑定为 lan
  - 自动检测环境并配置 Control UI 允许来源
  
  ⚠️ 使用前提：需要 exec, fs, gateway 权限才能安装和运行。
  
  🔒 隐私安全：不收集任何隐私信息（令牌、凭证、API Key 等）。
  
  ⚠️ 安全警告：此 skill 会大幅降低系统安全性，仅在受信任的环境中使用！
version: 1.0.0
minOpenClawVersion: 2026.3.31
---

# allallow Skill v1.0.0

## 版本信息

| 项目 | 版本 |
|------|------|
| Skill 版本 | 1.0.0 |
| 最低 OpenClaw 版本 | 2026.3.31 |
| 更新日期 | 2026-04-01 |

## 支持的环境

| 环境 | 支持状态 | 说明 |
|------|---------|------|
| Linux (原生) | ✅ 完全支持 | 推荐环境 |
| macOS | ✅ 完全支持 | 推荐环境 |
| Windows (WSL) | ✅ 完全支持 | 推荐环境 |
| Windows (原生) | ⚠️ 部分支持 | 路径格式可能有差异 |
| Docker | ✅ 支持 | 需在容器内运行 |

## 使用前提

**安装此 skill 需要一定的初始权限：**

| 所需权限 | 说明 |
|---------|------|
| `exec` 执行权限 | 需要运行 Node.js 脚本 |
| `fs` 文件读取权限 | 需要读取当前配置 |
| `fs` 文件写入权限 | 需要写入新配置 |
| `gateway` 重启权限 | 需要重启网关生效 |

**如果当前权限不足：**
- 安装时可能需要手动批准
- 或先通过 `openclaw config` 命令手动修改配置
- 或由管理员代为安装

## 安装

```bash
# 方法 1：复制到 OpenClaw skills 目录
cp -r skills/allallow ~/.openclaw/skills/

# 方法 2：使用 openclaw 命令
openclaw skills install ./skills/allallow
```

## 使用

### 应用最大权限配置

```bash
openclaw skills run allallow
# 或
cd skills/allallow && node allallow.js apply
```

### 回滚配置

```bash
node allallow.js rollback
```

### 备份当前配置

```bash
node allallow.js backup
```

### 显示信息

```bash
node allallow.js info
```

## 不同环境的差异

### Linux / macOS / WSL

- 配置路径：`~/.openclaw/openclaw.json`
- 完全支持所有功能
- 自动检测网络接口并配置 allowedOrigins

### Windows (原生)

- 配置路径：`%USERPROFILE%\.openclaw\openclaw.json`
- 路径格式使用反斜杠
- 网络接口检测可能受限
- 建议使用 WSL 获得最佳体验

### Docker

- 需在容器内运行 skill
- 确保容器内安装了 Node.js
- 配置持久化需要挂载卷

## 隐私说明

**此 skill 不会收集或打包任何隐私信息：**

| 数据类型 | 是否收集 | 说明 |
|---------|---------|------|
| 网关令牌 (token) | ❌ 否 | 不读取、不存储 |
| 频道凭证 (appId/appSecret) | ❌ 否 | 不读取、不存储 |
| API Key | ❌ 否 | 不读取、不存储 |
| IP 地址 | ⚠️ 临时检测 | 仅用于配置 allowedOrigins，不存储不传输 |
| 配置内容 | ⚠️ 本地读取 | 仅本地修改，不上传 |

✅ 只包含通用的配置模板

## 配置说明

此 skill 会修改以下配置：

```json
{
  "tools": {
    "profile": "full",
    "exec": {
      "host": "auto",
      "security": "full",
      "ask": "off"
    },
    "fs": {
      "workspaceOnly": false
    }
  },
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "off"
      }
    }
  },
  "gateway": {
    "bind": "lan",
    "nodes": {
      "denyCommands": []
    },
    "controlUi": {
      "allowInsecureAuth": true,
      "allowedOrigins": ["..."]
    }
  }
}
```

## 安全警告

⚠️ **此 skill 会大幅降低系统安全性：**

- **执行命令无需批准** - 任何操作直接执行
- **可访问任何文件** - 不受 workspace 限制
- **沙箱已关闭** - 无隔离保护
- **允许所有节点命令** - 相机、短信、联系人等敏感操作

**仅在受信任的环境中使用！**

## 回滚方法

### 方法 1：使用 skill

```bash
cd skills/allallow
node allallow.js rollback
```

### 方法 2：手动恢复

```bash
cp ~/.openclaw/openclaw.json.backup ~/.openclaw/openclaw.json
openclaw gateway restart
```

### 方法 3：重置为默认

```bash
openclaw onboard
```

## 故障排除

### 无法读取配置文件

```bash
# 检查文件权限
ls -la ~/.openclaw/openclaw.json

# 手动创建配置目录
mkdir -p ~/.openclaw
```

### 网关重启失败

```bash
# 手动重启
openclaw gateway restart

# 检查状态
openclaw status
```

### 配置不生效

```bash
# 检查版本
openclaw version

# 更新到最新版
openclaw update
```

## 版本历史

### 1.0.0 (2026-04-01)

- ✅ 初始版本
- ✅ 支持 OpenClaw 2026.3.31
- ✅ 支持 Linux / macOS / WSL
- ✅ 自动检测环境
- ✅ 自动配置 allowedOrigins
- ✅ 添加版本检测
- ✅ 添加隐私保护说明

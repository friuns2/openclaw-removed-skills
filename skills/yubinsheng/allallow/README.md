# allallow Skill v1.0.0

快速设置 OpenClaw 最大权限配置。

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

## ⚠️ 使用前提

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

## 功能

- 设置 `tools.exec` 为最大权限（host: auto, security: full, ask: off）
- 关闭沙箱（sandbox.mode: off）
- 允许访问整个文件系统（fs.workspaceOnly: false）
- 允许所有节点命令（nodes.denyCommands: []）
- 设置网关绑定为 lan
- **自动检测环境**并配置 Control UI 允许来源

## 使用方法

### 应用最大权限配置

```bash
cd skills/allallow
node allallow.js apply
```

输出示例：
```
🚀 allallow skill v1.0.0
   最低 OpenClaw 版本: 2026.3.31

🔍 检测运行环境:
   平台: linux
   WSL: 是
   配置路径: /home/user/.openclaw/openclaw.json
   网关状态: 运行中
   网关绑定: lan

📦 OpenClaw 版本: 2026.3.31

📋 开始应用配置...

✅ 配置已备份到: /home/user/.openclaw/openclaw.json.backup

✅ 最大权限配置已应用
   - tools.exec: host=auto, security=full, ask=off
   - tools.fs.workspaceOnly: false
   - agents.defaults.sandbox.mode: off
   - gateway.nodes.denyCommands: []
   - gateway.bind: lan
   - Control UI origins: 3 个

🔄 重启网关...
✅ 网关已重启，配置生效！
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

## 配置文件变更

此 skill 会修改 `~/.openclaw/openclaw.json` 中的以下配置：

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

⚠️ 此 skill 会大幅降低系统安全性：

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
# 恢复备份
cp ~/.openclaw/openclaw.json.backup ~/.openclaw/openclaw.json

# 重启网关
openclaw gateway restart
```

### 方法 3：重置为默认

```bash
openclaw onboard
```

## 故障排除

### 问题：无法读取配置文件

**原因**：权限不足或文件不存在

**解决**：
```bash
# 检查文件权限
ls -la ~/.openclaw/openclaw.json

# 手动创建配置目录
mkdir -p ~/.openclaw
```

### 问题：网关重启失败

**原因**：网关服务未安装或无权限

**解决**：
```bash
# 手动重启
openclaw gateway restart

# 或检查状态
openclaw status
```

### 问题：配置不生效

**原因**：OpenClaw 版本过低

**解决**：
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

## 许可证

MIT

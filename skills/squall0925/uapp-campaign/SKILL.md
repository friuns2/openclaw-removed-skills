---
name: uapp-campaign
version: 1.1.0
description: "小程序推广链接管理 skill。当用户需要创建推广链接或查询推广活动/渠道列表时使用。触发词：推广链接、推广活动、推广渠道、创建推广、推广列表、活动列表、渠道列表。注意：仅支持小程序/H5/小游戏应用，不支持 Android/iOS App。"
entry: scripts/campaign.py
---

## 使用流程

**Step 1：确认应用名称**
- 用户未提及小程序名时，询问：「请问是哪个小程序？」
- 若应用是 Android/iOS App，告知：「推广链接功能仅支持小程序/H5/小游戏应用」

**Step 2：确认操作意图**
- 创建推广链接 → 需要收集：活动名称（`--name`）、渠道名称（`--channel`）、落地页路径（`--path`，可选）
- 查询列表 → 确认查活动列表还是渠道列表（`--type campaign` 或 `--type channel`）

**Step 3：执行并解读输出**
- 创建成功后，告知用户活动名称和渠道名称，提示可通过列表查询获取完整推广链接 URL
- 列表查询后，用自然语言汇总条目数量和关键信息

## 边界条件与异常处理

| 情形 | 处理方式 |
|------|----------|
| 应用是 Android/iOS App | 告知不支持，推广链接仅限小程序/H5/小游戏 |
| 小程序名找不到匹配 | 提示「找不到该小程序，请确认名称；可用 uapp-assets 查询所有小程序列表」 |
| 创建时未提供活动名或渠道名 | 先询问补全，不要用空值执行 |
| 列表为空 | 提示「当前应用暂无推广记录」 |

## 典型问法与内部意图映射

| 典型问法 | 内部意图（CLI 参数） |
|---------|-------------------|
| "创建一条新的推广链接，名字是春季换新季，渠道是抖音" | `--create --name "春季换新季" --channel "抖音" --app <app_name>` |
| "我的推广链接列表" | `--list --type campaign --app <app_name>` |
| "查看所有推广渠道" | `--list --type channel --app <app_name>` |

## 支持的操作模式

### 创建推广链接

| 参数 | 说明 |
|-----|------|
| `--create` | 创建推广链接模式 |
| `--name` | 活动名称（必填） |
| `--channel` | 渠道名称（必填） |
| `--path` | 落地页路径（可选） |

### 查询列表

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `--list` | - | 查询列表模式 |
| `--type` | campaign | 列表类型：campaign(活动)/channel(渠道) |

## 调用示例

### 创建推广链接

```bash
# 创建推广链接（无落地页路径）
python3 scripts/campaign.py --create --name "春季换新季" --channel "抖音" --app "友小盟数据官"

# 创建推广链接（带落地页路径）
python3 scripts/campaign.py --create --name "春季特卖" --channel "微信推广" --path "mainpage" --app "友小盟数据官"
```

### 查询列表

```bash
# 查询推广活动列表
python3 scripts/campaign.py --list --type campaign --app "友小盟数据官"

# 查询推广渠道列表
python3 scripts/campaign.py --list --type channel --app "友小盟数据官"
```

### JSON 输出

添加 `--json` 参数获取结构化数据：

```bash
python3 scripts/campaign.py --list --type campaign --app "友小盟数据官" --json
```

## 配置方式

1. `--config /path/to/umeng-config.json`: 显式指定配置文件
2. `export UMENG_CONFIG_PATH=/path/to/umeng-config.json`: 环境变量
3. 在当前目录创建 `umeng-config.json`: 默认查找

配置文件格式参见项目根目录 `umeng-config.json` 示例。

## 注意事项

1. **仅支持小程序应用**：本 skill 仅支持 platform 为小程序/H5/小游戏的应用
2. **dataSourceId**：小程序 API 使用 `dataSourceId` 参数，值等同于 `appkey`
3. **推广链接 URL**：创建成功后，可通过列表接口获取完整的推广链接 URL

## 相关 Skill

- `uapp-umini`：小程序数据查询（概况、留存、页面分析等），支持查询推广活动统计数据

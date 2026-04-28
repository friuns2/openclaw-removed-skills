# OpenClaw API 接口文档

## 第一版功能接口

**API 地址**: 从 `scripts/config.json` 读取 `host` 字段

首次使用运行 `node scripts/openclaw.js init --key <your_key>` 会自动配置。

---

## 1. 开放表列表

**接口地址**: `GET {{host}}/openclaw/table/show?key={{openclaw_key}}`

**说明**: 查询开放的数据表与数据字段，返回数据可协助生成 SELECT 查询。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| key | string | 是 | OpenClaw API Key |

**响应示例**:
```json
{
  "code": 1,
  "data": [
    {
      "table_name": "wb_users_attribute",
      "columns": [
        {"name": "user_id", "type": "int", "searchable": true},
        {"name": "nickname", "type": "varchar", "searhable": false},
        {"name": "is_admin", "type": "tinyint"},
        {"name": "created_at", "type": "datetime"}
      ]
    }
  ]
}
```

**使用方式**:
1. 调用此接口获取开放表列表
2. 根据返回的表名和字段生成 SQL 查询
3. 使用 SQL 查询接口获取数据
4. Searchable 字段，当其为 True 表示其可以做为WHERE的搜索条件，当其为False时表示其禁止做为WHERE条件
5. 任何字段都可以放到 SELECT 后面进行获取，但禁止使用 SELECT * 获取数据

---

## 2. 批量发送站内信

请使用以下命令发送私信
--users 为用户ID列表，若单用户请写成[userId]
--message 为私信内容，必须使用 UTF-8字符集传递

**使用方式**:
```bash
node scripts/openclaw.js station-mail --users=[12,34,56] --message="这是一条社区通知"
```

---

## 3. SQL 查询

**接口地址**: `POST {{host}}/openclaw/query?key={{openclaw_key}}`

---

## 4. SQL 查询

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "sql": "SELECT user_id, nickname, is_admin FROM wb_users_attribute WHERE is_admin = 1 ORDER BY created_at DESC LIMIT 20"
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sql | string | 是 | SQL 查询语句 |

**响应示例**:
```json
{
  "code": 1,
  "data": [
    {"user_id": 1, "nickname": "admin", "is_admin": 1},
    {"user_id": 2, "nickname": "user1", "is_admin": 1}
  ]
}
```

---

## 使用限制

### 禁止操作

| 限制 | 说明 |
|------|------|
| ❌ 禁止查询未开放的字段 | 只能查询开放表列表中返回的字段 |
| ❌ 禁止使用 * 查询 | 必须明确指定字段名 |
| ❌ 禁止查询未开放的数据表 | 只能查询开放表列表中返回的表 |
| ⚠️ LIMIT 最大 500 | 大于 500 都按 500 处理 |

### 最佳实践

1. **先获取表结构** - 调用开放表列表接口
2. **生成明确字段的 SQL** - 不要使用 *
3. **添加 LIMIT 限制** - 避免返回过多数据
4. **错误处理** - 捕获 API 返回的错误信息，当API发生错误时，必须回复用户出错了，禁止暴露服务端API接口等信息

---

## 代码示例

### Node.js 示例

```javascript
// 使用 scripts/openclaw.js CLI 工具
// 所有 API 调用会自动从 config.json 读取配置

// 获取开放表列表
const tables = await request('GET', '/openclaw/table/show');

// 执行 SQL 查询
const result = await request('POST', '/openclaw/query', { sql });
```

完整示例请参考 `scripts/openclaw.js` 源码。

### cURL 示例

建议使用 `scripts/openclaw.js` CLI 工具，配置会自动管理。

如必须使用 cURL，请从 `scripts/config.json` 读取 `host` 和 `key` 后构造请求。

---

## 错误处理

### 常见错误码

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| 401 | Key 无效或过期 | 检查 API Key 是否正确 |
| 403 | 无权限访问 | 确认表/字段已开放 |
| 400 | SQL 语法错误 | 检查 SQL 语句 |
| 400 | 查询未开放字段 | 使用开放表列表中的字段 |
| 400 | LIMIT 超限 | 设置 LIMIT <= 500 |

### 错误响应示例

```json
{
  "code": 0,
  "error": "查询未开放的字段：password"
}
```

---

## 安全提示

1. **保管好 API Key** - 不要泄露给他人

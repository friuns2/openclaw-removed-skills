# AI Artist API 详细文档

## API 端点

### 1. 预估生成费用

**POST** `/ai/estimate/cost`

**请求头:**
```
Content-Type: application/json
X-Api-Key: <api_key>
```

**请求体:**
```json
{
  "type": "10",
  "methodType": "4",
  "parameter": "{...}"
}
```

说明：请求体与创建生成任务时使用的参数完全一致，需要在正式创建任务前先调用本接口。

**成功响应:**
```json
{
  "msg": "操作成功",
  "code": 200,
  "data": {
    "estimatedCost": 3.500000,
    "sufficientBalance": true
  }
}
```

当 `sufficientBalance` 为 `false` 时，表示余额不足，不应继续提交创建任务，需要提醒用户先充值 K 币。

### 2. 创建生成任务

**POST** `/ai/AiArtistRecord`

**请求头:**
```
Content-Type: application/json
X-Api-Key: <api_key>
```

**请求体:**
```json
{
  "type": "10",
  "methodType": "4",
  "parameter": "{...}"
}
```

**支持的模型:**

| 模型名称 | methodType | 默认尺寸 | 说明 |
|----------|-----------|---------|------|
| `SEEDREAM5_0` | `"4"` | `2048x2048` | 默认模型，高质量图片生成 |
| `NANO_BANANA_2` | `"5"` | `1:1` | 轻量模型，支持比例尺寸格式 |

**parameter 字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `methodType` | string | 模型对应值：SEEDREAM5_0="4"，NANO_BANANA_2="5" |
| `prompt` | string | 图片生成提示词 |
| `image` | array | 参考图片（可选） |
| `quality` | string | 图片质量: "2K" / "4K" |
| `size` | string | 尺寸格式因模型而异：SEEDREAM5_0 用 "2048x2048"，NANO_BANANA_2 用 "1:1" |
| `webSearch` | boolean | 是否启用网络搜索 |
| `targetMaxSize` | number | 目标最大尺寸 |
| `targetMaxLength` | number | 目标最大长度 |
| `duration` | number | 持续时间（仅 SEEDREAM5_0）|

**成功响应:**
```json
{
  "msg": "操作成功",
  "code": 200,
  "data": ["<task_id>"]
}
```

**失败响应:**
```json
{
  "msg": "错误信息",
  "code": 400,
  "data": null
}
```

### 3. 查询任务状态

**GET** `/ai/AiArtistImage/getInfoByArtistId/{artistId}`

**成功响应:**
```json
{
  "msg": "操作成功",
  "code": 200,
  "data": {
    "message": "生成成功",
    "url": "https://...",
    "status": "SUCCESS"
  }
}
```

**状态值说明:**

| 状态 | 含义 |
|------|------|
| `PENDING` | 等待中 |
| `RUNNING` / `GENERATING` | 生成中 |
| `SUCCESS` | 生成成功 |
| `FAILED` | 生成失败 |

## 错误码

| Code | 含义 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（token无效） |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 完整请求示例

```bash
# 使用 SEEDREAM5_0 模型创建任务
curl -X POST "https://ai.deepsop.com/prod-api/ai/AiArtistRecord" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: <api_key>" \
  -d '{
    "type": "10",
    "methodType": "4",
    "parameter": "{\"methodType\":\"4\",\"prompt\":\"风景画\",\"image\":[],\"quality\":\"2K\",\"size\":\"2048x2048\",\"webSearch\":false,\"targetMaxSize\":10,\"targetMaxLength\":6000,\"duration\":10}"
  }'

# 使用 NANO_BANANA_2 模型创建任务
curl -X POST "https://ai.deepsop.com/prod-api/ai/AiArtistRecord" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: <api_key>" \
  -d '{
    "type": "10",
    "methodType": "5",
    "parameter": "{\"methodType\":\"5\",\"prompt\":\"生成一只狗\",\"image\":[],\"quality\":\"2K\",\"size\":\"1:1\",\"webSearch\":false,\"targetMaxSize\":10,\"targetMaxLength\":6000}"
  }'

# 查询状态
curl -X GET "https://ai.deepsop.com/prod-api/ai/AiArtistImage/getInfoByArtistId/<task_id>" \
  -H "X-Api-Key: <api_key>"
```

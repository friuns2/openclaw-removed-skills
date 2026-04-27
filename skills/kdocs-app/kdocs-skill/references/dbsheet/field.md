# 字段管理

## 1. dbsheet.create_fields

#### 功能说明

在指定数据表中批量创建字段，支持文本、数值、单选、多选、日期、附件等多种类型。


#### 调用示例

创建多种类型字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "name": "状态",
      "type": "SingleSelect",
      "items": [
        {
          "value": "待处理"
        },
        {
          "value": "进行中"
        },
        {
          "value": "已完成"
        }
      ]
    },
    {
      "name": "截止日期",
      "type": "Date"
    },
    {
      "name": "备注",
      "type": "MultiLineText"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要创建的字段列表
  - `name` (string, 必填): 字段名称
  - `type` (string, 必填): 字段类型（见附录：字段类型）
  - `items` (array, 可选): 选项列表，用于 `SingleSelect`/`MultipleSelect` 类型，每项包含 `value`
  - `number_format` (string, 可选): 数字格式，用于 `Number` 类型，如 `"0.00_ "`
  - `sync_field` (boolean, 可选): 是否同步字段
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      {
        "id": "K",
        "name": "状态",
        "type": "SingleSelect",
        "items": [
          { "id": "E", "value": "待处理" },
          { "id": "F", "value": "进行中" },
          { "id": "G", "value": "已完成" }
        ]
      },
      { "id": "L", "name": "截止日期", "type": "Date" }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields[].id` | string | 新建字段 ID |
| `detail.fields[].name` | string | 字段名称 |
| `detail.fields[].type` | string | 字段类型 |
| `detail.fields[].items` | array | 选项列表（选项类型字段） |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：get_schema 确认字段已创建

---

## 2. dbsheet.update_fields

#### 功能说明

批量更新数据表中已有字段的名称、选项等属性。每项更新必须包含字段 ID。

#### 调用示例

更新字段名称和选项：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "id": "E",
      "name": "优先级",
      "items": [
        {
          "id": "B",
          "value": "低"
        },
        {
          "value": "中"
        },
        {
          "id": "D",
          "value": "高"
        }
      ]
    },
    {
      "id": "C",
      "max": 4
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要更新的字段列表，每项必须包含 `id` 字段
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `omit_failure` (boolean, 可选): 部分字段更新失败时是否继续执行；默认值：`false`

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      {
        "id": "E",
        "name": "优先级",
        "type": "SingleSelect",
        "items": [
          { "id": "B", "value": "低" },
          { "id": "H", "value": "中" },
          { "id": "D", "value": "高" }
        ]
      }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields` | array | 更新后的字段列表 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 确认目标字段存在及当前属性

---

## 3. dbsheet.delete_fields

#### 功能说明

批量删除数据表中的指定字段。

#### 调用示例

删除多个字段：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "fields": [
    {
      "id": "C"
    },
    {
      "id": "D"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `fields` (array, 必填): 要删除的字段列表，每项包含 `id`

#### 返回值说明

```json
{
  "detail": {
    "fields": [
      { "id": "C", "deleted": true },
      { "id": "D", "deleted": true }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.fields` | array | 删除结果列表，每项包含 `id` 和 `deleted` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_schema 核对拟删字段的名称和类型
- **用户确认**：删除字段不可恢复，字段数据将永久丢失，必须向用户确认字段列表
- **禁止**：未经用户在对话中明确同意，禁止调用

---


# 记录操作

## 1. dbsheet.create_records

#### 功能说明

在指定数据表中批量创建记录，通过字段名称或字段 ID 指定各字段的值。


#### 调用示例

批量创建记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "fields": {
        "名称": "任务A",
        "数量": 10,
        "状态": "待处理"
      }
    },
    {
      "fields": {
        "名称": "任务B",
        "数量": 20
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要创建的记录列表，每项包含 `fields` 对象（字段名→值映射）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key，默认 `false`（使用字段名）
- `value_prefer_id` (boolean, 可选): 字段值是否使用 ID 表示
- `omit_failure` (boolean, 可选): 部分记录创建失败时是否继续；默认值：`false`
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项；默认值：`true`

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "T", "fields": { "名称": "任务A", "数量": 10, "状态": "待处理" } },
      { "id": "U", "fields": { "名称": "任务B", "数量": 20 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records[].id` | string | 新建记录 ID |
| `detail.records[].fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


#### 操作约束

- **后置验证**：list_records 确认记录已创建

---

## 2. dbsheet.update_records

#### 功能说明

批量更新数据表中已有记录的字段值，每条记录必须提供记录 ID。

#### 调用示例

批量更新记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "id": "B",
      "fields": {
        "名称": "更新后的名称",
        "状态": "已完成"
      }
    },
    {
      "id": "C",
      "fields": {
        "数量": 999
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要更新的记录列表，每项必须包含 `id`（记录 ID）和 `fields`（字段值映射）
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `value_prefer_id` (boolean, 可选): 字段值是否使用 ID 表示
- `omit_failure` (boolean, 可选): 部分记录更新失败时是否继续；默认值：`false`
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `add_select_item` (boolean, 可选): 是否自动新增不存在的选项

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "B", "fields": { "名称": "更新后的名称", "状态": "已完成" } },
      { "id": "C", "fields": { "数量": 999 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records` | array | 更新后的记录列表，每项包含 `id` 和 `fields` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：get_record 或 list_records 确认目标记录存在及当前值
- **后置验证**：get_record 确认更新结果

---

## 3. dbsheet.list_records

#### 功能说明

分页遍历数据表中的记录，支持按视图过滤、指定返回字段，以及通过 `filter` 参数实现复杂查询条件（多字段 AND/OR 组合筛选）。


#### 调用示例

基础分页查询：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "page_size": 100,
  "offset": "",
  "fields": [
    "名称",
    "状态",
    "截止日期"
  ]
}
```

带筛选条件查询：

```json
{
  "file_id": "string",
  "sheet_id": 1,
  "page_size": 100,
  "offset": "",
  "filter": {
    "mode": "AND",
    "criteria": [
      {
        "field": "状态",
        "op": "Intersected",
        "values": [
          "进行中"
        ]
      },
      {
        "field": "数量",
        "op": "Greater",
        "values": [
          "10"
        ]
      },
      {
        "field": "名称",
        "op": "Contains",
        "values": [
          "关键词"
        ]
      }
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `page_size` (integer, 可选): 每页记录数
- `offset` (string, 可选): 翻页游标，首次请求传空字符串，后续传响应中的 `offset` 值
- `view_id` (string, 可选): 按指定视图返回记录
- `max_records` (integer, 可选): 最多返回的记录总数
- `fields` (array, 可选): 只返回指定字段列表，不填则返回所有字段
- `filter` (object, 可选): 筛选条件
  - `mode` (string, 必填): 条件连接方式：`"AND"` 或 `"OR"`
  - `criteria` (array, 必填): 筛选条件列表
    - `field` (string, 必填): 字段名称或 ID
    - `op` (string, 必填): 筛选操作符（见附录：筛选规则）
    - `values` (array, 可选): 筛选值，`Empty`/`NotEmpty` 时可省略
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `show_record_extra_info` (boolean, 可选): 是否返回记录额外信息
- `show_fields_info` (boolean, 可选): 是否在响应中返回字段定义信息

> **分页说明**：响应中的 `offset` 指向下一页第一条记录，下次请求将该值传入 `offset` 即可翻页。最后一页不再返回 `offset`。


#### 返回值说明

```json
{
  "detail": {
    "offset": "D",
    "records": [
      { "id": "E", "fields": { "名称": "任务A", "状态": "进行中", "数量": 15 } },
      { "id": "F", "fields": { "名称": "任务B", "状态": "进行中", "数量": 20 } }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.offset` | string | 下一页游标，无更多数据时不返回此字段 |
| `detail.records[].id` | string | 记录 ID |
| `detail.records[].fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


---

## 4. dbsheet.get_record

#### 功能说明

获取数据表中某条指定记录的完整字段内容。

#### 调用示例

获取单条记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "record_id": "B"
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `record_id` (string, 必填): 记录 ID
- `prefer_id` (boolean, 可选): 是否使用字段 ID 作为 key
- `text_value` (string, 可选): 文本值格式：`"original"`（原始值）或 `"display"`（显示值）
- `link_value` (string, 可选): 关联字段值格式：`"id"` 或 `"value"`
- `show_record_extra_info` (boolean, 可选): 是否返回记录额外信息
- `show_fields_info` (boolean, 可选): 是否返回字段定义信息

#### 返回值说明

```json
{
  "detail": {
    "id": "B",
    "fields": {
      "名称": "任务A",
      "数量": 123,
      "日期": "2021/5/1",
      "状态": "未开始"
    }
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.id` | string | 记录 ID |
| `detail.fields` | object | 各字段的值 |
| `result` | string | ok 表示成功 |


---

## 5. dbsheet.delete_records

#### 功能说明

批量删除数据表中的指定记录。

#### 调用示例

批量删除记录：

```json
{
  "file_id": "string",
  "sheet_id": 3,
  "records": [
    {
      "id": "B"
    },
    {
      "id": "C"
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 多维表格文件 ID
- `sheet_id` (integer, 必填): 目标数据表 ID
- `records` (array, 必填): 要删除的记录列表，每项包含 `id`
- `mode` (string, 可选): 删除模式，`"include"` 表示删除指定记录
- `is_batch` (boolean, 可选): 是否批量操作模式

#### 返回值说明

```json
{
  "detail": {
    "records": [
      { "id": "B", "deleted": true },
      { "id": "C", "deleted": true }
    ]
  },
  "result": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `detail.records` | array | 删除结果列表，每项包含 `id` 和 `deleted` |
| `result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：list_records 或 get_record 核对拟删记录内容
- **用户确认**：批量删除记录不可恢复，必须向用户确认记录列表和数量
- **禁止**：未经用户在对话中明确同意，禁止调用

---


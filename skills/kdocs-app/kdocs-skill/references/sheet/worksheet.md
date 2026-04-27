# 工作表管理

## 1. sheet.get_sheets_info

#### 功能说明

获取指定表格文件的所有工作表信息，包含每个工作表的名称、索引、数据区域范围等。


#### 调用示例

获取工作表信息：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID

#### 返回值说明

```json
{
  "sheetsInfo": [
    {
      "isEmpty": false,
      "colFrom": 0,
      "colTo": 5,
      "isVisible": true,
      "maxCol": 16383,
      "maxRow": 1048575,
      "rowFrom": 0,
      "rowTo": 50,
      "sheetId": 3,
      "sheetIdx": 0,
      "sheetName": "Sheet1",
      "sheetType": "et"
    }
  ]
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheetsInfo[].sheetId` | integer | 工作表 ID |
| `sheetsInfo[].sheetIdx` | integer | 工作表索引 |
| `sheetsInfo[].sheetName` | string | 工作表名称 |
| `sheetsInfo[].sheetType` | string | 工作表类型（见下表） |
| `sheetsInfo[].isEmpty` | boolean | 是否为空 |
| `sheetsInfo[].isVisible` | boolean | 是否可见 |
| `sheetsInfo[].maxRow` | integer | 最大行数（工作表总容量） |
| `sheetsInfo[].maxCol` | integer | 最大列数 |
| `sheetsInfo[].rowFrom` | integer | 数据区域起始行 |
| `sheetsInfo[].rowTo` | integer | 数据区域结束行（比 `maxRow` 更有参考价值） |
| `sheetsInfo[].colFrom` | integer | 数据区域起始列 |
| `sheetsInfo[].colTo` | integer | 数据区域结束列 |

**sheetType 工作表类型：**

| sheetType | 说明 |
|-----------|------|
| `et` | 普通电子表格 |
| `db` | 数据表 |
| `airApp` | 应用表 |
| `oldDb` | 旧的数据表 |
| `dbDashBoard` | 数据表的仪表盘 |
| `etDashBoard` | 普通表格的仪表盘 |
| `workbench` | 工作台 |

> rowTo/colTo 比 maxRow/maxCol 更有参考价值，表示实际数据区域

---

## 2. sheet.add_sheet

#### 功能说明

在指定表格文件中新增工作表。可指定名称、数量、插入位置和默认列宽。


#### 调用示例

在末尾新增工作表：

```json
{
  "file_id": "string",
  "name": "销售数据",
  "end": true
}
```

在指定工作表前插入：

```json
{
  "file_id": "string",
  "name": "新工作表",
  "before": {
    "sheetId": 3
  },
  "count": 1,
  "defColWidth": 1335
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `name` (string, 可选): 工作表名称
- `count` (integer, 可选): 新增数量；默认值：`1`
- `before` (object, 可选): 在指定工作表之前插入，格式 `{"sheetId": <id>}`。与 `after`、`end` 三选一
- `after` (object, 可选): 在指定工作表之后插入，格式 `{"sheetId": <id>}`。与 `before`、`end` 三选一
- `end` (boolean, 可选): 在末尾插入。与 `before`、`after` 三选一
- `defColWidth` (integer, 可选): 默认列宽（单位：缇，1 pixel ≈ 15 twip）

#### 返回值说明

```json
{
  "sheetId": 4
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheetId` | integer | 新建的工作表 ID |


---


# 数据操作

## 1. sheet.get_range_data

#### 功能说明

获取指定工作表中某个矩形区域内的单元格数据。行列索引均为 0-based。


#### 调用示例

读取 A1:F11 区域：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "range": {
    "rowFrom": 0,
    "rowTo": 10,
    "colFrom": 0,
    "colTo": 5
  }
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `sheetId` (integer, 必填): 工作表 ID
- `range` (object, 必填): 查询范围
  - `rowFrom` (integer, 必填): 起始行（0-based）
  - `rowTo` (integer, 必填): 结束行
  - `colFrom` (integer, 必填): 起始列（0-based）
  - `colTo` (integer, 必填): 结束列

#### 返回值说明

```json
{
  "rangeData": [
    {
      "cellText": "广州",
      "originalCellValue": "广州",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "numFormat": "G/通用格式",
      "isCellPic": false,
      "fmlaText": ""
    }
  ]
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `rangeData[].cellText` | string | 单元格显示文本 |
| `rangeData[].originalCellValue` | string | 原始值 |
| `rangeData[].rowFrom` | integer | 起始行 |
| `rangeData[].rowTo` | integer | 结束行 |
| `rangeData[].colFrom` | integer | 起始列 |
| `rangeData[].colTo` | integer | 结束列 |
| `rangeData[].numFormat` | string | 数字格式 |
| `rangeData[].isCellPic` | boolean | 是否为图片 |
| `rangeData[].fmlaText` | string | 公式文本 |


---

## 2. sheet.update_range_data

#### 功能说明

批量更新单元格选区数据，支持写值/公式、设置格式、合并单元格、写入图片。每项操作必须包含 `rowFrom`、`rowTo`、`colFrom`、`colTo`。


#### 调用示例

写入值：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "formula",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "formula": "Hello"
    }
  ]
}
```

设置格式：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "format",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "xf": {
        "font": {
          "name": "微软雅黑",
          "dyHeight": 220,
          "bls": true,
          "color": {
            "type": 2,
            "value": 16777215
          }
        },
        "alcH": 2,
        "alcV": 1,
        "wrap": true
      }
    }
  ]
}
```

合并单元格：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "merge",
      "rowFrom": 2,
      "rowTo": 3,
      "colFrom": 0,
      "colTo": 3,
      "type": "MergeCenter"
    }
  ]
}
```

写入图片：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "picture",
      "rowFrom": 0,
      "colFrom": 1,
      "cellPicInfo": {
        "tag": "url",
        "url": "https://example.com/image.png"
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `sheetId` (integer, 必填): 工作表 ID
- `rangeData` (array[object], 必填): 操作列表，每项必须包含 `opType` 和坐标字段，详见下方 rangeData 字段表

**rangeData 每项字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `opType` | string | 是 | 操作类型（见下表） |
| `rowFrom` | integer | 是 | 起始行（0-based） |
| `rowTo` | integer | 是 | 结束行 |
| `colFrom` | integer | 是 | 起始列（0-based） |
| `colTo` | integer | 是 | 结束列 |
| `formula` | string | 否 | 值或公式（`formula` 类型时使用） |
| `xf` | object | 否 | 格式对象（`format` 类型时使用） |
| `type` | string | 否 | 合并类型（`merge` 类型时使用） |
| `cellPicInfo` | object | 否 | 图片信息（`picture` 类型时使用） |

**opType 操作类型：**

| opType | 说明 | 需要的字段 |
|--------|------|-----------|
| `formula` | 写值/公式 | `formula` |
| `format` | 设置格式 | `xf` |
| `merge` | 合并单元格 | `type` |
| `picture` | 写入图片 | `cellPicInfo` |

**merge type 合并类型：**`MergeCenter`（居中合并）/ `MergeAcross`（跨越合并）/ `MergeCells`（合并单元格）

**cellPicInfo 图片信息：**

```json
{
  "tag": "url",
  "url": "https://example.com/image.png"
}
```

**xf 格式对象：**

```json
{
  "font": {
    "name": "微软雅黑",
    "dyHeight": 220,
    "charSet": 134,
    "bls": false,
    "italic": false,
    "strikeout": false,
    "uls": 0,
    "sss": 0,
    "themeFont": 2,
    "color": {"type": 2, "value": 16777215}
  },
  "wrap": false,
  "shrinkToFit": false,
  "locked": true,
  "hidden": false,
  "alcH": 0,
  "alcV": 1,
  "indent": 0,
  "readingOrder": 0,
  "trot": 0,
  "dgLeft": 0,
  "dgRight": 0,
  "dgTop": 0,
  "dgBottom": 0,
  "numfmt": "G/通用格式",
  "fill": {
    "type": 1,
    "back": {"type": 2, "value": 4294967040},
    "fore": {"type": 255}
  }
}
```

- `alcH`：水平对齐（1=左, 2=居中, 3=右, 4=填充, 5=两端, 6=跨列, 7=分散）
- `alcV`：垂直对齐（0=上, 1=中, 2=下, 3=两端, 4=分散）
- `dgLeft/dgRight/dgTop/dgBottom`：边框线型（0=无, 1=细线, 2=中等, 3=虚线, 4=点线, 5=粗线, 6=双线, 7=细虚线）

**颜色 color 参数：**

| type | 说明 |
|------|------|
| `0` | ICV 颜色模式 |
| `1` | THEME 颜色主题 |
| `2` | ARGB 颜色模式 |
| `254` | 无颜色（用于背景） |
| `255` | 自动颜色（用于前景，如字体和边框） |


#### 返回值说明

```json
{}

```


#### 操作约束

- **前置检查**：get_range_data 读取目标区域现有数据，确认覆盖范围
- **提示**：每项必须包含 rowFrom/rowTo/colFrom/colTo 四个坐标

---


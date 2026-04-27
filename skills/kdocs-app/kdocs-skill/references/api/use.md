# 四、用文档

## 1. read_file_content

#### 功能说明

文档内容抽取。支持将文档内容抽取为 markdown、纯文本或 KDC 结构化格式。**仅支持异步模式（mode=async）**：首次调用传入 `drive_id`、`file_id` 等，返回 `task_id`；通过 `task_id` 轮询直至 `task_status` 为 `success` 后获取内容。

> ⚠️ **不支持 .csv 格式**，遇到 CSV 文件请勿调用本工具，建议用户转为 .xlsx 后用 `sheet.*` 读取。

> ⚠️ **以下类型不以 `read_file_content` 作为结构化读写主路径**：
>
> - **Excel（.xlsx）与智能表格（.ksheet）**：使用 **`sheet.*`**。**获取内容**：`sheet.get_sheets_info` → `sheet.get_range_data`（矩形区域）。完整工具列表与参数见 `sheet_references.md`。
> - **多维表格（.dbt）**：使用 **`dbsheet.*`**。**获取结构**：`dbsheet.get_schema`；**获取内容**：`dbsheet.list_records`、`dbsheet.get_record`；完整工具列表与参数见 `dbsheet_reference.md`。

> ⚠️ **智能文档（.otl）**：`read_file_content` 对 otl 存在内容遗漏风险（部分组件类型可能丢失），日常读取应优先使用 `otl.block_query`。仅在需要导出 Markdown 格式时使用本工具，并**务必**按照 reference/otl_references.md 的参数要求调用。


#### 调用示例

读取文档为 Markdown：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "format": "markdown",
  "include_elements": [
    "para",
    "table"
  ],
  "mode": "async",
  "task_id": "string"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件 ID
- `format` (string, 可选): 文档内容目标格式。可选值：`kdc`（结构化表示）/ `plain`（纯文本）/ `markdown`
- `include_elements` (array, 可选): 指定抽取元素。默认元素为 `para`（段落），且一定会被导出；其余附加元素根据参数选择性导出。可选值：`para` / `table` / `component` / `textbox` / `all`
- `mode` (string, 可选): **仅支持 `async`**，无需传或固定传 `async`
- `task_id` (string, 可选): 异步任务 ID，用于结果轮询；首次调用不传，后续用返回的 `task_id` 查询直至 `task_status` 为 `success`

#### 返回值说明

```json
{
  "data": {
    "task_id": "string",
    "task_status": "success",
    "dst_format": "markdown",
    "markdown": "string",
    "plain": "string",
    "src_format": "otl",
    "version": "string",
    "doc": {}
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.task_id` | string | 任务 ID，异步模式下返回 |
| `data.task_status` | string | 任务状态。可选值：`success` / `running` / `failed` |
| `data.dst_format` | string | 目标格式：`kdc` / `plain` / `markdown` |
| `data.markdown` | string | markdown 内容数据，目标格式为 `markdown` 时适用 |
| `data.plain` | string | 纯文本内容数据，目标格式为 `plain` 时适用 |
| `data.doc` | object | 文字类的结构化数据，源格式为 otl/pdf/docx 且目标格式为 `kdc` 时适用 |
| `data.src_format` | string | 源格式（otl, docx, pdf, xlsx 等） |
| `data.version` | string | 版本号 |

> 首次调用返回 `task_id`，需轮询 `task_status` 直至 `success`
> 不支持 .csv 格式，禁止对 CSV 文件调用本工具
> 避免重复提交：同一 `file_id + format + include_elements` 在已有 `running` 任务时，优先继续使用原 `task_id` 轮询

---

## 2. search_files

#### 功能说明

支持按文件名、内容全文搜索，可按时间、创建者、文件类型等条件过滤。

#### 调用示例

搜索文档：

```json
{
  "keyword": "区域周报告",
  "type": "all",
  "file_type": "file",
  "parent_ids": [
    "string"
  ],
  "page_size": 20,
  "order": "desc",
  "order_by": "mtime",
  "with_total": true
}
```


#### 参数说明

- `keyword` (string, 可选): 搜索关键字
- `type` (string, 必填): 搜索类型。可选值：`file_name`表示搜索文件名，`content`表示搜索文件内容，`all`表示全局搜索。
- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 翻页 token
- `file_type` (string, 可选): 文件类型筛选。可选值：`folder` / `file`
- `file_exts` (array, 可选): 文件后缀过滤
- `drive_ids` (array, 可选): 搜索盘列表
- `parent_ids` (array, 可选): 搜索目录列表
- `creator_ids` (array, 可选): 创建者 ID。公网只支持选择是否自己创建的文件
- `modifier_ids` (array, 可选): 编辑者 ID
- `sharer_ids` (array, 可选): 分享者 ID
- `receiver_ids` (array, 可选): 接收者 ID
- `time_type` (string, 可选): 时间范围类型。可选值：`ctime` / `mtime` / `otime` / `stime`
- `start_time` (integer, 可选): 最小时间
- `end_time` (integer, 可选): 最大时间
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_link` (boolean, 可选): 是否返回文件分享信息
- `with_total` (boolean, 可选): 是否返回搜索到的总条数
- `with_drive` (boolean, 可选): 是否返回驱动盘
- `order` (string, 可选): 排序方式。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段。可选值：`ctime` / `mtime`
- `scope` (array, 可选): 搜索范围。可选值：`all` / `share_by_me` / `share_to_me` / `latest` / `personal_drive` / `group_drive` / `recycle` / `customize` / `latest_opened` / `latest_edited`
- `channels` (array, 可选): 渠道信息
- `device_ids` (array, 可选): 设备 ID
- `exclude_channels` (array, 可选): 排除渠道信息
- `exclude_file_exts` (array, 可选): 排除文件后缀
- `filter_user_id` (integer, 可选): 创建者分享者过滤
- `file_ext_groups` (array, 可选): 文件分组后缀
- `search_operator_name` (boolean, 可选): 搜索文件的创建者或文件分享者

#### 返回值说明

```json
{
  "data": {
    "items": [
      {
        "file": {
          "created_by": {
            "avatar": "string",
            "company_id": "string",
            "id": "string",
            "name": "string",
            "type": "user"
          },
          "ctime": 0,
          "drive_id": "string",
          "ext_attrs": [
            { "name": "string", "value": "string" }
          ],
          "id": "string",
          "link_id": "string",
          "link_url": "string",
          "modified_by": {
            "avatar": "string",
            "company_id": "string",
            "id": "string",
            "name": "string",
            "type": "user"
          },
          "mtime": 0,
          "name": "string",
          "parent_id": "string",
          "shared": true,
          "size": 0,
          "type": "folder",
          "version": 0
        },
        "file_src": {
          "name": "string",
          "path": "string",
          "type": "link"
        },
        "highlights": {
          "example_key": ["string"]
        },
        "otime": 0
      }
    ],
    "next_page_token": "string",
    "total": 0
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 搜索结果列表 |
| `data.items[].file` | object | 文件信息，通用文件信息结构（附录 A） |
| `data.items[].file_src` | object | 文件位置信息 |
| `data.items[].file_src.name` | string | 来源名称 |
| `data.items[].file_src.path` | string | 文件路径 |
| `data.items[].file_src.type` | string | 来源类型：`link` / `user_private` / `user_roaming` / `group_normal` / `group_dept` / `group_whole` |
| `data.items[].highlights` | map[string][]string | 匹配关键字 |
| `data.items[].otime` | integer | 文件打开时间 |
| `data.next_page_token` | string | 下一页 token |
| `data.total` | integer | 资源集合总数（仅 `with_total=true` 时返回） |

> 新建文件后搜索可能无法立即命中，需等待索引更新

---

## 3. get_file_link

#### 功能说明

获取文件的在线访问链接。

#### 调用示例

获取文件链接：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 文件 ID

#### 返回值说明

```json
{
  "file_id": "string",
  "file_url": "https://kdocs.cn/l/xxxxx",
  "name": "Q1销售报告"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 文件 ID |
| `file_url` | string | 在线访问链接 |
| `name` | string | 文件名 |


---


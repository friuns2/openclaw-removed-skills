# 多维表格（dbt）工具完整参考文档

本文件包含金山文档 Skill 多维表格的操作说明。

---

## 一、数据表管理

### 1. dbsheet.get_schema — 获取文档结构（表/字段/视图）
> 详见 [dbsheet.get_schema 完整参考](dbsheet/data_table.md)

### 2. dbsheet.create_sheet — 创建数据表
> 详见 [dbsheet.create_sheet 完整参考](dbsheet/data_table.md)

### 3. dbsheet.update_sheet — 修改数据表名称
> 详见 [dbsheet.update_sheet 完整参考](dbsheet/data_table.md)

### 4. dbsheet.delete_sheet — 删除数据表
> 详见 [dbsheet.delete_sheet 完整参考](dbsheet/data_table.md)

## 二、视图管理

### 5. dbsheet.create_view — 创建视图
> 详见 [dbsheet.create_view 完整参考](dbsheet/view.md)

### 6. dbsheet.update_view — 更新视图配置
> 详见 [dbsheet.update_view 完整参考](dbsheet/view.md)

### 7. dbsheet.delete_view — 删除视图
> 详见 [dbsheet.delete_view 完整参考](dbsheet/view.md)

## 三、字段管理

### 8. dbsheet.create_fields — 批量创建字段
> 详见 [dbsheet.create_fields 完整参考](dbsheet/field.md)

### 9. dbsheet.update_fields — 批量更新字段
> 详见 [dbsheet.update_fields 完整参考](dbsheet/field.md)

### 10. dbsheet.delete_fields — 批量删除字段
> 详见 [dbsheet.delete_fields 完整参考](dbsheet/field.md)

## 四、记录操作

### 11. dbsheet.create_records — 批量创建记录
> 详见 [dbsheet.create_records 完整参考](dbsheet/record.md)

### 12. dbsheet.update_records — 批量更新记录
> 详见 [dbsheet.update_records 完整参考](dbsheet/record.md)

### 13. dbsheet.list_records — 分页遍历记录（支持筛选）
> 详见 [dbsheet.list_records 完整参考](dbsheet/record.md)

### 14. dbsheet.get_record — 获取单条记录
> 详见 [dbsheet.get_record 完整参考](dbsheet/record.md)

### 15. dbsheet.delete_records — 批量删除记录
> 详见 [dbsheet.delete_records 完整参考](dbsheet/record.md)

## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `dbsheet.get_schema` | 数据表管理 | 获取文档结构（表/字段/视图） | `file_id` |
| 2 | `dbsheet.create_sheet` | 数据表管理 | 创建数据表 | `file_id`, `name` |
| 3 | `dbsheet.update_sheet` | 数据表管理 | 修改数据表名称 | `file_id`, `sheet_id` |
| 4 | `dbsheet.delete_sheet` | 数据表管理 | 删除数据表 | `file_id`, `sheet_id` |
| 5 | `dbsheet.create_view` | 视图管理 | 创建视图 | `file_id`, `sheet_id`, `name`, `type` |
| 6 | `dbsheet.update_view` | 视图管理 | 更新视图配置 | `file_id`, `sheet_id`, `view_id` |
| 7 | `dbsheet.delete_view` | 视图管理 | 删除视图 | `file_id`, `sheet_id`, `view_id` |
| 8 | `dbsheet.create_fields` | 字段管理 | 批量创建字段 | `file_id`, `sheet_id`, `fields` |
| 9 | `dbsheet.update_fields` | 字段管理 | 批量更新字段 | `file_id`, `sheet_id`, `fields` |
| 10 | `dbsheet.delete_fields` | 字段管理 | 批量删除字段 | `file_id`, `sheet_id`, `fields` |
| 11 | `dbsheet.create_records` | 记录操作 | 批量创建记录 | `file_id`, `sheet_id`, `records` |
| 12 | `dbsheet.update_records` | 记录操作 | 批量更新记录 | `file_id`, `sheet_id`, `records` |
| 13 | `dbsheet.list_records` | 记录操作 | 分页遍历记录（支持筛选） | `file_id`, `sheet_id` |
| 14 | `dbsheet.get_record` | 记录操作 | 获取单条记录 | `file_id`, `sheet_id`, `record_id` |
| 15 | `dbsheet.delete_records` | 记录操作 | 批量删除记录 | `file_id`, `sheet_id`, `records` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 多维表格读结构/数据 | `dbsheet.get_schema` → `dbsheet.list_records` / `dbsheet.get_record` |
| 多维表格增删改 | `dbsheet.get_schema` → `dbsheet.create_records` / `dbsheet.update_records` / `dbsheet.delete_records`|

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| 多维表格读不到结构化数据 | 误用 `read_file_content` 作主读 | 改用 `dbsheet.get_schema`、`dbsheet.list_records` 等，见 `references/dbsheet_reference.md` |

---

## 附录

### 字段类型

| 类型 | 说明 |
|------|------|
| `SingleLineText` | 单行文本 |
| `MultiLineText` | 多行文本 |
| `Number` | 数值 |
| `Currency` | 货币 |
| `Percentage` | 百分比 |
| `Date` | 日期 |
| `Time` | 时间 |
| `Checkbox` | 复选框 |
| `SingleSelect` | 单选项 |
| `MultipleSelect` | 多选项 |
| `Rating` | 等级 |
| `Complete` | 进度条 |
| `Phone` | 电话 |
| `Email` | 电子邮箱 |
| `Url` | 超链接 |
| `Contact` | 联系人 |
| `Attachment` | 附件 |
| `Link` | 关联 |
| `Note` | 富文本 |
| `Address` | 地址 |
| `AutoNumber` | 编号（自动填充） |
| `CreatedBy` | 创建者（自动填充） |
| `CreatedTime` | 创建时间（自动填充） |
| `LastModifiedBy` | 最后修改者（自动填充） |
| `LastModifiedTime` | 最后修改时间（自动填充） |
| `Formula` | 公式（自动计算） |
| `Lookup` | 引用（自动计算） |

### 视图类型

| 类型 | 说明 |
|------|------|
| `Grid` | 表格视图 |
| `Kanban` | 看板视图 |
| `Gallery` | 画册视图 |
| `Form` | 表单视图 |
| `Gantt` | 甘特视图 |
| `Calendar` | 日历视图 |

### 筛选规则（filter op）

| 操作符 | 适用字段类型 | 说明 |
|--------|-------------|------|
| `Equals` | 通用 | 等于 |
| `NotEqu` | 通用 | 不等于 |
| `Greater` | 数值、日期 | 大于 |
| `GreaterEqu` | 数值、日期 | 大于等于 |
| `Less` | 数值、日期 | 小于 |
| `LessEqu` | 数值、日期 | 小于等于 |
| `BeginWith` | 文本 | 开头是 |
| `EndWith` | 文本 | 结尾是 |
| `Contains` | 文本 | 包含 |
| `NotContains` | 文本 | 不包含 |
| `Intersected` | 单选、多选 | 选项包含指定值 |
| `Empty` | 通用 | 为空（`values` 可省略） |
| `NotEmpty` | 通用 | 不为空（`values` 可省略） |

### 错误响应

| 情况 | 响应示例 |
|------|---------|
| 命令不支持 | `{"msg":"core not support","result":"unSupport"}` |
| 内核错误 | `{"errno":-1880935404,"msg":"Invalid request","result":"ExecuteFailed"}` |
| HTTP 状态非 200 | 请求本身失败，检查 `file_id` 是否正确及鉴权信息 |

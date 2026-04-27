# 表格文档/智能表格（xlsx & ksheet）工具完整参考文档

本文件包含金山文档 Skill 中表格相关工具的完整 API 说明、详细调用示例、参数说明和返回值说明。

**适用范围**：本文档中的所有 `sheet.*` 工具同时适用于 Excel（.xlsx）和智能表格（.ksheet）。

---

### 表格工具概述

表格工具专门用于操作金山文档中的在线表格，提供工作表信息的查询、范围数据的获取以及批量更新等功能。支持两种表格类型：

- **Excel（.xlsx）**：传统在线表格
- **智能表格（.ksheet）**：高级结构化表格

### 创建表格文件

#### 创建 Excel 文件

通过 `create_file` 创建，`name` 须带 `.xlsx` 后缀，`file_type` 设为 `file`：

```json
{
  "name": "销售数据表.xlsx",
  "file_type": "file",
  "parent_id": "folder_abc123"
}
```

#### 创建智能表格

通过 `create_file` 创建，`name` 须带 `.ksheet` 后缀，`file_type` 设为 `file`：

```json
{
  "name": "项目任务跟踪表.ksheet",
  "file_type": "file",
  "parent_id": "folder_abc123"
}
```

### Excel vs 智能表格（ksheet）对比

| 特性 | Excel | 智能表格 ksheet |
|------|-------|----------------|
| 数据组织 | 传统行列表格 | 结构化字段+记录 |
| 视图 | 单一表格视图 | 多视图（表格/看板/日历/甘特图等） |
| 字段类型 | 通用单元格 | 丰富字段类型（单选/多选/日期/附件/关联等） |
| 适用场景 | 数据计算、报表、财务报表 | 项目管理、CRM、任务跟踪、库存管理 |
| 工作表/数据接口 | 使用 `sheet.*` 工具 | **同样使用 `sheet.*` 工具** |

### 使用场景

#### Excel 适用场景

| 场景 | 说明 |
|------|------|
| 数据记录 | 销售数据、财务报表 |
| 数据分析 | 结构化数据的读取与处理 |
| 报表汇总 | 多维度数据汇总 |
| 公式计算 | 需要复杂公式和数据透视 |

#### 智能表格 适用场景

| 场景 | 说明 |
|------|------|
| 项目管理 | 任务分配、进度跟踪 |
| CRM 管理 | 客户信息、跟进记录 |
| 资产管理 | 库存台账、设备管理 |
| 审批台账 | 合同风险排查台账等 |

### 类型选择建议

- 需要公式计算、数据透视 → 选 **Excel**
- 需要多视图、字段管理、看板展示 → 选 **ksheet**
- 需要做任务管理/项目跟踪 → 选 **ksheet**
- 需要做财务报表 → 选 **Excel**

> **注意**：无论是 Excel 还是 ksheet，工作表管理和数据操作都使用相同的 `sheet.*` 接口。只需将对应的文件 ID 传入即可。

---

## 一、工作表管理

### 1. sheet.get_sheets_info — 获取工作表列表
> 详见 [sheet.get_sheets_info 完整参考](sheet/worksheet.md)

### 2. sheet.add_sheet — 新增工作表
> 详见 [sheet.add_sheet 完整参考](sheet/worksheet.md)

## 二、数据操作

### 3. sheet.get_range_data — 获取选区数据
> 详见 [sheet.get_range_data 完整参考](sheet/data.md)

### 4. sheet.update_range_data — 批量更新选区数据
> 详见 [sheet.update_range_data 完整参考](sheet/data.md)

## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `sheet.get_sheets_info` | 工作表管理 | 获取工作表列表 | `file_id` |
| 2 | `sheet.add_sheet` | 工作表管理 | 新增工作表 | `file_id` |
| 3 | `sheet.get_range_data` | 数据操作 | 获取选区数据 | `file_id`, `sheetId`, `range` |
| 4 | `sheet.update_range_data` | 数据操作 | 批量更新选区数据 | `file_id`, `sheetId`, `rangeData` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 读表格（矩形区域） | `sheet.get_sheets_info` → `sheet.get_range_data` |
| 写表格（批量改单元格） | `sheet.get_range_data`（可选对照）→ `sheet.update_range_data` → `sheet.get_range_data` 验证 |

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| 表格读不到或结构不明 | 未先取工作表列表 / 区域错误 | 先 `sheet.get_sheets_info`，再 `sheet.get_range_data` |

---

## 附录

### 错误响应

| 情况 | 响应示例 |
|------|---------|
| 命令不支持 | `{"msg":"core not support","result":"unSupport"}` |
| 内核错误 | `{"errno":-1880935404,"msg":"Invalid request","result":"ExecuteFailed"}` |
| HTTP 状态非 200 | 请求本身失败，检查鉴权信息（Cookie/Origin） |

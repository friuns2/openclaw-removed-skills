---
name: sql-splitter
description: 拆分 SQL 文件为独立文件（存储过程、函数、视图、触发器、表结构、索引、约束），自动分析依赖并生成合并脚本
---

# SQL 文件拆分工具 v2.2

将包含多个 SQL 对象的单一文件或目录拆分为独立的 .sql 文件，
并自动分析对象间依赖关系，生成按依赖排序的合并脚本。

## v2.2 新功能

- **GUI 界面** - 提供图形化界面进行 SQL 文件拆分操作
- **断点续传** - 支持记录处理进度，中断后可以继续处理
- **批量并行处理** - 支持同时处理多个 SQL 文件，提升处理速度
- **结果预览和对比** - 可视化查看拆分结果，支持与原始文件对比
- **配置文件管理** - 保存和加载常用配置，支持导入导出

## v2.1 新功能

- **进度条显示** - 实时显示拆分进度（支持 tqdm）
- **详细错误处理** - 结构化错误信息，包含错误类型、上下文和修复建议
- **Dry-run 预览模式** - 预览拆分结果而不实际创建文件

## v2.0 重写要点

## 支持的 SQL 方言

- MySQL
- PostgreSQL
- Oracle
- SQL Server
- 达梦 (DM)
- 通用 (Generic)

## 支持的 SQL 对象类型

| 类型 | 前缀 | 说明 |
|------|------|------|
| 存储过程 | `proc_` | CREATE PROCEDURE |
| 函数 | `func_` | CREATE FUNCTION |
| 视图 | `view_` | CREATE VIEW |
| 触发器 | `trig_` | CREATE TRIGGER |
| 表结构 | `table_` | CREATE TABLE |
| 包 | `pkg_` | CREATE PACKAGE |
| 索引 | `idx_` | CREATE INDEX |
| 唯一索引 | `uidx_` | CREATE UNIQUE INDEX |
| 约束 | `con_` | ALTER TABLE ADD CONSTRAINT |
| 序列 | `seq_` | CREATE SEQUENCE |
| 同义词 | `syn_` | CREATE SYNONYM (Oracle) |
| 事件 | `evt_` | CREATE EVENT (MySQL) |
| 物化视图 | `mv_` | CREATE MATERIALIZED VIEW (PostgreSQL) |
| 类型 | `type_` | CREATE TYPE |

## v2.0 核心改进

### 边界检测重写
- 使用 **BEGIN...END 深度匹配**确定存储过程/函数/触发器边界
- 支持 IF...THEN...END IF、CASE...END CASE、LOOP...END LOOP 嵌套
- 不再依赖"下一个 CREATE 位置"做上界，**正确处理过程体内的嵌套 CREATE 语句**
- Oracle/DM: 通过 `/` 终止符定位；SQL Server: 通过 `GO` 定位
- PostgreSQL: 支持 `$$...$$` 包裹语法
- 字符串和注释内的分号/关键字不会干扰边界检测

### 依赖分析改进
- 函数调用检测改为**限定上下文模式**（:= 赋值、WHERE/HAVING 子句等），大幅减少误报
- SQL 关键字过滤表扩展到 150+ 个，涵盖内置函数、控制流、聚合等
- 自引用自动排除
- 循环依赖不再报错，按类型优先级追加

### 合并脚本方言适配
- Oracle/DM: `@@filename` + `SET DEFINE OFF`
- SQL Server: `:r filename` + `GO`
- PostgreSQL: `\i filename` + `ON_ERROR_STOP`
- MySQL: `source filename`
- 通用: 注释方式

### 架构优化
- 提取 `common.py` 共享模块：SQLDialect 枚举、对象前缀、类型优先级、关键字表
- `dependency_analyzer.py` 不再重复定义枚举，直接引用 common
- 拆分后自动调用依赖分析，生成 `merge_all.sql`
- 新增 37 个单元测试

## 使用方法

### GUI 模式（推荐）
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/gui.py
```

### 单文件拆分
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py <input.sql> [output_dir]
```

### 批量拆分（目录）
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch <目录路径> [输出目录]
```

### 批量拆分（多个文件）
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch "file1.sql,file2.sql,file3.sql" [输出目录]
```

### 指定方言
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --dialect oracle input.sql
```

支持的方言：`mysql`, `postgresql`, `oracle`, `sqlserver`, `dm`, `generic`

### 不生成合并脚本
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --no-merge input.sql
```

### 预览结果
```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --preview input.sql output_dir
```

### 检查点管理
```bash
# 列出所有检查点
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --list

# 查看恢复进度
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --resume input.sql

# 清理旧检查点
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --clear --days 7

# 删除检查点
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --delete input.sql
```

### 配置管理
```bash
# 列出所有配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --list

# 保存配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --save --name oracle --dialect oracle

# 加载配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --load --name oracle

# 导出配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --export --name oracle --export-path oracle_config.json

# 导入配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --import --import-path oracle_config.json --name oracle
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `input.sql` | 要拆分的 SQL 文件路径（单文件模式必需） |
| `--batch` | 批量模式标志 |
| `--dialect` | 指定 SQL 方言 |
| `--no-merge` | 不生成依赖排序的合并脚本 |
| `-q`, `--quiet` | 静默模式 |
| `output_dir` | 输出目录（可选，默认：原文件名_split） |

### 运行测试
```bash
cd ~/.openclaw/skills/sql-splitter/scripts
python3 -m unittest test_sql_splitter -v
```

## 输出示例

假设输入文件 `myapp.sql` 包含：
- 表 `users`
- 视图 `v_users`（依赖 users）
- 存储过程 `sp_update`（依赖 users）

输出：
```
myapp_split/
├── table_users.sql
├── view_v_users.sql
├── proc_sp_update.sql
└── merge_all.sql          ← 按依赖排序的合并脚本
```

`merge_all.sql` 内容（以 Oracle 为例）：
```sql
-- [1/3] table: users
@@table_users.sql

-- [2/3] view: v_users  -- depends on: users
@@view_v_users.sql

-- [3/3] procedure: sp_update  -- depends on: users
@@proc_sp_update.sql
```

## 文件结构

```
sql-splitter/
├── SKILL.md                       ← 本文档
├── V21_USAGE_GUIDE.md            ← v2.1 使用指南
└── scripts/
    ├── common.py                  ← 共享模块（枚举、常量、工具函数）
    ├── split_sql.py               ← v2.0 主拆分脚本
    ├── split_sql_v21.py           ← v2.1 主拆分脚本（带错误处理）
    ├── split_sql_v22.py           ← v2.2 主拆分脚本（集成所有新功能）
    ├── dependency_analyzer.py     ← 依赖分析器
    ├── error_handler.py           ← 错误处理模块
    ├── gui.py                     ← GUI 界面
    ├── checkpoint.py              ← 断点续传模块
    ├── batch_processor.py         ← 批量并行处理模块
    ├── result_previewer.py        ← 结果预览和对比模块
    ├── config_manager.py          ← 配置文件管理模块
    ├── test_sql_splitter.py       ← 单元测试（37个）
    └── test_v21_features.py       ← v2.1 功能测试
```

## 注意事项

- 使用正则+深度匹配识别 SQL 对象边界，对极复杂嵌套语法可能有局限
- 默认 UTF-8 编码，遇到编码问题自动 replace
- 建议先备份原文件
- 批量模式会自动创建以原文件名命名的子目录
- 自动检测 SQL 方言，也可手动指定
- 同名文件自动追加序号（如 `proc_sp_init_2.sql`）

## 常见问题

### 拆分结果不正确（多个对象混在一个文件中）

**症状**：拆分后生成的文件包含多个 SQL 对象，而不是每个对象一个文件。

**原因**：原始 SQL 文件中的对象缺少分号结束符。sql-splitter 依赖分号来确定对象的结束位置。

**解决方案**：为每个 SQL 语句添加分号。例如：

```sql
-- 错误：缺少分号
Create table a(
  Id int,
  Name varchar(10)
)

Create table b(
  Id int,
  Name varchar(10)
)

-- 正确：添加分号
Create table a(
  Id int,
  Name varchar(10)
);

Create table b(
  Id int,
  Name varchar(10)
);
```

**快速修复方法**：
```bash
# 使用 sed 为每个 CREATE 语句后的空行添加分号
sed -i '' '/^Create /,/^)/s/)$/);/' input.sql
```

### 视图未被识别

**症状**：拆分后没有生成视图文件，或视图被识别为其他对象类型。

**原因**：视图语法不规范，缺少 `AS` 关键字。

**解决方案**：修正视图语法，添加 `AS` 关键字。例如：

```sql
-- 错误：缺少 AS
create view v_a
(
select * from dual
);

-- 正确：添加 AS
CREATE VIEW v_a AS
SELECT * FROM dual;
```

### 存储过程/函数未被正确拆分

**症状**：多个存储过程混在一个文件中，或产生重复文件。

**原因**：存储过程语法不规范，缺少 `AS`/`BEGIN` 关键字或分隔符。

**解决方案**：根据数据库类型修正语法：

**SQL Server**：
```sql
-- 错误：缺少 AS 和 GO
create proc p_a
(
select * from dual
);
create proc p_b
(
select * from dual
);

-- 正确：添加 AS 和 GO
CREATE PROCEDURE p_a
AS
BEGIN
    SELECT * FROM dual;
END
GO

CREATE PROCEDURE p_b
AS
BEGIN
    SELECT * FROM dual;
END
GO
```

**Oracle/达梦**：
```sql
-- 错误：缺少 IS/AS 和 /
CREATE PROCEDURE p_a
BEGIN
    SELECT * FROM dual;
END

-- 正确：添加 IS/AS 和 /
CREATE OR REPLACE PROCEDURE p_a IS
BEGIN
    SELECT * FROM dual;
END;
/
```

**MySQL**：
```sql
-- 错误：缺少 DELIMITER
CREATE PROCEDURE p_a()
BEGIN
    SELECT * FROM dual;
END

-- 正确：使用 DELIMITER
DELIMITER //
CREATE PROCEDURE p_a()
BEGIN
    SELECT * FROM dual;
END //
DELIMITER ;
```

### 产生重复文件

**症状**：拆分后生成多个内容相同或相似的文件（如 `proc_p_a.sql` 和 `proc_p_a_2.sql`）。

**原因**：对象边界检测失败，通常由以下原因导致：
- 对象之间缺少分隔符（分号、GO、/ 等）
- 对象语法不规范（缺少 AS、BEGIN 等）
- 嵌套对象语法错误

**解决方案**：
1. 检查并修正原始 SQL 文件的语法
2. 确保每个对象之间有正确的分隔符
3. 使用 `--dialect` 参数明确指定数据库类型
4. 对于复杂情况，考虑手动拆分或使用数据库工具导出

### 预检查清单

在运行 sql-splitter 之前，建议检查以下内容：

- [ ] 每个 SQL 语句都有分号结束符
- [ ] 视图包含 `AS` 关键字
- [ ] 存储过程/函数包含 `AS`/`BEGIN` 关键字
- [ ] SQL Server 对象之间有 `GO` 分隔符
- [ ] Oracle/达梦 对象末尾有 `/` 终止符
- [ ] MySQL 存储过程使用 `DELIMITER`
- [ ] 对象名称没有特殊字符或保留字冲突
- [ ] 文件编码为 UTF-8

## 更新日志

### v2.2.0 (2026-04-27)
- **新增 GUI 界面** - 提供图形化界面进行 SQL 文件拆分操作
  - 支持文件浏览、参数配置、进度显示
  - 实时输出日志和错误信息
  - 配置自动保存和加载
- **新增断点续传功能** - 支持记录处理进度，中断后可以继续处理
  - 自动保存处理进度到检查点文件
  - 支持查看恢复进度和状态
  - 支持清理旧检查点
- **新增批量并行处理** - 支持同时处理多个 SQL 文件，提升处理速度
  - 可配置最大并发数
  - 支持目录批量处理
  - 支持进度回调
- **新增结果预览和对比** - 可视化查看拆分结果，支持与原始文件对比
  - 生成详细的文件统计信息
  - 支持表格化显示
  - 支持与原始文件内容对比
- **新增配置文件管理** - 保存和加载常用配置，支持导入导出
  - 支持多配置管理
  - 支持 JSON/YAML 格式导入导出
  - 配置验证功能

### v2.0.2 (2026-04-24)
- **修复重复文件问题**：添加去重逻辑，避免同一对象被多个正则表达式重复匹配
  - 去重标准：相同起始位置、对象类型、对象名称
  - 解决 SQL Server 存储过程产生重复文件的问题
  - 新增去重功能测试用例

### v2.0.1 (2026-04-24)
- 文档更新：新增常见问题章节
  - 视图未被识别的解决方案（缺少 AS 关键字）
  - 存储过程/函数未被正确拆分的解决方案（缺少 AS/BEGIN/分隔符）
  - 产生重复文件的原因和解决方案
  - 预检查清单（运行前检查项）

### v2.0.0 (2026-04-19)
- 重写对象边界检测：BEGIN/END/IF/CASE/LOOP 深度匹配
- 不再依赖"下一个 CREATE"作为上界，修复嵌套 CREATE 截断问题
- 提取 common.py 共享模块，消除枚举重复定义
- 依赖分析器：限定上下文检测、扩展关键字过滤、自引用排除
- 合并脚本按方言适配（Oracle/SQL Server/PostgreSQL/MySQL/DM）
- 拆分后自动生成 merge_all.sql
- 新增 37 个单元测试
- SQL Server 正则修复：方括号标识符匹配

### v1.1.0 (2026-04-13)
- 新增索引支持：CREATE INDEX, CREATE UNIQUE INDEX
- 新增约束支持：ALTER TABLE ADD CONSTRAINT
- 所有 6 种方言均支持索引/约束识别
- 支持 CLUSTERED/NONCLUSTERED (SQL Server)
- 支持 BITMAP 索引 (Oracle/达梦)

### v1.0.0
- 初始版本

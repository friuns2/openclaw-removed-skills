# SQL 拆分工具 v2.2 使用指南

## 新功能概览

v2.2 版本在 v2.1 基础上增加了五个重要的新功能：

1. **GUI 界面** - 提供图形化界面进行 SQL 文件拆分操作
2. **断点续传** - 支持记录处理进度，中断后可以继续处理
3. **批量并行处理** - 支持同时处理多个 SQL 文件，提升处理速度
4. **结果预览和对比** - 可视化查看拆分结果，支持与原始文件对比
5. **配置文件管理** - 保存和加载常用配置，支持导入导出

## 安装依赖

```bash
# GUI 需要 tkinter（Python 标准库，通常已安装）
# 批量处理需要 concurrent.futures（Python 标准库）
# 配置管理需要 yaml（可选，用于 YAML 格式支持）
pip install pyyaml
```

## 使用方法

### 1. GUI 模式（推荐）

启动 GUI 界面：

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/gui.py
```

GUI 界面功能：

- **文件选择**：点击"浏览..."按钮选择输入文件和输出目录
- **方言选择**：选择 SQL 方言（auto/mysql/postgresql/oracle/sqlserver/dm/generic）
- **选项配置**：
  - 预览模式：不实际创建文件，只预览结果
  - 不生成合并脚本：跳过 merge_all.sql 生成
  - 显示进度条：显示处理进度
  - 详细输出：显示详细日志
- **操作按钮**：
  - 开始拆分：开始处理
  - 停止：中断处理
  - 清空输出：清空日志区域
  - 保存配置：保存当前配置
- **进度显示**：实时显示处理进度百分比
- **输出区域**：显示处理日志和错误信息

### 2. 断点续传

#### 列出所有检查点

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --list
```

输出示例：
```
检查点列表:
  /test/input.sql: 50/100 (in_progress)
  /test/schema.sql: 100/100 (completed)
```

#### 查看恢复进度

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --resume input.sql
```

输出示例：
```
恢复进度: 50.0%
可以恢复: True
状态: in_progress
```

#### 清理旧检查点

```bash
# 清理 7 天前的检查点
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --clear --days 7
```

#### 删除检查点

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --checkpoint --delete input.sql
```

### 3. 批量并行处理

#### 处理单个文件

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch input.sql output_dir
```

#### 处理整个目录

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch --directory input_dir output_dir
```

#### 指定文件模式

```bash
# 只处理 .sql 文件
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch --directory input_dir output_dir --pattern "*.sql"

# 只处理以 test_ 开头的文件
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch --directory input_dir output_dir --pattern "test_*.sql"
```

#### 配置并发数

```bash
# 使用 8 个并发线程
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch input_dir output_dir --max-workers 8
```

#### 禁用断点续传

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --batch input_dir output_dir --no-checkpoint
```

### 4. 结果预览和对比

#### 基本预览

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --preview input.sql output_dir
```

输出示例：
```
================================================================================
SQL 拆分结果预览
================================================================================
原始文件: input.sql
输出目录: output_dir
拆分文件数: 3
总大小: 15.23 KB

统计信息:
  procedure: 1
  function: 1
  view: 1

文件列表:
--------------------------------------------------------------------------------
文件: proc_test_proc1.sql
  大小: 5.12 KB
  行数: 150
  类型: procedure
  名称: test_proc1

文件: func_test_func1.sql
  大小: 4.56 KB
  行数: 120
  类型: function
  名称: test_func1

文件: view_test_view1.sql
  大小: 5.55 KB
  行数: 130
  类型: view
  名称: test_view1

================================================================================
```

#### 表格化显示

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --preview input.sql output_dir --table
```

输出示例：
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    SQL 拆分结果摘要                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│ 原始文件: input.sql                                                          │
│ 输出目录: output_dir                                                          │
│ 拆分文件数: 3                                                                │
│ 总大小: 15.23 KB                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ 统计信息:                                                                    │
│   function: 1                                                               │
│   procedure: 1                                                              │
│   view: 1                                                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ 文件列表:                                                                    │
│   func_test_func1.sql              4.56 KB          120 行                │
│   proc_test_proc1.sql              5.12 KB          150 行                │
│   view_test_view1.sql              5.55 KB          130 行                │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### 与原始文件对比

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --preview input.sql output_dir --compare
```

### 5. 配置文件管理

#### 列出所有配置

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --list
```

输出示例：
```
配置列表:
  default: auto
  oracle: oracle
  mysql: mysql
```

#### 保存配置

```bash
# 保存为默认配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --save

# 保存为指定名称的配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --save --name oracle --dialect oracle --output-dir /test/output
```

#### 加载配置

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --load --name oracle
```

输出示例：
```
配置: oracle
  方言: oracle
  输出目录: /test/output
  最大并发: 4
  使用检查点: True
```

#### 导出配置

```bash
# 导出为 JSON 格式
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --export --name oracle --export-path oracle_config.json

# 导出为 YAML 格式
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --export --name oracle --export-path oracle_config.yaml --format yaml
```

#### 导入配置

```bash
# 从 JSON 文件导入
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --import --import-path oracle_config.json --name oracle

# 从 YAML 文件导入
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --import --import-path oracle_config.yaml --name oracle
```

#### 删除配置

```bash
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py --config --delete --name oracle
```

## Python API 使用

### GUI 模式

```python
from gui import SQLSplitterGUI
import tkinter as tk

root = tk.Tk()
app = SQLSplitterGUI(root)
root.mainloop()
```

### 断点续传

```python
from checkpoint import CheckpointManager, CheckpointData

manager = CheckpointManager()

# 创建检查点
checkpoint = manager.create_checkpoint(
    input_file="/test/input.sql",
    output_dir="/test/output",
    dialect="oracle",
    total_objects=100
)

# 更新检查点
checkpoint = manager.update_checkpoint(checkpoint, processed_file="proc_test.sql")

# 保存检查点
manager.save_checkpoint(checkpoint)

# 加载检查点
loaded_checkpoint = manager.load_checkpoint("/test/input.sql")

# 获取恢复进度
resume_info = manager.get_resume_progress("/test/input.sql")
if resume_info:
    print(f"恢复进度: {resume_info['progress']:.1%}")
```

### 批量并行处理

```python
from batch_processor import BatchProcessor, SQLDialect

processor = BatchProcessor(max_workers=4)

# 设置进度回调
def progress_callback(completed, total, message):
    print(f"[{completed}/{total}] {message}")

processor.set_progress_callback(progress_callback)

# 处理目录
result = processor.process_directory(
    input_dir="/test/input",
    output_base_dir="/test/output",
    pattern="*.sql",
    dialect=SQLDialect.ORACLE,
    options={
        'verbose': True,
        'dry_run': False,
        'show_progress': True,
        'no_merge': False
    }
)

print(result.get_summary())
```

### 结果预览

```python
from result_previewer import ResultPreviewer

previewer = ResultPreviewer()

# 预览结果
preview = previewer.preview_split_result(
    original_file="/test/input.sql",
    output_dir="/test/output"
)

# 格式化输出
print(previewer.format_preview(preview))

# 表格化输出
print(previewer.generate_summary_table(preview))

# 与原始文件对比
diff = previewer.compare_with_original("/test/input.sql", "/test/output")
print(diff)
```

### 配置管理

```python
from config_manager import ConfigManager, SplitConfig

manager = ConfigManager()

# 创建配置
config = SplitConfig(
    dialect="oracle",
    output_dir="/test/output",
    max_workers=8,
    use_checkpoint=True
)

# 保存配置
manager.save_config(config, "oracle")

# 加载配置
loaded_config = manager.load_config("oracle")

# 列出所有配置
configs = manager.list_configs()
for cfg in configs:
    print(f"{cfg['name']}: {cfg['dialect']}")

# 导出配置
manager.export_config("oracle", "oracle_config.json", "json")

# 导入配置
manager.import_config("oracle_config.json", "oracle_imported")
```

## 实际应用场景

### 场景 1: 使用 GUI 处理单个文件

```bash
# 启动 GUI
python3 ~/.openclaw/skills/sql-splitter/scripts/gui.py

# 在 GUI 中：
# 1. 点击"浏览..."选择输入文件
# 2. 点击"浏览..."选择输出目录
# 3. 选择 SQL 方言
# 4. 配置选项（如需要）
# 5. 点击"开始拆分"
# 6. 查看输出日志
# 7. 点击"保存配置"保存当前配置
```

### 场景 2: 批量处理大型项目

```bash
# 使用 8 个并发线程处理整个目录
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --batch \
  --directory /project/sql_files \
  /project/output \
  --max-workers 8 \
  --dialect oracle
```

### 场景 3: 断点续传处理大文件

```bash
# 第一次处理（可能中断）
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  large_file.sql \
  output_dir \
  --dialect oracle

# 查看恢复进度
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --checkpoint --resume large_file.sql

# 继续处理（会自动从检查点恢复）
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  large_file.sql \
  output_dir \
  --dialect oracle
```

### 场景 4: 预览和验证结果

```bash
# 先预览结果
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --preview \
  input.sql \
  output_dir \
  --table

# 与原始文件对比
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --preview \
  input.sql \
  output_dir \
  --compare

# 确认无误后实际拆分
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  input.sql \
  output_dir
```

### 场景 5: 使用配置文件

```bash
# 保存常用配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --config --save \
  --name oracle \
  --dialect oracle \
  --output-dir /project/oracle_output \
  --max-workers 8

# 在其他机器上导入配置
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  --config --import \
  --import-path oracle_config.json \
  --name oracle

# 使用配置处理文件
python3 ~/.openclaw/skills/sql-splitter/scripts/split_sql_v22.py \
  input.sql \
  output_dir \
  --dialect oracle
```

## 性能优化建议

1. **大文件处理**：使用断点续传功能，避免中断后重新处理
2. **批量处理**：使用批量并行处理，设置合适的并发数（建议 4-8）
3. **预览模式**：使用预览模式先验证结果，避免不必要的文件操作
4. **配置管理**：保存常用配置，避免重复输入参数
5. **GUI 模式**：对于不熟悉命令行的用户，使用 GUI 模式更友好

## 常见问题

### Q: GUI 模式需要安装额外依赖吗？

A: 不需要。GUI 使用 tkinter，这是 Python 标准库的一部分，通常已经安装。

### Q: 断点续传会占用大量磁盘空间吗？

A: 不会。检查点文件很小，只包含处理进度信息，不包含实际文件内容。

### Q: 批量并行处理会影响结果正确性吗？

A: 不会。每个文件的处理是独立的，并行处理不会影响结果正确性。

### Q: 配置文件支持哪些格式？

A: 支持 JSON 和 YAML 两种格式。JSON 是默认格式，YAML 需要安装 pyyaml。

### Q: 如何在代码中使用这些新功能？

A: 所有新功能都提供了 Python API，可以直接导入使用。参考上面的 Python API 使用章节。

## 总结

v2.2 版本通过 GUI 界面、断点续传、批量并行处理、结果预览和配置管理，显著提升了用户体验：

- **GUI 界面**：让不熟悉命令行的用户也能轻松使用
- **断点续传**：处理大文件时不怕中断，可以随时恢复
- **批量并行处理**：提升处理速度，适合大型项目
- **结果预览**：可视化查看结果，便于验证
- **配置管理**：保存常用配置，提高工作效率

这些优化使得 SQL 拆分工具更加专业、易用和高效。

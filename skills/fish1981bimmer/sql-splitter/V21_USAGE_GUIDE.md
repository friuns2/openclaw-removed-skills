# SQL 拆分工具 v2.1 使用指南

## 新功能概览

v2.1 版本在 v2.0 基础上增加了三个重要的用户体验优化：

1. **进度条显示** - 实时显示拆分进度
2. **详细错误处理** - 提供错误类型、上下文和修复建议
3. **Dry-run 预览模式** - 在不实际生成文件的情况下预览拆分结果

## 安装依赖

```bash
# 安装 tqdm（进度条支持，可选）
pip install tqdm
```

## 使用方法

### 基本用法

```bash
# 基本拆分（自动检测方言）
python3 split_sql_v21.py input.sql output_dir

# 指定方言
python3 split_sql_v21.py input.sql output_dir --dialect oracle

# 静默模式
python3 split_sql_v21.py input.sql output_dir -q
```

### 新功能使用

#### 1. 进度条显示

默认启用进度条（如果安装了 tqdm）：

```bash
python3 split_sql_v21.py large_file.sql output_dir
```

输出示例：
```
[detect] 方言: ORACLE
[scan] 找到 150 个对象
拆分对象: 100%|██████████| 150/150 [00:02<00:00, 75.23个/s]
  [ok] proc_user_login.sql
  [ok] func_get_balance.sql
  ...
```

禁用进度条：

```bash
python3 split_sql_v21.py large_file.sql output_dir --no-progress
```

#### 2. Dry-run 预览模式

预览拆分结果，不实际生成文件：

```bash
python3 split_sql_v21.py input.sql output_dir --dry-run
```

输出示例：
```
[detect] 方言: ORACLE
[dry-run] 预览模式：将输出到 output_dir
[scan] 找到 3 个对象
  [dry-run] [ok] proc_test_proc1.sql
  [dry-run] [ok] func_test_func1.sql
  [dry-run] [ok] view_test_view1.sql

[done] 共拆分 3 个对象
[统计]
  procedure: 1
  function: 1
  view: 1
[dry-run] 预览模式完成，未实际生成文件
```

#### 3. 详细错误处理

当遇到错误时，会显示详细的错误信息和修复建议：

```bash
python3 split_sql_v21.py invalid.sql output_dir
```

错误输出示例：
```
[error] 错误信息:
  - [file_read_error] 无法读取文件 invalid.sql
    建议: 检查文件是否存在且有读取权限
```

## Python API 使用

### 基本用法

```python
from split_sql_v21 import split_sql_file, SQLDialect

# 基本拆分
result = split_sql_file('input.sql', 'output_dir')

# 检查结果
if result.success:
    print(f"成功拆分 {result.total} 个对象")
    for obj_type, count in result.stats.items():
        print(f"  {obj_type}: {count}")
else:
    print("拆分失败:")
    for error in result.errors:
        print(f"  - {error.message}")
        if error.suggestion:
            print(f"    建议: {error.suggestion}")
```

### 使用新功能

```python
from split_sql_v21 import split_sql_file, SQLDialect

# Dry-run 模式
result = split_sql_file(
    'input.sql',
    'output_dir',
    dialect=SQLDialect.ORACLE,
    verbose=True,
    dry_run=True,  # 预览模式
    show_progress=True,  # 显示进度条
)

# 检查结果
print(f"预览结果: {result.total} 个对象")
print(f"将创建的文件: {result.files_created}")

# 禁用进度条
result = split_sql_file(
    'input.sql',
    'output_dir',
    show_progress=False,  # 不显示进度条
)
```

### 错误处理示例

```python
from split_sql_v21 import split_sql_file
from error_handler import SplitError, ErrorType

result = split_sql_file('input.sql', 'output_dir')

if not result.success:
    print("拆分过程中遇到错误:")
    for error in result.errors:
        if isinstance(error, SplitError):
            print(f"错误类型: {error.error_type.value}")
            print(f"错误消息: {error.message}")
            if error.line_num:
                print(f"位置: 行 {error.line_num}")
            if error.context:
                print(f"上下文: {error.context}")
            if error.suggestion:
                print(f"修复建议: {error.suggestion}")
```

## 返回结果结构

`SplitResult` 对象包含以下字段：

```python
@dataclass
class SplitResult:
    success: bool              # 是否成功
    output_dir: str           # 输出目录
    files_created: List[str]  # 创建的文件列表
    errors: List[SplitError]  # 错误列表
    warnings: List[SplitWarning]  # 警告列表
    stats: Dict[str, int]     # 统计信息
    total: int                # 总文件数
    merge_script: str         # 合并脚本路径
    dry_run: bool             # 是否为预览模式
```

## 错误类型

`ErrorType` 枚举包含以下错误类型：

- `FILE_READ_ERROR` - 文件读取错误
- `FILE_WRITE_ERROR` - 文件写入错误
- `SYNTAX_ERROR` - SQL 语法错误
- `MISSING_SEMICOLON` - 缺少分号
- `MISSING_KEYWORD` - 缺少关键字
- `DEPENDENCY_ERROR` - 依赖错误
- `BOUNDARY_DETECTION_ERROR` - 边界检测错误
- `UNKNOWN_ERROR` - 未知错误

## 实际应用场景

### 场景 1: 大型 SQL 文件拆分

```bash
# 拆分大型文件，显示进度
python3 split_sql_v21.py large_schema.sql split_output --dialect oracle
```

### 场景 2: 预览拆分结果

```bash
# 先预览，确认无误后再实际拆分
python3 split_sql_v21.py schema.sql output --dry-run

# 确认无误后，实际执行
python3 split_sql_v21.py schema.sql output
```

### 场景 3: CI/CD 集成

```python
import sys
from split_sql_v21 import split_sql_file

result = split_sql_file(
    'schema.sql',
    'split_output',
    verbose=False,
    show_progress=False,
)

if not result.success:
    print("拆分失败:", file=sys.stderr)
    for error in result.errors:
        print(f"  {error.message}", file=sys.stderr)
    sys.exit(1)

print(f"成功拆分 {result.total} 个文件")
```

### 场景 4: 错误诊断

```python
from split_sql_v21 import split_sql_file

result = split_sql_file('problematic.sql', 'output')

if result.errors:
    print("发现以下问题:")
    for error in result.errors:
        print(f"\n错误: {error.message}")
        if error.suggestion:
            print(f"建议: {error.suggestion}")
        if error.line_num:
            print(f"位置: 第 {error.line_num} 行")
```

## 性能优化建议

1. **大文件处理**: 使用 `--no-progress` 禁用进度条可以略微提升性能
2. **批量处理**: 使用 `--batch` 参数处理多个文件
3. **预览模式**: 使用 `--dry-run` 先预览结果，避免不必要的文件操作

## 兼容性说明

- v2.1 完全兼容 v2.0 的所有功能
- 新参数都是可选的，默认行为与 v2.0 一致
- 如果未安装 tqdm，进度条会自动降级为简单文本显示

## 常见问题

### Q: tqdm 未安装会影响使用吗？
A: 不会。程序会自动检测，如果 tqdm 不可用，会使用简单的文本显示。

### Q: dry-run 模式会创建任何文件吗？
A: 不会。dry-run 模式只分析 SQL 文件并返回预览结果，不会创建任何文件或目录。

### Q: 如何在代码中判断是否为 dry-run 模式？
A: 检查 `result.dry_run` 字段：
```python
if result.dry_run:
    print("这是预览模式，未实际创建文件")
```

### Q: 错误信息中的 suggestion 字段一定有值吗？
A: 不一定。某些错误可能没有具体的修复建议，此时 `suggestion` 为 `None`。

## 总结

v2.1 版本通过进度条、详细错误处理和 dry-run 模式，显著提升了用户体验：

- **进度条**: 让用户了解处理进度，特别是处理大文件时
- **错误处理**: 提供清晰的错误信息和修复建议，便于问题诊断
- **Dry-run**: 安全预览，避免误操作，提高工作效率

这些优化使得 SQL 拆分工具更加专业和易用。
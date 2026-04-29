---
name: cn-pdf-assistant
version: "1.2.0"
description: "PDF文档处理工具。本地处理PDF文件，支持文本提取、智能摘要、表格导出、关键词问答、PDF拆分。纯本地处理，保护文档隐私。"
metadata:
  openclaw:
    emoji: "📄"
    category: productivity
    tags:
      - pdf
      - document
      - extract
---

## 功能
- PDF文本提取（支持指定页码范围）
- 智能摘要生成（章节标题识别+关键词频率分析）
- 表格提取（pdfplumber引擎）
- 关键词问答（基于段落匹配）
- PDF按页拆分
- 纯本地处理，无需联网

## 使用方法
```
python3 scripts/pdf_assistant.py <PDF文件路径> --action text
python3 scripts/pdf_assistant.py <PDF文件路径> --action summary
python3 scripts/pdf_assistant.py <PDF文件路径> --action tables
python3 scripts/pdf_assistant.py <PDF文件路径> --action ask --question "关键词"
python3 scripts/pdf_assistant.py <PDF文件路径> --action split
```

## 依赖
- Python 3.7+
- PyPDF2, pdfplumber, pandas, openpyxl

## 权限声明
- 读取本地PDF文件
- 生成输出文件

## 使用场景
- 论文阅读：快速提取核心内容
- 合同审查：提取关键条款
- 财报分析：提取表格数据
- 资料整理：批量拆分PDF文档

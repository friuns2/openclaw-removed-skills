---
name: cn-readability-extractor
description: "网页内容提取器。输入URL，提取正文内容，去除广告和导航。"
metadata: {"openclaw": {"emoji": "📄"}}
---

# 网页内容提取器

输入URL，提取干净正文。

## 功能
- 从URL提取正文
- 去除广告、导航、脚本
- 提取标题和描述
- 中英文支持

## 用法
```bash
python3 scripts/readability.py https://example.com
```

## 依赖
- Python 3.7+
- requests, certifi

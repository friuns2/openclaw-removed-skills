---
name: cn-web-clipper
description: "网页剪藏工具。发送网页链接，提取正文内容保存为本地Markdown文件。"
metadata:
  openclaw:
    emoji: "📎"
---

# 网页剪藏

发送网页链接，提取正文保存为Markdown。

## 功能
- 网页正文提取
- 本地Markdown保存
- 标题/作者/日期识别
- 批量URL处理

## 用法
```bash
python3 scripts/clip_webpage.py <URL>
python3 scripts/clip_webpage.py <URL> --dir <保存目录>
```

## 依赖
- Python 3.7+
- requests, beautifulsoup4

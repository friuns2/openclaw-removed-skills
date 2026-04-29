---
name: cn-meeting-minutes
version: "1.2.0"
description: "会议纪要生成工具。输入会议录音文件，自动生成结构化纪要文档，包含关键讨论点、决策结论、待办事项，输出Markdown格式。"
metadata:
  openclaw:
    emoji: "📝"
    category: productivity
    tags:
      - meeting
      - minutes
      - transcription
---

## 功能
- 结构化纪要生成（主题+讨论点+决策+待办）
- 关键词密度分析提取讨论点
- 正则匹配提取待办事项（责任人+截止日期）
- 正则匹配提取决策结论
- Markdown格式输出
- 支持MP3/WAV/M4A音频格式

## 使用方法
```
python3 scripts/meeting_minutes.py <音频文件路径> -o <输出文件>
```

## 依赖
- Python 3.7+
- requests

## 权限声明
- 读取本地音频文件
- 生成Markdown纪要文件

## 使用场景
- 周会/站会纪要整理
- 客户会议记录与跟进
- 培训课程内容整理
- 面试/调研录音文字化

---
name: daily-movie
description: "Daily movie & TV recommendation — curated by genre, mood, or theme. One great watch per day with synopsis, streaming platform, and audience ratings."
keywords:
  - 今天看什么
  - 电影推荐
  - 看什么电影
  - 剧推荐
  - 今晚看什么
  - 每日电影
  - 电影
  - 剧集
  - 好看的电影
  - 值得看的剧
  - 豆瓣高分
  - IMDb
  - Netflix
  - 爱奇艺
  - 优酷
  - 腾讯视频
  - 剧情片
  - 喜剧
  - 悬疑
  - 爱情片
  - 动作片
  - 科幻
  - 纪录片
  - 动画
  - 韩剧
  - 美剧
  - 日剧
  - 国产剧
  - 经典电影
  - 新片推荐
  - movie recommendation
  - what to watch
  - film of the day
  - Netflix recommendation
  - series recommendation
  - best movies
  - top rated
  - must watch
  - TV show
  - binge watch
metadata:
  openclaw:
    runtime:
      node: ">=18"
---

# 每日影视推荐

> 每日影视推荐 — 今日精选 · 评分推荐 · 观影指南 · 中英双语

## 何时使用

- 用户说"今晚看什么""电影推荐""推荐部电影"
- 用户说"what to watch""movie recommendation"
- 用户说"好看的剧""最近有什么新片"
- 用户说"Netflix推荐""豆瓣高分""IMDb top"

---

## 推送管理

```bash
node scripts/push-toggle.js on <userId>
node scripts/push-toggle.js on <userId> --morning 10:00 --evening 19:00 --channel feishu
node scripts/push-toggle.js off <userId>
node scripts/push-toggle.js status <userId>
```

支持渠道：`telegram` / `feishu` / `slack` / `discord`

# AI 慧记 — 使用场景与触发条件

## 场景一：查询会议列表

- **触发**："帮我查一下最近的慧记"、"我的会议记录列表"、"最近有什么会议"
- **接口**：chatListByPage
- **语义分流**：用户未提供会议号 → 走归属维度列表
- **示例**：
  ```bash
  python3 scripts/huiji/chat-list-by-page.py 0 10
  ```

## 场景二：按会议号查询

- **触发**："会议号 xxx 的纪要"、"这场会议的慧记"（用户提供了会议号）
- **接口**：listHuiJiIdsByMeetingNumberV2
- **语义分流**：用户提供了会议号 → 走会议维度查询
- **示例**：
  ```bash
  python3 scripts/huiji/list-by-meeting-number.py MTG-20260327-001
  ```

## 场景三：获取会议原文

- **触发**："这个会议说了什么"、"会议内容"、"转写原文"
- **策略**：统一通过 `get-transcript.py` 入口，脚本自动处理：
  - **进行中**：有缓存则 splitRecordListV2 增量拉取，无缓存则 splitRecordList 全量
  - **已结束**：先 checkSecondSttV2 改写原文，失败则 splitRecordList 兜底
- **示例**：
  ```bash
  python3 scripts/huiji/get-transcript.py <meetingChatId>
  ```

## 场景四：AI 分析（基于原文）

拿到原文后，AI 根据用户意图进行分析：

### 📝 会议总结
- **触发**："总结一下"、"会议纪要"、"概要"
- **能力**：生成结构化纪要（主题、要点、决策、遗留问题）

### ✅ 待办提取
- **触发**："有什么待办"、"谁负责什么"、"跟进事项"
- **能力**：从原文中提取待办事项、责任人、截止时间

### 🔍 专题分析
- **触发**："关于 xxx 讨论了什么"、"财务那块说了什么"
- **能力**：按主题定位相关讨论内容并提取

## 场景五：搜索会议

- **触发**："帮我找 xxx 的会议"、"搜索 xxx"
- **接口**：chatListByPage + nameBlur
- **示例**：
  ```bash
  python3 scripts/huiji/chat-list-by-page.py --body '{"pageNum":0,"pageSize":10,"nameBlur":"周会"}'
  ```

## 场景六：解析分享链接并获取原文

- **触发**："帮我看下这个慧记分享链接"、"这个分享里说了什么"
- **接口**：getChatFromShareId
- **说明**：短链/长链/shareId 统一传给脚本，由脚本内部自动解析
- **示例**：
  ```bash
  python3 scripts/huiji/get-chat-from-share-id.py f12505e3-3ecb-47f1-87e4-277b2b1a243e
  python3 scripts/huiji/get-chat-from-share-id.py --body '{"shareId":"f12505e3-3ecb-47f1-87e4-277b2b1a243e"}'
  ```

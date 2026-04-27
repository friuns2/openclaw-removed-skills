# POST /ai-huiji/meetingChat/checkSecondSttV2

## 作用

查询已结束会议的改写原文处理状态。会议结束后服务端会对会中转写做大模型二次改写，成功时内容通常比分片原文更准确，且可能包含发言人等维度。

**仅用于已结束会议**。进行中会议不要调用此接口。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meetingChatId` | String | 是 | 慧记 ID |

## 响应参数

| 字段 | 类型 | 说明 |
|---|---|---|
| `totalProgress` | Integer | 总进度（0-100） |
| `state` | Integer | 状态：1=处理中, 2=成功, 3=失败 |
| `sttPartList` | List | 改写转写分片列表（成功且有内容时作为原文首选来源） |
| `errMsg` | String | 失败时的错误信息 |

## 状态处理策略

| state | 含义 | 处理方式 |
|---|---|---|
| `2` | 成功 | 优先使用 `sttPartList` 作为原文（最优） |
| `1` | 处理中 | 提示改写中，用缓存或 splitRecordList 分片兜底 |
| `3` | 失败 | fallback 到 splitRecordList 全量兜底 |

## ⚠️ 容错规则

- **刚结束的会议**：改写可能尚未开始，checkSecondSttV2 可能返回空或 state=1。此时 **splitRecordList 是唯一来源**，不可因 checkSecondSttV2 无数据而报错
- **sttPartList 为空**：即使 state=2，若 `sttPartList` 为空或无法解析，仍 fallback 到 splitRecordList
- **永远不向用户报错**：checkSecondSttV2 失败时静默切换到 splitRecordList

## 请求示例

```bash
python3 scripts/huiji/check-second-stt-v2.py abc123

python3 scripts/huiji/check-second-stt-v2.py --body '{"meetingChatId":"abc123"}'
```

## 脚本映射

- `../../scripts/huiji/check-second-stt-v2.py`

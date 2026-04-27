# POST /ai-huiji/meetingChat/splitRecordList

## 作用

全量查询指定慧记的分片转写原文。每个分片包含该时段的转写文本，按 startTime 排序拼接即为连续的完整原文。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meetingChatId` | String | 是 | 慧记 ID（来自 chatListByPage 的 `_id` 或 listHuiJiIdsByMeetingNumberV2 的 `_id`） |

## 响应参数

`data` 类型为 `List<SplitRecordVO>`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `startTime` | Long | 开始时间（录音经过的毫秒数，用于排序和增量游标） |
| `text` | String | 转写文本 |
| `realTime` | Long | 现实时间戳（毫秒） |

## 使用说明

- 返回的分片按 `startTime` 排序后拼接 `text`，即为完整的转写原文
- `startTime` 是相对录音起点的毫秒偏移，用于 splitRecordListV2 增量查询的游标
- 适用于进行中会议的实时转写和已结束会议的兜底原文

## 请求示例

```bash
python3 scripts/huiji/split-record-list.py abc123

python3 scripts/huiji/split-record-list.py --body '{"meetingChatId":"abc123"}'
```

## 脚本映射

- `../../scripts/huiji/split-record-list.py`

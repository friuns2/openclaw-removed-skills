# POST /ai-huiji/meetingChat/splitRecordListV2

## 作用

增量查询指定慧记的分片转写原文。在 splitRecordList 的基础上增加 `lastStartTime` 参数，传入时仅返回 `startTime` 大于该值的分片，用于减少重复传输。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meetingChatId` | String | 是 | 慧记 ID |
| `lastStartTime` | Long | 否 | 上次已同步的最大 startTime（毫秒偏移）。不传：返回全量；传：仅返回更新的分片 |

## 响应参数

`data` 类型为 `List<SplitRecordVO>`，字段同 splitRecordList：

| 字段 | 类型 | 说明 |
|---|---|---|
| `startTime` | Long | 开始时间（录音经过的毫秒数） |
| `text` | String | 转写文本 |
| `realTime` | Long | 现实时间戳（毫秒） |

## 使用说明

- **增量模式**：传入 `lastStartTime`（取上次缓存中最大分片的 startTime），仅返回新分片
- **全量模式**：不传 `lastStartTime`，行为与 splitRecordList 一致
- `startTime` 为 null 的分片在增量模式下会被过滤掉
- 适用于进行中会议的轮询拉取，配合本地缓存使用

## 请求示例

```bash
# 全量（等同于 splitRecordList）
python3 scripts/huiji/split-record-list-v2.py abc123

# 增量（只拉 startTime > 120034 的新分片）
python3 scripts/huiji/split-record-list-v2.py abc123 120034

# JSON body
python3 scripts/huiji/split-record-list-v2.py --body '{"meetingChatId":"abc123","lastStartTime":120034}'
```

## 脚本映射

- `../../scripts/huiji/split-record-list-v2.py`

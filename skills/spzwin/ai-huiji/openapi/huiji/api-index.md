# AI 慧记 — 接口索引

**生产域名**: `https://sg-al-ai-voice-assistant.mediportal.com.cn/api/open-api`

**鉴权**：所有接口只需 `appKey`（Header），无需 access-token。

| # | 接口 | 方法 | 路径 | 文档 | 脚本 |
|---|---|---|---|---|---|
| 1 | chatListByPage | POST | /ai-huiji/meetingChat/chatListByPage | [chat-list-by-page.md](chat-list-by-page.md) | [chat-list-by-page.py](../../scripts/huiji/chat-list-by-page.py) |
| 2 | listHuiJiIdsByMeetingNumberV2 | POST | /ai-huiji/meetingChat/listHuiJiIdsByMeetingNumberV2 | [list-by-meeting-number.md](list-by-meeting-number.md) | [list-by-meeting-number.py](../../scripts/huiji/list-by-meeting-number.py) |
| 3 | splitRecordList | POST | /ai-huiji/meetingChat/splitRecordList | [split-record-list.md](split-record-list.md) | [split-record-list.py](../../scripts/huiji/split-record-list.py) |
| 4 | splitRecordListV2 | POST | /ai-huiji/meetingChat/splitRecordListV2 | [split-record-list-v2.md](split-record-list-v2.md) | [split-record-list-v2.py](../../scripts/huiji/split-record-list-v2.py) |
| 5 | checkSecondSttV2 | POST | /ai-huiji/meetingChat/checkSecondSttV2 | [check-second-stt-v2.md](check-second-stt-v2.md) | [check-second-stt-v2.py](../../scripts/huiji/check-second-stt-v2.py) |
| 6 | getChatFromShareId | POST | /ai-huiji/meetingChat/getChatFromShareId | [get-chat-from-share-id.md](get-chat-from-share-id.md) | [get-chat-from-share-id.py](../../scripts/huiji/get-chat-from-share-id.py) |

# POST /ai-huiji/meetingChat/listHuiJiIdsByMeetingNumberV2

## 作用

按视频会议号查询当前用户在该场会议参与关系下可访问的慧记列表。即使会议由他人录制、慧记归属不在当前用户名下，只要当前用户参与了该会议，仍可通过此接口查到。

**与 chatListByPage 的差异**：chatListByPage 查的是「归属在当前用户名下」的慧记；本接口查的是「我参加了的那场视频会议」下的慧记。二者不可替代。

## 鉴权

只需 `appKey`，无需 access-token。

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `meetingNumber` | String | 是 | 视频会议号（与会议域一致） |
| `lastTs` | Long | 否 | 增量时间戳（毫秒）。未传或为 0：拉取最近一个月；>0：增量拉取时间戳大于 lastTs 的数据 |

## 响应参数

`data` 类型为 `List<FindChatVO>`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `_id` | String | 慧记 ID（即 meetingChatId，注意 `__` 后缀处理规则） |
| `name` | String | 慧记名称 |
| `recordState` | Integer | 录音状态（见下方状态说明） |
| `createTime` | Long | 创建时间（毫秒时间戳） |
| `finishTime` | Long | 结束时间（毫秒时间戳），进行中时为 null |
| `meetingLength` | Long | 会议时长（毫秒） |
| `personId` | String | 关联人员 ID，可能为 null |

## 会议状态判断（recordState）

| `recordState` | 状态 | 后续操作 |
|---|---|---|
| `0` | 进行中 | 用 get-transcript.py 获取实时转写 |
| `1` | 处理中 | 稍后重试 |
| `2` | 已完成 | 用 get-transcript.py 获取改写原文 |
| `3` | 失败 | 提示用户 |

> 注意：`recordState` 与 chatListByPage 返回的 `combineState` 含义不同，不可混用。

## 请求示例

```bash
# 基本用法
python3 scripts/huiji/list-by-meeting-number.py 20260327

# 增量拉取
python3 scripts/huiji/list-by-meeting-number.py --body '{"meetingNumber":"20260327","lastTs":1716345600000}'
```

## 脚本映射

- `../../scripts/huiji/list-by-meeting-number.py`

# 广告线索表单（clue）

> 所属 skill：`siluzan-tso`。
>
> 对应页面：`/clue-form`。支持 **TikTok** 和 **Meta（Facebook）** 两种媒体。

> **注意**：线索数据直接来自媒体 API，**不支持服务端分页**，数据量大时建议 `--json` 导出后自行处理。

```bash
siluzan-tso clue -m <媒体> -a <账户ID> [选项]
```

| 选项                 | 说明                                                              |
| -------------------- | ----------------------------------------------------------------- |
| `-m, --media`        | `TikTok \| Meta`（默认 TikTok）                                   |
| `-a, --account <id>` | TikTok：`advertiserId`（mediaCustomerId）；Meta：Facebook 页面 ID |
| `--region <region>`  | TikTok 专用：`eu \| us \| other \| ALL`（默认 ALL）               |
| `--start <date>`     | Meta 专用：开始日期（YYYY-MM-DD）                                 |
| `--end <date>`       | Meta 专用：结束日期（YYYY-MM-DD）                                 |
| `--json`             | 输出原始 JSON                                                     |

**TikTok 示例：**

```bash
# 查询 TikTok 全部区域线索
siluzan-tso clue -m TikTok -a 1234567890

# 只查欧洲区线索
siluzan-tso clue -m TikTok -a 1234567890 --region eu

# 查美国区，JSON 输出
siluzan-tso clue -m TikTok -a 1234567890 --region us --json
```

**Meta 示例：**

```bash
# 查询 Meta 线索（3月份）
siluzan-tso clue -m Meta -a 987654321 --start 2026-03-01 --end 2026-03-31

# JSON 输出
siluzan-tso clue -m Meta -a 987654321 --start 2026-03-01 --json
```

**输出字段说明（TikTok）：**

| 字段                                | 来源            |
| ----------------------------------- | --------------- |
| 姓名、邮箱、手机                    | `custom_fields` |
| 表单名、广告名、区域、时间、lead_id | `system_fields` |

**输出字段说明（Meta）：**

| 字段             | 来源         |
| ---------------- | ------------ |
| 姓名、邮箱、手机 | `field_data` |
| 表单名、创建时间 | 顶层字段     |

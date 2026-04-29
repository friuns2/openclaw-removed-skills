---

## name: 96push
description: "Remote control 96Push desktop client — query platforms/accounts, create content, publish to multiple social media platforms, poll results. Use when user mentions 96push, publishing, social media, multi-platform, or content distribution."

# 96Push Remote Control

Use the bundled script to remotely control the user's local 96Push desktop client via ACP proxy.

## Requirements

- Provide API key via either:
  - environment variable: `PUSH_API_KEY`, or
  - `~/.openclaw/.env` line: `PUSH_API_KEY=pk_...`
- If the key is missing, the script will return setup instructions. Guide the user:
  1. Download 96Push from [https://push.96.cn](https://push.96.cn)
  2. Launch and login
  3. Go to profile (bottom-left avatar) → API Key → Generate
  4. Tell me the key, I'll save it to `~/.openclaw/.env`

## Commands

All commands via `python3 {baseDir}/scripts/96push.py <command> [options]`.

### Query

```bash
# health check
python3 {baseDir}/scripts/96push.py check

# platforms
python3 {baseDir}/scripts/96push.py platforms
python3 {baseDir}/scripts/96push.py platforms --article
python3 {baseDir}/scripts/96push.py platforms --video

# accounts
python3 {baseDir}/scripts/96push.py accounts
python3 {baseDir}/scripts/96push.py all-accounts

# content
python3 {baseDir}/scripts/96push.py articles --page 1 --size 10 --status 1
python3 {baseDir}/scripts/96push.py article --id 42

# publish records
python3 {baseDir}/scripts/96push.py records --page 1 --size 10
python3 {baseDir}/scripts/96push.py record --id 7

# dashboard
python3 {baseDir}/scripts/96push.py dashboard
python3 {baseDir}/scripts/96push.py overview
python3 {baseDir}/scripts/96push.py user

# platform configs
python3 {baseDir}/scripts/96push.py plat-sets --pid 3
```

### Create Content

```bash
# content type can be omitted when --files clearly indicates image/video
# video files (.mp4/.mov/.avi/.mkv/.webm/.m4v/.flv/.wmv) are inferred as --type video

# article — needs title + markdown (or content as HTML)
python3 {baseDir}/scripts/96push.py create --type article --title "标题" --markdown "# 内容" --desc "摘要"

# article with explicit cover image(s)
python3 {baseDir}/scripts/96push.py create --type article --title "标题" --markdown "# 内容" --thumb '["https://example.com/cover.jpg"]'

# graph_text — needs title + files (image URLs, at least 1)
python3 {baseDir}/scripts/96push.py create --type graph_text --title "图集" --files '["url1","url2"]'

# video — needs title + files (1 video URL), desc strongly recommended
python3 {baseDir}/scripts/96push.py create --type video --title "视频" --files '["video_url"]' --desc "视频描述"
python3 {baseDir}/scripts/96push.py create --title "视频" --files '["https://example.com/video.mp4"]' --desc "视频描述"
```

### Update / Delete Content

```bash
python3 {baseDir}/scripts/96push.py update --id 42 --title "新标题" --markdown "# 新内容"
python3 {baseDir}/scripts/96push.py delete-article --id 42
```

### Publish

```bash
# simple mode — just account IDs (uses default/empty settings)
python3 {baseDir}/scripts/96push.py publish --type article --id 42 --accounts "1,5,8"
python3 {baseDir}/scripts/96push.py publish --type video --id 42 --accounts "1,5,8"

# if --type is omitted, the script reads content detail and infers article/graph_text/video

# advanced mode — full settings per account (see platform settings reference)
python3 {baseDir}/scripts/96push.py publish --type article --id 42 --accounts-json '[{"id":1,"platName":"微信公众号","settings":{"publishType":"publish","origin":false}},{"id":5,"platName":"知乎","settings":{"topic":"AI/科技"}}]'

# draft only
python3 {baseDir}/scripts/96push.py publish --type article --id 42 --accounts "1,5" --draft

# poll result
python3 {baseDir}/scripts/96push.py poll --id 7
python3 {baseDir}/scripts/96push.py poll --id 7 --interval 10 --max 30
```

### Manage Platform Configs

```bash
# create a reusable config
python3 {baseDir}/scripts/96push.py create-plat-set --pid 1 --name "公众号默认" --setting '{"publishType":"publish","leave":true}'

# update config
python3 {baseDir}/scripts/96push.py update-plat-set --sid 1 --pid 1 --name "公众号原创" --setting '{"publishType":"publish","origin":true}'

# delete config
python3 {baseDir}/scripts/96push.py delete-plat-set --sid 1
```

## Typical Workflow

1. `check` — confirm client is online
2. `accounts` — list available accounts, let user pick targets
3. `create` — create content (see content creation rules below)
4. `publish` — submit and wait for results (**call ONCE only**, see critical rules below). The command automatically polls until completion — no need to call `poll` separately.
5. Report results to the user

---

## CRITICAL: Publish Anti-Spam Rules (MUST FOLLOW)

**⚠️ NEVER call `publish` more than ONCE per content per batch of accounts.**

The publish command triggers browser automation that takes 30-60 seconds to complete. The script has a built-in guard that rejects publish if another task is already running. Follow these rules strictly:

1. **ONE publish call per batch.** The `publish` command now automatically waits for completion — it submits the task and polls until done. Do NOT call `poll` separately unless you used `--no-wait`.
2. **If publish times out**, it does NOT mean publish failed — the browser automation may still be running. Do NOT retry publish. Instead, ask the user to check the 96Push client.
3. **If publish returns `PUBLISH_ALREADY_RUNNING`**, do NOT retry. Wait for the active task to complete.
4. **If publish returns HTTP 425**, another task is in progress. Wait and report to user, do NOT retry.
5. **NEVER loop or retry the publish command.** Each call creates a new browser automation task. Calling it 10 times creates 10 browser windows fighting for the same page.
6. **The complete sequence is always**: `publish` (once, waits automatically) → report result to user.

---

## Content Creation Rules (IMPORTANT)

### PublishData Fields


| Field     | Type     | Required    | Description                                              |
| --------- | -------- | ----------- | -------------------------------------------------------- |
| title     | string   | **Yes**     | Content title                                            |
| desc      | string   | No          | Description/summary                                      |
| content   | string   | Conditional | HTML content (articles need this)                        |
| markdown  | string   | Conditional | Markdown source (articles need this)                     |
| autoThumb | bool     | No          | Auto-extract cover from content (default true)           |
| thumb     | string[] | Conditional | Cover image **public URLs** (see platform requirements). **No local paths or base64** — must be HTTP(S) URLs. |
| files     | string[] | Conditional | Media **public URLs** — **only for graph_text (images) and video (video URL)**. NOT used for articles. **Must be HTTP(S) URLs**, daemon auto-downloads. |


### By Content Type

**Type selection rule**:

- If the user wants to create or publish a video, use `--type video` explicitly whenever possible.
- If `--type` is omitted, the CLI now infers the type from `--files` or existing content detail.
- If `--type article` is passed together with video/image `files`, the CLI treats the media files as authoritative and avoids creating/publishing the content as an article.
- Never create article content with video URLs in `files`; video URLs must be video content.

**Article (文章)**:

- **Must have**: `title` + `content` (HTML) or `markdown`
- **Cover image (thumb)**: Some platforms require at least one cover. Set `autoThumb: true` to auto-extract from content images, or provide explicit `thumb` URLs.
- **desc**: Optional summary text, some platforms use it.
- **Do NOT set `files`** for articles — `files` is only for graph_text/video. Images in articles go into the markdown/content body. Cover images go into `thumb`.

**Graph Text (图文/图集)**:

- **Must have**: `title` + `files` (array of image URLs, at least 1)
- **Cover**: Auto-generated from first image if `thumb` is empty.
- **No content/markdown needed** — the images ARE the content.

**Video (视频)**:

- **Must have**: `title` + `files` (array with exactly 1 video URL)
- **Cover**: Auto-generated from video frame if `thumb` is empty. Many platforms require a cover — provide one if possible.
- **desc**: Strongly recommended — most video platforms use it as the video description.

### Cover Image Requirements by Platform


| Platform                  | Article Cover         | Graph Text Cover | Video Cover     |
| ------------------------- | --------------------- | ---------------- | --------------- |
| WeChat (wechat)           | Required (1 image)    | Auto from images | Required        |
| Douyin (douyin)           | N/A                   | Auto             | Auto from video |
| Toutiao (toutiaohao)      | Required (1-3 images) | Auto             | Auto            |
| Xiaohongshu (xiaohongshu) | N/A                   | Auto from images | Auto            |
| Bilibili (bilibili)       | Optional (headerImg)  | Auto             | Required        |
| Zhihu (zhihu)             | Optional              | Auto             | Auto            |
| Baijiahao (baijiahao)     | Required (1-3 images) | Auto             | Required        |
| CSDN (csdn)               | Optional              | N/A              | Auto            |
| Weibo (sina)              | N/A                   | Auto             | Auto            |
| Kuaishou (kuaishou)       | N/A                   | Auto             | Auto            |
| Sohu (sohuhao)            | Auto from content     | Auto             | Auto            |


**Rule**: When in doubt, always provide at least one `thumb` image. `autoThumb: true` will try to extract from content but may fail if content has no images.

**IMPORTANT**: `thumb` and `files` only accept **public HTTP(S) URLs**. The Go daemon will automatically download images from these URLs before publishing. Do NOT pass local file paths or base64 data — they will not work through the remote proxy.

---

## Platform Settings Reference (IMPORTANT)

When publishing, each account in `postAccounts` needs a `settings` object. **Different platforms require different fields.** Settings are passed as JSON in the `--accounts-json` parameter or pre-configured via `plat-sets`.

### Common Fields


| Field        | Type   | Description                                                        |
| ------------ | ------ | ------------------------------------------------------------------ |
| timerPublish | object | `{"enable": true, "timer": "YYYY-MM-DD HH:MM:SS"}`                 |
| lookScope    | uint   | Visibility: 0=public, 1=friends, 2=private                         |
| source       | uint   | Content declaration (AI/repost/original, values vary per platform) |
| classify     | string | Category/section                                                   |
| collection   | string | Collection/column                                                  |
| origin       | bool   | Declare as original                                                |
| labels/tag   | string | Tags (separator varies: `/` or `,`)                                |


### Platform-Specific Settings

**wechat (微信公众号)** — Article/Graph Text:

- `author`: Author name
- `publishType`: `"mass"` (群发) or `"publish"` (发布)
- `origin`: Declare original (default false)
- `leave`: Enable comments (default true)
- Timer: now+5min ~ 7 days

**wechat (微信公众号)** — Video (extra fields):

- `materTitle`: Material title
- `barrage`: Enable bullet comments
- `turn2Channel`: Convert to Video Channel

**douyin (抖音)**:

- `allowSave`: Allow others to save (default true)
- `lookScope`: 0=public, 1=friends, 2=private
- `hotspot`: Related trending topic
- `music`: Background music

**toutiaohao (今日头条)** — Article:

- `starter`: Toutiao exclusive
- `syncPublish`: Also publish as Weitoutiao
- Timer: now+2h ~ 7 days. Cannot use timer if `collection` is set.

**xiaohongshu (小红书)**:

- `origin`: Declare original
- `source`: Content declaration — 0=none, 1=fiction/entertainment, 2=AI-generated, 3=marked in body, 4=self-shot, 5=repost source
- `reprint`: Media/source name, only used when `source=5`. Do not combine `origin=true` with `source=5`.
- `mark`: Tag user/location `{"user": true, "search": "keyword"}`
- `lookScope`: 0=public, 1=friends, 2=private
- Timer: now+1h ~ 14 days.
- Draft save clicks `暂存离开`; publish clicks `发布` or `定时发布`.

**bilibili (哔哩哔哩)** — Video/Graph Text:

- `partition`: Section/category (important!)
- `reprint`: Repost source (empty = self-made)
- `creation`: Allow derivative works
- `dynamic`: Fan notification text

**bilibili (哔哩哔哩)** — Article:

- `classify`: Column category
- `headerImg`: Header image URL
- `labels`: Tags (max 10)

**zhihu (知乎)** — Article:

- `question`: Submit to a question
- `source`: Creation declaration — 0=none, 1=spoiler, 2=medical, 3=fiction, 4=finance, 5=AI-assisted
- `topic`: Article topics (max 3, `/` separated)
- `collection`: Column name
- `origin`: Source type — 0=none, 1=official site, 2=news report, 3=TV media, 4=print media
- Draft save is auto-save based and waits for `/api/articles/drafts`; publish waits for `POST /content/publish`.
- Video: set `classify` when possible; `reprint=true` means repost, `false` means original. Timer: now+1h ~ 14 days.

**omtencent (腾讯内容开放平台)** — Article/Video:

- `classify`: Category. For stable tests, use `科技` for articles.
- `labels`: Tags separated by `/`, max 9 tags and max 8 Chinese chars each.
- `activity`: Platform activity keyword.
- `source`: Content declaration — 1=AI generated, 2=fiction/entertainment, 3=from internet, 4=personal opinion, 5=old news. Empty or 0 currently defaults to 4.
- Timer: now+5min ~ 7 days.
- Save/publish waits for platform submit responses; if the AIGC declaration dialog appears, submit it and click save/publish again.

**baijiahao (百家号)**:

- `classify`: Category `"一级/二级"` format
- `byAI`: AI creation declaration
- Timer: now+1h ~ 7 days

**csdn (CSDN)** — Article:

- `labels`: Tags (`/` separated, max 7)
- `artType`: 0=original, 1=repost, 2=translation
- `originLink`: Required for reposts
- Timer: now+4h ~ 7 days

**juejin (掘金)**:

- `tag`: **Required** — must have at least one tag
- `classify`: Category

**kuaishou (快手)**:

- `sameFrame`: Allow others to film with this
- `download`: Allow download
- `sameCity`: Show in same-city feed

**sina (新浪微博)** — Video/Graph Text:

- `type`: 0=original, 1=derivative, 2=repost
- `stress`: Allow highlights (default true)
- `wait`: Wait X seconds before posting

**sina (新浪微博)** — Article:

- `onlyFans`: Only fans can read full text (default true)

**sohuhao (搜狐号)** — Article/Graph Text/Video:

- `classify`: Attribute/category — 观点评论/故事传记/消息资讯/八卦爆料/经验教程/知识科普/测评盘点/见闻记录/运势/搞笑段子/美图/美文
- `declaration`: Source declaration — 0=无特别声明, 1=引用声明, 2=包含AI创作内容, 3=包含虚构创作
- `topic`: Topic keyword (search-based)
- `loginView`: Require login to read full text (default false)
- Timer: now+1h ~ 7 days
- Cover: Auto-extracted from article images if not manually provided; upload also supported

### Timer Publish Constraints


| Platform   | Min Time      | Max Time |
| ---------- | ------------- | -------- |
| wechat     | now + 5 min   | 7 days   |
| toutiaohao | now + 2 hours | 7 days   |
| baijiahao  | now + 1 hour  | 7 days   |
| csdn       | now + 4 hours | 7 days   |
| acfun      | now + 4 hours | 14 days  |
| pinduoduo  | now + 4 hours | 7 days   |
| sohuhao    | now + 1 hour  | 7 days   |
| tiktok     | now + 2 hours | 30 days  |


---

## Output Format Suggestions

### Publish Results

```
📤 Publish Results (Record #7)

✅ WeChat (@AccountA) — Success, 12s
✅ Zhihu (@AccountB) — Success, 8s
❌ Baijiahao (@AccountC) — Failed: Login expired

Success: 2/3, Failed: 1/3
```

### Account List

```
📋 Logged-in Accounts:

1. WeChat - AccountA (ID: 1) [article, graph_text]
2. Douyin - AccountB (ID: 5) [video, graph_text]
3. Bilibili - AccountC (ID: 8) [article, video, graph_text]
```

## Error Handling

- 503 CLIENT_OFFLINE → "96Push not running. Launch it from [https://push.96.cn](https://push.96.cn)"
- 425 → "Another publish task is running. Do NOT retry — use `poll` to wait for the active task."
- `PUBLISH_ALREADY_RUNNING` → A task is already in progress. Use `poll --id <active_record_id>` from the error response. Do NOT call publish again.
- 504 TIMEOUT → "Client response timed out. The task may still be running — check with `poll`."
- 401/403 → "API Key invalid or expired, regenerate in 96Push profile"
- Account `login=false` → "Account login expired, re-login in 96Push client"
- Poll timeout → Report to user: "Publishing is taking longer than expected. The browser automation may still be running. Please check the 96Push client." Do NOT retry publish.

## Safety Rules

- Never expose the API key in responses
- List target accounts and confirm with user before publishing
- Require confirmation before delete operations
- Remote publish must use `headless: true`
- Never guess account IDs — always query first
- Don't output raw Base64 image data — just mention it exists
- `thumb` and `files` must be **public HTTP(S) URLs** — never pass local paths or base64
- If user provides a local image, ask them to upload it to an image hosting service first and provide the URL
- When creating content, validate required fields before calling create API
- When building settings, check platform requirements — missing required fields cause publish failures
- **NEVER call `publish` more than once for the same content+accounts batch.** Each call creates a real browser automation task. Duplicate calls will open multiple browsers fighting over the same page, causing all of them to fail and potentially crashing the client.
- **NEVER retry `publish` on failure or timeout.** If publish fails, report the error to the user. If poll times out, report timeout to the user. Let the user decide what to do.
- **Always use `poll` after `publish`.** The publish command only starts the task — it returns immediately. You MUST poll to get the result.

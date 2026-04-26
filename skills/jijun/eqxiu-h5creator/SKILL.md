---
name: eqxiu-h5creator
description:   易企秀 AIGC H5 创作工具，通过对话引导用户填写信息，自动生成翻页 H5 邀请函、营销海报、表单问卷等作品。
  当用户想要生成/制作/创建 H5 页面时使用此 Skill，包括婚礼邀请函、会议邀请函、年会海报、节日祝福等场景。

  核心功能：
  1. 品类选择——从易企秀支持的 H5 品类中选定（邀请函/海报/表单等）
  2. 风格选择——可选指定视觉风格
  3. 内容生成——根据用户提供的标题、字段信息生成大纲和大纲模板
  4. 输出作品链接——返回可编辑的 H5 链接
  5. 文本可用性校验——制作完成后必须检查文本并修复问题，再把预览链接交付用户
  6. 素材与配图——查询/上传个人素材；查询作品中可替换「正文配图」并执行换图（需同一 token）
  工作流程：品类选择 → 字段填写 → 风格选择（可选）→ 生成 outline → 生成 scene-tpl → 文本校验与修复 →（可选）素材上传/换正文配图 → 交付预览链接

  触发词：制作H5、生成H5、创建H5、做一个H5、易企秀、
  H5邀请函、年会H5、婚礼邀请函、会议邀请函、生日祝福H5、
  节日海报H5、H5页面生成、翻页H5怎么做、怎么做一个邀请函H5

summary:   易企秀 AIGC 创作 Skill，通过对话引导用户填写品类、标题、字段信息，
  自动生成翻页 H5 作品。调用 `scripts/eqxiu_aigc_client.py`（实现位于同目录 `scripts/eqxiu_aigc/` 包）执行完整链路。

read_when:
  - 用户提到"制作/生成/创建 H5"、"做个邀请函"、"做一张年会海报"
  - 用户想用易企秀但不知道怎么做、需要 AI 帮助生成 H5
  - 用户描述"我想做一个XX的翻页H5"
  - 用户要换 H5 里的图片、换正文配图、改配图、上传素材到易企秀或查自己的素材列表

---

# 易企秀 AIGC H5 HTTP 调用

- 命令行：`python scripts/eqxiu_aigc_client.py ...`
- 鉴权：客户端支持 `X-Openclaw-Token` 登录、状态校验与自动透传。
- 获取`X-Openclaw-Token`地址：`https://www.eqxiu.com/skillAccess/token`


## 调用顺序（必须遵守）

### 认证（推荐先执行）

```bash
# 交互式保存 token 到 ~/.eqxiu/config.json，如果存在token，验证token有效性即可
python scripts/eqxiu_aigc_client.py login

# 校验 token 是否有效
python scripts/eqxiu_aigc_client.py auth status
```

说明：
- `auth status` 返回 `{"success": true, "code": 200, ...}` 代表 token 有效。
- 返回 `{"success": false, "code": 1002, "msg":"认证失败", ...}` 代表 token 无效。
- 也可用 `--access-token` 覆盖配置中的 token。

易企秀链路依赖上游返回字段，**不要**颠倒顺序。

1. **`GET /iaigc/category`** — 列出制作种类。每条含 `categoryId`、`name`、`desc`、`fields`、`twoLevelCategoryId`、`threeLevelCategoryIds`（数组）等。
2. **（可选）`GET /iaigc/style`** — 查风格列表，供 `scene-tpl` 的 `styleId`。需要某条品类里的 `twoLevelCategoryId` 与 `threeLevelCategoryIds` 中的**某一个**三级 id（整数）。支持查询参数 `pageNo`（默认 1）、`pageSize`（默认 20，上限 100）。成功时本服务响应体里的 `data` 与易企秀分页一致：`{ pageNo, pageSize, total, data }`，其中内层 `data` 为模板完整对象数组（每项含 `id`、`productTitle`、`sceneExtract` 等）；选风格时一般用每项的 `id` 作为 `styleId`。
3. **`POST /iaigc/outline`** — 提交 `sceneFields` + `categoryId`（等于所选品类的 `categoryId`）。返回 `imageId`、`outline`、`outlineTaskId`。
4. **`POST /iaigc/scene-tpl`** — 提交与步骤 3 **相同**的 `sceneFields` 与 **相同**的品类 id 作为 `sceneId`，并带上步骤 3 的 `title`（用户给定）、`outlineTaskId`、`outline`；建议带上 `imageId`（来自步骤 3）；若步骤 2 选了模板则带 `styleId`。

对话中向用户确认：`title`、各 field 的文案、是否指定 `styleId`（可先展示 `style` 接口返回的 `id`/`productTitle` 等字段）。

## 构造 sceneFields

- 根据步骤 1 返回条目的 `fields`（及业务说明）组装数组：`[{"id": <整数>, "value": "<字符串>"}, ...]`。
- `id` 必须与品类定义的字段 id 一致；缺字段或错 id 易导致上游失败。

## 客户端脚本

以下命令均在 `skills/eqxiu-h5creator/scripts/` 下执行（或任意目录使用脚本绝对路径）；实现代码在同级包 `eqxiu_aigc/`。

### 创作主链路（iaigc）

```bash
# 1) 品类列表
python scripts/eqxiu_aigc_client.py category

# 2) 风格（示例 id 需换成品类数据中的真实值）
python scripts/eqxiu_aigc_client.py --access-token xxx style --two <twoLevelCategoryId> --three <某个threeLevelCategoryId>

# 3) 仅生成 outline
python scripts/eqxiu_aigc_client.py --access-token xxx outline --category-id <categoryId> --fields-json '[{"id":1,"value":"某主题"}]'

# 4) 仅生成 scene-tpl（body 需含完整 JSON，通常由 outline 结果拼装）
python scripts/eqxiu_aigc_client.py --access-token xxx scene-tpl --json-file path/to/body.json

# 一键：outline → scene-tpl（同一 categoryId、同一份 sceneFields）
python scripts/eqxiu_aigc_client.py --access-token xxx pipeline --category-id <id> --title "作品标题" --fields-json '[...]' [--style-id <可选>]

# 文本修正并发布（作品须归属当前用户）
python scripts/eqxiu_aigc_client.py --access-token xxx validate-fix --scene-id <scene_id> --page-id <page_id> --element-id <element_id> --content "修正后的文案" [--preview-url "<previewUrl>"]
```

### 素材库（易企秀 material-api，非 iaigc）

| 目的 | CLI 子命令 | 说明 |
|------|------------|------|
| **查询素材** | `material-list` | 分页列出当前用户已上传素材（默认 `fileType=1` 图片）。 |
| **文件上传** | `upload` | 需 `pip install cos-python-sdk-v5`。 |

```bash
# 查询当前用户上传素材（换图前可先查已有 path，或给用户选图）
python scripts/eqxiu_aigc_client.py --access-token xxx material-list [--page-no 1] [--page-size 30] [--file-type 1] [--tag-id -1] 

# 本地文件上传 COS 并登记素材库；成功 JSON 中含 cos.key / cos.assetUrl、material（业务对象，含可用于 H5 的 path 等字段，以实际返回为准）
python scripts/eqxiu_aigc_client.py --access-token xxx upload --file /path/to/image.png

### 作品内「正文配图」（本服务 iaigc + 易企秀 gRPC，需作品归属用户换图）

| 目的 | CLI 子命令 | 对应 HTTP |
|------|------------|-----------|
| **查询可替换图片** | `body-images` | `GET /iaigc/h5_scene/get_body_images?id=<scene_id>&page_id=<可选>` |
| **替换图片** | `replace-body-image` | `POST /iaigc/h5_scene/replace_body_image` |

```bash
# 列出作品中 name=正文配图 的图片：每页含 elements[].id / src / src_url，供换图参数
python scripts/eqxiu_aigc_client.py --access-token xxx body-images --scene-id <scene_id> [--page-id <仅某一页>]

# 将某一 element 换为新图；--src 一般为素材 path 或与生成作品时一致的 asset 路径（可先 upload 再取 material 或 cos.key）
python scripts/eqxiu_aigc_client.py --access-token xxx replace-body-image --scene-id <scene_id> --page-id <page_id> --element-id <元素id> --src "<新图 path 或 URL>" [--source-id <可选>]
```

**换图推荐顺序**：`body-images` 拿到 `page_id` + `element_id` + 当前 `src` →（如需新文件）`upload` 得到可写进作品的 `src` → `replace-body-image`。`pipeline` 成功后的 `validation.body_images` 与 `body-images` 结构一致，可跳过首次查询。

所有需鉴权的子命令都会携带 `X-Openclaw-Token`（`--access-token` 或 `~/.eqxiu/config.json`）。

`pipeline` 子命令内部顺序固定为：先 `create_outline`，再 `create_scene_tpl`，并把 `outlineTaskId`、`outline`、`imageId` 自动传入第二步；最后会自动读取可编辑文本与正文配图列表，输出到 `validation.editable_text`、`validation.body_images` 供大模型校验与换图（换图失败时 `body_images` 可能为空数组）。

## 二次编辑（文本 + 素材 + 配图）

### 文本

当 `pipeline` 返回 `validation.editable_text` 后，先让大模型判断文本是否需要修正；若需要，调用 `validate-fix` 执行修正并发布：

```bash
# 1) 先执行 pipeline，拿到 validation.editable_text 给大模型判断
python scripts/eqxiu_aigc_client.py --access-token xxx pipeline --category-id <id> --title "作品标题" --fields-json '[...]'

# 2) 若有问题，调用 validate-fix 按元素修正（自动 publish）
python scripts/eqxiu_aigc_client.py --access-token xxx validate-fix --scene-id <scene_id> --page-id <page-id> --element-id <element_id> --content "更新后的文案" --preview-url "<previewUrl>"
```

### 素材与正文配图

- **查询素材**：`material-list` 调易企秀 `material-api` 的 `list2`；从返回里取可用于作品的图片 path/url（字段名以实际 JSON 为准）。
- **上传文件**：`upload` 走 COS + `saveFile`；依赖 `cos-python-sdk-v5`。上传成功后用返回中的路径作为 `replace-body-image --src` 的输入（与作品内 `properties.src` 格式一致即可）。
- **查询可替换图片**：`body-images` 或直接使用 `pipeline` 输出的 `validation.body_images`；仅包含 `name=正文配图` 且类型为图片的组件。
- **替换图片**：`replace-body-image` 必须带作品归属用户同一 token；`element_id` 须与 `body-images` 中某项一致，否则接口会拒绝。

返回与使用要点：
- `pipeline` 会自动输出 `validation.editable_text`、`validation.body_images`；后者在部分环境拉取失败时可能为空数组，可再执行一次 `body-images`。
- `validate-fix` 必要参数：`scene-id`、`page-id`、`element-id`、`content`。
- 文本修正后把 `previewUrl` 返回给用户；换图成功后服务端同样会 publish，可再次打开预览链接确认。
- 细调文字样式可在 `validate-fix` 中使用 `--css-json`。

## 代理在对话中的建议流程

1. 执行 `category`（或 GET），让用户选定品类；记录 `categoryId` 与 `fields`。
2. 询问用户各字段文案，组装 `sceneFields`。
3. 若需要固定风格：用该品类的 `twoLevelCategoryId` 与选定的三级 id 调 `style`，用户选 `styleId`。
4. 调 `outline`（或 `pipeline` 前半段）；失败则根据 `msg` 重试或改字段。
5. 调 `scene-tpl`（或 `pipeline` 一次性完成）；成功 `data` 一般为 `{"sceneId":{id},"previewUrl":"https://h5.eqxiu.com/s/{code}"}`, "editUrl"：`https://www.eqxiu.com/c/{id}`（以服务实际返回为准），点击链接登陆后就可以编辑了。
6. 把 `validation.editable_text` 交给大模型审查；有问题则 `validate-fix` 并交付 `previewUrl`。
7. **（可选）** 若用户要换内页配图：根据 `validation.body_images`（或 `body-images`）定位 `page_id` / `element_id`；若需新图则先 `upload` 再 `replace-body-image --src …`；若从已有素材选图则先 `material-list` 再换图。

## 超时与错误

- `outline`、`scene-tpl` 可能极慢，客户端默认超时约 **900s**；可用 `--timeout` 调整。素材 `list2`、COS 相关请求使用较短超时（由客户端内部限制，避免拖死长轮询）。
- `iaigc` 业务错误多为 `success: false` 与 `msg`；脚本非零退出并打印 JSON。`upload` / `material-list` 失败时也会打印结构化 JSON（含 `code`/`msg`）。

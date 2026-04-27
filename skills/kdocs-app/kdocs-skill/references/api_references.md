# 金山文档 Skill 工具完整参考

本文件包含金山文档 Skill 所有工具的 API 说明、参数、返回值。

> **通用返回字段**：所有接口均返回 `code`（状态码，0 表示成功）和 `msg`（人可阅读的文本信息）。

---

## 一、写文档

- **1. create_file** — 在云盘下新建文件或文件夹  
  > 详见 [create_file 完整参考](api/write.md)

- **2. scrape_url** — 网页剪藏，抓取网页内容并自动保存为智能文档  
  > 详见 [scrape_url 完整参考](api/write.md)

- **3. scrape_progress** — 查询网页剪藏任务进度  
  > 详见 [scrape_progress 完整参考](api/write.md)

- **4. upload_file** — 全量上传写入文件（更新已有 docx/pdf 或新建并上传本地文件）  
  > 详见 [upload_file 完整参考](api/write.md)

- **5. upload_attachment** — 向已有文档上传附件，支持 URL 或 Base64  
  > 详见 [upload_attachment 完整参考](api/write.md)

## 二、读文档

- **6. list_files** — 获取指定文件夹下的子文件列表  
  > 详见 [list_files 完整参考](api/read.md)

- **7. download_file** — 获取文件下载信息  
  > 详见 [download_file 完整参考](api/read.md)

## 三、管文档

### 文件操作

- **8. move_file** — 批量移动文件(夹)  
  > 详见 [move_file 完整参考](api/manage_file.md)

- **9. rename_file** — 重命名文件（夹）  
  > 详见 [rename_file 完整参考](api/manage_file.md)

- **10. copy_file** — 复制文件到指定目录（可跨盘）  
  > 详见 [copy_file 完整参考](api/manage_file.md)

- **11. check_file_name** — 检查目录下文件名是否已存在  
  > 详见 [check_file_name 完整参考](api/manage_file.md)

### 分享与信息

- **12. share_file** — 开启文件分享  
  > 详见 [share_file 完整参考](api/manage_share.md)

- **13. set_share_permission** — 修改分享链接属性  
  > 详见 [set_share_permission 完整参考](api/manage_share.md)

- **14. cancel_share** — 取消文件分享  
  > 详见 [cancel_share 完整参考](api/manage_share.md)

- **15. get_share_info** — 获取分享链接信息  
  > 详见 [get_share_info 完整参考](api/manage_share.md)

- **16. get_file_info** — 获取文件（夹）详细信息  
  > 详见 [get_file_info 完整参考](api/manage_share.md)

### 标签管理

- **17. list_labels** — 分页获取云盘自定义标签列表（可按归属者、标签类型筛选）  
  > 详见 [list_labels 完整参考](api/manage_label.md)

- **18. create_label** — 创建自定义标签  
  > 详见 [create_label 完整参考](api/manage_label.md)

- **19. get_label_meta** — 获取单个标签详情（含系统标签固定 ID）  
  > 详见 [get_label_meta 完整参考](api/manage_label.md)

- **20. get_label_objects** — 获取某标签下的对象列表（文件/云盘等）  
  > 详见 [get_label_objects 完整参考](api/manage_label.md)

- **21. batch_add_label_objects** — 批量为多个文档对象添加同一标签（打标签）  
  > 详见 [batch_add_label_objects 完整参考](api/manage_label.md)

- **22. batch_remove_label_objects** — 批量取消标签  
  > 详见 [batch_remove_label_objects 完整参考](api/manage_label.md)

- **23. batch_update_label_objects** — 批量更新标签下对象排序或属性  
  > 详见 [batch_update_label_objects 完整参考](api/manage_label.md)

- **24. batch_update_labels** — 批量修改自定义标签名称或属性  
  > 详见 [batch_update_labels 完整参考](api/manage_label.md)

### 收藏管理

- **25. list_star_items** — 获取收藏（星标）列表  
  > 详见 [list_star_items 完整参考](api/manage_star.md)

- **26. batch_create_star_items** — 批量添加收藏  
  > 详见 [batch_create_star_items 完整参考](api/manage_star.md)

- **27. batch_delete_star_items** — 批量移除收藏  
  > 详见 [batch_delete_star_items 完整参考](api/manage_star.md)

### 最近与回收站

- **28. list_latest_items** — 获取最近访问文档列表  
  > 详见 [list_latest_items 完整参考](api/manage_other.md)

- **29. list_deleted_files** — 获取回收站文件列表  
  > 详见 [list_deleted_files 完整参考](api/manage_other.md)

- **30. restore_deleted_file** — 将回收站文件还原到原位置  
  > 详见 [restore_deleted_file 完整参考](api/manage_other.md)

## 四、用文档

- **31. read_file_content** — 文档内容抽取为 Markdown/纯文本  
  > 详见 [read_file_content 完整参考](api/use.md)

- **32. search_files** — 文件（夹）搜索  
  > 详见 [search_files 完整参考](api/use.md)

- **33. get_file_link** — 获取文件的云文档在线访问链接  
  > 详见 [get_file_link 完整参考](api/use.md)

## 附录

### A. 通用文件信息结构（FileInfo）

`create_file`、`upload_file`（步骤三）、`rename_file`、`list_files` 等接口返回的文件信息共用以下结构。响应字段表中 `array[FileInfo]` 即引用此结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 文件 ID |
| `name` | string | 文件名 |
| `type` | string | 文件类型：`file` / `folder` / `shortcut` |
| `size` | integer | 文件大小 |
| `parent_id` | string | 父目录 ID |
| `drive_id` | string | 驱动盘 ID |
| `version` | integer | 文件版本 |
| `ctime` | integer | 文件创建时间（时间戳，秒） |
| `mtime` | integer | 文件修改时间（时间戳，秒） |
| `shared` | boolean | 是否开启分享（link.status = 'open' 时为 true） |
| `link_id` | string | 分享 ID |
| `link_url` | string | 分享链接 URL |
| `created_by` | object | 文件创建者信息 |
| `created_by.id` | string | 身份 ID |
| `created_by.name` | string | 用户或应用的名称 |
| `created_by.type` | string | 身份类型：`user` / `sp` / `unknown` |
| `created_by.avatar` | string | 头像 |
| `created_by.company_id` | string | 身份所归属的公司 |
| `modified_by` | object | 文件修改者信息（结构同 created_by） |
| `ext_attrs` | array[object] | 文件扩展属性（`with_ext_attrs=true` 时返回），每项含 name 和 value |
| `drive` | object | 文件驱动盘信息（`with_drive=true` 时返回）

**`permission` 对象**（`with_permission=true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `comment` | boolean | 评论 |
| `copy` | boolean | 复制 |
| `copy_content` | boolean | 内容复制 |
| `delete` | boolean | 文件删除 |
| `download` | boolean | 下载 |
| `history` | boolean | 历史版本（仅公网支持） |
| `list` | boolean | 列表 |
| `move` | boolean | 文件移动 |
| `new_empty` | boolean | 新建 |
| `perm_ctl` | boolean | 权限管理 |
| `preview` | boolean | 预览 |
| `print` | boolean | 打印 |
| `rename` | boolean | 文件重命名 |
| `saveas` | boolean | 另存为（仅公网支持） |
| `secret` | boolean | 安全文档（仅公网支持） |
| `share` | boolean | 分享 |
| `update` | boolean | 编辑/更新 |
| `upload` | boolean | 上传：手动上传新版本

### B. 工具速查表

| #  | 工具名 | 分类 | 功能 | 必填参数 |
|----|--------|------|------|----------|
| 1  | `create_file` | 写文档 | 在云盘下新建文件或文件夹 | `drive_id`, `parent_id`, `file_type`, `name` |
| 2  | `scrape_url` | 写文档 | 网页剪藏，抓取网页内容并自动保存为智能文档 | `url` |
| 3  | `scrape_progress` | 写文档 | 查询网页剪藏任务进度 | `job_id` |
| 4  | `upload_file` | 写文档 | 全量上传写入文件（更新已有 docx/pdf 或新建并上传本地文件） | `drive_id`, `parent_id`, `content_base64` |
| 5  | `upload_attachment` | 写文档 | 向已有文档上传附件，支持 URL 或 Base64 | `file_id`, `filename` |
| 6  | `list_files` | 读文档 | 获取指定文件夹下的子文件列表 | `drive_id`, `parent_id`, `page_size` |
| 7  | `download_file` | 读文档 | 获取文件下载信息 | `drive_id`, `file_id` |
| 8  | `move_file` | 管文档 | 批量移动文件(夹) | `drive_id`, `file_ids`, `dst_drive_id`, `dst_parent_id` |
| 9  | `rename_file` | 管文档 | 重命名文件（夹） | `drive_id`, `file_id`, `dst_name` |
| 10  | `copy_file` | 管文档 | 复制文件到指定目录（可跨盘） | `drive_id`, `file_id`, `dst_drive_id`, `dst_parent_id` |
| 11  | `check_file_name` | 管文档 | 检查目录下文件名是否已存在 | `drive_id`, `parent_id`, `name` |
| 12  | `share_file` | 管文档 | 开启文件分享 | `drive_id`, `file_id`, `scope` |
| 13  | `set_share_permission` | 管文档 | 修改分享链接属性 | `link_id` |
| 14  | `cancel_share` | 管文档 | 取消文件分享 | `drive_id`, `file_id` |
| 15  | `get_share_info` | 管文档 | 获取分享链接信息 | `link_id` |
| 16  | `get_file_info` | 管文档 | 获取文件（夹）详细信息 | `file_id` |
| 17  | `list_labels` | 管文档 | 分页获取云盘自定义标签列表（可按归属者、标签类型筛选） | `page_size` |
| 18  | `create_label` | 管文档 | 创建自定义标签 | `allotee_type`, `name` |
| 19  | `get_label_meta` | 管文档 | 获取单个标签详情（含系统标签固定 ID） | `label_id` |
| 20  | `get_label_objects` | 管文档 | 获取某标签下的对象列表（文件/云盘等） | `label_id`, `object_type`, `page_size` |
| 21  | `batch_add_label_objects` | 管文档 | 批量为多个文档对象添加同一标签（打标签） | `label_id`, `objects` |
| 22  | `batch_remove_label_objects` | 管文档 | 批量取消标签 | `label_id`, `objects` |
| 23  | `batch_update_label_objects` | 管文档 | 批量更新标签下对象排序或属性 | `label_id`, `objects` |
| 24  | `batch_update_labels` | 管文档 | 批量修改自定义标签名称或属性 | `labels` |
| 25  | `list_star_items` | 管文档 | 获取收藏（星标）列表 | `page_size` |
| 26  | `batch_create_star_items` | 管文档 | 批量添加收藏 | `objects` |
| 27  | `batch_delete_star_items` | 管文档 | 批量移除收藏 | `objects` |
| 28  | `list_latest_items` | 管文档 | 获取最近访问文档列表 | `page_size` |
| 29  | `list_deleted_files` | 管文档 | 获取回收站文件列表 | `page_size` |
| 30  | `restore_deleted_file` | 管文档 | 将回收站文件还原到原位置 | `file_id` |
| 31  | `read_file_content` | 用文档 | 文档内容抽取为 Markdown/纯文本 | `drive_id`, `file_id` |
| 32  | `search_files` | 用文档 | 文件（夹）搜索 | `type`, `page_size` |
| 33  | `get_file_link` | 用文档 | 获取文件的云文档在线访问链接 | `file_id` |

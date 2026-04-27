# 演示文稿操作

## 1. wpp.execute

#### 功能说明

在在线演示文稿中执行 JSAPI，提供对演示文稿操作的**原子能力**，如：
- 幻灯片操作（添加版式页、删除、复制粘贴、获取数量）
- 插入形状（矩形、圆形、三角形、圆角矩形等）

详细功能清单和使用场景请参考 [wpp_execute/execute.md](wpp_execute/execute.md)。

### 使用原则（重要）

**何时使用**：
- ✅ **优先选择**：需要对演示文稿进行幻灯片增删、形状插入等操作时
- ✅ 需要使用已定义的原子能力时

**使用要求**：
1. **严格遵循工作流**：必须按照 [wpp_execute/execute.md](wpp_execute/execute.md) 中的 **"使用工作流"** 步骤执行
2. **使用已有模板**：只能使用已提供的功能模板，禁止随意生成或自创脚本
3. **功能检查优先**：执行前必须在功能清单中确认功能是否支持，不支持的功能应明确告知用户
4. **统一 try/catch**：所有脚本执行时必须用 try/catch 包裹，返回统一的 `{ok, message, data}` 结构


#### 调用示例

添加指定版式幻灯片到第2页：

```json
{
  "file_id": "file_xxx",
  "command": "addLayoutSlide",
  "param": {
    "slideIndex": 2,
    "layout": 2
  }
}
```

删除第3张幻灯片：

```json
{
  "file_id": "file_xxx",
  "command": "deleteSlide",
  "param": {
    "slideIndex": 3
  }
}
```

复制第1张幻灯片到第3页位置：

```json
{
  "file_id": "file_xxx",
  "command": "copyPasteSlide",
  "param": {
    "slideIndex": 1,
    "pasteIndex": 3
  }
}
```

获取幻灯片数量：

```json
{
  "file_id": "file_xxx",
  "command": "getSlidesCount",
  "param": {}
}
```

在第1张幻灯片插入矩形：

```json
{
  "file_id": "file_xxx",
  "command": "addRectangle",
  "param": {
    "slideIndex": 1,
    "left": 100,
    "top": 100,
    "width": 200,
    "height": 200
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `command` (string, 必填): 命令名称，用于标识要执行的操作类型。可选值：
- `addLayoutSlide`：添加指定版式幻灯片
- `deleteSlide`：删除幻灯片
- `copyPasteSlide`：复制粘贴幻灯片
- `getSlidesCount`：获取幻灯片数量
- `addRectangle`：插入矩形
- `addOval`：插入圆形
- `addTriangle`：插入三角形
- `addRoundedRectangle`：插入圆角矩形

- `param` (object, 可选): 命令参数对象，不同 command 对应不同字段。具体参数见各命令的详情文档

#### 返回值说明

```json
成功：
```json
{"ok": true, "message": "success", "data": null}
```

失败：
```json
{"ok": false, "message": "Slides.Item: index out of range", "data": null}
```

获取幻灯片数量：
```json
{"ok": true, "message": "success", "data": 5}
```

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | boolean | 操作是否成功 |
| `message` | string | 成功为 `success`，失败为错误信息 |
| `data` | any | 返回数据，因命令而异 |


#### 操作约束

- **前置检查**：执行前必须在功能清单中确认功能是否支持
- **提示**：只能使用已提供的功能模板，禁止随意生成或自创脚本
- **幂等**：否 — 非幂等操作，重试前需确认当前幻灯片状态

---


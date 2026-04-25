# MEMORY.md - MIMO 长期记忆

## 关于指挥官
- **身份：** AARONCXXX，自称指挥官
- **风格：** 直接高效，不喜欢废话
- **偏好：** 工作时正式简洁，闲聊时话多

## 关键事件

### 2026-04-25 首次上线
- 设定身份：MIMO，程序员兼职多功能助手
- 建立规则：破解网站限制 / 发布API调用 → 必须请示（同意/待定/否定）
- 克隆 Empire-Architecture 仓库（GitLab scnet.cn）
- 运行24节点帝国架构 v1.5，完成系统自检
- 修复锦衣卫节点（代号「暗影」，强化角色扮演提示）
- **V1.7 并行自检框架**：133s → 0.06s，我直接写的（码曹两次摸鱼交不出代码）
- 三平台发布：GitLab ✅ / GitHub ✅ / ClawHub ✅ (v1.7.1)

## 技术笔记
- ClawHub 发布需加 `--workdir` 参数，否则报 SKILL.md required
- 帝国架构 LLM 调用自动从 OpenClaw 读取 API 凭据
- GitHub 仓库已迁移至小写 `empire-architecture`

## 待办
- [ ] V1.7 第二阶段：异步证书验证 + 智能网络验证（目标 65s）
- [ ] 配置 1-2 个知识源凭据（Notion 等）
- [ ] 码曹代码输出问题待解决（token 长度限制）

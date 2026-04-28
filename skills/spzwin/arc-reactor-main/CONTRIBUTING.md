# CONTRIBUTING.md — ARC Reactor 协作规范

所有 Agent（Codex / Claude Code / OpenClaw 子 Agent / 人类）必须遵守。

## 多 Agent 同一账户注意事项

所有 Agent 共用 `evan-zhang` 账户。以下规则确保不撞车：

- **分支名必须加 Agent 前缀**（见下方命名规范），避免推到同一个分支
- **Commit message 末尾标注作者**：`(by Codex)` / `(by Claude)` / `(by Orchestrator)`
- **先 fetch 再 push**：`git fetch origin` 确保本地最新
- **Git 并发保护**：如果两个 Agent push 同一分支，第二个会被拒绝（fast-forward 检查）

## 工作流

```
① gh issue list（先查有没有相关 Issue）
② gh issue create（没有就新建，描述清楚要改什么）
③ 在 Issue 上评论 "认领 by {agent-name}"（避免重复劳动）
④ git fetch origin && git checkout -b {agent-prefix}/{number}-{简述} origin/main
⑤ 写代码 + 测试
⑥ git push origin {agent-prefix}/{number}-{简述}
⑦ gh pr create --base main（标题写 Closes #{number}）
⑧ 审查自己的 PR（见下方审查清单）
⑨ gh pr merge（合入）
⑩ 通知用户新功能已上线
```

## 铁律

1. **永远从最新 main 拉分支**：`git fetch origin && git rebase origin/main`
2. **禁止直接 push main**：Branch Protection 已开启，force push 会被拒绝
3. **禁止跳过 PR**：所有改动必须走 PR，哪怕是一行修复
4. **改之前先查 Issue**：`gh issue list` 看有没有人已经在做了
5. **PR 合入前必须审查**：见下方审查清单

## PR 审查清单

合入自己的 PR 之前，必须确认：

- [ ] `git diff main...HEAD --stat` 看改了哪些文件
- [ ] 没有误删已有功能（特别是 `archive-manager.py`）
- [ ] `python3 scripts/archive-manager.py --help` 功能完整
- [ ] 没有跟其他 open PR 冲突（`gh pr list`）
- [ ] 如果有冲突：先 rebase 最新 main 再合

## 冲突处理

如果 PR 跟其他 PR 冲突：
1. `git fetch origin && git rebase origin/main`
2. 解决冲突
3. `git push origin {branch} --force-with-lease`（在自己的分支上 force push 是安全的）
4. 重新检查后合入

## Issue 命名规范

- `feat: xxx` — 新功能
- `fix: xxx` — 修 bug
- `refactor: xxx` — 重构
- `docs: xxx` — 文档
- `chore: xxx` — 杂项

## 分支命名规范

必须加 Agent 前缀，避免撞车：

- `codex/{number}-{简短描述}` — Codex Agent 的分支
- `claude/{number}-{简短描述}` — Claude Code Agent 的分支
- `orchestrator/{number}-{简短描述}` — 编排者的分支
- `manual/{number}-{简短描述}` — 人工操作

例：`codex/22-multi-kb`、`claude/27-fact-index`

## 谁来 Review？

当前阶段：Agent 自审 + 功能验证。
未来：可以配置 CODEOWNERS 要求交叉审查。

# 发布检查清单

发版前建议逐项检查当前单 Skill 包。

## 结构检查

- `huifu-payment-integration/SKILL.md` 是否是唯一正式 Skill 入口
- `references/` 是否保持单层平铺，不再依赖旧目录跳转
- Skill 包内是否已移除本地 PHP 模板资产和非官方自维护 client
- 是否已经移除二维码等非 Skill 必需资源

## 规范检查

- `SKILL.md` frontmatter 是否只使用 Agent Skills 规范允许字段
- `name` 是否与目录名一致
- `description` 是否说明“做什么”和“什么时候用”
- `agents/openai.yaml` 是否已生成且与主 Skill 当前口径一致
- 主 `SKILL.md` 是否控制在 `500` 行以内

## 内容检查

- 托管支付 Java SDK 版本是否仍为 `3.0.36`
- 聚合支付 Java SDK 版本是否仍为 `1.0.5`
- PHP SDK 包基线是否仍为 `huifurepo/dg-php-sdk 2.0.26`，并且安装、升级、备用下载口径一致
- 前端 JS SDK 是否避免描述为“最新版”，并写清以项目锁定版本接入、升级前查询 npm registry
- `HUIFU_SKILL_SOURCE` 是否都写成 `<skill_source>`
- 逐页接口文档里的公共请求参数段，是否都明确写出 `jpt-x-skill-source` 约束
- 逐页接口文档是否都写清“Java 与 PHP 都要求 `jpt-x-skill-source`，且在 `data.huifu_id` 存在时都要带 `jpt-x-skill-huifu_id`；当前 Java SDK 基线自动补，当前 Skill 包对齐的官方 PHP SDK 主链路在 `MerConfig.skill_source` 已配置时也会自动补”
- 聚合支付 PHP 覆盖边界是否已明确为下单、扫码交易查询、关单、关单查询、退款、退款查询、对账
- 前端回调不等于最终支付成功的边界是否在主 Skill 和 checkout 文档里都已保留

## 上传检查

- Skill 内是否只包含 `SKILL.md`、`agents/`、`references/`
- 是否没有把仓库开发期校验脚本目录打进 Skill 包
- 是否没有把仓库级 `README.md`、`CHANGELOG.md`、`docs/`、`LICENSE` 当作 Skill 必需内容

## 校验检查

- 已执行 `python3 scripts/validate_skills.py`
- 所有相对路径引用都存在
- 删除旧目录后，文档中没有残留旧目录名的失效路径

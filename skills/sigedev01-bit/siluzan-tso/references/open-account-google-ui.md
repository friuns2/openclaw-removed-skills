# Google 开户：网页交互与 CLI 对照（/openAnAccount）

> 路由：`{webUrl}/v3/foreign_trade/tso/openAnAccount?mediaType=Google&...`  
> 前端组件：`openAnAccount.vue` + 顶部流程条 `GGOPASteps.vue`

---

## 一、页面顶部「五步」是什么？

与**表单分步**不是同一套数字，但语义连贯：

| 步骤 | 文案（意译） | 用户要做什么                       | CLI / Skill 能做什么                                          |
| ---- | ------------ | ---------------------------------- | ------------------------------------------------------------- |
| ①    | 准备开户资料 | 准备公司名、网址、类型、账户信息等 | 说明清单；**无法**代替用户准备资质                            |
| ②    | 填写申请     | 网页里完成第 1、2 步表单并提交     | **`open-account google-wizard`** 或 **`open-account google`** |
| ③    | 等待审核     | 等待媒体/平台审核                  | **`account-history -m Google`** 轮询                          |
| ④    | 审核通过     | 查看通过结果                       | 同上                                                          |
| ⑤    | 充值并激活   | **必须在网页完成充值**             | 引导 `config show` → `webUrl` + 充值路径（见 `finance.md`）   |

页面上还有提示：**美元账户最低充值约 100 USD、人民币约 700 CNY**（以实际页面为准）。

---

## 二、网页里实际填表是「两步」

### 第 1 步（企业 / 推广信息）

| 网页控件 | 说明                                         | CLI 对应                                       |
| -------- | -------------------------------------------- | ---------------------------------------------- |
| 公司名称 | 文本，可联想已有广告主                       | `--company`                                    |
| 网址     | 左侧下拉 `https://` / `http://` + 右侧输入框 | `--promotion-link`（可只写域名，CLI 会补协议） |
| 类型     | 单选 **B2B / B2C / APP**                     | `--promotion-type`：`b2b` \| `b2c` \| `app`    |
| 行业级联 | 当前前端已隐藏                               | 可选 `--industry1` / `--industry2`             |

提交第 1 步后，后台会**创建或更新广告主组**并拿到 `magKey`；CLI 已内置该逻辑，**无需**用户自己查 `magKey`。

### 第 2 步（广告账户表格，与下拉菜单一致）

| 网页控件 | 说明                                              | CLI 对应                                                 |
| -------- | ------------------------------------------------- | -------------------------------------------------------- |
| 账户名称 | 文本，默认与公司名一致                            | `--account-name`                                         |
| 币种     | 下拉：**CNY / USD**（HKD 对代理商场景为禁用）     | `--currency`：`CNY` \| `USD`                             |
| 时区     | 下拉：文案为 **`(Time)Name`**，值为 **IANA Code** | `--timezone`；列表用 **`open-account google-timezones`** |
| 开户数量 | 1～3，且多行总和 ≤3（网页表格）                   | `--counts`（1～3）                                       |
| 开户邮箱 | 接收 Google 账户邀请的邮箱（不限 Gmail / `.com`） | `--invite-email`                                         |

**币种 ↔ 默认时区（与网页 `changeCurrency` 一致）**

- 选 **CNY** → 默认 **`Asia/Shanghai`**
- 选 **USD**（或其它非 CNY）→ 默认 **`Asia/Hong_Kong`**

其它时区请从 **`siluzan-tso open-account google-timezones`** 里取 **Code** 列（与网页下拉同一接口）。

---

## 三、推荐用法

### 1）非交互提交（Agent / 脚本首选）

```bash
# 常用时区速查（无需每次运行 google-timezones）：
# Asia/Shanghai      北京/上海（CNY 默认）
# Asia/Hong_Kong     香港（USD 默认）
# America/New_York   美东
# America/Los_Angeles 美西
# Europe/London      伦敦
# 完整列表：siluzan-tso open-account google-timezones [--keyword <关键词>]

siluzan-tso open-account google \
  --company "某某公司" \
  --promotion-link "https://www.example.com" \
  --promotion-type b2c \
  --account-name "某某公司-美国投放" \
  --currency USD \
  --timezone "America/New_York" \
  --invite-email "user@gmail.com" \
  --counts 1
```

### 2）交互向导（人工终端操作，需要真实 TTY）

```bash
# 注意：需要真实终端，CI / 管道 / AI Agent 环境下无法使用
siluzan-tso open-account google-wizard
```

### 3）审核与后续

```bash
# 轮询审核进度
siluzan-tso account-history -m Google

# 提交后需在网页查看/确认：开户记录（勿用 manageAccounts）
# {webUrl}/v3/foreign_trade/tso/accountOpeningHistory?tso=%2Fv3umijs%2Ftso%2FaccountOpeningHistory
# （非交互 `open-account google` 成功时 CLI 也会打印该链接）

# 审核通过后，充值激活（必须网页完成）
# siluzan-tso config show 取 webUrl，打开：{webUrl}/v3/foreign_trade/tso/recharge
# 美元账户最低约 100 USD，人民币账户约 700 CNY
```

---

## 四、给 AI Agent 的简短指令模板

当用户说「我要在丝路赞开 Google 户」时：

1. 收集必填字段：公司名、推广网址、推广类型、账户名、币种、时区、邀请邮箱。
2. 时区未知时，先给出常用时区表（见上方速查），或运行 `open-account google-timezones --keyword <关键词>` 辅助选择。
3. 拼一条 `open-account google` 非交互命令提交。
4. 提交后：`account-history -m Google` 轮询进度。
5. 审核通过后：引导充值激活，给出充值网页路径（见第三步）。

---

## 五、相关命令速查

| 命令                            | 作用                                    |
| ------------------------------- | --------------------------------------- |
| `open-account google-wizard`    | 交互向导（对齐网页两步表单 + 五步说明） |
| `open-account google-timezones` | 时区列表（网页下拉同源）                |
| `open-account google`           | 非交互一次性提交                        |
| `account-history -m Google`     | 开户审核进度                            |

更完整的参数表见 `accounts.md` → **open-account** 章节。

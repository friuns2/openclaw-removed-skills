# CLI 使用技巧：--json + Node.js 精准查询

> 所有 `siluzan-tso` 命令都支持 `--json` 输出原始 JSON。
> 结合 `node -e` 单行代码，可实现过滤、提取、汇总等复杂查询，无需额外依赖。

---

## 基础模式：`--json` + `node -e` 管道

### 过滤特定字段

```bash
# 只看 Google 账户的 mediaCustomerId 和账户名
siluzan-tso list-accounts -m Google --json | node -e "
const d = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
d.forEach(a => console.log(a.mediaCustomerId, a.mediaCustomerName));
"
```

Windows 下用临时文件替代管道（PowerShell 管道传 JSON 时编码不稳定）：

```powershell
siluzan-tso list-accounts -m Google --json > tmp.json
node -e "
const d = JSON.parse(require('fs').readFileSync('tmp.json','utf8'));
d.forEach(a => console.log(a.mediaCustomerId, a.mediaCustomerName));
"
```

---

## 常用场景示例

### 1. 从账户列表提取特定账户的 ID

```bash
# 找出名称包含 "Brand A" 的账户 ID
siluzan-tso list-accounts -m Google --json > /tmp/accounts.json
node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/accounts.json','utf8'));
const target = list.find(a => a.mediaCustomerName.includes('Brand A'));
console.log(target ? target.mediaCustomerId : 'not found');
"
```

### 2. 余额低于阈值的账户告警

```bash
siluzan-tso balance -m Google --json > /tmp/bal.json
node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/bal.json','utf8'));
const low = list.filter(a => Number(a.balance) < 100);
if (low.length === 0) { console.log('所有账户余额充足'); process.exit(0); }
console.log('⚠️ 余额不足账户：');
low.forEach(a => console.log(' ', a.mediaCustomerId, a.mediaCustomerName, '余额:', a.balance, a.currencyCode));
"
```

### 3. 汇总消耗数据

```bash
# 计算所有 Google 账户过去 7 天总消耗
siluzan-tso stats -m Google --days 7 --json > /tmp/stats.json
node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/stats.json','utf8'));
const total = list.reduce((sum, a) => sum + Number(a.cost ?? 0), 0);
const clicks = list.reduce((sum, a) => sum + Number(a.clicks ?? 0), 0);
console.log('总消耗:', total.toFixed(2), '  总点击:', clicks);
list.sort((a, b) => Number(b.cost) - Number(a.cost))
    .slice(0, 5)
    .forEach(a => console.log(' ', a.mediaCustomerId, a.mediaCustomerName, a.cost));
"
```

### 4. 从广告系列列表提取 ID

```bash
siluzan-tso ad campaigns -a <mediaCustomerId> --json > /tmp/campaigns.json
node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/campaigns.json','utf8'));
// 找出状态为 ENABLED 的系列
list.filter(c => c.status === 'ENABLED')
    .forEach(c => console.log(c.id, c.name));
"
```

### 5. 检查预警规则是否已存在（避免重复创建）

```bash
siluzan-tso forewarning list -m Google --json > /tmp/fw.json
node -e "
const rules = JSON.parse(require('fs').readFileSync('/tmp/fw.json','utf8'));
const name = '日消耗预警';
const exists = rules.some(r => r.name === name);
console.log(exists ? '已存在，跳过创建' : '不存在，可以创建');
"
```

### 6. 从 ad smart prepare 输出提取关键词列表

```bash
siluzan-tso ad smart prepare -a <accountId> --url "https://example.com" -w "shoes" --json > /tmp/aigc.json
node -e "
const data = JSON.parse(require('fs').readFileSync('/tmp/aigc.json','utf8'));

// 按月搜索量排序，取前 15 个
const top = data.keywordIdeas
  .sort((a, b) => (b.monthlySearch ?? 0) - (a.monthlySearch ?? 0))
  .slice(0, 15)
  .map(k => k.keyword);

console.log('推荐关键词（逗号分隔，可直接用于 keyword-create）：');
console.log(top.join(','));
console.log('');
console.log('行业:', data.industry?.industryName, '/ 语言ID:', data.industry?.languageId);
console.log('账户货币:', data.account?.currencyCode);
"
```

### 7. 根据地区预算比例计算各地区日预算

```bash
node -e "
const data = JSON.parse(require('fs').readFileSync('/tmp/aigc.json','utf8'));
const totalBudget = 200; // 总日预算（USD）
const currency = data.account?.currencyCode ?? 'USD';

console.log('地区预算分配（总预算', totalBudget, currency + '）：');
data.budgetProportions.forEach(bp => {
  const budget = (totalBudget * bp.budgetProportion).toFixed(2);
  console.log(' ', bp.areaCode, '(' + bp.regionCodes.join(', ') + '):', budget, currency, '('+ (bp.budgetProportion * 100).toFixed(0) + '%)');
});
"
```

### 8. 查找某个 entityId（解绑/分享操作前必须用）

```bash
# 注意：account delink / account share 需要 entityId，不是 mediaCustomerId
siluzan-tso list-accounts -m Google --json > /tmp/accounts.json
node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/accounts.json','utf8'));
const keyword = 'Brand A';  // 替换为账户名关键词
const match = list.filter(a => a.mediaCustomerName.includes(keyword));
match.forEach(a => {
  console.log('mediaCustomerName:', a.mediaCustomerName);
  console.log('mediaCustomerId:  ', a.mediaCustomerId);  // 用于 balance/stats/ad
  console.log('entityId:         ', a.entityId ?? a.id); // 用于 account delink/share
  console.log('---');
});
"
```

---

## 多命令串联（将中间结果存文件）

对于需要多步骤的操作，将每步的 `--json` 输出存到临时文件，后续步骤读取使用：

```bash
# 步骤 1：获取账户列表，提取目标账户 ID
siluzan-tso list-accounts -m Google --json > /tmp/step1.json
ACCOUNT_ID=$(node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/step1.json','utf8'));
const t = list.find(a => a.mediaCustomerName.includes('Brand A'));
process.stdout.write(t ? t.mediaCustomerId : '');
")

# 步骤 2：用提取到的 ID 查询广告系列
siluzan-tso ad campaigns -a "$ACCOUNT_ID" --json > /tmp/step2.json

# 步骤 3：提取第一个启用的系列 ID
CAMPAIGN_ID=$(node -e "
const list = JSON.parse(require('fs').readFileSync('/tmp/step2.json','utf8'));
const c = list.find(c => c.status === 'ENABLED');
process.stdout.write(c ? c.id : '');
")

echo "Account: $ACCOUNT_ID  Campaign: $CAMPAIGN_ID"
```

Windows PowerShell 等效写法：

```powershell
siluzan-tso list-accounts -m Google --json | Out-File tmp.json -Encoding UTF8
$accountId = node -e "
const list = JSON.parse(require('fs').readFileSync('tmp.json','utf8'));
const t = list.find(a => a.mediaCustomerName.includes('Brand A'));
process.stdout.write(t ? t.mediaCustomerId : '');
"
siluzan-tso ad campaigns -a $accountId --json | Out-File tmp2.json -Encoding UTF8
```

---

## 调试技巧

### 查看原始 API 响应结构（`--verbose`）

```bash
# --verbose 会把请求 URL 和原始响应输出到 stderr
siluzan-tso list-accounts -m Google --json --verbose 2>&1 | head -50
```

### 验证 JSON 格式是否正确

```bash
siluzan-tso list-accounts -m Google --json | node -e "
try {
  const d = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('✓ 有效 JSON，共', d.length ?? Object.keys(d).length, '条记录');
  console.log('字段列表:', Object.keys(d[0] ?? d));
} catch(e) { console.error('✗ JSON 解析失败:', e.message); }
"
```

### 查看所有可用字段（探索未知响应结构）

```bash
siluzan-tso ad batch list --json | node -e "
const d = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
const first = Array.isArray(d) ? d[0] : d;
console.log('可用字段：');
Object.entries(first ?? {}).forEach(([k,v]) => console.log(' ', k, ':', JSON.stringify(v)?.slice(0,60)));
"
```

---

## 通用分页与查询建议

- 绝大多数列表类命令默认每页 20 条记录，数据量较大时建议显式指定分页参数。
- 建议在拉取大批量数据时使用命令自带的 `--page-size`（如设置为 `100`）与 `--page` 组合翻页，确认无更多数据后再停止，避免遗漏。

---

## AI Agent 使用规范

- **优先用 `--json` 而不是解析人类友好输出**：文字输出格式可能变化，JSON 结构稳定。
- **中间结果用文件传递**：跨步骤数据不要靠记忆，写到 `/tmp/` 或当前目录。
- **Windows 上避免直接管道 JSON**：PowerShell 管道可能改变编码，用 `Out-File -Encoding UTF8` + 读文件替代。
- **用 `process.stdout.write` 而不是 `console.log` 提取单个值**：前者不带换行符，方便直接赋给 shell 变量。
- **节点代码复杂时拆分写法**：不要写超过 10 行的 `node -e` 单行，改用 `node -e "$(cat <<'EOF'\n...\nEOF\n)"`。

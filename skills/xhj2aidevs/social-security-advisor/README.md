# social-security-advisor 内部技术文档

> ⚠️ 本文件仅供开发维护参考，**不在发布包中包含**。

## 计算器脚本

```bash
# 职工社保
python scripts/social_security_calculator.py --city 城市名 --salary 月工资

# 灵活就业
python scripts/social_security_calculator.py --city 城市名 --type flex --base-rate 80

# 查看支持城市
python scripts/social_security_calculator.py --list-cities

# 养老金测算
python scripts/social_security_calculator.py --retirement \
  --city 北京 --years 30 --avg-index 0.8 --retire-age 60
```

## 自学习机制

- 经验文件：`data/social_security_learn.json`
- 热门城市追踪、热门险种追踪、热门模块追踪
- 补贴类型自发现、城市名自发现
- 失败恢复：连续失败3次后自动将发现的城市/险种临时加入推荐列表

```bash
python scripts/self_learning.py --stats
python scripts/self_learning.py --success "北京" "养老保险" "缴费计算"
python scripts/self_learning.py --failure "城市不在脚本支持列表中"
python scripts/self_learning.py --reset
```

## 2026年重大政策变化速览

1. 灵活就业参保无需户籍+无需挂靠
2. 缴费基数下限降至社平工资50%
3. 4050补贴"终身一次制"
4. 失业金与4050补贴不可同时领取
5. 平台经济职业伤害保险试点扩围
6. 国办发25号文应届毕业生25%社保补贴

## 补贴价值示例

| 城市 | 人群 | 每月补贴 | 最长可领总额 |
|------|------|---------|------------|
| 北京 | 4050人员 | ≈1250元/月 | 约4.5万元（3年） |
| 广州 | 困难人员 | 800元/月固定 | 约4.8万元（5年） |
| 杭州 | 困难人员 | 实际缴费2/3 | ≈年最高3200元 |

## 更新日志

- v2.0.2：ClawdHub审核合规修复
- v2.0.0：补贴优惠查询模块 + 2026年政策更新
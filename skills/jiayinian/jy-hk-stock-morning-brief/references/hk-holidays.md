# 港股假期日历参考

## 2026 年港股交易假期

以下日期港股市场休市（数据来源：港交所）：

### 元旦
- 2026-01-01（星期四）

### 春节
- 2026-02-17（星期二）
- 2026-02-18（星期三）
- 2026-02-19（星期四）

### 清明节
- 2026-04-06（星期一）

### 复活节
- 2026-04-03（星期五）耶稣受难节
- 2026-04-04（星期六）复活节
- 2026-04-06（星期一）复活节星期一

### 劳动节
- 2026-05-01（星期五）

### 佛诞
- 2026-05-25（星期一）

### 端午节
- 2026-06-19（星期五）

### 国庆节
- 2026-10-01（星期四）
- 2026-10-02（星期五）

### 中秋节
- 2026-09-25（星期五）

### 圣诞节
- 2026-12-25（星期五）
- 2026-12-26（星期六） Boxing Day
- 2026-12-28（星期一）补假

## 交易日判断逻辑

```python
def is_hk_trading_day(date_str):
    """
    判断是否为港股交易日
    """
    from datetime import datetime
    
    date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # 周末休市
    if date.weekday() >= 5:  # 周六=5, 周日=6
        return False
    
    # 港股假期（根据年份动态加载）
    hk_holidays_2026 = [
        "2026-01-01",
        "2026-02-17", "2026-02-18", "2026-02-19",
        "2026-04-03", "2026-04-04", "2026-04-06",
        "2026-05-01", "2026-05-25",
        "2026-06-19",
        "2026-09-25",
        "2026-10-01", "2026-10-02",
        "2026-12-25", "2026-12-26", "2026-12-28",
    ]
    
    if date_str in hk_holidays_2026:
        return False
    
    return True


def get_previous_trading_day(date_str=None):
    """
    获取前一个港股交易日
    """
    from datetime import datetime, timedelta
    
    if date_str:
        target = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target = datetime.now()
    
    # 向前追溯，直到找到交易日
    days_back = 1
    while True:
        candidate = target - timedelta(days=days_back)
        candidate_str = candidate.strftime("%Y-%m-%d")
        if is_hk_trading_day(candidate_str):
            return candidate_str
        days_back += 1
        # 防止无限循环
        if days_back > 30:
            raise Exception("无法找到前一个交易日")
```

## 半日市

港股在以下日期可能为半日市（上午交易，下午休市）：

- 除夕（12 月 31 日）
- 农历除夕
- 圣诞节前夕（12 月 24 日）

半日市交易时间：09:30 - 12:00

## 备注

1. 假期安排以港交所官方公告为准
2. 如遇特殊情况（如台风、暴雨），港交所可能临时宣布休市
3. 北向资金（港股通）在内地假期也会休市，需注意两地假期差异

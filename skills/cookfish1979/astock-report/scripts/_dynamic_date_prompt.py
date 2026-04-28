"""生成含动态日期的cron prompt片段（供晨报/晚报/收盘小结使用）"""
from datetime import datetime, timedelta

def today_str():
    return datetime.now().strftime("%Y年%m月%d日")

def yesterday_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y年%m月%d日")

# 晨报prompt第一步：自动获取今日/昨日日期
MORNING_STEP1 = f"""第一步：先运行以下命令获取今日和昨日日期：
```bash
python3 -c "from datetime import datetime, timedelta; t=datetime.now(); print('TODAY='+t.strftime('%Y年%m月%d日')+' YESTERDAY='+(t-timedelta(days=1)).strftime('%Y年%m月%d日'))"
```
将输出的TODAY（如{today_str()}）记为{{{{TODAY}}}}，YESTERDAY记为{{{{YESTERDAY}}}}，随后所有搜索必须使用这两个日期，不得使用其他日期。"""

EVENING_STEP1 = f"""第一步：先运行以下命令获取今日日期：
```bash
python3 -c "from datetime import datetime; print(datetime.now().strftime('%%Y年%%m月%%d日'))"
```
将输出的日期记为{{{{TODAY}}}}（如{today_str()}），随后所有搜索必须使用该日期，不得使用其他日期。"""

CLOSE_STEP1 = f"""第一步：先运行以下命令获取今日和昨日日期：
```bash
python3 -c "from datetime import datetime, timedelta; t=datetime.now(); print('TODAY='+t.strftime('%Y年%m月%%d日')+' YESTERDAY='+(t-timedelta(days=1)).strftime('%%Y年%%m月%%d日'))"
```
将输出的TODAY记为{{{{TODAY}}}}，YESTERDAY记为{{{{YESTERDAY}}}}，随后所有搜索和报告标题必须使用这两个日期，不得使用其他日期。"""

if __name__ == "__main__":
    print("=== 晨报日期 ===")
    print(MORNING_STEP1)
    print("=== 晚报日期 ===")
    print(EVENING_STEP1)
    print("=== 收盘小结日期 ===")
    print(CLOSE_STEP1)

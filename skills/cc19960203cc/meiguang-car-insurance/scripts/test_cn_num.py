# -*- coding: utf-8 -*-
import inspect, sys
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts')
from run_extract import chinese_num

# Get source
src = inspect.getsource(chinese_num)
with open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\cn_func.txt', 'w', encoding='utf-8') as f:
    f.write(src)
print(src)

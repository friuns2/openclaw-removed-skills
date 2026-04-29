# -*- coding: utf-8 -*-
"""清理太平洋手机号正则的重复项"""
import io

fpath = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py'
with io.open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove duplicate 联\s*系\s*电\s*话 patterns (keep only one per safe_extract block)
# Pattern: two consecutive 联\s*系\s*电\s*话 lines
content = content.replace(
    'r"联\\s*系\\s*电\\s*话[：:\\s]*(1[3-9][\\d\\*]{9,14})",\n        r"联\\s*系\\s*电\\s*话[：:\\s]*(1[3-9][\\d\\*]{9,14})",',
    'r"联\\s*系\\s*电\\s*话[：:\\s]*(1[3-9][\\d\\*]{9,14})",'
)

with io.open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)
print('done')

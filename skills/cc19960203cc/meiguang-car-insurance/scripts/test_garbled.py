# -*- coding: utf-8 -*-
import io
with io.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
result = []
for i in range(1055, min(1095, len(lines))):
    result.append(f'{i+1}: {repr(lines[i])}')
with io.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\check_block.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
print('done')

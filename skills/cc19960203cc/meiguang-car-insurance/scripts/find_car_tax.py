# -*- coding: utf-8 -*-
import io
with io.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
result = []
for i in range(1030, min(1110, len(lines))):
    result.append(f'{i+1}: {repr(lines[i])}')
with io.open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\huai_block.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
print('Done', len(lines), 'total lines')

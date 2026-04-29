# -*- coding: utf-8 -*-
import io, re

fpath = r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py'
with io.open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find NATURE_LIST definition
idx = content.find('NATURE_LIST')
print(f'NATURE_LIST at {idx}')
if idx >= 0:
    print(repr(content[idx:idx+300]))

# Find what the pattern looks like
idx2 = content.find('NATURE_PATTERN')
print(f'\nNATURE_PATTERN at {idx2}')
if idx2 >= 0:
    print(repr(content[idx2:idx2+200]))

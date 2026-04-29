# -*- coding: utf-8 -*-
with open('run_extract.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "当年应缴（车船税）garbled" and replace it
for i, l in enumerate(lines):
    if '当年应缴（车船税）garbled' in l:
        print(f"Found at line {i+1}: {l.rstrip()}")
        # Find and replace the next ~25 lines
        for j in range(i+1, min(i+30, len(lines))):
            print(f"  {j+1}: {lines[j].rstrip()}")
        break

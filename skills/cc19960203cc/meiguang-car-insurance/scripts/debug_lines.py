# -*- coding: utf-8 -*-
with open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py', 'rb') as f:
    content = f.read()

# Find all occurrences of 保险起期 pattern with YYYY-MM-DD and add 年月日 version
# The current pattern is: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}...)"
# We need to add before it: r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日...)",

# Pattern to find: the YYYY-MM-DD 保险起期 line (with escape sequences)
# In bytes: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}
target = b'r"\xe4\xbf\x9d\xe9\x99\x86\xe8\xb5\xb7\xe6\x9c\x9f[：:\s]*(\xe5\xb9\xb4\xe5\x8d\x81\xe4\xb8\x80\xe6\x9c\x88'

# Check if this target is in content
print('Year format pattern in content:', target in content)

# Also check the existing YYYY-MM-DD pattern
target2 = b'r"\xe4\xbf\x9d\xe9\x99\x86\xe8\xb5\xb7\xe6\x9c\x9f[：:\s]*(\xd4\xed'
print('YYYY-MM-DD pattern in content:', target2 in content)

# Count occurrences
count_yyyy = content.count(b'\xd4\xed-\xd4\xed-\xd4\xed')  # YYYY-MM-DD in bytes
print('YYYY-MM-DD occurrences in 保险起期 context:', count_yyyy)

# Find all 保险起期 safe_extract blocks
import re
text = content.decode('utf-8', errors='replace')

# Find: safe_extract(text, [...r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}...
# We want to add r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日...
# right before the YYYY-MM-DD version

# Pattern to find and replace in the raw bytes
# The structure is: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}
# This appears in the file as the Python source code

# Since we can't easily do this with regex on bytes, let's find the exact byte positions
# and insert the new pattern before each occurrence

# Count how many times 保险起期 with YYYY-MM-DD appears
count = text.count(r'保险起期[：:\s]*(\d{4}-\d{2}-\d{2}')
print('Count of 保险起期 YYYY-MM-DD patterns:', count)

# Find all positions
positions = []
idx = 0
while True:
    idx = text.find(r'保险起期[：:\s]*(\d{4}-\d{2}-\d{2}', idx)
    if idx < 0:
        break
    positions.append(idx)
    idx += 1

print('Positions:', positions[:5])
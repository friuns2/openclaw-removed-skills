# -*- coding: utf-8 -*-
with open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of 保险起期 with YYYY-MM-DD pattern and add 年月日 version
# Pattern: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}
# Add before it: r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日

import re

# Find and replace all occurrences
# The pattern in the file looks like: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}
# We need to insert a 年月日 version before each occurrence

new_content = content

# For 保险起期 - add 年月日 pattern before YYYY-MM-DD
# Pattern: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}
# New: r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日...),\n        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}...

# For 保险止期 - same

# The key is to find each safe_extract block that contains 保险起期 YYYY-MM-DD pattern
# and add the 年月日 version before it

# Use a simple text replacement approach
# Find: r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",
# Replace with: r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日(?:\s+\d{2}:\d{2}:\d{2})?)",\n        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",

old_pattern = r'        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",'
new_pattern = r'''        r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日(?:\s+\d{2}:\d{2}:\d{2})?)",
        r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",'''

if old_pattern in content:
    new_content = content.replace(old_pattern, new_pattern, 1)  # Only first to test
    changed = 'replaced (first occurrence)'
else:
    changed = 'NOT FOUND - trying without leading spaces'

# Try without specific indentation
old2 = r'r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",'
if old2 in new_content:
    new2 = r'r"保险起期[：:\s]*(\d{4}年\d{2}月\d{2}日(?:\s+\d{2}:\d{2}:\d{2})?)",\n    r"保险起期[：:\s]*(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)",'
    new_content = new_content.replace(old2, new2)
    changed = 'replaced with no-indent version'

print(f'Change result: {changed}')
print(f'Replacements made: {content.count(new_pattern) if new_pattern in new_content else 0}')

with open(r'C:\Users\Administrator\.openclaw\workspace\skills\meiguang-car-insurance\scripts\run_extract.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('done')
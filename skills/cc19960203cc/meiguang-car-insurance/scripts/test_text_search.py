import pdfplumber, os, re
import sys
sys.path.insert(0, '.')
from run_extract import safe_extract

folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)

with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

print('Text length:', len(text))
print()

# Find the insurance period line
for i, line in enumerate(text.split('\n')):
    if '365' in line or ('保险期间' in line and '2026' in line):
        print(f'Line {i}: {repr(line[:80])}')

# Search for the exact insurance period text
idx = text.find('保险期间')
print()
print('保险期间 found at:', idx)
if idx >= 0:
    print('Around it:', repr(text[idx:idx+80]))

# Try searching in the WHOLE text (not just first 200 chars)
# Search for '365天起'
idx2 = text.find('365天起')
print()
print('365天起 found at:', idx2)

# Search for '从2026'
idx3 = text.find('从2026')
print('从2026 found at:', idx3)

# Try searching for just '365'
idx4 = text.find('365')
print('365 (first) found at:', idx4)
if idx4 >= 0:
    print('Around 365:', repr(text[idx4:idx4+60]))

# The insurance period line should have 365, 2026, 2027
# Let's find lines that have ALL THREE
print()
print('Lines with 365 AND 2026 AND 2027:')
for i, line in enumerate(text.split('\n')):
    has_365 = '365' in line
    has_2026 = '2026' in line
    has_2027 = '2027' in line
    if has_365 and has_2026 and has_2027:
        print(f'  Line {i}: {repr(line[:80])}')
        # Also try the pattern on this line
        pat = r'保险期间：365天起，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止'
        m = re.search(pat, line)
        print(f'  Pattern match: {m}')
        if m:
            print(f'  Groups: {repr(m.group(1))} {repr(m.group(2))}')

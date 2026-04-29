import pdfplumber, os, re
import sys
sys.path.insert(0, '.')
from run_extract import route_type

folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)

with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

print('Filename:', fname)
print('Text length:', len(text))
print('First 200 chars:', repr(text[:200]))
print()

rt = route_type(text)
print('route_type:', repr(rt))

# What does parse_changxing do with this text?
from run_extract import parse_changxing, safe_extract

# Test the 司乘险 pattern directly on text
pat = r'保险期间：365天起，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止'
m = re.search(pat, text)
print()
print('Pattern match in text:', m)
if m:
    print('Groups:', repr(m.group(1)), repr(m.group(2)))

# What does safe_extract return for the first pattern?
result = safe_extract(text, [pat])
print('safe_extract result:', repr(result))

# Now call parse_changxing directly
try:
    result2 = parse_changxing(text, p)
    print()
    print('parse_changxing result keys:')
    for k, v in result2.items():
        if v:
            print(f'  {k}: {repr(str(v)[:60])}')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()

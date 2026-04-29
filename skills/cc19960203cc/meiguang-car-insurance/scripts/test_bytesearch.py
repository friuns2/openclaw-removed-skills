import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)

with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Search the FULL text for the insurance period pattern
# Try both with and without 从
patterns = [
    r'保险期间：365天起，从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止',
    r'365天起，从?(\d{4}年\d{2}月\d{2}日)零时起至',
    r'365天起(\d{4}年)',
    r'365天起',
]

for pat in patterns:
    m = re.search(pat, text)
    print(f'Pattern {repr(pat[:40])}: {bool(m)}')
    if m:
        print(f'  Matched: {repr(m.group(0)[:50])}')

# Also check: what is the actual substring in the text that looks like it should match?
# Find '保险期间' in the full text
idx = text.find('保险期间')
print()
print(f'保险期间 at {idx}')
print('Around it:', repr(text[idx:idx+50]))

# Try with bytes
text_bytes = text.encode('utf-8')
# Search for the bytes of '365天起，从'
target = '365天起，从'.encode('utf-8')
print()
print('Searching for', target, 'in text bytes')
print('Found:', target in text_bytes)

# What if it's '365天起，' without 从?
target2 = '365天起，'.encode('utf-8')
print('Searching for', target2)
print('Found:', target2 in text_bytes)

# What ARE the bytes between 365 and 2026?
idx_365 = text_bytes.find(b'365')
print()
print('Bytes from 365 to 2026:', text_bytes[idx_365:idx_365+20])

import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

print('Text len:', len(text))

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line:
        print('LINE:', repr(line[:100]))
        break

# Test the pattern directly
# The exact text is: 保险期间：365天起，2026年04月22日零时起至2027年04月21日二十四时止。
pat = r'保险期间：365天起[，,]\s*(\d{4}年\d{2}月\d{2}日)[\s\xa0]*零时起至(\d{4}年\d{2}月\d{2}日)[\s\xa0]*二十四时止'
m = re.search(pat, text)
print('Match:', m)
if m:
    print('Groups:', repr(m.group(1)), repr(m.group(2)))
    print('Combined:', m.group(1) + ' 至 ' + m.group(2))

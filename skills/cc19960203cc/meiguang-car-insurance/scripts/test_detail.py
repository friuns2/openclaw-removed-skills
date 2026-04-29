import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)

with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line and '2027' in line:
        print('Insurance period line:', repr(line[:80]))
        
        # Find the exact position of 365 and what follows
        idx_365 = line.find('365')
        print()
        print('After 365 (20 chars):', repr(line[idx_365:idx_365+20]))
        print('After 365 (40 bytes):', line[idx_365:idx_365+40].encode('utf-8'))
        
        # What characters are between , and 2 in 2026?
        idx_2026 = line.find('2026')
        print()
        print('Char before 2026:', repr(line[idx_2026-1]), 'ord:', ord(line[idx_2026-1]))
        print('Chars 3 before 2026:', repr(line[idx_2026-3:idx_2026]))
        print('Chars 5 before 2026:', repr(line[idx_2026-5:idx_2026]))
        print('Chars 10 before 2026:', repr(line[idx_2026-10:idx_2026]))
        
        # The bytes
        start = idx_2026 - 5
        seg = line[start:idx_2026+5]
        print()
        print('Segment bytes:', seg.encode('utf-8'))
        
        # Check each char
        for i, c in enumerate(seg):
            print(f'  [{start+i}] {c!r} U+{ord(c):04X}')
        
        # Now try the regex
        pat = r'保险期间：365天起,从?(\d{4}年\d{2}月\d{2}日)零时起至(\d{4}年\d{2}月\d{2}日)二十四时止'
        m = re.search(pat, line)
        print()
        print('Regex match:', m)
        if m:
            print('Groups:', m.group(1), m.group(2))
        
        break

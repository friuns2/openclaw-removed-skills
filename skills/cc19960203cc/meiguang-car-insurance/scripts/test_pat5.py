import pdfplumber, os, re
folder = r'C:\Users\Administrator\Desktop\车险保单'
fname = [f for f in os.listdir(folder) if '司乘' in f and f.endswith('(1).pdf')][0]
p = os.path.join(folder, fname)
with pdfplumber.open(p) as pdf:
    text = pdf.pages[0].extract_text()

# Find the insurance period line
for line in text.split('\n'):
    if '365' in line and '2026' in line and '2027' in line:
        print('LINE repr:', repr(line[:90]))
        
        # Find the exact substring
        idx = line.find('从')
        print()
        print('Looking for 从 (U+4ECE):')
        print('  idx of 从:', idx)
        if idx >= 0:
            print('  char[idx]:', repr(line[idx]), 'ord:', ord(line[idx]))
        
        # Also try to find where 365天起，is
        idx2 = line.find('365')
        print()
        print('365 at:', idx2)
        print('Chars 365 to 2026:', repr(line[idx2:idx2+15]))
        
        # Check if there's 从 between 365天起，and 2026
        seg = line[idx2:idx2+20]
        print('Segment:', repr(seg))
        print('Bytes:', seg.encode('utf-8'))
        
        # Now test the regex pattern WITHOUT 从
        # The pattern I'm trying: 保险期间：365天起，(\d{4}年\d{2}月\d{2}日)
        pat1 = r'保险期间：365天起，(\d{4}年\d{2}月\d{2}日)'
        m1 = re.search(pat1, line)
        print()
        print('Pattern1 (without 从):', m1)
        
        # With 从 allowed
        pat2 = r'保险期间：365天起.，?(\d{4}年\d{2}月\d{2}日)'
        m2 = re.search(pat2, line)
        print('Pattern2 (with .，?):', m2)
        
        # The actual pattern
        pat3 = r'保险期间：365天起，(\d{4}年\d{2}月\d{2}日)'
        m3 = re.search(pat3, line)
        print('Pattern3 (exact match):', m3)
        
        # Try finding 365 followed by any char then 年
        pat4 = r'365.{1,5}年'
        m4 = re.search(pat4, line)
        print('Pattern4 (365...年):', m4)
        if m4:
            print('  Matched:', repr(m4.group(0)))
        
        break
